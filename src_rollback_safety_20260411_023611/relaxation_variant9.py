"""
Variant 9: Adaptive Thresholds for Full Research Stack

Changes from baseline relaxation.py:
- Adaptive thresholds based on artifact type detection
- Pottery: stricter thresholds (uniform appearance expected)
- Sculpture: relaxed thresholds (variable appearance expected)
- Mixed/Default: baseline thresholds
- Works with BASELINE formula (color^4 × texture^2 × gabor^2 × haralick^2)
- Combines with weighted ensemble from ensemble_postprocess_variant9

Goal: Context-aware classification with full optimization stack.
Target: 99.3% accuracy (arXiv:2309.13512)
"""

import numpy as np
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 50
CONVERGENCE_THRESHOLD = 1e-4

# Adaptive threshold profiles
THRESHOLDS = {
    'pottery': {
        'match': 0.78,
        'weak': 0.63,
        'assembly': 0.68
    },
    'sculpture': {
        'match': 0.70,
        'weak': 0.55,
        'assembly': 0.60
    },
    'default': {
        'match': 0.75,
        'weak': 0.60,
        'assembly': 0.65
    }
}

# Default to baseline thresholds
MATCH_SCORE_THRESHOLD = THRESHOLDS['default']['match']
WEAK_MATCH_SCORE_THRESHOLD = THRESHOLDS['default']['weak']
ASSEMBLY_CONFIDENCE_THRESHOLD = THRESHOLDS['default']['assembly']


def detect_artifact_type(appearance_stats: dict) -> str:
    """
    Detect artifact type based on appearance statistics.

    Heuristics:
    - Pottery: high color uniformity, moderate texture variation
    - Sculpture: moderate color variation, high texture variation
    - Default: everything else

    Args:
        appearance_stats: Dictionary with 'color_std', 'texture_std', etc.

    Returns:
        'pottery', 'sculpture', or 'default'
    """
    if appearance_stats is None:
        return 'default'

    color_std = appearance_stats.get('color_std', 0.5)
    texture_std = appearance_stats.get('texture_std', 0.5)

    # Pottery: uniform color, moderate texture
    if color_std < 0.15 and 0.10 < texture_std < 0.30:
        logger.info("Adaptive thresholds: detected POTTERY (uniform appearance)")
        return 'pottery'

    # Sculpture: variable appearance
    elif texture_std > 0.30:
        logger.info("Adaptive thresholds: detected SCULPTURE (variable appearance)")
        return 'sculpture'

    # Default: mixed or uncertain
    else:
        logger.info("Adaptive thresholds: using DEFAULT thresholds")
        return 'default'


def set_adaptive_thresholds(artifact_type: str):
    """
    Set global thresholds based on detected artifact type.

    Args:
        artifact_type: 'pottery', 'sculpture', or 'default'
    """
    global MATCH_SCORE_THRESHOLD, WEAK_MATCH_SCORE_THRESHOLD, ASSEMBLY_CONFIDENCE_THRESHOLD

    profile = THRESHOLDS.get(artifact_type, THRESHOLDS['default'])
    MATCH_SCORE_THRESHOLD = profile['match']
    WEAK_MATCH_SCORE_THRESHOLD = profile['weak']
    ASSEMBLY_CONFIDENCE_THRESHOLD = profile['assembly']

    logger.info("Adaptive thresholds set for %s: match=%.2f, weak=%.2f, assembly=%.2f",
               artifact_type, MATCH_SCORE_THRESHOLD, WEAK_MATCH_SCORE_THRESHOLD,
               ASSEMBLY_CONFIDENCE_THRESHOLD)


# Import all other functions from baseline
from relaxation import (
    initialize_probabilities,
    compute_support,
    update_probabilities,
    run_relaxation,
    extract_top_assemblies,
    classify_pair_score,
    classify_assembly
)
