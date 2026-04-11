"""
Hard Discriminator Module - Variant 0 Iteration 5
EVOLUTIONARY OPTIMIZATION: Ultra-strict (may be too aggressive)

Iteration 5 Strategy:
- Ultra-strict thresholds to test limits
- 0.78→0.80 color, 0.73→0.75 texture
- Likely to sacrifice positive accuracy
- Use as upper bound to find optimal range

Changes from iteration 4:
- Line 118: bc_color < 0.78 → bc_color < 0.80
- Line 118: bc_texture < 0.73 → bc_texture < 0.75
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

    # ITERATION 5: Ultra-strict 0.80/0.75
    if bc_color < 0.80 or bc_texture < 0.75:
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
