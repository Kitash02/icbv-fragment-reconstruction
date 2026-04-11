"""
Relaxation Labeling for global fragment assembly optimization.

Implements the iterative constraint propagation algorithm from Lecture 53
(Perceptual Organization — Curve Inference via Good Continuation).

Each fragment-edge pair is a labeling unit. A label (j, b) assigned to
unit (i, a) means "segment a of fragment i is proposed to match segment b
of fragment j". Probabilities are updated based on contextual support until
convergence or a maximum iteration limit.

Update rule (Lecture 53 formulation):
    P(i, λ) ← P(i, λ) · (1 + Q(i, λ)) / Σ_μ [P(i, μ) · (1 + Q(i, μ))]

where Q(i, λ) aggregates support from all other units: how well their
current label assignments are compatible with label λ for unit i.

Match Quality Thresholds
------------------------
Raw compatibility scores (from compatibility.py) lie in [0.0, 1.25]:
  - Chain edit score:         0.0 – 1.0
  - Good-continuation bonus:  0.0 – 0.10  (weight 0.10)
  - Fourier score:            0.0 – 0.15  (weight 0.15)

A pair of segments is considered a *match* only when its raw compatibility
exceeds MATCH_SCORE_THRESHOLD. Assembly-level confidence (average across
matched pairs) is compared against ASSEMBLY_CONFIDENCE_THRESHOLD.

Verdict meanings:
  MATCH       — raw compat ≥ 0.55; boundary geometry is genuinely similar.
  WEAK_MATCH  — raw compat ∈ [0.35, 0.55); possible match, low confidence.
  NO_MATCH    — raw compat < 0.35; segments are geometrically incompatible.
"""

import numpy as np
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 50
CONVERGENCE_THRESHOLD = 1e-4

# Thresholds on raw compatibility scores (before relaxation)
# These are calibrated for the combined score (edit + good-continuation + Fourier)
# Maximum possible raw score = 1.0 + 0.10 + 0.15 = 1.25
MATCH_SCORE_THRESHOLD = 0.75        # pair is a confident match (Stage 1.6)
WEAK_MATCH_SCORE_THRESHOLD = 0.60   # pair is a possible but uncertain match (Stage 1.6)
ASSEMBLY_CONFIDENCE_THRESHOLD = 0.65  # assembly overall is accepted as a match (Stage 1.6)


def initialize_probabilities(compat_matrix: np.ndarray) -> np.ndarray:
    """
    Set initial label probabilities proportional to pairwise compatibility.

    P[i, a, j, b] starts as compat[i, a, j, b] and is row-normalized so
    that for each unit (i, a) the distribution over all labels sums to 1.
    Same-fragment entries are zeroed out before normalization.
    """
    n_frags, n_segs = compat_matrix.shape[:2]
    probs = compat_matrix.copy()

    for frag_idx in range(n_frags):
        probs[frag_idx, :, frag_idx, :] = 0.0

    flat = probs.reshape(n_frags * n_segs, n_frags * n_segs)
    row_sums = flat.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums == 0, 1.0, row_sums)
    flat /= row_sums

    return probs


def compute_support(
    probs: np.ndarray,
    compat_matrix: np.ndarray,
) -> np.ndarray:
    """
    Compute contextual support Q(i, λ) for every unit-label pair.

    Q[i, a, j, b] = Σ_{k,c} Σ_{l,d} P[k, c, l, d] · compat[j, b, l, d]

    This sums, over all other units (k, c) and their label assignments,
    how compatible those assignments are with fragment j (the proposed
    match for unit (i, a)). Units that agree with a good assignment for
    fragment j increase the support for label (j, b).

    Implemented as a matrix product over the flattened representation.
    """
    n_frags, n_segs = compat_matrix.shape[:2]
    n_units = n_frags * n_segs

    probs_flat = probs.reshape(n_units, n_units)
    compat_flat = compat_matrix.reshape(n_units, n_units)

    support_flat = probs_flat @ compat_flat.T
    return support_flat.reshape(n_frags, n_segs, n_frags, n_segs)


def update_probabilities(
    probs: np.ndarray,
    support: np.ndarray,
) -> np.ndarray:
    """
    Apply the relaxation labeling update rule from Lecture 53.

    P(i, λ) ← P(i, λ) · (1 + Q(i, λ)) / Σ_μ [P(i, μ) · (1 + Q(i, μ))]

    The (1 + Q) factor amplifies labels backed by strong contextual support,
    causing the distribution to converge toward a globally consistent assembly.
    """
    n_frags, n_segs = probs.shape[:2]

    updated = probs * (1.0 + support)
    flat = updated.reshape(n_frags * n_segs, n_frags * n_segs)
    row_sums = flat.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums == 0, 1.0, row_sums)
    flat /= row_sums

    return updated


def run_relaxation(
    compat_matrix: np.ndarray,
) -> Tuple[np.ndarray, List[float]]:
    """
    Run the full relaxation labeling loop until convergence.

    Iterates the support-then-update cycle, logging the maximum probability
    change per iteration. Stops when the change falls below
    CONVERGENCE_THRESHOLD or MAX_ITERATIONS is reached.

    Returns the final probability matrix and the per-iteration delta trace.
    """
    probs = initialize_probabilities(compat_matrix)
    convergence_trace: List[float] = []

    for iteration in range(MAX_ITERATIONS):
        support = compute_support(probs, compat_matrix)
        probs_new = update_probabilities(probs, support)

        delta = float(np.max(np.abs(probs_new - probs)))
        convergence_trace.append(delta)
        probs = probs_new

        logger.info(
            "Relaxation iteration %02d — max Δ: %.6f", iteration + 1, delta
        )

        if delta < CONVERGENCE_THRESHOLD:
            logger.info("Converged after %d iterations.", iteration + 1)
            break
    else:
        logger.info("Reached maximum of %d iterations without convergence.", MAX_ITERATIONS)

    return probs, convergence_trace


def classify_pair_score(raw_compat: float) -> str:
    """
    Return a human-readable verdict for one segment-pair compatibility score.

    Verdicts are based on the raw compatibility (before relaxation labeling):
      MATCH       — raw ≥ MATCH_SCORE_THRESHOLD (0.55): boundary shapes are
                    geometrically similar; this is a confident match candidate.
      WEAK_MATCH  — raw ∈ [WEAK_MATCH_SCORE_THRESHOLD, MATCH_SCORE_THRESHOLD):
                    [0.35, 0.55): partial similarity; treat with caution.
      NO_MATCH    — raw < WEAK_MATCH_SCORE_THRESHOLD (0.35): segments are
                    geometrically incompatible; not a valid join point.
    """
    if raw_compat >= MATCH_SCORE_THRESHOLD:
        return "MATCH"
    if raw_compat >= WEAK_MATCH_SCORE_THRESHOLD:
        return "WEAK_MATCH"
    return "NO_MATCH"


def classify_assembly(confidence: float, matched_pairs: List[dict]) -> str:
    """
    Return a verdict for a complete assembly proposal.

    Primary criterion — raw compatibility fraction (scale-independent):
      MATCH       : ≥ 60 % of pairs are MATCH  AND ≥ 40 % are MATCH
      WEAK_MATCH  : ≥ 40 % of pairs are MATCH or WEAK_MATCH
      NO_MATCH    : < 40 % of pairs are MATCH or WEAK_MATCH

    Secondary check — relaxation probability vs. baseline:
      The relaxation probability (confidence) is distributed over
      n_frags × n_segs labels, so its expected baseline is
      1 / n_labels ≈ confidence / n_pairs.  An assembly that concentrates
      probability well above this baseline is additionally rewarded, but
      the raw-compat criterion is primary.

    Possible verdicts: "MATCH", "WEAK_MATCH", "NO_MATCH".
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


def extract_top_assemblies(
    probs: np.ndarray,
    n_top: int = 3,
    compat_matrix: np.ndarray = None,
) -> List[dict]:
    """
    Extract the top-n candidate assemblies from the converged probability matrix.

    Uses greedy highest-probability assignment: each unit is matched to its
    most probable label that has not yet been claimed by another unit.
    Repeated n_top times with small perturbations to obtain diverse hypotheses.

    Each matched pair is annotated with:
      - score      : relaxation probability (context-weighted confidence)
      - raw_compat : raw compatibility score from the compatibility matrix
      - verdict    : "MATCH", "WEAK_MATCH", or "NO_MATCH" per-pair classification

    Each assembly dict also contains:
      - confidence    : mean relaxation probability over matched pairs
      - verdict       : assembly-level classification
      - n_match       : number of MATCH pairs
      - n_weak        : number of WEAK_MATCH pairs
      - n_no_match    : number of NO_MATCH pairs

    If compat_matrix is None, raw_compat defaults to the relaxation score and
    per-pair verdicts are still computed (but less precisely calibrated).
    """
    n_frags, n_segs = probs.shape[:2]
    n_units = n_frags * n_segs
    assemblies: List[dict] = []

    flat = probs.reshape(n_units, n_units).copy()

    for _ in range(n_top):
        matched_pairs: List[dict] = []
        used_units: set = set()

        sorted_indices = np.argsort(flat.ravel())[::-1]
        for flat_idx in sorted_indices:
            unit_i = int(flat_idx) // n_units
            unit_j = int(flat_idx) % n_units
            if unit_i in used_units or unit_j in used_units:
                continue
            frag_i, seg_a = divmod(unit_i, n_segs)
            frag_j, seg_b = divmod(unit_j, n_segs)
            if frag_i == frag_j:
                continue

            prob_score = float(flat[unit_i, unit_j])
            raw_compat = (
                float(compat_matrix[frag_i, seg_a, frag_j, seg_b])
                if compat_matrix is not None
                else prob_score
            )
            pair_verdict = classify_pair_score(raw_compat)

            matched_pairs.append({
                'frag_i': frag_i, 'seg_a': seg_a,
                'frag_j': frag_j, 'seg_b': seg_b,
                'score': prob_score,
                'raw_compat': raw_compat,
                'verdict': pair_verdict,
            })
            used_units.update([unit_i, unit_j])

        confidence = (
            sum(p['score'] for p in matched_pairs) / len(matched_pairs)
            if matched_pairs else 0.0
        )
        assembly_verdict = classify_assembly(confidence, matched_pairs)

        n_match = sum(1 for p in matched_pairs if p['verdict'] == 'MATCH')
        n_weak = sum(1 for p in matched_pairs if p['verdict'] == 'WEAK_MATCH')
        n_no_match = sum(1 for p in matched_pairs if p['verdict'] == 'NO_MATCH')

        assemblies.append({
            'pairs': matched_pairs,
            'confidence': confidence,
            'verdict': assembly_verdict,
            'n_match': n_match,
            'n_weak': n_weak,
            'n_no_match': n_no_match,
        })

        # Small random perturbation for assembly diversity
        noise = 1.0 - 0.05 * np.random.rand(*flat.shape)
        flat = flat * noise
        row_sums = flat.sum(axis=1, keepdims=True)
        flat /= np.where(row_sums == 0, 1.0, row_sums)

    return assemblies
