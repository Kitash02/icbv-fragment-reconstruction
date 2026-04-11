#!/usr/bin/env python3
"""
Test runner for Variant 2: Hierarchical Ensemble (Fast Routing)

Changes from Stage 1.6:
- Uses hierarchical decision tree instead of 5-way voting
- Fast path for easy cases: morphology → color+geom → fallback to full voting
- Same formula and thresholds as baseline (0.75 / 0.60 / 0.65)
- Target: Same accuracy as baseline with 2-3x speedup on ensemble voting
"""

import sys
import os
from pathlib import Path

# Add src to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

# Monkey-patch: Replace ensemble_postprocess with variant 2
import ensemble_postprocess_variant2
sys.modules['ensemble_postprocess'] = ensemble_postprocess_variant2

# Now run the standard test suite
import run_test

if __name__ == "__main__":
    print("="*80)
    print("VARIANT 2: HIERARCHICAL ENSEMBLE (FAST ROUTING)")
    print("="*80)
    print("Configuration:")
    print("  - Formula: Stage 1.6 baseline (color^4 × texture^2 × gabor^2 × haralick^2)")
    print("  - Thresholds: 0.75 / 0.60 / 0.65")
    print("  - Ensemble: HIERARCHICAL (fast rejection + fast match + fallback to 5-way)")
    print("  - Description: Hierarchical routing for speed without accuracy loss")
    print("  - Target: Same accuracy as baseline with 2-3x speedup")
    print("="*80)
    print()

    # Run standard benchmark
    run_test.main()
