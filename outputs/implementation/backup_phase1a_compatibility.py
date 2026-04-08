"""
Pairwise edge-compatibility scoring between fragment boundary segments.

Implements the compatibility measure described in Lecture 72 (2D Shape
Analysis) and Lecture 23 (Edge Detection), with an additional appearance
similarity term from Lecture 71 (Object Recognition).

Primary signal -- Curvature Profile Cross-Correlation (Lecture 72):
  The continuous analog of first-difference chain code. Each segment's
  turning-angle sequence kappa(i) = atan2(v[i]xv[i-1], v[i]*v[i-1]) is
  computed and compared via normalized circular cross-correlation (FFT).
  This is fully rotation-invariant for ANY angle -- not just multiples of 45deg.
  It is also O(n log n), faster than the O(n^2) chain edit distance it replaces.

Secondary signal -- Fourier Descriptor distance (Lecture 72):
  FFT magnitude spectrum of the pixel coordinates z[n]=x[n]+jy[n].
  Captures global segment shape; orthogonal to local curvature.

Bonus -- Good Continuation (Lecture 52):
  Gestalt principle: smooth joins (low curvature change at junction) scored higher.

Penalty -- Color Histogram Dissimilarity (Lecture 71):
  Fragments from the same archaeological artifact share the same pigment palette.
  This signal uses the Bhattacharyya coefficient between HSV color histograms
  to penalize pairs of fragments whose global color distributions are incompatible.
  Fragments from different source images receive a strong penalty that overrides
  any incidental geometric similarity.

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

logger = logging.getLogger(__name__)

GOOD_CONTINUATION_SIGMA = 0.5
GOOD_CONTINUATION_WEIGHT = 0.10
FOURIER_WEIGHT = 0.25          # global shape complement to local curvature
FOURIER_SEGMENT_ORDER = 8      # number of Fourier coefficients per segment

# Color histogram penalty (Lecture 71 -- appearance-based recognition)
# A fragment pair whose color distributions differ significantly is penalized.
# Weight 0.8 means: a completely mismatched pair (BC~=0.1) loses 0.72 from its score,
# reliably placing it below both the WEAK_MATCH threshold (0.35) and MATCH (0.55).
COLOR_PENALTY_WEIGHT = 0.80
COLOR_HIST_BINS_HUE = 16       # hue bins in HSV histogram
COLOR_HIST_BINS_SAT = 4        # saturation bins in HSV histogram


def edit_distance(seq_a: List[int], seq_b: List[int]) -> int:
    """
    Levenshtein edit distance between two integer sequences.

    Retained for backwards compatibility with tests and the chain-code
    representation. The primary segment matching now uses curvature
    profile cross-correlation (profile_similarity), which is both more
    accurate and faster for continuous rotation invariance.

    Implemented via single-row dynamic programming in O(m*n) time and
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


def segment_compatibility(seg_a: List[int], seg_b: List[int]) -> float:
    """
    Normalized compatibility score between two chain code segments.

    This is a simple wrapper for backward compatibility with unit tests.
    Returns 1.0 - (edit_distance / max_length), clamped to [0, 1].

    The production system uses profile_similarity() with curvature profiles
    for better rotation invariance.
    """
    if not seg_a or not seg_b:
        return 0.0

    dist = edit_distance(seg_a, seg_b)
    max_len = max(len(seg_a), len(seg_b))

    if max_len == 0:
        return 1.0

    return max(0.0, 1.0 - dist / max_len)


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
           xcorr(tau) = IFFT( FFT(kappa_a) * conj(FFT(kappa_b)) )  -- O(N log N)
       The peak of xcorr gives the best circular shift alignment.
    4. Anti-parallel hypotheses: also compare kappa_a against -kappa_b[::-1]
       (reverse traversal direction, negated turning angles), which is the
       physically correct model for two fragment edges that meet.
    5. Return max peak / N as a score in [0, 1].

    Why this achieves full rotation invariance:
      kappa(i) = atan2(v[i] x v[i-1], v[i] * v[i-1]) depends only on the
      *relative* angle between consecutive tangents. Rotating the entire
      segment by any angle theta adds theta to every absolute tangent angle, but
      the differences kappa(i) are unchanged. No quantization, no grid artifacts.

    Straight-line segments (kappa ~= 0 everywhere) receive score 0.5 -- they
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

    # Four hypotheses: forward / anti-parallel x original / flipped
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
    (Object Recognition) -- colour histograms are among the simplest and most
    discriminative appearance descriptors when the lighting is consistent.

    Returns
    -------
    hist : float32 vector of length (COLOR_HIST_BINS_HUE x COLOR_HIST_BINS_SAT),
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

    BC = Sigma sqrt(p_i * q_i) in [0, 1].
    BC = 1.0 : identical histograms (perfect color match).
    BC ~= 0.0 : non-overlapping color distributions (completely different images).

    Fragment pairs with BC well below 1.0 are penalized in the compatibility
    matrix, because low BC implies the fragments come from different source
    images and cannot physically belong to the same artifact.
    """
    if len(sig_a) == 0 or len(sig_b) == 0:
        return 0.5   # uninformative -- no penalty
    bc = float(np.sum(np.sqrt(np.clip(sig_a, 0, None) * np.clip(sig_b, 0, None))))
    return float(np.clip(bc, 0.0, 1.0))


def segment_fourier_score(
    seg_pixels_a: np.ndarray,
    seg_pixels_b: np.ndarray,
) -> float:
    """
    Global shape similarity between two pixel segments via Fourier descriptors.

    Treats each segment's pixel coordinates as a complex 1-D signal,
    computes its DFT, and compares the low-frequency magnitude spectra
    (Lecture 72 -- 2D Shape Analysis). Segments with similar boundary curves
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


def _build_color_sim_matrix(
    all_images: List[np.ndarray],
) -> np.ndarray:
    """
    Build a symmetric (n_frags x n_frags) matrix of Bhattacharyya color similarity.

    Entry [i, j] is the Bhattacharyya coefficient between the HSV color
    histograms of fragment i and fragment j. Used to penalize cross-image pairs.
    """
    n = len(all_images)
    sigs = [compute_color_signature(img) for img in all_images]
    mat = np.ones((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            bc = color_bhattacharyya(sigs[i], sigs[j])
            mat[i, j] = bc
            mat[j, i] = bc
    return mat


def build_compatibility_matrix(
    all_segments: List[List[List[int]]],
    all_pixel_segments: Optional[List[List[np.ndarray]]] = None,
    all_images: Optional[List[np.ndarray]] = None,
) -> np.ndarray:
    """
    Build the full pairwise compatibility matrix over all fragment segments.

    all_segments[i][a]       -- chain code segment (retained for good-continuation)
    all_pixel_segments[i][a] -- pixel coordinate segment (required for curvature)
    all_images[i]            -- BGR image of fragment i (required for color penalty)

    Returns a 4D array C of shape (n_frags, n_segs, n_frags, n_segs) where
    C[i, a, j, b] combines four signals (Lectures 23, 52, 71, 72):

      1. Curvature profile cross-correlation (PRIMARY -- Lecture 72)
         Continuous, fully rotation-invariant. O(n log n) per pair.

      2. Good-continuation bonus (Lecture 52)
         Gestalt principle: smooth curvature at the join point.

      3. Fourier descriptor score (Lecture 72)
         Global segment shape via FFT magnitude spectrum.

      4. Color histogram penalty (Lecture 71)
         Fragments from the same artifact share the same pigment palette.
         Pairs from different source images are penalized proportionally to
         their Bhattacharyya histogram distance.

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

    # Pre-compute fragment-level color similarity matrix (Lecture 71)
    color_sim_mat: Optional[np.ndarray] = None
    if all_images is not None:
        color_sim_mat = _build_color_sim_matrix(all_images)
        logger.info(
            "Color similarity matrix (Bhattacharyya): min=%.3f  mean=%.3f  max=%.3f",
            float(color_sim_mat[color_sim_mat < 1.0].min()) if (color_sim_mat < 1.0).any() else 1.0,
            float(color_sim_mat[color_sim_mat < 1.0].mean()) if (color_sim_mat < 1.0).any() else 1.0,
            float(color_sim_mat[color_sim_mat < 1.0].max()) if (color_sim_mat < 1.0).any() else 1.0,
        )

    for frag_i, segs_i in enumerate(all_segments):
        for seg_a, chain_a in enumerate(segs_i):
            for frag_j, segs_j in enumerate(all_segments):
                if frag_i == frag_j:
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

                    # TERTIARY: color histogram penalty (Lecture 71)
                    # Penalizes pairs whose color distributions are incompatible.
                    # Same-image pairs: BC~=0.8->penalty~=0.16 (minor reduction).
                    # Cross-image pairs: BC~=0.1->penalty~=0.72 (score collapses).
                    if color_sim_mat is not None:
                        bc = color_sim_mat[frag_i, frag_j]
                        color_penalty = (1.0 - bc) * COLOR_PENALTY_WEIGHT
                        score = max(0.0, score - color_penalty)

                    compat[frag_i, seg_a, frag_j, seg_b] = score

    logger.info(
        "Compatibility matrix built: shape=%s, mean=%.4f, max=%.4f",
        compat.shape, float(compat.mean()), float(compat.max())
    )
    return compat
