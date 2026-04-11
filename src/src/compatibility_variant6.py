"""
Pairwise edge-compatibility scoring between fragment boundary segments.

Implements the compatibility measure described in Lecture 72 (2D Shape
Analysis) and Lecture 23 (Edge Detection), with an additional appearance
similarity term from Lecture 71 (Object Recognition).

Primary signal — Curvature Profile Cross-Correlation (Lecture 72):
  The continuous analog of first-difference chain code. Each segment's
  turning-angle sequence κ(i) = atan2(v[i]×v[i-1], v[i]·v[i-1]) is
  computed and compared via normalized circular cross-correlation (FFT).
  This is fully rotation-invariant for ANY angle — not just multiples of 45°.
  It is also O(n log n), faster than the O(n²) chain edit distance it replaces.

Secondary signal — Fourier Descriptor distance (Lecture 72):
  FFT magnitude spectrum of the pixel coordinates z[n]=x[n]+jy[n].
  Captures global segment shape; orthogonal to local curvature.

Bonus — Good Continuation (Lecture 52):
  Gestalt principle: smooth joins (low curvature change at junction) scored higher.

Penalty — Multiplicative Appearance Dissimilarity (Stage 1.6):
  Fragments from the same archaeological artifact share the same appearance.
  Multi-modal fusion: color^2 × texture^2 × gabor^2 × haralick^2
  VARIANT 6: Equal feature weighting for better positive recall.

Anti-parallel matching (physics of fragment joins):
  When two fragments meet, their edges are traversed in opposite directions.
  The curvature profile comparison therefore tests both the forward and the
  anti-parallel (reversed + negated) versions of each candidate segment.
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

# Appearance-based multiplicative penalty weights (Stage 1.6)
# VARIANT 6: All powers set to 2.0 for equal feature weighting
POWER_COLOR = 4.0      # Evolutionary test
POWER_TEXTURE = 2.0    # Equal weight
POWER_GABOR = 2.0      # Equal weight
POWER_HARALICK = 2.0   # Equal weight

COLOR_HIST_BINS_HUE = 16       # hue bins in HSV histogram
COLOR_HIST_BINS_SAT = 4        # saturation bins in HSV histogram


def edit_distance(seq_a: List[int], seq_b: List[int]) -> int:
    """
    Levenshtein edit distance between two integer sequences.

    Retained for backwards compatibility with tests and the chain-code
    representation. The primary segment matching now uses curvature
    profile cross-correlation (profile_similarity), which is both more
    accurate and faster for continuous rotation invariance.

    Implemented via single-row dynamic programming in O(m·n) time and
    O(n) space.
    """
    m, n = len(seq_a), len(seq_b)
    if m == 0:
        return n
    if n == 0:
        return m

    prev_row = list(range(n + 1))
    for i in range(1, m + 1):
        curr_row = [i] + [0] * n
        for j in range(1, n + 1):
            if seq_a[i - 1] == seq_b[j - 1]:
                curr_row[j] = prev_row[j - 1]
            else:
                curr_row[j] = 1 + min(
                    prev_row[j],
                    curr_row[j - 1],
                    prev_row[j - 1],
                )
        prev_row = curr_row

    return prev_row[n]


def _resample_profile(profile: np.ndarray, n: int) -> np.ndarray:
    """Linearly resample a 1-D profile to length n."""
    if len(profile) == n:
        return profile
    src_t = np.linspace(0.0, 1.0, len(profile))
    dst_t = np.linspace(0.0, 1.0, n)
    return np.interp(dst_t, src_t, profile)


def profile_similarity(kappa_a: np.ndarray, kappa_b: np.ndarray) -> float:
    """
    Rotation-invariant segment similarity via curvature cross-correlation.

    Algorithm (continuous analog of first-difference chain code, Lecture 72):
    -------------------------------------------------------------------------
    1. Resample both curvature profiles to the same length N.
    2. Zero-mean and unit-variance normalise each profile.
    3. Compute circular cross-correlation via FFT:
           xcorr(τ) = IFFT( FFT(κ_a) · conj(FFT(κ_b)) )  — O(N log N)
       The peak of xcorr gives the best circular shift alignment.
    4. Anti-parallel hypotheses: also compare κ_a against -κ_b[::-1]
       (reverse traversal direction, negated turning angles), which is the
       physically correct model for two fragment edges that meet.
    5. Return max peak / N as a score in [0, 1].

    Why this achieves full rotation invariance:
      κ(i) = atan2(v[i] × v[i-1], v[i] · v[i-1]) depends only on the
      *relative* angle between consecutive tangents. Rotating the entire
      segment by any angle θ adds θ to every absolute tangent angle, but
      the differences κ(i) are unchanged. No quantization, no grid artifacts.

    Straight-line segments (κ ≈ 0 everywhere) receive score 0.5 — they
    are uninformative but not clearly incompatible.
    """
    if len(kappa_a) < 2 or len(kappa_b) < 2:
        return 0.5

    n = max(len(kappa_a), len(kappa_b))
    a = _resample_profile(kappa_a, n)
    b = _resample_profile(kappa_b, n)

    def _normalise(v: np.ndarray) -> np.ndarray:
        std = v.std()
        if std < 1e-6:
            return np.zeros_like(v)
        return (v - v.mean()) / std

    a_n = _normalise(a)

    # Four hypotheses: forward / anti-parallel × original / flipped
    # Anti-parallel = reversed order + negated sign (opposite traversal)
    hypotheses = [b, -b[::-1], -b, b[::-1]]
    best_peak = -np.inf

    for candidate in hypotheses:
        b_n = _normalise(candidate)
        fa = np.fft.rfft(a_n, n=n)
        fb = np.fft.rfft(b_n, n=n)
        xcorr = np.fft.irfft(fa * np.conj(fb), n=n)
        peak = float(xcorr.max()) / n
        if peak > best_peak:
            best_peak = peak

    # Map from [-1, 1] to [0, 1]
    score = (best_peak + 1.0) / 2.0
    return float(np.clip(score, 0.0, 1.0))


def good_continuation_bonus(chain_end: List[int], chain_start: List[int]) -> float:
    """
    Gestalt good-continuation bonus at a proposed fragment join point.

    Estimates the curvature change at the junction from the final direction
    code of one segment and the initial direction code of the next. A smooth
    join (small direction change) receives a high bonus; a sharp turn receives
    near zero. Implements the good-continuation principle from Lecture 52.
    """
    if not chain_end or not chain_start:
        return 0.0
    direction_change = abs(chain_end[-1] - chain_start[0]) % 8
    normalized_change = direction_change / 4.0
    return float(np.exp(-normalized_change / GOOD_CONTINUATION_SIGMA))


def compute_color_signature(image_bgr: np.ndarray) -> np.ndarray:
    """
    Compact HSV color histogram for appearance-based fragment matching.

    Fragments from the same archaeological artifact share the same pigment
    palette. This signature captures the global color distribution in HSV
    space: hue (dominant color family) binned coarsely, plus saturation
    (vividness) to distinguish neutral grays from saturated pigments.

    Implements fragment-level appearance matching in the spirit of Lecture 71
    (Object Recognition) — colour histograms are among the simplest and most
    discriminative appearance descriptors when the lighting is consistent.

    Returns
    -------
    hist : float32 vector of length (COLOR_HIST_BINS_HUE × COLOR_HIST_BINS_SAT),
           normalized to sum to 1.
    """
    n_bins = COLOR_HIST_BINS_HUE * COLOR_HIST_BINS_SAT
    if image_bgr is None or image_bgr.size == 0:
        return np.zeros(n_bins, dtype=np.float32)

    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist(
        [hsv], [0, 1], None,
        [COLOR_HIST_BINS_HUE, COLOR_HIST_BINS_SAT],
        [0, 180, 0, 256],
    )
    hist = hist.flatten().astype(np.float32)
    total = hist.sum()
    return hist / total if total > 1e-8 else hist


def color_bhattacharyya(sig_a: np.ndarray, sig_b: np.ndarray) -> float:
    """
    Bhattacharyya coefficient between two color histogram signatures.

    BC = Σ sqrt(p_i · q_i) ∈ [0, 1].
    BC = 1.0 : identical histograms (perfect color match).
    BC ≈ 0.0 : non-overlapping color distributions (completely different images).

    Fragment pairs with BC well below 1.0 are penalized in the compatibility
    matrix, because low BC implies the fragments come from different source
    images and cannot physically belong to the same artifact.
    """
    if len(sig_a) == 0 or len(sig_b) == 0:
        return 0.5   # uninformative — no penalty
    bc = float(np.sum(np.sqrt(np.clip(sig_a, 0, None) * np.clip(sig_b, 0, None))))
    return float(np.clip(bc, 0.0, 1.0))


def compute_lbp_texture_signature(image: np.ndarray, radius: int = 3, n_points: int = 24) -> np.ndarray:
    """
    Compute rotation-invariant uniform Local Binary Pattern (LBP) texture signature.

    LBP captures micro-texture patterns robust to illumination changes.
    Returns a 26-bin histogram (rotation-invariant uniform patterns + non-uniform).
    """
    try:
        from skimage.feature import local_binary_pattern
    except ImportError:
        logger.warning("scikit-image not available, LBP texture unavailable")
        return np.array([])

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    lbp = local_binary_pattern(gray, n_points, radius, method='uniform')
    n_bins = n_points + 2  # uniform patterns + non-uniform bin
    hist, _ = np.histogram(lbp.ravel(), bins=n_bins, range=(0, n_bins), density=True)
    return hist.astype(np.float32)


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


def compute_haralick_signature(image: np.ndarray, distances: list = [1, 3, 5]) -> np.ndarray:
    """
    Compute Haralick GLCM (Gray-Level Co-occurrence Matrix) texture features.

    GLCM captures second-order texture statistics (contrast, correlation, energy, homogeneity).
    Returns 4 features × len(distances) × 5 orientations = 60 features.
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

    # Quantize to 64 levels for efficiency
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

    Lab color space is perceptually uniform (Euclidean distance ≈ perceived difference).
    Returns bins_l × bins_ab × bins_ab = 512 features (8×8×8).
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    hist = cv2.calcHist(
        [lab], [0, 1, 2], None,
        [bins_l, bins_ab, bins_ab],
        [0, 256, 0, 256, 0, 256],
    )
    hist = hist.flatten().astype(np.float32)
    total = hist.sum()
    return hist / total if total > 1e-8 else hist


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


def segment_fourier_score(
    seg_pixels_a: np.ndarray,
    seg_pixels_b: np.ndarray,
) -> float:
    """
    Global shape similarity between two pixel segments via Fourier descriptors.

    Treats each segment's pixel coordinates as a complex 1-D signal,
    computes its DFT, and compares the low-frequency magnitude spectra
    (Lecture 72 — 2D Shape Analysis). Segments with similar boundary curves
    produce similar spectra and receive a higher score.
    """
    def segment_fft(pts: np.ndarray) -> np.ndarray:
        z = pts[:, 0].astype(float) + 1j * pts[:, 1].astype(float)
        Z = np.fft.fft(z)
        Z[0] = 0.0
        scale = abs(Z[1]) if abs(Z[1]) > 1e-8 else 1.0
        return np.abs(Z[1: FOURIER_SEGMENT_ORDER + 1]) / scale

    if len(seg_pixels_a) < 2 or len(seg_pixels_b) < 2:
        return 0.0

    spec_a = segment_fft(seg_pixels_a)
    spec_b = segment_fft(seg_pixels_b)
    dist = float(np.linalg.norm(spec_a - spec_b))
    return float(1.0 / (1.0 + dist))


def _build_appearance_similarity_matrices(
    all_images: List[np.ndarray],
) -> dict:
    """
    Build symmetric (n_frags × n_frags) matrices for ALL appearance features.

    Returns dict with keys: 'color', 'texture', 'gabor', 'haralick'
    Each matrix[i, j] = Bhattacharyya coefficient for that feature modality.

    Stage 1.6: Multi-modal fusion with multiplicative penalty.
    """
    n = len(all_images)

    # Extract all feature signatures
    logger.info("Extracting appearance features from %d fragments...", n)

    color_sigs = []
    texture_sigs = []
    gabor_sigs = []
    haralick_sigs = []

    for i, img in enumerate(all_images):
        color_sigs.append(compute_lab_color_signature(img))
        texture_sigs.append(compute_lbp_texture_signature(img))
        gabor_sigs.append(compute_gabor_signature(img))
        haralick_sigs.append(compute_haralick_signature(img))

        logger.info(
            "Fragment %d features: color=%d, texture=%d, gabor=%d, haralick=%d",
            i, len(color_sigs[-1]), len(texture_sigs[-1]),
            len(gabor_sigs[-1]), len(haralick_sigs[-1])
        )

    # Build similarity matrices
    matrices = {
        'color': np.ones((n, n), dtype=float),
        'texture': np.ones((n, n), dtype=float),
        'gabor': np.ones((n, n), dtype=float),
        'haralick': np.ones((n, n), dtype=float),
    }

    for i in range(n):
        for j in range(i + 1, n):
            bc_color = appearance_bhattacharyya(color_sigs[i], color_sigs[j])
            bc_texture = appearance_bhattacharyya(texture_sigs[i], texture_sigs[j])
            bc_gabor = appearance_bhattacharyya(gabor_sigs[i], gabor_sigs[j])
            bc_haralick = appearance_bhattacharyya(haralick_sigs[i], haralick_sigs[j])

            matrices['color'][i, j] = matrices['color'][j, i] = bc_color
            matrices['texture'][i, j] = matrices['texture'][j, i] = bc_texture
            matrices['gabor'][i, j] = matrices['gabor'][j, i] = bc_gabor
            matrices['haralick'][i, j] = matrices['haralick'][j, i] = bc_haralick

    # Log statistics
    for key, mat in matrices.items():
        off_diag = mat[~np.eye(n, dtype=bool)]
        logger.info(
            "Appearance similarity (%s): min=%.3f  mean=%.3f  max=%.3f",
            key, float(off_diag.min()), float(off_diag.mean()), float(off_diag.max())
        )

    return matrices


def build_compatibility_matrix(
    all_segments: List[List[List[int]]],
    all_pixel_segments: Optional[List[List[np.ndarray]]] = None,
    all_images: Optional[List[np.ndarray]] = None,
) -> np.ndarray:
    """
    Build the full pairwise compatibility matrix over all fragment segments.

    all_segments[i][a]       — chain code segment (retained for good-continuation)
    all_pixel_segments[i][a] — pixel coordinate segment (required for curvature)
    all_images[i]            — BGR image of fragment i (required for appearance penalty)

    Returns a 4D array C of shape (n_frags, n_segs, n_frags, n_segs) where
    C[i, a, j, b] combines four signals (Lectures 23, 52, 71, 72):

      1. Curvature profile cross-correlation (PRIMARY — Lecture 72)
         Continuous, fully rotation-invariant. O(n log n) per pair.

      2. Good-continuation bonus (Lecture 52)
         Gestalt principle: smooth curvature at the join point.

      3. Fourier descriptor score (Lecture 72)
         Global segment shape via FFT magnitude spectrum.

      4. Multiplicative appearance penalty (Stage 1.6)
         Multi-modal fusion: color^2 × texture^2 × gabor^2 × haralick^2
         VARIANT 6: Equal feature weighting for better positive recall.

    Diagonal blocks (i == j) are zeroed out (no self-matching).
    Falls back to chain edit-distance if pixel segments are unavailable.
    """
    n_frags = len(all_segments)
    n_segs = max((len(segs) for segs in all_segments), default=1)
    compat = np.zeros((n_frags, n_segs, n_frags, n_segs), dtype=float)

    use_pixels = all_pixel_segments is not None

    # Pre-compute curvature profiles for all segments (avoids recomputation)
    curvature_profiles: List[List[np.ndarray]] = []
    if use_pixels:
        for pixel_segs in all_pixel_segments:
            curvature_profiles.append([
                compute_curvature_profile(ps) for ps in pixel_segs
            ])

    # Pre-compute fragment-level appearance similarity matrices (Stage 1.6)
    appearance_mats: Optional[dict] = None
    if all_images is not None:
        appearance_mats = _build_appearance_similarity_matrices(all_images)

    for frag_i, segs_i in enumerate(all_segments):
        for seg_a, chain_a in enumerate(segs_i):
            for frag_j, segs_j in enumerate(all_segments):
                if frag_i == frag_j:
                    continue

                # Track 2: Early rejection with hard discriminators
                # Check BEFORE expensive curvature computation
                if appearance_mats is not None and all_images is not None:
                    bc_color = appearance_mats['color'][frag_i, frag_j]
                    bc_texture = appearance_mats['texture'][frag_i, frag_j]

                    # Apply hard rejection check
                    if hard_reject_check(all_images[frag_i], all_images[frag_j],
                                       bc_color, bc_texture):
                        # Skip this pair - early rejection
                        continue

                for seg_b, chain_b in enumerate(segs_j):

                    if use_pixels:
                        # PRIMARY: continuous curvature cross-correlation
                        kappa_a = curvature_profiles[frag_i][seg_a]
                        kappa_b = curvature_profiles[frag_j][seg_b]
                        base = profile_similarity(kappa_a, kappa_b)

                        # SECONDARY: Fourier global shape
                        pix_a = all_pixel_segments[frag_i][seg_a]
                        pix_b = all_pixel_segments[frag_j][seg_b]
                        fourier = segment_fourier_score(pix_a, pix_b)
                        score = base + FOURIER_WEIGHT * fourier
                    else:
                        # Fallback: chain edit-distance (discrete, less accurate)
                        base = 1.0 - edit_distance(chain_a, chain_b) / max(
                            len(chain_a), len(chain_b), 1
                        )
                        score = float(np.clip(base, 0.0, 1.0))

                    cont = good_continuation_bonus(chain_a, chain_b)
                    score += GOOD_CONTINUATION_WEIGHT * cont

                    # TERTIARY: Multiplicative appearance penalty (Stage 1.6)
                    # VARIANT 6: Multi-modal fusion with equal powers (all = 2.0)
                    # BC=1.0 (perfect match) → multiplier=1.0 (no penalty)
                    # BC=0.80 (different sources) → multiplier≈0.64 (36% reduction)
                    if appearance_mats is not None:
                        bc_color = appearance_mats['color'][frag_i, frag_j]
                        bc_texture = appearance_mats['texture'][frag_i, frag_j]
                        bc_gabor = appearance_mats['gabor'][frag_i, frag_j]
                        bc_haralick = appearance_mats['haralick'][frag_i, frag_j]

                        # Stage 1.6 formula: multiplicative penalty with feature powers
                        if len(appearance_mats['haralick']) > 0:
                            # All 4 features available
                            appearance_multiplier = (bc_color ** POWER_COLOR) * \
                                                   (bc_texture ** POWER_TEXTURE) * \
                                                   (bc_gabor ** POWER_GABOR) * \
                                                   (bc_haralick ** POWER_HARALICK)
                        elif len(appearance_mats['gabor']) > 0:
                            # 3 features (no Haralick)
                            appearance_multiplier = (bc_color ** POWER_COLOR) * \
                                                   (bc_texture ** POWER_TEXTURE) * \
                                                   (bc_gabor ** POWER_GABOR)
                        else:
                            # Fallback: color + texture only
                            bc_appearance = np.sqrt(bc_color * bc_texture)
                            appearance_multiplier = bc_appearance ** POWER_COLOR

                        # Apply multiplicative penalty
                        score = score * appearance_multiplier

                    compat[frag_i, seg_a, frag_j, seg_b] = score

    logger.info(
        "Compatibility matrix built: shape=%s, mean=%.4f, max=%.4f",
        compat.shape, float(compat.mean()), float(compat.max())
    )

    # Return both compatibility matrix and appearance matrices (for Track 3)
    return compat, appearance_mats
