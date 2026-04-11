"""
Ensemble Voting Post-Processing Filter (Track 3 Integration)

This module applies the ensemble voting system from arXiv:2309.13512 as a
post-processing filter after relaxation labeling. The goal is to re-classify
borderline cases (especially WEAK_MATCH verdicts) using the 5-way voting
ensemble to achieve higher accuracy.

Strategy (Option B - Low Risk):
- Run AFTER relaxation labeling produces assemblies
- Re-classify WEAK_MATCH pairs using ensemble voting
- Leave MATCH and NO_MATCH verdicts unchanged (high confidence)
- Only modify borderline cases where voting can help

Integration Point: src/main.py, after run_relaxation() but before visualization
"""

import numpy as np
import logging
from typing import List, Dict, Optional
from ensemble_voting import ensemble_verdict_five_way

logger = logging.getLogger(__name__)


def reclassify_borderline_cases(
    assemblies: List[Dict],
    compat_matrix: np.ndarray,
    appearance_mats: Optional[Dict[str, np.ndarray]] = None,
    all_images: Optional[List[np.ndarray]] = None
) -> List[Dict]:
    """
    Re-classify WEAK_MATCH pairs in assemblies using ensemble voting.

    The ensemble uses 5 discriminators:
    1. Raw compatibility score (geometric)
    2. Color similarity (Bhattacharyya)
    3. Texture similarity (LBP Bhattacharyya)
    4. Gabor similarity (frequency-domain texture)
    5. Morphological similarity (edge density + entropy)

    Args:
        assemblies: List of assembly dictionaries from extract_top_assemblies()
        compat_matrix: 4D compatibility matrix (n_frags, n_segs, n_frags, n_segs)
        appearance_mats: Dictionary with keys 'color', 'texture', 'gabor', 'haralick'
        all_images: List of fragment images (for computing edge/entropy on-demand)

    Returns:
        Updated assemblies with re-classified pairs
    """
    if appearance_mats is None or all_images is None:
        logger.warning(
            "Ensemble post-processing skipped: appearance matrices not available"
        )
        return assemblies

    # Track statistics
    n_reclassified = 0
    n_upgraded = 0  # WEAK_MATCH -> MATCH
    n_downgraded = 0  # WEAK_MATCH -> NO_MATCH
    n_assemblies_changed = 0

    logger.info("=" * 60)
    logger.info("ENSEMBLE POST-PROCESSING (Track 3)")
    logger.info("=" * 60)

    # Import morphological discriminators
    from hard_discriminators import compute_edge_density, compute_texture_entropy

    # Pre-compute edge density and entropy for all fragments
    edge_densities = [compute_edge_density(img) for img in all_images]
    entropies = [compute_texture_entropy(img) for img in all_images]

    logger.info("Pre-computed morphological features for %d fragments", len(all_images))

    # Process each assembly
    for asm_idx, assembly in enumerate(assemblies):
        original_verdict = assembly['verdict']
        changed = False

        # Process each pair in the assembly
        for pair in assembly['pairs']:
            frag_i = pair['frag_i']
            frag_j = pair['frag_j']
            seg_a = pair['seg_a']
            seg_b = pair['seg_b']
            original_pair_verdict = pair['verdict']

            # Only re-classify WEAK_MATCH pairs (borderline cases)
            if original_pair_verdict != 'WEAK_MATCH':
                continue

            # Get raw compatibility score
            raw_compat = pair['raw_compat']

            # Get appearance similarities
            bc_color = appearance_mats['color'][frag_i, frag_j]
            bc_texture = appearance_mats['texture'][frag_i, frag_j]
            bc_gabor = appearance_mats['gabor'][frag_i, frag_j]

            # Compute morphological differences
            edge_density_diff = abs(edge_densities[frag_i] - edge_densities[frag_j])
            entropy_diff = abs(entropies[frag_i] - entropies[frag_j])

            # Apply ensemble voting
            ensemble_verdict = ensemble_verdict_five_way(
                raw_compat=raw_compat,
                bc_color=bc_color,
                bc_texture=bc_texture,
                bc_gabor=bc_gabor,
                edge_density_diff=edge_density_diff,
                entropy_diff=entropy_diff
            )

            # Check if verdict changed
            if ensemble_verdict != original_pair_verdict:
                n_reclassified += 1
                changed = True

                if ensemble_verdict == 'MATCH':
                    n_upgraded += 1
                    logger.info(
                        "Assembly #%d: frag%d[seg%d] <-> frag%d[seg%d] "
                        "UPGRADED: WEAK_MATCH -> MATCH (ensemble confidence)",
                        asm_idx + 1, frag_i, seg_a, frag_j, seg_b
                    )
                elif ensemble_verdict == 'NO_MATCH':
                    n_downgraded += 1
                    logger.info(
                        "Assembly #%d: frag%d[seg%d] <-> frag%d[seg%d] "
                        "DOWNGRADED: WEAK_MATCH -> NO_MATCH (ensemble rejection)",
                        asm_idx + 1, frag_i, seg_a, frag_j, seg_b
                    )

                # Update pair verdict
                pair['verdict'] = ensemble_verdict

        # Recompute assembly verdict after re-classification
        if changed:
            n_assemblies_changed += 1
            assembly['verdict'] = _recompute_assembly_verdict(assembly)

            if assembly['verdict'] != original_verdict:
                logger.info(
                    "Assembly #%d verdict changed: %s -> %s",
                    asm_idx + 1, original_verdict, assembly['verdict']
                )

    # Log summary statistics
    logger.info("=" * 60)
    logger.info("ENSEMBLE POST-PROCESSING SUMMARY")
    logger.info("=" * 60)
    logger.info("Total pairs re-classified: %d", n_reclassified)
    logger.info("  Upgraded (WEAK -> MATCH): %d", n_upgraded)
    logger.info("  Downgraded (WEAK -> NO_MATCH): %d", n_downgraded)
    logger.info("Assemblies with verdict changes: %d / %d",
                n_assemblies_changed, len(assemblies))
    logger.info("=" * 60)

    return assemblies


def _recompute_assembly_verdict(assembly: Dict) -> str:
    """
    Recompute assembly verdict based on updated pair verdicts.

    Matches the logic from relaxation.classify_assembly():
    - MATCH: >=60% of pairs are MATCH or WEAK_MATCH
    - WEAK_MATCH: >=40% of pairs are MATCH or WEAK_MATCH
    - NO_MATCH: Otherwise

    Args:
        assembly: Assembly dictionary with 'pairs' list

    Returns:
        Updated verdict: "MATCH", "WEAK_MATCH", or "NO_MATCH"
    """
    pairs = assembly['pairs']
    n_pairs = len(pairs)

    if n_pairs == 0:
        return 'NO_MATCH'

    # Count verdicts
    n_match = sum(1 for p in pairs if p['verdict'] == 'MATCH')
    n_weak = sum(1 for p in pairs if p['verdict'] == 'WEAK_MATCH')
    n_valid = n_match + n_weak

    # Update counts in assembly
    assembly['n_match'] = n_match
    assembly['n_weak'] = n_weak
    assembly['n_no_match'] = n_pairs - n_valid

    # Apply thresholds
    valid_ratio = n_valid / n_pairs
    match_ratio = n_match / n_pairs

    if match_ratio >= 0.40 or valid_ratio >= 0.60:
        return 'MATCH'
    elif valid_ratio >= 0.40:
        return 'WEAK_MATCH'
    else:
        return 'NO_MATCH'


def get_ensemble_statistics(assemblies: List[Dict]) -> Dict:
    """
    Compute statistics on ensemble post-processing for analysis.

    Args:
        assemblies: List of assemblies after ensemble post-processing

    Returns:
        Dictionary with counts and percentages
    """
    total_assemblies = len(assemblies)
    total_pairs = sum(len(a['pairs']) for a in assemblies)

    verdict_counts = {
        'MATCH': sum(1 for a in assemblies if a['verdict'] == 'MATCH'),
        'WEAK_MATCH': sum(1 for a in assemblies if a['verdict'] == 'WEAK_MATCH'),
        'NO_MATCH': sum(1 for a in assemblies if a['verdict'] == 'NO_MATCH'),
    }

    pair_verdict_counts = {
        'MATCH': 0,
        'WEAK_MATCH': 0,
        'NO_MATCH': 0,
    }

    for assembly in assemblies:
        for pair in assembly['pairs']:
            pair_verdict_counts[pair['verdict']] += 1

    return {
        'total_assemblies': total_assemblies,
        'total_pairs': total_pairs,
        'assembly_verdicts': verdict_counts,
        'pair_verdicts': pair_verdict_counts,
    }
