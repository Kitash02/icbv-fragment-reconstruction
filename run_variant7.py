#!/usr/bin/env python3
"""
Test runner for Variant 7: Optimized Powers + Tuned Thresholds

Changes from Stage 1.6:
- Optimized powers: color^5, texture^2.5, gabor^2, haralick^2
- Tuned thresholds: 0.72 / 0.58 / 0.62
- Target: Best balance of formula and thresholds
"""

import sys
import os
from pathlib import Path

# Add src to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

# Monkey-patch: Replace both compatibility and relaxation modules
import compatibility_variant7
import relaxation_variant7
sys.modules['compatibility'] = compatibility_variant7
sys.modules['relaxation'] = relaxation_variant7

# Now run the standard test suite
import run_test

if __name__ == "__main__":
    print("="*80)
    print("VARIANT 7: OPTIMIZED POWERS + TUNED THRESHOLDS")
    print("="*80)
    print("Configuration:")
    print("  - Formula: color^5 × texture^2.5 × gabor^2 × haralick^2")
    print("    - POWER_COLOR: 5.0 (was 4.0)")
    print("    - POWER_TEXTURE: 2.5 (was 2.0)")
    print("    - POWER_GABOR: 2.0 (unchanged)")
    print("    - POWER_HARALICK: 2.0 (unchanged)")
    print("  - Thresholds: 0.72 / 0.58 / 0.62 (vs baseline 0.75 / 0.60 / 0.65)")
    print("    - MATCH: ≥ 0.72 (slightly relaxed)")
    print("    - WEAK_MATCH: ≥ 0.58 (slightly relaxed)")
    print("    - ASSEMBLY: ≥ 0.62 (slightly relaxed)")
    print("  - Ensemble: Baseline (five-way voting)")
    print("  - Target: Optimized balance of discrimination and recall")
    print("="*80)
    print()

    # Run standard benchmark
    run_test.main()
