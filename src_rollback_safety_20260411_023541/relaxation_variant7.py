"""
Variant 7: Tuned Thresholds

Changes from baseline relaxation.py:
- MATCH_SCORE_THRESHOLD: 0.72 (was 0.75)
- WEAK_MATCH_SCORE_THRESHOLD: 0.58 (was 0.60)
- ASSEMBLY_CONFIDENCE_THRESHOLD: 0.62 (was 0.65)

Goal: Slightly relaxed thresholds to work with optimized powers.
Balances precision and recall for the new formula.
"""

import numpy as np
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 50
CONVERGENCE_THRESHOLD = 1e-4

# TUNED thresholds (Variant 7)
MATCH_SCORE_THRESHOLD = 0.72        # Tuned from 0.75
WEAK_MATCH_SCORE_THRESHOLD = 0.58   # Tuned from 0.60
ASSEMBLY_CONFIDENCE_THRESHOLD = 0.62  # Tuned from 0.65


# Import all other functions from baseline
from relaxation import (
    initialize_probabilities,
    compute_support,
    update_probabilities,
    run_relaxation,
    extract_top_assemblies,
    classify_pair,
    classify_assembly
)
