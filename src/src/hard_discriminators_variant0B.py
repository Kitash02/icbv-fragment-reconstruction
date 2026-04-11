"""
Hard Discriminator Module for Pottery Fragment Rejection - VARIANT 0B
EVEN STRICTER THRESHOLDS

Implements fast, hard rejection criteria based on arXiv:2511.12976 (MCAQ-YOLO)
and arXiv:2309.13512 (99.3% accuracy ensemble). These checks run BEFORE
expensive curvature computation to quickly reject obviously incompatible pairs.

VARIANT 0B CHANGES:
- Line 124: Changed from `if bc_color < 0.70 or bc_texture < 0.65:`
- Changed to: `if bc_color < 0.75 or bc_texture < 0.70:`
- TARGET: Eliminate remaining 9 false positives (especially getty 17009652 & 21778090)
- EXPECTED: Negative accuracy 85%+ (from current 75%)
"""

import cv2
import numpy as np
from scipy.stats import entropy
import logging

logger = logging.getLogger(__name__)


def compute_edge_density(image: np.ndarray) -> float:
    """
    Compute edge density: fraction of pixels that are edges.

    From arXiv:2511.12976 (MCAQ-YOLO): Edge density captures
    morphological complexity. Different pottery types have different
    edge patterns due to manufacturing techniques.

    Args:
        image: BGR or grayscale image

    Returns:
        Edge density in [0, 1] (fraction of pixels that are edges)
    """
    if image is None or image.size == 0:
        return 0.0

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.sum(edges > 0)) / edges.size
    return edge_density


def compute_texture_entropy(image: np.ndarray) -> float:
    """
    Compute Shannon entropy of grayscale histogram.

    From arXiv:2511.12976 (MCAQ-YOLO): Texture entropy measures
    randomness/disorder. Different pottery has different surface
    randomness due to clay composition and firing.

    Args:
        image: BGR or grayscale image

    Returns:
        Entropy value (higher = more random/disordered)
    """
    if image is None or image.size == 0:
        return 0.0

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist = hist.ravel() / (hist.sum() + 1e-10)  # Normalize to probability
    tex_entropy = entropy(hist)
    return float(tex_entropy)


def hard_reject_check(
    image_i: np.ndarray,
    image_j: np.ndarray,
    bc_color: float,
    bc_texture: float
) -> bool:
    """
    Fast hard rejection check. Returns True if pair should be REJECTED.

    From arXiv:2309.13512 (99.3% ensemble accuracy): Use multiple
    independent discriminators. If ANY fails significantly, reject early.

    Strategy:
    1. Edge Density: Different pottery types have different edge patterns
    2. Texture Entropy: Different clay/firing creates different randomness
    3. Combined Appearance: Both color AND texture must be similar

    Args:
        image_i: First fragment image (BGR)
        image_j: Second fragment image (BGR)
        bc_color: Bhattacharyya coefficient for color (0-1)
        bc_texture: Bhattacharyya coefficient for texture (0-1)

    Returns:
        True if pair should be rejected, False if it passes to full check
    """
    # Check 1: Edge Density Difference
    # Different manufacturing techniques create different edge patterns
    edge_density_i = compute_edge_density(image_i)
    edge_density_j = compute_edge_density(image_j)
    edge_diff = abs(edge_density_i - edge_density_j)

    if edge_diff > 0.15:  # 15% difference is significant
        logger.debug(
            "REJECT: Edge density diff %.3f (i=%.3f, j=%.3f)",
            edge_diff, edge_density_i, edge_density_j
        )
        return True

    # Check 2: Texture Entropy Difference
    # Different clay composition creates different texture randomness
    entropy_i = compute_texture_entropy(image_i)
    entropy_j = compute_texture_entropy(image_j)
    entropy_diff = abs(entropy_i - entropy_j)

    if entropy_diff > 0.5:  # 0.5 entropy units is significant
        logger.debug(
            "REJECT: Entropy diff %.3f (i=%.3f, j=%.3f)",
            entropy_diff, entropy_i, entropy_j
        )
        return True

    # Check 3: Combined Appearance Gate
    # BOTH color AND texture must be reasonably similar
    # (Prevents one high score from masking the other)
    # VARIANT 0B: EVEN STRICTER - Raised from 0.70/0.65 to 0.75/0.70
    if bc_color < 0.75 or bc_texture < 0.70:
        logger.debug(
            "REJECT: Appearance gate (color=%.3f, texture=%.3f)",
            bc_color, bc_texture
        )
        return True

    # All checks passed - proceed to full compatibility computation
    return False


def should_early_stop_negative_tests(num_failed: int, num_tested: int) -> bool:
    """
    Check if we should stop testing early due to systematic failure.

    Early stop rule: If 18+ negative cases fail (50% of 36), it's a
    systematic issue not an edge case. Stop to save time.

    Args:
        num_failed: Number of negative test cases that failed
        num_tested: Total number of negative test cases tested so far

    Returns:
        True if should stop testing early
    """
    EARLY_STOP_THRESHOLD = 18  # 50% of 36 negative cases

    if num_failed >= EARLY_STOP_THRESHOLD:
        logger.warning(
            "EARLY STOP: %d/%d negative cases failed (threshold=%d)",
            num_failed, num_tested, EARLY_STOP_THRESHOLD
        )
        return True

    return False
