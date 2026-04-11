#!/usr/bin/env python3
"""
Test runner for Variant 1: Weighted Ensemble Only (arXiv:2510.17145)

Changes from Stage 1.6:
- Uses weighted ensemble voting instead of 5-way voting
- Weights: Color(0.35), Raw(0.25), Texture(0.20), Morph(0.15), Gabor(0.05)
- Target: 97.49% accuracy (paper claim)
"""

import sys
import os
from pathlib import Path

# Add src to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

# Monkey-patch: Replace ensemble_postprocess with variant 1
import ensemble_postprocess_variant1
sys.modules['ensemble_postprocess'] = ensemble_postprocess_variant1

# Now run the standard test suite
import run_test

if __name__ == "__main__":
    print("="*80)
    print("VARIANT 1: WEIGHTED ENSEMBLE ONLY")
    print("="*80)
    print("Configuration:")
    print("  - Formula: Stage 1.6 baseline (color^4 × texture^2 × gabor^2 × haralick^2)")
    print("  - Thresholds: 0.75 / 0.60 / 0.65")
    print("  - Ensemble: WEIGHTED (color=0.35, raw=0.25, texture=0.20, morph=0.15, gabor=0.05)")
    print("  - Target: 97.49% (arXiv:2510.17145)")
    print("="*80)
    print()

    # Run standard benchmark
    run_test.main()
