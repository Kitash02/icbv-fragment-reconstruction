#!/usr/bin/env python3
"""
Test runner for Variant 0 Iteration 1
EVOLUTIONARY OPTIMIZATION

Iteration 1 Configuration:
- hard_disc_color: 0.72 (was 0.70, +2.8%)
- hard_disc_texture: 0.67 (was 0.65, +3.1%)
- color_precheck_gap: 0.15 (unchanged)
- color_precheck_low_max: 0.75 (unchanged)

Strategy: Incremental tightening to reduce false positives
Target: 85%+ negative, 70%+ positive
"""

import sys
import os
from pathlib import Path

# Add src to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

# Monkey-patch: Replace hard_discriminators module with iteration 1
import hard_discriminators_variant0_iter1
sys.modules['hard_discriminators'] = hard_discriminators_variant0_iter1

# Now run the standard test suite
import run_test

if __name__ == "__main__":
    print("="*80)
    print("VARIANT 0 - ITERATION 1: EVOLUTIONARY OPTIMIZATION")
    print("="*80)
    print()
    print("Configuration:")
    print("  - hard_disc_color: 0.72 (baseline: 0.70, +2.8%)")
    print("  - hard_disc_texture: 0.67 (baseline: 0.65, +3.1%)")
    print("  - color_precheck_gap: 0.15 (unchanged)")
    print("  - color_precheck_low_max: 0.75 (unchanged)")
    print()
    print("Strategy:")
    print("  - Incremental tightening to reduce cross-source false positives")
    print("  - Small steps to preserve true match detection")
    print()
    print("Target:")
    print("  - Negative accuracy: 85%+ (from ~75% baseline)")
    print("  - Positive accuracy: 70%+ (from ~78% baseline)")
    print("="*80)
    print()

    # Run standard benchmark
    run_test.main()
