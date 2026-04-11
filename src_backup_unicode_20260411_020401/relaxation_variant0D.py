"""
Variant 0D: ALL FIXES COMBINED - Optimal Baseline Configuration

This variant combines ALL three fixes that showed promise individually:
1. Stricter hard discriminators (0.75/0.70 vs baseline 0.55/0.35)
2. Ensemble gating with stricter requirements
3. Current color pre-check (0.15/0.75)

Changes from baseline relaxation.py:
- MATCH_SCORE_THRESHOLD: 0.75 (vs 0.55 baseline, +36%)
- WEAK_MATCH_SCORE_THRESHOLD: 0.70 (vs 0.35 baseline, +100%)
- ASSEMBLY_CONFIDENCE_THRESHOLD: 0.65 (unchanged)

Expected Result:
- Target: 85%+ negative accuracy, 75%+ positive accuracy
- This should be the optimal configuration before adaptive/ensemble methods
- Should match or exceed any single fix alone

Integration: Works with ensemble_postprocess_variant0D which adds ensemble gating
"""

import numpy as np
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 50
CONVERGENCE_THRESHOLD = 1e-4

# STRICTER thresholds - primary fix for negative accuracy
MATCH_SCORE_THRESHOLD = 0.75        # STRICTER: was 0.55 in baseline (+36%)
WEAK_MATCH_SCORE_THRESHOLD = 0.70   # MUCH STRICTER: was 0.35 in baseline (+100%)
ASSEMBLY_CONFIDENCE_THRESHOLD = 0.65  # baseline (unchanged)

# Import all other functions from baseline relaxation
from relaxation import (
    initialize_probabilities,
    compute_support,
    update_probabilities,
    run_relaxation,
    extract_top_assemblies,
)


def classify_pair_score(raw_compat: float) -> str:
    """
    Return a human-readable verdict for one segment-pair compatibility score.

    VARIANT 0D: Uses STRICTER thresholds to reduce false positives.

    Verdicts are based on the raw compatibility (before relaxation labeling):
      MATCH       — raw ≥ 0.75 (was 0.55): very high geometric similarity
      WEAK_MATCH  — raw ∈ [0.70, 0.75): good similarity but not confident
      NO_MATCH    — raw < 0.70 (was 0.35): geometrically incompatible
    """
    if raw_compat >= MATCH_SCORE_THRESHOLD:
        return "MATCH"
    if raw_compat >= WEAK_MATCH_SCORE_THRESHOLD:
        return "WEAK_MATCH"
    return "NO_MATCH"


def classify_assembly(confidence: float, matched_pairs: List[dict]) -> str:
    """
    Return a verdict for a complete assembly proposal.

    VARIANT 0D: Uses same logic as baseline but with stricter pair thresholds.

    Primary criterion — raw compatibility fraction (scale-independent):
      MATCH       : ≥ 60 % of pairs are MATCH  AND ≥ 40 % are MATCH
      WEAK_MATCH  : ≥ 40 % of pairs are MATCH or WEAK_MATCH
      NO_MATCH    : < 40 % of pairs are MATCH or WEAK_MATCH
    """
    if not matched_pairs:
        return "NO_MATCH"

    n_pairs = len(matched_pairs)
    n_strong = sum(
        1 for p in matched_pairs
        if p.get('raw_compat', 0.0) >= MATCH_SCORE_THRESHOLD
    )
    n_valid = sum(
        1 for p in matched_pairs
        if p.get('raw_compat', 0.0) >= WEAK_MATCH_SCORE_THRESHOLD
    )
    frac_strong = n_strong / n_pairs
    frac_valid = n_valid / n_pairs

    if frac_strong >= 0.60 and frac_valid >= 0.40:
        return "MATCH"
    if frac_valid >= 0.40:
        return "WEAK_MATCH"
    return "NO_MATCH"
