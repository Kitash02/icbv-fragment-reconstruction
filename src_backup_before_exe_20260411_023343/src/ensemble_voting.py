"""
Ensemble Voting System for Pottery Fragment Classification

Implements the 5-way voting ensemble from arXiv:2309.13512 which achieved
99.3% accuracy on object classification with similar appearance.

Key Insight: Multiple weak discriminators voting independently are more
robust than a single strong discriminator. Each voter uses different features,
so failures are uncorrelated.

Voting Strategy (Pessimistic for Archaeology):
- MATCH: Requires 3+ MATCH votes (60% confidence threshold)
- NO_MATCH: Requires 2+ NO_MATCH votes (40% rejection - pessimistic!)
- WEAK_MATCH: Otherwise (uncertain cases)

This pessimistic bias is intentional: in archaeology, it's better to miss
some true matches than to propose false assemblies.
"""

import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def classify_by_threshold(score: float, match_thresh: float, weak_thresh: float) -> str:
    """
    Classify a score into MATCH, WEAK_MATCH, or NO_MATCH.

    Args:
        score: Similarity score in [0, 1]
        match_thresh: Threshold for confident match
        weak_thresh: Threshold for possible match

    Returns:
        "MATCH", "WEAK_MATCH", or "NO_MATCH"
    """
    if score >= match_thresh:
        return "MATCH"
    elif score >= weak_thresh:
        return "WEAK_MATCH"
    else:
        return "NO_MATCH"


def ensemble_verdict_five_way(
    raw_compat: float,
    bc_color: float,
    bc_texture: float,
    bc_gabor: float,
    edge_density_diff: float,
    entropy_diff: float
) -> str:
    """
    5-way ensemble voting for final fragment pair verdict.

    From arXiv:2309.13512: Combined Classifier with soft voting achieved
    99.3% accuracy vs 92.4% for hard voting. Each voter uses different
    features, so errors are uncorrelated.

    Voters:
    1. Raw Compatibility (curvature + fourier + good-continuation)
    2. Color Discriminator (Lab histogram, pigment chemistry)
    3. Texture Discriminator (LBP histogram, local patterns)
    4. Gabor Discriminator (frequency-domain texture)
    5. Morphological Discriminator (edge density + entropy)

    Args:
        raw_compat: Raw compatibility score from curvature matching [0, 1.25]
        bc_color: Bhattacharyya coefficient for color [0, 1]
        bc_texture: Bhattacharyya coefficient for LBP texture [0, 1]
        bc_gabor: Cosine similarity for Gabor features [0, 1]
        edge_density_diff: Absolute difference in edge density [0, 1]
        entropy_diff: Absolute difference in texture entropy [0, inf]

    Returns:
        "MATCH", "WEAK_MATCH", or "NO_MATCH"
    """
    votes = []

    # Voter 1: Raw Compatibility Score
    # Uses geometric features (curvature, fourier, good-continuation)
    # Thresholds calibrated for max raw score = 1.25
    vote1 = classify_by_threshold(raw_compat, match_thresh=0.85, weak_thresh=0.70)
    votes.append(vote1)

    # Voter 2: Color Discriminator
    # Pigment chemistry is artifact-specific (most discriminative)
    # Higher threshold since color is primary signal
    vote2 = classify_by_threshold(bc_color, match_thresh=0.78, weak_thresh=0.65)
    votes.append(vote2)

    # Voter 3: Texture Discriminator (LBP)
    # Local binary patterns capture local surface structure
    # Moderate threshold (texture is secondary)
    vote3 = classify_by_threshold(bc_texture, match_thresh=0.72, weak_thresh=0.58)
    votes.append(vote3)

    # Voter 4: Gabor Discriminator
    # Frequency-domain texture (captures grain patterns)
    # Lower threshold (Gabor is less discriminative for pottery)
    vote4 = classify_by_threshold(bc_gabor, match_thresh=0.70, weak_thresh=0.55)
    votes.append(vote4)

    # Voter 5: Morphological Discriminator
    # Edge density and entropy capture manufacturing differences
    # Inverted logic: LOW difference = MATCH
    morph_score = 1.0 - min(edge_density_diff / 0.20 + entropy_diff / 0.70, 1.0)
    vote5 = classify_by_threshold(morph_score, match_thresh=0.75, weak_thresh=0.60)
    votes.append(vote5)

    # Count votes
    match_votes = votes.count("MATCH")
    no_match_votes = votes.count("NO_MATCH")
    weak_match_votes = votes.count("WEAK_MATCH")

    # Log voting breakdown
    logger.debug(
        "Ensemble votes: %s -> M:%d W:%d N:%d",
        votes, match_votes, weak_match_votes, no_match_votes
    )

    # Voting Rule (Pessimistic Bias for Archaeology)
    # Archaeology prefers false negatives over false positives
    # (Better to miss a match than propose a false assembly)

    # MATCH: Need strong consensus (3+ MATCH votes)
    if match_votes >= 3:
        return "MATCH"

    # NO_MATCH: Pessimistic threshold (2+ NO_MATCH votes)
    # This is intentionally low to reject uncertain cases
    elif no_match_votes >= 2:
        return "NO_MATCH"

    # WEAK_MATCH: Everything else (mixed or all WEAK_MATCH)
    else:
        return "WEAK_MATCH"


def ensemble_verdict_weighted(
    raw_compat: float,
    bc_color: float,
    bc_texture: float,
    bc_gabor: float,
    edge_density_diff: float,
    entropy_diff: float,
    weights: Dict[str, float] = None
) -> str:
    """
    Weighted ensemble voting (alternative to equal voting).

    From arXiv:2510.17145: Late fusion with learned weights achieved
    97.49% accuracy. Weights reflect discriminative power of each feature.

    Default weights (based on empirical pottery analysis):
    - Color: 0.35 (highest - pigment is artifact-specific)
    - Raw compatibility: 0.25 (geometric features)
    - Texture: 0.20 (local patterns)
    - Morphological: 0.15 (edge + entropy)
    - Gabor: 0.05 (lowest - too generic for pottery)

    Args:
        Same as ensemble_verdict_five_way, plus:
        weights: Optional custom weights (must sum to 1.0)

    Returns:
        "MATCH", "WEAK_MATCH", or "NO_MATCH"
    """
    if weights is None:
        # Iteration 1: Reduced color dominance to decrease FN rate
        weights = {
            'color': 0.30,
            'raw_compat': 0.28,
            'texture': 0.23,
            'morphological': 0.14,
            'gabor': 0.05
        }

    # Normalize scores to [0, 1]
    raw_compat_norm = min(raw_compat / 1.25, 1.0)  # Max raw score = 1.25
    morph_score = 1.0 - min(edge_density_diff / 0.20 + entropy_diff / 0.70, 1.0)

    # Compute weighted average
    weighted_score = (
        weights['color'] * bc_color +
        weights['raw_compat'] * raw_compat_norm +
        weights['texture'] * bc_texture +
        weights['gabor'] * bc_gabor +
        weights['morphological'] * morph_score
    )

    logger.debug(
        "Weighted ensemble: score=%.3f (color=%.3fx%.2f, raw=%.3fx%.2f, "
        "texture=%.3fx%.2f, gabor=%.3fx%.2f, morph=%.3fx%.2f)",
        weighted_score,
        bc_color, weights['color'],
        raw_compat_norm, weights['raw_compat'],
        bc_texture, weights['texture'],
        bc_gabor, weights['gabor'],
        morph_score, weights['morphological']
    )

    # Classify weighted score
    return classify_by_threshold(weighted_score, match_thresh=0.75, weak_thresh=0.60)


def ensemble_verdict_hierarchical(
    raw_compat: float,
    bc_color: float,
    bc_texture: float,
    bc_gabor: float,
    edge_density_diff: float,
    entropy_diff: float
) -> str:
    """
    Hierarchical decision tree (fast path for easy cases).

    Strategy:
    1. Easy rejections: Check morphological first (fast)
    2. Easy matches: Check color + raw_compat (high confidence)
    3. Hard cases: Full ensemble voting

    This is faster than full voting for ~80% of cases.

    Args:
        Same as ensemble_verdict_five_way

    Returns:
        "MATCH", "WEAK_MATCH", or "NO_MATCH"
    """
    # Stage 1: Fast rejection (morphological check)
    if edge_density_diff > 0.15 or entropy_diff > 0.5:
        logger.debug("Hierarchical: Fast reject (morphology)")
        return "NO_MATCH"

    # Stage 2: Fast match (color + geometric consensus)
    if bc_color >= 0.80 and raw_compat >= 0.85:
        logger.debug("Hierarchical: Fast match (color+geom consensus)")
        return "MATCH"

    # Stage 3: Fast reject (color OR geometric failure)
    if bc_color < 0.55 or raw_compat < 0.60:
        logger.debug("Hierarchical: Fast reject (color or geom failure)")
        return "NO_MATCH"

    # Stage 4: Hard case - use full ensemble
    logger.debug("Hierarchical: Hard case -> full ensemble")
    return ensemble_verdict_five_way(
        raw_compat, bc_color, bc_texture, bc_gabor,
        edge_density_diff, entropy_diff
    )


def get_ensemble_statistics(verdicts: List[str]) -> Dict[str, float]:
    """
    Compute statistics on ensemble verdicts for analysis.

    Args:
        verdicts: List of verdicts from ensemble_verdict_* functions

    Returns:
        Dictionary with counts and percentages
    """
    total = len(verdicts)
    if total == 0:
        return {}

    match_count = verdicts.count("MATCH")
    weak_count = verdicts.count("WEAK_MATCH")
    no_match_count = verdicts.count("NO_MATCH")

    return {
        'total': total,
        'match_count': match_count,
        'match_pct': 100.0 * match_count / total,
        'weak_count': weak_count,
        'weak_pct': 100.0 * weak_count / total,
        'no_match_count': no_match_count,
        'no_match_pct': 100.0 * no_match_count / total,
    }
