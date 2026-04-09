#!/usr/bin/env python3
"""
Test runner for Variant 0 Iteration 2
EVOLUTIONARY OPTIMIZATION

Iteration 2 Configuration:
- hard_disc_color: 0.74 (was 0.72, +2.8%)
- hard_disc_texture: 0.69 (was 0.67, +3.0%)
- color_precheck_gap: 0.15 (unchanged)
- color_precheck_low_max: 0.75 (unchanged)

Strategy: Moderate tightening for 90%+ negative accuracy
Target: 90%+ negative, 70%+ positive
"""

import sys
import os
from pathlib import Path

# Add src to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

# Monkey-patch: Replace hard_discriminators module with iteration 2
import hard_discriminators_variant0_iter2
sys.modules['hard_discriminators'] = hard_discriminators_variant0_iter2

# Now run the standard test suite
import run_test

if __name__ == "__main__":
    print("="*80)
    print("VARIANT 0 - ITERATION 2: EVOLUTIONARY OPTIMIZATION")
    print("="*80)
    print()
    print("Configuration:")
    print("  - hard_disc_color: 0.74 (baseline: 0.70, +5.7%)")
    print("  - hard_disc_texture: 0.69 (baseline: 0.65, +6.2%)")
    print("  - color_precheck_gap: 0.15 (unchanged)")
    print("  - color_precheck_low_max: 0.75 (unchanged)")
    print()
    print("Strategy:")
    print("  - Moderate tightening to push negative accuracy toward 90%")
    print("  - Monitor positive accuracy for acceptable trade-off")
    print()
    print("Target:")
    print("  - Negative accuracy: 90%+ (from ~75% baseline)")
    print("  - Positive accuracy: 70%+ (from ~78% baseline)")
    print("="*80)
    print()

    # Run standard benchmark
    run_test.main()
