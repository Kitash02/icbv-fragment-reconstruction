#!/usr/bin/env python3
"""
Test runner for Variant 3: Tuned Weighted Ensemble

Changes from Stage 1.6:
- Uses weighted ensemble voting with custom weights
- Weights: Color(0.40), Raw(0.25), Texture(0.15), Morph(0.15), Gabor(0.05)
- Same formula and thresholds as baseline
- Target: Improved discrimination through optimized weighting
"""

import sys
import os
from pathlib import Path

# Add src to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

# Monkey-patch: Replace ensemble_postprocess with variant 3
import ensemble_postprocess_variant3
sys.modules['ensemble_postprocess'] = ensemble_postprocess_variant3

# Now run the standard test suite
import run_test

if __name__ == "__main__":
    print("="*80)
    print("VARIANT 3: TUNED WEIGHTED ENSEMBLE")
    print("="*80)
    print("Configuration:")
    print("  - Formula: Stage 1.6 baseline (color^4 × texture^2 × gabor^2 × haralick^2)")
    print("  - Thresholds: 0.75 / 0.60 / 0.65")
    print("  - Ensemble: WEIGHTED with custom weights")
    print("    - Color: 0.40 (increased from 0.35)")
    print("    - Raw: 0.25 (unchanged)")
    print("    - Texture: 0.15 (decreased from 0.20)")
    print("    - Morph: 0.15 (unchanged)")
    print("    - Gabor: 0.05 (unchanged)")
    print("  - Target: Better discrimination through color emphasis")
    print("="*80)
    print()

    # Run standard benchmark
    run_test.main()
