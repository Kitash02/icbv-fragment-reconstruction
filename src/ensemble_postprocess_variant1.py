"""
Variant 1: Weighted Ensemble Post-Processing (arXiv:2510.17145 - 97.49%)

Changes from baseline:
- Replace ensemble_verdict_five_way() with ensemble_verdict_weighted()
- Uses learned weights: Color(0.35), Raw(0.25), Texture(0.20), Morph(0.15), Gabor(0.05)
"""

import numpy as np
import logging
from typing import List, Dict, Optional
from ensemble_voting import ensemble_verdict_weighted  # KEY CHANGE

logger = logging.getLogger(__name__)


def reclassify_borderline_cases(
    assemblies: List[Dict],
    compat_matrix: np.ndarray,
    appearance_mats: Optional[Dict[str, np.ndarray]] = None,
    all_images: Optional[List[np.ndarray]] = None
) -> List[Dict]:
    """
    Re-classify WEAK_MATCH pairs using WEIGHTED ensemble voting (Variant 1).
    """
    if appearance_mats is None or all_images is None:
        logger.warning("Ensemble post-processing skipped: appearance matrices not available")
        return assemblies

    n_reclassified = 0
    n_upgraded = 0
    n_downgraded = 0
    n_assemblies_changed = 0

    logger.info("=" * 60)
    logger.info("WEIGHTED ENSEMBLE POST-PROCESSING (Variant 1)")
    logger.info("=" * 60)

    from hard_discriminators import compute_edge_density, compute_texture_entropy

    edge_densities = [compute_edge_density(img) for img in all_images]
    entropies = [compute_texture_entropy(img) for img in all_images]

    logger.info("Pre-computed morphological features for %d fragments", len(all_images))

    for asm_idx, assembly in enumerate(assemblies):
        original_verdict = assembly['verdict']
        changed = False

        for pair in assembly['pairs']:
            frag_i = pair['frag_i']
            frag_j = pair['frag_j']
            seg_a = pair['seg_a']
            seg_b = pair['seg_b']
            original_pair_verdict = pair['verdict']

            if original_pair_verdict != 'WEAK_MATCH':
                continue

            raw_compat = pair['raw_compat']
            bc_color = appearance_mats['color'][frag_i, frag_j]
            bc_texture = appearance_mats['texture'][frag_i, frag_j]
            bc_gabor = appearance_mats['gabor'][frag_i, frag_j]
            edge_density_diff = abs(edge_densities[frag_i] - edge_densities[frag_j])
            entropy_diff = abs(entropies[frag_i] - entropies[frag_j])

            # KEY CHANGE: Use weighted ensemble instead of five_way
            ensemble_verdict = ensemble_verdict_weighted(
                raw_compat=raw_compat,
                bc_color=bc_color,
                bc_texture=bc_texture,
                bc_gabor=bc_gabor,
                edge_density_diff=edge_density_diff,
                entropy_diff=entropy_diff
            )

            if ensemble_verdict != original_pair_verdict:
                n_reclassified += 1
                changed = True

                if ensemble_verdict == 'MATCH':
                    n_upgraded += 1
                    logger.info("Assembly #%d: frag%d[seg%d] ↔ frag%d[seg%d] UPGRADED: WEAK_MATCH → MATCH",
                               asm_idx + 1, frag_i, seg_a, frag_j, seg_b)
                elif ensemble_verdict == 'NO_MATCH':
                    n_downgraded += 1
                    logger.info("Assembly #%d: frag%d[seg%d] ↔ frag%d[seg%d] DOWNGRADED: WEAK_MATCH → NO_MATCH",
                               asm_idx + 1, frag_i, seg_a, frag_j, seg_b)

                pair['verdict'] = ensemble_verdict

        if changed:
            n_assemblies_changed += 1
            assembly['verdict'] = _recompute_assembly_verdict(assembly)

            if assembly['verdict'] != original_verdict:
                logger.info("Assembly #%d verdict changed: %s → %s",
                           asm_idx + 1, original_verdict, assembly['verdict'])

    logger.info("=" * 60)
    logger.info("WEIGHTED ENSEMBLE SUMMARY (Variant 1)")
    logger.info("=" * 60)
    logger.info("Total pairs re-classified: %d", n_reclassified)
    logger.info("  Upgraded (WEAK → MATCH): %d", n_upgraded)
    logger.info("  Downgraded (WEAK → NO_MATCH): %d", n_downgraded)
    logger.info("Assemblies with verdict changes: %d / %d", n_assemblies_changed, len(assemblies))
    logger.info("=" * 60)

    return assemblies


def _recompute_assembly_verdict(assembly: Dict) -> str:
    """Recompute assembly verdict based on updated pair verdicts."""
    pairs = assembly['pairs']
    n_pairs = len(pairs)

    if n_pairs == 0:
        return 'NO_MATCH'

    n_match = sum(1 for p in pairs if p['verdict'] == 'MATCH')
    n_weak = sum(1 for p in pairs if p['verdict'] == 'WEAK_MATCH')
    n_valid = n_match + n_weak

    assembly['n_match'] = n_match
    assembly['n_weak'] = n_weak
    assembly['n_no_match'] = n_pairs - n_valid

    valid_ratio = n_valid / n_pairs
    match_ratio = n_match / n_pairs

    if match_ratio >= 0.40 or valid_ratio >= 0.60:
        return 'MATCH'
    elif valid_ratio >= 0.40:
        return 'WEAK_MATCH'
    else:
        return 'NO_MATCH'
