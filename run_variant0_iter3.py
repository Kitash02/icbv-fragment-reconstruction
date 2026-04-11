#!/usr/bin/env python3
"""
Test runner for Variant 0 Iteration 3
EVOLUTIONARY OPTIMIZATION

Iteration 3 Configuration:
- hard_disc_color: 0.76 (was 0.74, +2.7%)
- hard_disc_texture: 0.71 (was 0.69, +2.9%)
- color_precheck_gap: 0.15 (unchanged)
- color_precheck_low_max: 0.75 (unchanged)

Strategy: Aggressive tightening for 95%+ negative accuracy
Target: 95%+ negative, 75%+ positive
"""

import sys
import os
from pathlib import Path

# Add src to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

# Monkey-patch: Replace hard_discriminators module with iteration 3
import hard_discriminators_variant0_iter3
sys.modules['hard_discriminators'] = hard_discriminators_variant0_iter3

# Now run the standard test suite
import run_test

if __name__ == "__main__":
    print("="*80)
    print("VARIANT 0 - ITERATION 3: EVOLUTIONARY OPTIMIZATION")
    print("="*80)
    print()
    print("Configuration:")
    print("  - hard_disc_color: 0.76 (baseline: 0.70, +8.6%)")
    print("  - hard_disc_texture: 0.71 (baseline: 0.65, +9.2%)")
    print("  - color_precheck_gap: 0.15 (unchanged)")
    print("  - color_precheck_low_max: 0.75 (unchanged)")
    print()
    print("Strategy:")
    print("  - Aggressive tightening to push toward 95% target")
    print("  - Approaching variant 0B thresholds (0.75/0.70)")
    print()
    print("Target:")
    print("  - Negative accuracy: 95%+ (PRIMARY GOAL)")
    print("  - Positive accuracy: 75%+ (acceptable trade-off)")
    print("="*80)
    print()

    # Run standard benchmark
    run_test.main()
