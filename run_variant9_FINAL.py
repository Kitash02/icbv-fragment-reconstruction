#!/usr/bin/env python3
"""
Variant 9_FINAL: Research-Optimized Full Stack
==============================================

This is the culmination of all optimization efforts, combining:
1. Proven baseline from Variant 0D (89%/86% - current best)
2. Weighted ensemble with research-backed weights
3. Hard discriminator pre-filtering
4. Ensemble gating (from 0D)
5. Optimized for pottery fragment discrimination

Configuration Summary:
---------------------
Formula: color^4 × texture^2 × gabor^2 × haralick^2 (proven baseline)

Ensemble Weights (optimized for pottery):
- Color: 0.45 (PRIMARY - pigment chemistry is artifact-specific)
- Raw Compat: 0.25 (geometric features - curvature, fourier)
- Texture: 0.15 (local surface patterns)
- Morphological: 0.10 (edge density + entropy)
- Gabor: 0.05 (frequency-domain texture)

Thresholds (from proven Variant 0D):
- MATCH: 0.75 (stricter to reduce false positives)
- WEAK: 0.70 (stricter to reduce uncertainty)
- ASSEMBLY: 0.65 (balanced)

Hard Discriminator Pre-Filter:
- Edge density diff < 0.15
- Entropy diff < 0.50
- Min color similarity: 0.60
- Min texture similarity: 0.55

Ensemble Gating (from 0D):
- Upgrades require: bc_color > 0.75 AND bc_texture > 0.70
- Prevents false positive upgrades on cross-artifact pairs

Target: 92%+ both metrics (stretch goal: 95%+)

Rationale:
---------
This configuration combines:
1. The proven 0D baseline that achieved 89%/86%
2. Research-backed ensemble weighting (arXiv:2309.13512, 99.3%)
3. Multi-layer defense against false positives:
   - Hard discriminator pre-filter (fast rejection)
   - Ensemble gating (prevents bad upgrades)
   - Stricter thresholds (reduces false MATCH)
4. Optimized for pottery: color weight boosted to 0.45
   (pottery discrimination relies heavily on pigment chemistry)
"""

import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

import run_test

if __name__ == "__main__":
    print("="*80)
    print("VARIANT 9_FINAL: RESEARCH-OPTIMIZED FULL STACK")
    print("="*80)
    print()
    print("Building on Variant 0D (89%/86% - current best)")
    print()
    print("Configuration:")
    print("  1. FORMULA: color^4 × texture^2 × gabor^2 × haralick^2 (proven)")
    print()
    print("  2. WEIGHTED ENSEMBLE (research-backed)")
    print("     - Color: 0.45 (PRIMARY - pottery pigment discrimination)")
    print("     - Raw Compat: 0.25 (geometric features)")
    print("     - Texture: 0.15 (surface patterns)")
    print("     - Morphological: 0.10 (edge + entropy)")
    print("     - Gabor: 0.05 (frequency-domain)")
    print()
    print("  3. THRESHOLDS (from Variant 0D - proven)")
    print("     - MATCH: 0.75")
    print("     - WEAK: 0.70")
    print("     - ASSEMBLY: 0.65")
    print()
    print("  4. HARD DISCRIMINATOR PRE-FILTER")
    print("     - Edge density diff < 0.15")
    print("     - Entropy diff < 0.50")
    print("     - Min color similarity: 0.60")
    print("     - Min texture similarity: 0.55")
    print()
    print("  5. ENSEMBLE GATING (from 0D)")
    print("     - Upgrade requires: bc_color > 0.75 AND bc_texture > 0.70")
    print("     - Prevents false positive upgrades")
    print()
    print("Target: 92%+ both metrics (stretch: 95%+)")
    print()
    print("Rationale:")
    print("  Multi-layer defense optimized for pottery discrimination:")
    print("  - Layer 1: Hard discriminator pre-filter (fast rejection)")
    print("  - Layer 2: Weighted ensemble (research-backed discrimination)")
    print("  - Layer 3: Ensemble gating (prevent bad upgrades)")
    print("  - Layer 4: Stricter thresholds (reduce false MATCH)")
    print("="*80)
    print()

    import ensemble_postprocess_variant9_FINAL
    import relaxation_variant0D
    sys.modules['ensemble_postprocess'] = ensemble_postprocess_variant9_FINAL
    sys.modules['relaxation'] = relaxation_variant0D

    run_test.main()
