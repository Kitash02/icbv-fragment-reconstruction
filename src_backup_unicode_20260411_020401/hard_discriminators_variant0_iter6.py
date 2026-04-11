"""
Hard Discriminator Module - Variant 0 Iteration 6
EVOLUTIONARY OPTIMIZATION: Hybrid approach with relaxed color precheck

Iteration 6 Strategy:
- Based on analysis: Some false positives have BC scores in the 0.75-0.80 range
- Instead of just raising thresholds, also relax color_precheck to let more through
- Then use stricter hard_disc to filter: 0.76 color, 0.72 texture
- Different philosophy: Let candidates through, filter hard at compatibility stage

This tests whether the issue is premature rejection vs insufficient discrimination.
"""

import cv2
import numpy as np
from scipy.stats import entropy
import logging

logger = logging.getLogger(__name__)


def compute_edge_density(image: np.ndarray) -> float:
    if image is None or image.size == 0:
        return 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.sum(edges > 0)) / edges.size
    return edge_density


def compute_texture_entropy(image: np.ndarray) -> float:
    if image is None or image.size == 0:
        return 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist = hist.ravel() / (hist.sum() + 1e-10)
    tex_entropy = entropy(hist)
    return float(tex_entropy)


def hard_reject_check(
    image_i: np.ndarray,
    image_j: np.ndarray,
    bc_color: float,
    bc_texture: float
) -> bool:
    edge_density_i = compute_edge_density(image_i)
    edge_density_j = compute_edge_density(image_j)
    edge_diff = abs(edge_density_i - edge_density_j)

    if edge_diff > 0.15:
        logger.debug(
            "REJECT: Edge density diff %.3f (i=%.3f, j=%.3f)",
            edge_diff, edge_density_i, edge_density_j
        )
        return True

    entropy_i = compute_texture_entropy(image_i)
    entropy_j = compute_texture_entropy(image_j)
    entropy_diff = abs(entropy_i - entropy_j)

    if entropy_diff > 0.5:
        logger.debug(
            "REJECT: Entropy diff %.3f (i=%.3f, j=%.3f)",
            entropy_diff, entropy_i, entropy_j
        )
        return True

    # ITERATION 6: Balanced approach - 0.76/0.72
    if bc_color < 0.76 or bc_texture < 0.72:
        logger.debug(
            "REJECT: Appearance gate (color=%.3f, texture=%.3f)",
            bc_color, bc_texture
        )
        return True

    return False


def should_early_stop_negative_tests(num_failed: int, num_tested: int) -> bool:
    EARLY_STOP_THRESHOLD = 18
    if num_failed >= EARLY_STOP_THRESHOLD:
        logger.warning(
            "EARLY STOP: %d/%d negative cases failed (threshold=%d)",
            num_failed, num_tested, EARLY_STOP_THRESHOLD
        )
        return True
    return False
