"""
Variant 8: Adaptive Gabor Weighting (CRITICAL FIX for BC=1.0 problem)

ROOT CAUSE:
  Gabor BC = 1.0 for ALL brown artifact pairs (both same and different artifacts).
  This means Gabor provides ZERO discriminative power for brown/beige surfaces.

FIX STRATEGY:
  When Gabor BC is suspiciously high (>0.95) AND both textures are homogeneous (low spectral diversity):
    → Treat Gabor as UNINFORMATIVE
    → Reduce Gabor's weight in appearance penalty
    → Increase reliance on color/texture/Haralick discriminators

  Adaptive weighting:
    - Normal mode: color^4 × texture^2 × gabor^2 × haralick^2
    - Adaptive mode (Gabor uninformative): color^5 × texture^3 × gabor^0.5 × haralick^3

EXPECTED IMPACT:
  - Negative accuracy: 77.8% → 85-90% (eliminate 4-5 of 7 false positives)
  - Positive accuracy: 77.8% → 75-80% (minimal impact, relies on other discriminators)
  - Overall: 77.8% → 85-88%

This corresponds to information theory principles: uninformative features should have
reduced weight in classification decisions (Lecture 71: Object Recognition).
"""

# Import base compatibility module
from compatibility import *
import numpy as np

# Adaptive appearance weights (overrides)
POWER_COLOR_NORMAL = 4.0
POWER_TEXTURE_NORMAL = 2.0
POWER_GABOR_NORMAL = 2.0
POWER_HARALICK_NORMAL = 2.0

# When Gabor is uninformative, rebalance weights
POWER_COLOR_ADAPTIVE = 5.0
POWER_TEXTURE_ADAPTIVE = 3.0
POWER_GABOR_ADAPTIVE = 0.5  # Greatly reduced
POWER_HARALICK_ADAPTIVE = 3.0

# Thresholds for detecting uninformative Gabor
SPECTRAL_DIVERSITY_THRESHOLD = 0.15   # Coefficient of variation below this = homogeneous
UNINFORMATIVE_GABOR_THRESHOLD = 0.95  # BC above this + homogeneous = uninformative


def compute_gabor_spectral_diversity(gabor_signature: np.ndarray, n_scales: int = 5,
                                     n_orientations: int = 8, n_channels: int = 3) -> float:
    """
    Compute spectral diversity metric from Gabor signature.

    Measures variance of mean responses across orientations.
    Low diversity → homogeneous texture (papyrus, smooth pottery)
    High diversity → structured texture (cord-marked pottery, inscribed scrolls)

    Returns: coefficient of variation (std/mean) of orientation-specific responses
    """
    if len(gabor_signature) == 0:
        return 0.0

    # Gabor signature structure: [mean, std] × n_scales × n_orientations × n_channels
    # Extract only mean values (every other feature starting at index 0)
    means = gabor_signature[::2]  # shape: (120,) = 5 scales × 8 orientations × 3 channels

    # Reshape to (n_scales, n_orientations, n_channels)
    means_reshaped = means.reshape(n_scales, n_orientations, n_channels)

    # Average across scales and channels to get orientation-specific responses
    orientation_responses = means_reshaped.mean(axis=(0, 2))

    # Compute coefficient of variation (normalized std)
    mean_resp = orientation_responses.mean()
    std_resp = orientation_responses.std()

    if mean_resp < 1e-8:
        return 0.0

    return float(std_resp / mean_resp)


def is_gabor_uninformative(bc_gabor: float, diversity_a: float, diversity_b: float) -> bool:
    """
    Determine if Gabor BC is uninformative.

    Uninformative when:
      - BC is suspiciously high (>0.95)
      - Both textures are homogeneous (low diversity)

    This catches cases where two different homogeneous surfaces produce identical
    Gabor signatures, providing no discrimination between same/different artifacts.

    Returns: True if uninformative, False if informative
    """
    both_homogeneous = (diversity_a < SPECTRAL_DIVERSITY_THRESHOLD and
                       diversity_b < SPECTRAL_DIVERSITY_THRESHOLD)

    return bc_gabor > UNINFORMATIVE_GABOR_THRESHOLD and both_homogeneous


def build_appearance_matrices(images: List[np.ndarray]):
    """
    Build appearance similarity matrices with adaptive Gabor weighting (Variant 8 FIX).

    Computes spectral diversity for each fragment and tracks which pairs have
    uninformative Gabor signatures.
    """
    n = len(images)
    color_sigs = []
    texture_sigs = []
    gabor_sigs = []
    gabor_diversities = []  # NEW: track spectral diversity
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
        'gabor_diversity': gabor_diversities,
        'gabor_uninformative': np.zeros((n, n), dtype=bool),  # NEW: track uninformative pairs
    }

    for i in range(n):
        for j in range(i + 1, n):
            bc_color = appearance_bhattacharyya(color_sigs[i], color_sigs[j])
            bc_texture = appearance_bhattacharyya(texture_sigs[i], texture_sigs[j])
            bc_gabor = appearance_bhattacharyya(gabor_sigs[i], gabor_sigs[j])
            bc_haralick = appearance_bhattacharyya(haralick_sigs[i], haralick_sigs[j])

            # NEW: Check if Gabor is uninformative for this pair
            gabor_uninform = is_gabor_uninformative(bc_gabor, gabor_diversities[i], gabor_diversities[j])

            matrices['color'][i, j] = matrices['color'][j, i] = bc_color
            matrices['texture'][i, j] = matrices['texture'][j, i] = bc_texture
            matrices['gabor'][i, j] = matrices['gabor'][j, i] = bc_gabor
            matrices['haralick'][i, j] = matrices['haralick'][j, i] = bc_haralick
            matrices['gabor_uninformative'][i, j] = matrices['gabor_uninformative'][j, i] = gabor_uninform

            logger.debug(
                "Pair (%d, %d): color=%.3f, texture=%.3f, gabor=%.3f %s, haralick=%.3f",
                i, j, bc_color, bc_texture, bc_gabor,
                "(UNINFORMATIVE)" if gabor_uninform else "", bc_haralick
            )

    return matrices


def compute_compatibility_matrix(
    contours: List[np.ndarray],
    images: List[np.ndarray],
    min_segment_length: int = 20,
    use_fourier: bool = True,
) -> np.ndarray:
    """
    Variant 8: Adaptive Gabor weighting based on informativeness.

    When Gabor BC is uninformative (high BC + both homogeneous):
      - Reduce Gabor weight from 2.0 to 0.5
      - Increase color/texture/Haralick weights to compensate
      - This forces discrimination to rely on more informative features
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
                # Hard discriminator check
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
                bc_gabor = appearance_mats['gabor'][i, j]
                bc_haralick = appearance_mats['haralick'][i, j]
                gabor_uninform = appearance_mats['gabor_uninformative'][i, j]

                # ADAPTIVE WEIGHTING (Variant 8 FIX)
                if gabor_uninform:
                    # Gabor is uninformative → reduce its weight, increase others
                    appearance_penalty = (
                        bc_color ** POWER_COLOR_ADAPTIVE *
                        bc_texture ** POWER_TEXTURE_ADAPTIVE *
                        bc_gabor ** POWER_GABOR_ADAPTIVE *
                        bc_haralick ** POWER_HARALICK_ADAPTIVE
                    )
                    mode = "ADAPTIVE"
                else:
                    # Gabor is informative → use normal weights
                    appearance_penalty = (
                        bc_color ** POWER_COLOR_NORMAL *
                        bc_texture ** POWER_TEXTURE_NORMAL *
                        bc_gabor ** POWER_GABOR_NORMAL *
                        bc_haralick ** POWER_HARALICK_NORMAL
                    )
                    mode = "NORMAL"

                final_score = score_geom * appearance_penalty

                logger.debug(
                    "Pair (%d, %d) [%s]: geom=%.3f, app_penalty=%.3f → final=%.3f",
                    i, j, mode, score_geom, appearance_penalty, final_score
                )
            else:
                final_score = score_geom

            C[i, j] = C[j, i] = final_score

    return C
