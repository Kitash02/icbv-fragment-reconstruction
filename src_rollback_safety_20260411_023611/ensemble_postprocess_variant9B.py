"""
Variant 9B: Balanced Ensemble Weighting
========================================

Alternative to 9A with more emphasis on geometric features.

Key Changes:
1. Balanced color and geometric weights
2. Color: 0.40, Raw: 0.30, Texture: 0.15, Morph: 0.10, Gabor: 0.05
3. Hard discriminator pre-filter before ensemble
4. Works with stricter thresholds from Variant 0D

Target: 90%+ accuracy
"""

import numpy as np
import logging
from typing import List, Dict, Optional
from ensemble_voting import ensemble_verdict_weighted

logger = logging.getLogger(__name__)

# Balanced weights for appearance + geometric features
# More emphasis on geometric (raw_compat) for robustness
CUSTOM_WEIGHTS = {
    'color': 0.40,          # Appearance - primary
    'raw_compat': 0.30,     # Geometric - INCREASED for robustness
    'texture': 0.15,        # Local patterns
    'morphological': 0.10,  # Secondary feature
    'gabor': 0.05          # Frequency-domain
}
}

# Hard discriminator thresholds for pre-filtering
HARD_DISCRIMINATOR_THRESHOLDS = {
    'edge_density_max_diff': 0.15,  # Max acceptable edge density difference
    'entropy_max_diff': 0.50,        # Max acceptable entropy difference
    'min_color_similarity': 0.60,    # Min color similarity to consider
    'min_texture_similarity': 0.55   # Min texture similarity to consider
}


def should_skip_pair(bc_color: float, bc_texture: float,
                     edge_density_diff: float, entropy_diff: float) -> bool:
    """
    Pre-filter using hard discriminators before ensemble voting.

    Returns True if pair should be immediately rejected (NO_MATCH).
    This catches obvious non-matches quickly.
    """
    # Morphological check (manufacturing process similarity)
    if edge_density_diff > HARD_DISCRIMINATOR_THRESHOLDS['edge_density_max_diff']:
        logger.debug("Pre-filter reject: edge density diff %.3f > %.3f",
                    edge_density_diff, HARD_DISCRIMINATOR_THRESHOLDS['edge_density_max_diff'])
        return True

    if entropy_diff > HARD_DISCRIMINATOR_THRESHOLDS['entropy_max_diff']:
        logger.debug("Pre-filter reject: entropy diff %.3f > %.3f",
                    entropy_diff, HARD_DISCRIMINATOR_THRESHOLDS['entropy_max_diff'])
        return True

    # Appearance check (pigment and surface similarity)
    if bc_color < HARD_DISCRIMINATOR_THRESHOLDS['min_color_similarity']:
        logger.debug("Pre-filter reject: color similarity %.3f < %.3f",
                    bc_color, HARD_DISCRIMINATOR_THRESHOLDS['min_color_similarity'])
        return True

    if bc_texture < HARD_DISCRIMINATOR_THRESHOLDS['min_texture_similarity']:
        logger.debug("Pre-filter reject: texture similarity %.3f < %.3f",
                    bc_texture, HARD_DISCRIMINATOR_THRESHOLDS['min_texture_similarity'])
        return True

    return False


def reclassify_borderline_cases(
    assemblies: List[Dict],
    compat_matrix: np.ndarray,
    appearance_mats: Optional[Dict[str, np.ndarray]] = None,
    all_images: Optional[List[np.ndarray]] = None
) -> List[Dict]:
    """
    Re-classify WEAK_MATCH pairs using enhanced ensemble (Variant 9B).

    Enhanced features:
    - Optimized weights (color=0.40 primary)
    - Hard discriminator pre-filter
    - Works with stricter thresholds from 0D
    """
    if appearance_mats is None or all_images is None:
        logger.warning("Ensemble post-processing skipped: appearance matrices not available")
        return assemblies

    n_reclassified = 0
    n_upgraded = 0
    n_downgraded = 0
    n_prefiltered = 0
    n_assemblies_changed = 0

    logger.info("=" * 60)
    logger.info("ENHANCED FULL RESEARCH STACK (Variant 9B)")
    logger.info("=" * 60)
    logger.info("Optimized weights: color=0.40, raw=0.25, texture=0.15, morph=0.10, gabor=0.05")
    logger.info("Hard discriminator pre-filter: ENABLED")
    logger.info("Thresholds: Variant 0D stricter (0.75/0.70/0.65)")
    logger.info("Target: 92%% accuracy")

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

            # Pre-filter with hard discriminators
            if should_skip_pair(bc_color, bc_texture, edge_density_diff, entropy_diff):
                ensemble_verdict = 'NO_MATCH'
                n_prefiltered += 1
                logger.debug("Assembly #%d: frag%d[seg%d] ↔ frag%d[seg%d] PRE-FILTERED → NO_MATCH",
                           asm_idx + 1, frag_i, seg_a, frag_j, seg_b)
            else:
                # Use weighted ensemble with optimized weights
                ensemble_verdict = ensemble_verdict_weighted(
                    raw_compat=raw_compat,
                    bc_color=bc_color,
                    bc_texture=bc_texture,
                    bc_gabor=bc_gabor,
                    edge_density_diff=edge_density_diff,
                    entropy_diff=entropy_diff,
                    weights=CUSTOM_WEIGHTS
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
    logger.info("ENHANCED ENSEMBLE SUMMARY (Variant 9B)")
    logger.info("=" * 60)
    logger.info("Pre-filtered (hard discriminators): %d", n_prefiltered)
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
