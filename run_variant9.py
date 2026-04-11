#!/usr/bin/env python3
"""
Test runner for Variant 9: Full Research Stack

Changes from Stage 1.6:
- Same formula as baseline (color^4 × texture^2 × gabor^2 × haralick^2)
- Weighted ensemble: color=0.40, raw=0.25, texture=0.15, morph=0.15, gabor=0.05
- Adaptive thresholds based on artifact type
- Target: 99.3% (arXiv:2309.13512)
- Description: "All optimizations: weighted voting + adaptive thresholds (99.3% target)"
"""

import sys
import os
from pathlib import Path

# Add src to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

# Monkey-patch: Replace BOTH ensemble_postprocess AND relaxation modules with variant 9
import ensemble_postprocess_variant9
import relaxation_variant9
sys.modules['ensemble_postprocess'] = ensemble_postprocess_variant9
sys.modules['relaxation'] = relaxation_variant9

# Now run the standard test suite
import run_test

if __name__ == "__main__":
    print("="*80)
    print("VARIANT 9: FULL RESEARCH STACK")
    print("="*80)
    print("Configuration:")
    print("  - Formula: BASELINE (color^4 × texture^2 × gabor^2 × haralick^2)")
    print("    - POWER_COLOR: 4.0 (baseline)")
    print("    - POWER_TEXTURE: 2.0 (baseline)")
    print("    - POWER_GABOR: 2.0 (baseline)")
    print("    - POWER_HARALICK: 2.0 (baseline)")
    print("  - Ensemble: WEIGHTED with tuned weights")
    print("    - Color: 0.40, Raw: 0.25, Texture: 0.15, Morph: 0.15, Gabor: 0.05")
    print("  - Thresholds: ADAPTIVE based on artifact type")
    print("    - Pottery: 0.78 / 0.63 / 0.68 (stricter - uniform appearance)")
    print("    - Sculpture: 0.70 / 0.55 / 0.60 (relaxed - variable appearance)")
    print("    - Mixed/Default: 0.75 / 0.60 / 0.65 (baseline)")
    print("  - Target: 99.3% (arXiv:2309.13512)")
    print("  - Description: All optimizations combined (weighted voting + adaptive thresholds)")
    print("="*80)
    print()

    # Run standard benchmark
    run_test.main()
