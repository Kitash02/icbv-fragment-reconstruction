"""
Pairwise edge-compatibility scoring between fragment boundary segments.

CRITICAL FIX (Stage 1.7): Gabor Spectral Diversity Penalty
============================================================

Problem:
  The Gabor filter in compatibility.py (lines 253-283) returns bc_gabor = 1.0000
  for ALL brown/beige artifact pairs, providing ZERO discrimination.

Root Cause:
  Gabor filters measure oriented frequency similarity via mean+std across scales/orientations.
  When normalized to probability distributions for Bhattacharyya coefficient, homogeneous
  brown surfaces (papyrus, pottery, scrolls) produce nearly identical normalized signatures
  because:
    - All have similar frequency content (low variance in brown/beige)
    - All have similar mean responses (uniform lighting)
    - Normalization removes absolute scale information

  Result: BC ≈ 1.0 for both same-artifact AND cross-artifact brown pairs.

Solution:
  Add spectral diversity metric that measures orientation-specific variance:
    - Homogeneous surfaces → low variance across orientations → diversity penalty
    - Structured surfaces → high variance across orientations → no penalty

  Final score: bc_gabor_raw × spectral_diversity_factor

  Where:
    diversity_A = std(mean_responses_per_orientation) / mean(mean_responses_per_orientation)
    diversity_B = similar for fragment B

    If both < threshold (0.15): both homogeneous → penalty = 0.5
    Else: at least one has structure → penalty = 1.0 (no change)

Expected Impact:
  - Negative accuracy: 77.8% → 88-92% (eliminate 4-5 of 7 false positives)
  - Positive accuracy: 77.8% → 77-80% (minimal impact on true matches)
  - Overall: 77.8% → 85-88%

This fix corresponds to texture discrimination principles from Lecture 21-23
(Early Vision: texture analysis requires second-order statistics beyond simple
mean/std aggregation).
"""

import cv2
import numpy as np
import logging
from typing import List, Optional

from chain_code import compute_curvature_profile
from hard_discriminators import hard_reject_check

logger = logging.getLogger(__name__)

GOOD_CONTINUATION_SIGMA = 0.5
GOOD_CONTINUATION_WEIGHT = 0.10
FOURIER_WEIGHT = 0.25          # global shape complement to local curvature
FOURIER_SEGMENT_ORDER = 8      # number of Fourier coefficients per segment

# Appearance-based multiplicative penalty weights (Stage 1.7 - Gabor fixed)
POWER_COLOR = 4.0      # Primary discriminator (pigment chemistry)
POWER_TEXTURE = 2.0    # Secondary discriminator (material texture)
POWER_GABOR = 2.0      # Tertiary discriminator (oriented patterns) - NOW FIXED
POWER_HARALICK = 2.0   # Quaternary discriminator (second-order texture)

COLOR_HIST_BINS_HUE = 16       # hue bins in HSV histogram
COLOR_HIST_BINS_SAT = 4        # saturation bins in HSV histogram

# Spectral diversity thresholds (NEW)
SPECTRAL_DIVERSITY_THRESHOLD = 0.15   # coefficient of variation threshold
HOMOGENEOUS_PENALTY = 0.5              # penalty when both textures are homogeneous


def edit_distance(seq_a: List[int], seq_b: List[int]) -> int:
    """
    Dynamic-programming edit distance between two integer sequences.
    """
    m, n = len(seq_a), len(seq_b)
    if m == 0 or n == 0:
        return max(m, n)
    dp = np.zeros((m + 1, n + 1), dtype=int)
    dp[:, 0] = np.arange(m + 1)
    dp[0, :] = np.arange(n + 1)
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if seq_a[i - 1] == seq_b[j - 1] else 1
            dp[i, j] = min(
                dp[i - 1, j] + 1,
                dp[i, j - 1] + 1,
                dp[i - 1, j - 1] + cost,
            )
    return int(dp[m, n])


def segment_similarity(
    seg_a: np.ndarray,
    seg_b: np.ndarray,
    kappa_a: Optional[np.ndarray] = None,
    kappa_b: Optional[np.ndarray] = None,
    bonus_good_continuation: bool = False,
) -> float:
    """
    Curvature-profile cross-correlation with anti-parallel matching.
    """
    if kappa_a is None:
        kappa_a = compute_curvature_profile(seg_a)
    if kappa_b is None:
        kappa_b = compute_curvature_profile(seg_b)

    if len(kappa_a) == 0 or len(kappa_b) == 0:
        return 0.0

    def circular_correlation(x: np.ndarray, y: np.ndarray) -> float:
        if len(x) == 0 or len(y) == 0:
            return 0.0
        n = max(len(x), len(y))
        x_pad = np.pad(x, (0, n - len(x)), mode='wrap')
        y_pad = np.pad(y, (0, n - len(y)), mode='wrap')
        x_fft = np.fft.fft(x_pad)
        y_fft = np.fft.fft(y_pad)
        corr_fft = x_fft * np.conj(y_fft)
        corr = np.fft.ifft(corr_fft).real
        peak = np.max(corr)
        norm = np.sqrt(np.sum(x_pad**2) * np.sum(y_pad**2))
        return float(peak / norm) if norm > 1e-9 else 0.0

    score_forward = circular_correlation(kappa_a, kappa_b)
    score_antiparallel = circular_correlation(kappa_a, -kappa_b[::-1])
    base_score = max(score_forward, score_antiparallel)

    if bonus_good_continuation and len(seg_a) > 1 and len(seg_b) > 1:
        tangent_a = seg_a[-1] - seg_a[-2]
        tangent_b = seg_b[0] - seg_b[-1]
        tangent_a = tangent_a / (np.linalg.norm(tangent_a) + 1e-9)
        tangent_b = tangent_b / (np.linalg.norm(tangent_b) + 1e-9)
        kink = float(np.arctan2(
            tangent_a[0]*tangent_b[1] - tangent_a[1]*tangent_b[0],
            tangent_a[0]*tangent_b[0] + tangent_a[1]*tangent_b[1]
        ))
        continuation_bonus = np.exp(-0.5 * (kink / GOOD_CONTINUATION_SIGMA)**2)
        base_score = (1 - GOOD_CONTINUATION_WEIGHT) * base_score + \
                     GOOD_CONTINUATION_WEIGHT * continuation_bonus

    return float(np.clip(base_score, 0.0, 1.0))


def compute_hsv_histogram(image: np.ndarray) -> np.ndarray:
    """
    HSV color histogram (Hue × Saturation bins).
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist(
        [hsv], [0, 1], None,
        [COLOR_HIST_BINS_HUE, COLOR_HIST_BINS_SAT],
        [0, 180, 0, 256]
    )
    hist = hist.flatten().astype(np.float32)
    return hist / (hist.sum() + 1e-8)


def compute_lbp_texture_signature(image: np.ndarray, radius: int = 3, n_points: int = 24) -> np.ndarray:
    """
    Local Binary Pattern (LBP) texture descriptor.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    h, w = gray.shape
    lbp = np.zeros_like(gray, dtype=np.uint8)

    for i in range(radius, h - radius):
        for j in range(radius, w - radius):
            center = gray[i, j]
            code = 0
            for p in range(n_points):
                angle = 2 * np.pi * p / n_points
                x = int(round(j + radius * np.cos(angle)))
                y = int(round(i - radius * np.sin(angle)))
                if 0 <= y < h and 0 <= x < w:
                    code |= (int(gray[y, x] >= center) << p)
            lbp[i, j] = code % 256

    hist, _ = np.histogram(lbp.ravel(), bins=256, range=(0, 256))
    hist = hist.astype(np.float32)
    return hist / (hist.sum() + 1e-8)


def compute_gabor_signature(image: np.ndarray, n_scales: int = 5, n_orientations: int = 8) -> np.ndarray:
    """
    Compute Gabor filter bank response signature for oriented texture analysis.

    Gabor filters detect edges and textures at multiple scales and orientations.
    Returns mean and std of responses: 2 × n_scales × n_orientations × 3 channels = 240 features.
    """
    if len(image.shape) == 3:
        image_float = image.astype(np.float32) / 255.0
    else:
        image_float = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0

    features = []
    for scale in range(1, n_scales + 1):
        wavelength = 2 ** (scale + 1)
        for theta in np.linspace(0, np.pi, n_orientations, endpoint=False):
            kernel = cv2.getGaborKernel(
                ksize=(31, 31),
                sigma=wavelength * 0.56,
                theta=theta,
                lambd=wavelength,
                gamma=0.5,
                psi=0,
            )
            for channel in range(3):
                filtered = cv2.filter2D(image_float[:, :, channel], cv2.CV_32F, kernel)
                features.append(float(filtered.mean()))
                features.append(float(filtered.std()))

    return np.array(features, dtype=np.float32)


def compute_gabor_spectral_diversity(gabor_signature: np.ndarray, n_scales: int = 5,
                                     n_orientations: int = 8, n_channels: int = 3) -> float:
    """
    Compute spectral diversity metric from Gabor signature.

    Measures variance of mean responses across orientations (NOT across scales).
    Low diversity → homogeneous texture (papyrus, smooth pottery)
    High diversity → structured texture (cord-marked pottery, inscribed scrolls)

    Returns: coefficient of variation (std/mean) of orientation-specific mean responses
    """
    if len(gabor_signature) == 0:
        return 0.0

    # Gabor signature structure: [mean, std] × n_scales × n_orientations × n_channels
    # Total: 2 × 5 × 8 × 3 = 240 features
    # Extract only the mean values (every other feature starting at index 0)
    means = gabor_signature[::2]  # shape: (120,) = 5 scales × 8 orientations × 3 channels

    # Reshape to (n_scales, n_orientations, n_channels)
    means_reshaped = means.reshape(n_scales, n_orientations, n_channels)

    # Average across scales and channels to get orientation-specific responses
    # Shape: (n_orientations,)
    orientation_responses = means_reshaped.mean(axis=(0, 2))

    # Compute coefficient of variation (normalized std)
    mean_resp = orientation_responses.mean()
    std_resp = orientation_responses.std()

    if mean_resp < 1e-8:
        return 0.0

    cv = std_resp / mean_resp
    return float(cv)


def compute_haralick_signature(image: np.ndarray, distances: list = [1, 3, 5]) -> np.ndarray:
    """
    Compute Haralick GLCM (Gray-Level Co-occurrence Matrix) texture features.
    """
    try:
        from skimage.feature import graycomatrix, graycoprops
    except ImportError:
        logger.warning("scikit-image not available, Haralick features unavailable")
        return np.array([])

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    gray_quantized = (gray // 4).astype(np.uint8)

    angles = [0, np.pi/4, np.pi/2, 3*np.pi/4, np.pi]
    glcm = graycomatrix(
        gray_quantized,
        distances=distances,
        angles=angles,
        levels=64,
        symmetric=True,
        normed=True,
    )

    features = []
    for prop in ['contrast', 'correlation', 'energy', 'homogeneity']:
        features.extend(graycoprops(glcm, prop).ravel())

    return np.array(features, dtype=np.float32)


def compute_lab_color_signature(image: np.ndarray, bins_l: int = 8, bins_ab: int = 8) -> np.ndarray:
    """
    Compute perceptually uniform Lab color histogram.
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    hist = cv2.calcHist(
        [lab], [0, 1, 2], None,
        [bins_l, bins_ab, bins_ab],
        [0, 256, 0, 256, 0, 256]
    )
    hist = hist.flatten().astype(np.float32)
    return hist / (hist.sum() + 1e-8)


def color_bhattacharyya(sig_a: np.ndarray, sig_b: np.ndarray) -> float:
    """
    Bhattacharyya coefficient for color histograms.
    """
    if len(sig_a) == 0 or len(sig_b) == 0:
        return 1.0
    sig_a_norm = sig_a / (sig_a.sum() + 1e-8)
    sig_b_norm = sig_b / (sig_b.sum() + 1e-8)
    bc = float(np.sum(np.sqrt(np.clip(sig_a_norm * sig_b_norm, 0, None))))
    return float(np.clip(bc, 0.0, 1.0))


def appearance_bhattacharyya(sig_a: np.ndarray, sig_b: np.ndarray) -> float:
    """
    Bhattacharyya coefficient between two feature signatures (color, texture, etc).

    BC = Σ sqrt(p_i · q_i) ∈ [0, 1].
    BC = 1.0 : identical features (perfect match).
    BC ≈ 0.0 : non-overlapping features (completely different).
    """
    if len(sig_a) == 0 or len(sig_b) == 0:
        return 1.0   # uninformative — no penalty

    # Normalize to probability distributions
    sig_a_norm = sig_a / (sig_a.sum() + 1e-8)
    sig_b_norm = sig_b / (sig_b.sum() + 1e-8)

    bc = float(np.sum(np.sqrt(np.clip(sig_a_norm * sig_b_norm, 0, None))))
    return float(np.clip(bc, 0.0, 1.0))


def appearance_bhattacharyya_with_diversity(sig_a: np.ndarray, sig_b: np.ndarray,
                                            diversity_a: float, diversity_b: float) -> float:
    """
    Enhanced Bhattacharyya coefficient with spectral diversity penalty (NEW).

    If both textures are homogeneous (low spectral diversity), apply penalty.
    This discriminates between:
      - Cross-artifact brown pairs (both homogeneous) → penalty applied → lower score
      - Same-artifact textured pairs (at least one has structure) → no penalty → unchanged

    Args:
        sig_a, sig_b: Gabor feature signatures
        diversity_a, diversity_b: Spectral diversity metrics (coefficient of variation)

    Returns:
        Modified Bhattacharyya coefficient with diversity penalty
    """
    # Compute raw BC
    bc_raw = appearance_bhattacharyya(sig_a, sig_b)

    # Apply penalty if both textures are homogeneous
    if diversity_a < SPECTRAL_DIVERSITY_THRESHOLD and diversity_b < SPECTRAL_DIVERSITY_THRESHOLD:
        penalty = HOMOGENEOUS_PENALTY
        logger.debug(
            "Spectral diversity penalty applied: div_A=%.3f, div_B=%.3f, penalty=%.2f",
            diversity_a, diversity_b, penalty
        )
    else:
        penalty = 1.0  # no penalty

    return bc_raw * penalty


def segment_fourier_score(seg_a: np.ndarray, seg_b: np.ndarray, order: int = FOURIER_SEGMENT_ORDER) -> float:
    """
    Fourier descriptor distance for global segment shape.
    """
    if len(seg_a) < 3 or len(seg_b) < 3:
        return 0.0

    def fourier_descriptor(seg: np.ndarray, order: int) -> np.ndarray:
        z = seg[:, 0] + 1j * seg[:, 1]
        z_fft = np.fft.fft(z)
        n = len(z_fft)
        if n < order:
            return np.abs(z_fft[1:])
        return np.abs(z_fft[1:order+1])

    fd_a = fourier_descriptor(seg_a, order)
    fd_b = fourier_descriptor(seg_b, order)

    if len(fd_a) == 0 or len(fd_b) == 0:
        return 0.0

    min_len = min(len(fd_a), len(fd_b))
    fd_a = fd_a[:min_len]
    fd_b = fd_b[:min_len]

    fd_a = fd_a / (fd_a[0] + 1e-9)
    fd_b = fd_b / (fd_b[0] + 1e-9)

    dist = np.linalg.norm(fd_a - fd_b)
    max_dist = np.sqrt(len(fd_a)) * 2
    score = 1.0 - min(dist / max_dist, 1.0)
    return float(np.clip(score, 0.0, 1.0))


def build_appearance_matrices(images: List[np.ndarray]):
    """
    Build appearance similarity matrices (FIXED: Gabor with spectral diversity).

    Returns:
        dict: {
            'color': matrix,
            'texture': matrix,
            'gabor': matrix (NOW FIXED with diversity penalty),
            'haralick': matrix,
            'gabor_diversity': list of diversity values per fragment
        }
    """
    n = len(images)
    color_sigs = []
    texture_sigs = []
    gabor_sigs = []
    gabor_diversities = []  # NEW
    haralick_sigs = []

    logger.info("Computing appearance signatures for %d fragments...", n)
    for i, img in enumerate(images):
        color_sigs.append(compute_lab_color_signature(img))
        texture_sigs.append(compute_lbp_texture_signature(img))

        # Compute Gabor signature and diversity
        gabor_sig = compute_gabor_signature(img)
        gabor_sigs.append(gabor_sig)
        diversity = compute_gabor_spectral_diversity(gabor_sig)
        gabor_diversities.append(diversity)

        haralick_sigs.append(compute_haralick_signature(img))

        logger.info(
            "Fragment %d features: color=%d, texture=%d, gabor=%d (diversity=%.3f), haralick=%d",
            i, len(color_sigs[-1]), len(texture_sigs[-1]),
            len(gabor_sigs[-1]), diversity, len(haralick_sigs[-1])
        )

    # Build similarity matrices
    matrices = {
        'color': np.ones((n, n), dtype=float),
        'texture': np.ones((n, n), dtype=float),
        'gabor': np.ones((n, n), dtype=float),
        'haralick': np.ones((n, n), dtype=float),
        'gabor_diversity': gabor_diversities,  # NEW: expose diversity values
    }

    for i in range(n):
        for j in range(i + 1, n):
            bc_color = appearance_bhattacharyya(color_sigs[i], color_sigs[j])
            bc_texture = appearance_bhattacharyya(texture_sigs[i], texture_sigs[j])

            # NEW: Use diversity-aware Gabor comparison
            bc_gabor = appearance_bhattacharyya_with_diversity(
                gabor_sigs[i], gabor_sigs[j],
                gabor_diversities[i], gabor_diversities[j]
            )

            bc_haralick = appearance_bhattacharyya(haralick_sigs[i], haralick_sigs[j])

            matrices['color'][i, j] = matrices['color'][j, i] = bc_color
            matrices['texture'][i, j] = matrices['texture'][j, i] = bc_texture
            matrices['gabor'][i, j] = matrices['gabor'][j, i] = bc_gabor
            matrices['haralick'][i, j] = matrices['haralick'][j, i] = bc_haralick

            logger.debug(
                "Pair (%d, %d): color=%.3f, texture=%.3f, gabor=%.3f (div: %.3f, %.3f), haralick=%.3f",
                i, j, bc_color, bc_texture, bc_gabor,
                gabor_diversities[i], gabor_diversities[j], bc_haralick
            )

    return matrices


def compute_compatibility_matrix(
    contours: List[np.ndarray],
    images: List[np.ndarray],
    min_segment_length: int = 20,
    use_fourier: bool = True,
) -> np.ndarray:
    """
    FIXED: Gabor filter now includes spectral diversity penalty.

    Main compatibility matrix computation with appearance-based discrimination.
    """
    n = len(contours)
    C = np.zeros((n, n), dtype=float)

    if len(images) != n:
        logger.warning("Image count (%d) != contour count (%d), appearance unavailable", len(images), n)
        appearance_mats = None
    else:
        appearance_mats = build_appearance_matrices(images)

    for i in range(n):
        for j in range(i + 1, n):
            if appearance_mats is not None:
                # Hard discriminator check (brown paper veto, etc)
                if not hard_reject_check(
                    i, j,
                    color_bc=appearance_mats['color'][i, j],
                    texture_bc=appearance_mats['texture'][i, j],
                    gabor_bc=appearance_mats['gabor'][i, j],
                    haralick_bc=appearance_mats['haralick'][i, j],
                ):
                    C[i, j] = C[j, i] = 0.0
                    continue

            seg_i = contours[i]
            seg_j = contours[j]

            if len(seg_i) < min_segment_length or len(seg_j) < min_segment_length:
                C[i, j] = C[j, i] = 0.0
                continue

            kappa_i = compute_curvature_profile(seg_i)
            kappa_j = compute_curvature_profile(seg_j)

            score_curvature = segment_similarity(
                seg_i, seg_j, kappa_i, kappa_j, bonus_good_continuation=True
            )

            if use_fourier:
                score_fourier = segment_fourier_score(seg_i, seg_j)
                score_geom = (1 - FOURIER_WEIGHT) * score_curvature + FOURIER_WEIGHT * score_fourier
            else:
                score_geom = score_curvature

            if appearance_mats is not None:
                bc_color = appearance_mats['color'][i, j]
                bc_texture = appearance_mats['texture'][i, j]
                bc_gabor = appearance_mats['gabor'][i, j]  # NOW FIXED
                bc_haralick = appearance_mats['haralick'][i, j]

                appearance_penalty = (
                    bc_color ** POWER_COLOR *
                    bc_texture ** POWER_TEXTURE *
                    bc_gabor ** POWER_GABOR *
                    bc_haralick ** POWER_HARALICK
                )

                final_score = score_geom * appearance_penalty

                logger.debug(
                    "Pair (%d, %d): geom=%.3f, app_penalty=%.3f "
                    "(color^4=%.3f, tex^2=%.3f, gab^2=%.3f, har^2=%.3f) → final=%.3f",
                    i, j, score_geom, appearance_penalty,
                    bc_color**POWER_COLOR, bc_texture**POWER_TEXTURE,
                    bc_gabor**POWER_GABOR, bc_haralick**POWER_HARALICK,
                    final_score
                )
            else:
                final_score = score_geom

            C[i, j] = C[j, i] = final_score

    return C
