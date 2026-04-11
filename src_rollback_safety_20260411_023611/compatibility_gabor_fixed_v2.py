"""
REVISED STRATEGY: Gabor Spectral Diversity as Secondary Discriminator

PROBLEM WITH FIRST APPROACH:
  Penalizing homogeneous textures affects BOTH same-artifact and cross-artifact pairs
  equally, because brown pottery from the same artifact is also homogeneous.

REVISED APPROACH:
  Instead of penalizing low diversity directly, use diversity as a CONSISTENCY CHECK:

  - If Gabor BC is suspiciously high (>0.95) AND both are homogeneous
    → This suggests two SIMILAR-looking but DIFFERENT homogeneous surfaces
    → Apply "suspiciously-similar" penalty

  - If Gabor BC is high AND at least one has structure
    → This is genuinely similar texture (same artifact)
    → No penalty

  Rationale:
    Same artifact → fragments have BOTH similar appearance AND similar local context
    Different artifacts → may have similar appearance but different local context

    The "suspiciously similar" penalty catches cases where the signature is TOO perfect
    (1.0000) for two supposedly independent surfaces.

IMPLEMENTATION:
  1. Keep original Gabor computation (no changes)
  2. Add suspiciously_similar_penalty() function
  3. Apply at final scoring stage ONLY when BC > 0.95 and both homogeneous
  4. Penalty factor: 0.7 (less aggressive than 0.5)

This is more conservative and targets only the suspiciously-perfect matches.
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
FOURIER_WEIGHT = 0.25
FOURIER_SEGMENT_ORDER = 8

# Appearance-based multiplicative penalty weights
POWER_COLOR = 4.0
POWER_TEXTURE = 2.0
POWER_GABOR = 2.0
POWER_HARALICK = 2.0

COLOR_HIST_BINS_HUE = 16
COLOR_HIST_BINS_SAT = 4

# Spectral diversity thresholds (REVISED)
SPECTRAL_DIVERSITY_THRESHOLD = 0.15
SUSPICIOUS_SIMILARITY_THRESHOLD = 0.95  # BC > this triggers check
SUSPICIOUS_SIMILARITY_PENALTY = 0.7     # More conservative than 0.5


def edit_distance(seq_a: List[int], seq_b: List[int]) -> int:
    """Dynamic-programming edit distance."""
    m, n = len(seq_a), len(seq_b)
    if m == 0 or n == 0:
        return max(m, n)
    dp = np.zeros((m + 1, n + 1), dtype=int)
    dp[:, 0] = np.arange(m + 1)
    dp[0, :] = np.arange(n + 1)
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if seq_a[i - 1] == seq_b[j - 1] else 1
            dp[i, j] = min(dp[i - 1, j] + 1, dp[i, j - 1] + 1, dp[i - 1, j - 1] + cost)
    return int(dp[m, n])


def segment_similarity(
    seg_a: np.ndarray, seg_b: np.ndarray,
    kappa_a: Optional[np.ndarray] = None,
    kappa_b: Optional[np.ndarray] = None,
    bonus_good_continuation: bool = False,
) -> float:
    """Curvature-profile cross-correlation with anti-parallel matching."""
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
    """HSV color histogram."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [COLOR_HIST_BINS_HUE, COLOR_HIST_BINS_SAT], [0, 180, 0, 256])
    hist = hist.flatten().astype(np.float32)
    return hist / (hist.sum() + 1e-8)


def compute_lbp_texture_signature(image: np.ndarray, radius: int = 3, n_points: int = 24) -> np.ndarray:
    """Local Binary Pattern texture descriptor."""
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
    """Compute Gabor filter bank response signature."""
    if len(image.shape) == 3:
        image_float = image.astype(np.float32) / 255.0
    else:
        image_float = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0

    features = []
    for scale in range(1, n_scales + 1):
        wavelength = 2 ** (scale + 1)
        for theta in np.linspace(0, np.pi, n_orientations, endpoint=False):
            kernel = cv2.getGaborKernel(
                ksize=(31, 31), sigma=wavelength * 0.56, theta=theta,
                lambd=wavelength, gamma=0.5, psi=0,
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
    Returns coefficient of variation (std/mean) of orientation-specific responses.
    """
    if len(gabor_signature) == 0:
        return 0.0

    means = gabor_signature[::2]  # Extract mean values
    means_reshaped = means.reshape(n_scales, n_orientations, n_channels)
    orientation_responses = means_reshaped.mean(axis=(0, 2))

    mean_resp = orientation_responses.mean()
    std_resp = orientation_responses.std()

    if mean_resp < 1e-8:
        return 0.0

    return float(std_resp / mean_resp)


def compute_haralick_signature(image: np.ndarray, distances: list = [1, 3, 5]) -> np.ndarray:
    """Compute Haralick GLCM texture features."""
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
    glcm = graycomatrix(gray_quantized, distances=distances, angles=angles,
                       levels=64, symmetric=True, normed=True)

    features = []
    for prop in ['contrast', 'correlation', 'energy', 'homogeneity']:
        features.extend(graycoprops(glcm, prop).ravel())

    return np.array(features, dtype=np.float32)


def compute_lab_color_signature(image: np.ndarray, bins_l: int = 8, bins_ab: int = 8) -> np.ndarray:
    """Compute perceptually uniform Lab color histogram."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    hist = cv2.calcHist([lab], [0, 1, 2], None, [bins_l, bins_ab, bins_ab], [0, 256, 0, 256, 0, 256])
    hist = hist.flatten().astype(np.float32)
    return hist / (hist.sum() + 1e-8)


def color_bhattacharyya(sig_a: np.ndarray, sig_b: np.ndarray) -> float:
    """Bhattacharyya coefficient for color histograms."""
    if len(sig_a) == 0 or len(sig_b) == 0:
        return 1.0
    sig_a_norm = sig_a / (sig_a.sum() + 1e-8)
    sig_b_norm = sig_b / (sig_b.sum() + 1e-8)
    bc = float(np.sum(np.sqrt(np.clip(sig_a_norm * sig_b_norm, 0, None))))
    return float(np.clip(bc, 0.0, 1.0))


def appearance_bhattacharyya(sig_a: np.ndarray, sig_b: np.ndarray) -> float:
    """Bhattacharyya coefficient between two feature signatures."""
    if len(sig_a) == 0 or len(sig_b) == 0:
        return 1.0
    sig_a_norm = sig_a / (sig_a.sum() + 1e-8)
    sig_b_norm = sig_b / (sig_b.sum() + 1e-8)
    bc = float(np.sum(np.sqrt(np.clip(sig_a_norm * sig_b_norm, 0, None))))
    return float(np.clip(bc, 0.0, 1.0))


def suspiciously_similar_penalty(bc_gabor: float, diversity_a: float, diversity_b: float) -> float:
    """
    Apply penalty for suspiciously-similar homogeneous textures (REVISED STRATEGY).

    If Gabor BC is very high (>0.95) AND both textures are homogeneous,
    this suggests two different but visually-similar homogeneous surfaces.

    Same artifact → would have contextual differences preventing perfect BC
    Different artifacts → can have perfect BC due to lack of distinctive features

    Returns: penalty factor (1.0 = no penalty, <1.0 = apply penalty)
    """
    both_homogeneous = (diversity_a < SPECTRAL_DIVERSITY_THRESHOLD and
                       diversity_b < SPECTRAL_DIVERSITY_THRESHOLD)

    if bc_gabor > SUSPICIOUS_SIMILARITY_THRESHOLD and both_homogeneous:
        logger.debug(
            "Suspiciously similar: BC=%.4f, div_A=%.3f, div_B=%.3f → penalty=%.2f",
            bc_gabor, diversity_a, diversity_b, SUSPICIOUS_SIMILARITY_PENALTY
        )
        return SUSPICIOUS_SIMILARITY_PENALTY

    return 1.0  # no penalty


def segment_fourier_score(seg_a: np.ndarray, seg_b: np.ndarray, order: int = FOURIER_SEGMENT_ORDER) -> float:
    """Fourier descriptor distance for global segment shape."""
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
    """Build appearance similarity matrices (with diversity tracking)."""
    n = len(images)
    color_sigs, texture_sigs, gabor_sigs, gabor_diversities, haralick_sigs = [], [], [], [], []

    logger.info("Computing appearance signatures for %d fragments...", n)
    for i, img in enumerate(images):
        color_sigs.append(compute_lab_color_signature(img))
        texture_sigs.append(compute_lbp_texture_signature(img))

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

    matrices = {
        'color': np.ones((n, n), dtype=float),
        'texture': np.ones((n, n), dtype=float),
        'gabor': np.ones((n, n), dtype=float),
        'haralick': np.ones((n, n), dtype=float),
        'gabor_diversity': gabor_diversities,
    }

    for i in range(n):
        for j in range(i + 1, n):
            bc_color = appearance_bhattacharyya(color_sigs[i], color_sigs[j])
            bc_texture = appearance_bhattacharyya(texture_sigs[i], texture_sigs[j])
            bc_gabor_raw = appearance_bhattacharyya(gabor_sigs[i], gabor_sigs[j])
            bc_haralick = appearance_bhattacharyya(haralick_sigs[i], haralick_sigs[j])

            # Apply suspiciously-similar penalty (REVISED)
            gabor_penalty = suspiciously_similar_penalty(
                bc_gabor_raw, gabor_diversities[i], gabor_diversities[j]
            )
            bc_gabor = bc_gabor_raw * gabor_penalty

            matrices['color'][i, j] = matrices['color'][j, i] = bc_color
            matrices['texture'][i, j] = matrices['texture'][j, i] = bc_texture
            matrices['gabor'][i, j] = matrices['gabor'][j, i] = bc_gabor
            matrices['haralick'][i, j] = matrices['haralick'][j, i] = bc_haralick

            logger.debug(
                "Pair (%d, %d): color=%.3f, texture=%.3f, gabor=%.3f (raw=%.3f, penalty=%.2f), haralick=%.3f",
                i, j, bc_color, bc_texture, bc_gabor, bc_gabor_raw, gabor_penalty, bc_haralick
            )

    return matrices


def compute_compatibility_matrix(
    contours: List[np.ndarray],
    images: List[np.ndarray],
    min_segment_length: int = 20,
    use_fourier: bool = True,
) -> np.ndarray:
    """
    REVISED: Gabor filter with suspiciously-similar penalty for homogeneous textures.
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
                bc_gabor = appearance_mats['gabor'][i, j]  # Already has penalty applied
                bc_haralick = appearance_mats['haralick'][i, j]

                appearance_penalty = (
                    bc_color ** POWER_COLOR *
                    bc_texture ** POWER_TEXTURE *
                    bc_gabor ** POWER_GABOR *
                    bc_haralick ** POWER_HARALICK
                )

                final_score = score_geom * appearance_penalty

                logger.debug(
                    "Pair (%d, %d): geom=%.3f, app_penalty=%.3f → final=%.3f",
                    i, j, score_geom, appearance_penalty, final_score
                )
            else:
                final_score = score_geom

            C[i, j] = C[j, i] = final_score

    return C
