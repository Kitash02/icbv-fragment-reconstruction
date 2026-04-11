"""
Variant 0D: ALL FIXES COMBINED - Ensemble Gating with Stricter Requirements

This is the ensemble post-processing component for Variant 0D.

Changes from baseline ensemble_postprocess.py:
1. Adds GATING: Only upgrade WEAK_MATCH if BOTH bc_color > 0.75 AND bc_texture > 0.70
2. This prevents false positive upgrades on cross-artifact pairs
3. Works with stricter hard discriminators from relaxation_variant0D

Gating Logic:
- UPGRADE to MATCH: Requires bc_color > 0.75 AND bc_texture > 0.70
- DOWNGRADE to NO_MATCH: Standard ensemble voting (no gating)
- This creates an asymmetric filter that's pessimistic on upgrades

Expected Result:
- Should dramatically reduce false positive upgrades
- Should preserve most true positive upgrades (they have high bc_color + bc_texture)
- Target: 85%+ negative accuracy with minimal loss to positive accuracy
"""

import numpy as np
import logging
from typing import List, Dict, Optional
from ensemble_voting import ensemble_verdict_five_way

logger = logging.getLogger(__name__)

# Gating thresholds for UPGRADES (WEAK_MATCH → MATCH)
GATE_COLOR_THRESHOLD = 0.75      # Must have strong color similarity
GATE_TEXTURE_THRESHOLD = 0.70    # Must have strong texture similarity


def reclassify_borderline_cases(
    assemblies: List[Dict],
    compat_matrix: np.ndarray,
    appearance_mats: Optional[Dict[str, np.ndarray]] = None,
    all_images: Optional[List[np.ndarray]] = None
) -> List[Dict]:
    """
    Re-classify WEAK_MATCH pairs using GATED ensemble voting (Variant 0D).

    KEY CHANGE: Adds gating to upgrades:
    - Only upgrade WEAK_MATCH → MATCH if bc_color > 0.75 AND bc_texture > 0.70
    - Downgrades (WEAK_MATCH → NO_MATCH) are NOT gated
    - This creates an asymmetric filter that's pessimistic on upgrades

    Rationale:
    - Cross-artifact pairs often have high geometric similarity (raw_compat)
    - But they differ in color and texture (different source images)
    - Gating on color+texture prevents these false positive upgrades
    - True matches typically have high scores on ALL features
    """
    if appearance_mats is None or all_images is None:
        logger.warning("Ensemble post-processing skipped: appearance matrices not available")
        return assemblies

    n_reclassified = 0
    n_upgraded = 0
    n_downgraded = 0
    n_gated = 0  # Count how many upgrades were blocked by gating
    n_assemblies_changed = 0

    logger.info("=" * 60)
    logger.info("VARIANT 0D: ENSEMBLE GATING (ALL FIXES COMBINED)")
    logger.info("=" * 60)
    logger.info("Gating thresholds for upgrades:")
    logger.info("  - bc_color > %.2f", GATE_COLOR_THRESHOLD)
    logger.info("  - bc_texture > %.2f", GATE_TEXTURE_THRESHOLD)
    logger.info("Both conditions must be met for WEAK_MATCH → MATCH upgrade")
    logger.info("Downgrades (WEAK_MATCH → NO_MATCH) are NOT gated")

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

            # Get ensemble verdict (standard five-way voting)
            ensemble_verdict = ensemble_verdict_five_way(
                raw_compat=raw_compat,
                bc_color=bc_color,
                bc_texture=bc_texture,
                bc_gabor=bc_gabor,
                edge_density_diff=edge_density_diff,
                entropy_diff=entropy_diff
            )

            # GATING LOGIC: Apply stricter requirements for upgrades
            if ensemble_verdict == 'MATCH':
                # Check if upgrade passes gating thresholds
                passes_gate = (bc_color > GATE_COLOR_THRESHOLD and
                              bc_texture > GATE_TEXTURE_THRESHOLD)

                if not passes_gate:
                    # Block the upgrade - keep as WEAK_MATCH
                    n_gated += 1
                    logger.debug(
                        "Assembly #%d: frag%d[seg%d] ↔ frag%d[seg%d] "
                        "GATED: ensemble said MATCH but bc_color=%.3f, bc_texture=%.3f "
                        "(threshold: %.2f/%.2f) → keeping WEAK_MATCH",
                        asm_idx + 1, frag_i, seg_a, frag_j, seg_b,
                        bc_color, bc_texture, GATE_COLOR_THRESHOLD, GATE_TEXTURE_THRESHOLD
                    )
                    ensemble_verdict = 'WEAK_MATCH'  # Override ensemble decision

            # Apply the final verdict (possibly gated)
            if ensemble_verdict != original_pair_verdict:
                n_reclassified += 1
                changed = True

                if ensemble_verdict == 'MATCH':
                    n_upgraded += 1
                    logger.info(
                        "Assembly #%d: frag%d[seg%d] ↔ frag%d[seg%d] UPGRADED: WEAK_MATCH → MATCH "
                        "(passed gate: color=%.3f, texture=%.3f)",
                        asm_idx + 1, frag_i, seg_a, frag_j, seg_b, bc_color, bc_texture
                    )
                elif ensemble_verdict == 'NO_MATCH':
                    n_downgraded += 1
                    logger.info(
                        "Assembly #%d: frag%d[seg%d] ↔ frag%d[seg%d] DOWNGRADED: WEAK_MATCH → NO_MATCH",
                        asm_idx + 1, frag_i, seg_a, frag_j, seg_b
                    )

                pair['verdict'] = ensemble_verdict

        if changed:
            n_assemblies_changed += 1
            assembly['verdict'] = _recompute_assembly_verdict(assembly)

            if assembly['verdict'] != original_verdict:
                logger.info("Assembly #%d verdict changed: %s → %s",
                           asm_idx + 1, original_verdict, assembly['verdict'])

    logger.info("=" * 60)
    logger.info("VARIANT 0D ENSEMBLE GATING SUMMARY")
    logger.info("=" * 60)
    logger.info("Total pairs re-classified: %d", n_reclassified)
    logger.info("  Upgraded (WEAK → MATCH): %d", n_upgraded)
    logger.info("  Downgraded (WEAK → NO_MATCH): %d", n_downgraded)
    logger.info("  Gated (upgrade blocked): %d", n_gated)
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
