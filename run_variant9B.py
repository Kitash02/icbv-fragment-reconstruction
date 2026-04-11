#!/usr/bin/env python3
"""
Variant 9B: Aggressive Ensemble Weighting
==========================================

Alternative optimization focusing on geometric features.

Strategy:
1. Balance color and geometric (raw_compat) features
2. Color: 0.40, Raw: 0.30, Texture: 0.15, Morph: 0.10, Gabor: 0.05
3. Use Variant 0D thresholds (proven)
4. Target: 90%+ both metrics

Rationale:
- Some failures may be due to over-reliance on color
- Geometric features (curvature matching) are more robust
- This variant balances appearance and geometry
"""

import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

import run_test

if __name__ == "__main__":
    print("="*80)
    print("VARIANT 9B: AGGRESSIVE ENSEMBLE WEIGHTING")
    print("="*80)
    print("Configuration:")
    print("  - Formula: BASELINE (color^4 × texture^2 × gabor^2 × haralick^2)")
    print("  - Ensemble: BALANCED (color=0.40, raw=0.30, texture=0.15, morph=0.10, gabor=0.05)")
    print("  - Thresholds: STRICTER from Variant 0D (0.75/0.70/0.65)")
    print("  - Strategy: Balance appearance and geometric features")
    print("  - Target: 90%+ both metrics")
    print("="*80)
    print()

    import ensemble_postprocess_variant9B
    import relaxation_variant0D
    sys.modules['ensemble_postprocess'] = ensemble_postprocess_variant9B
    sys.modules['relaxation'] = relaxation_variant0D

    run_test.main()
