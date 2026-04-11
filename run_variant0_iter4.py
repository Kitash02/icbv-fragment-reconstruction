#!/usr/bin/env python3
"""
Test runner for Variant 0 Iteration 4
EVOLUTIONARY OPTIMIZATION

Iteration 4 Configuration:
- hard_disc_color: 0.78 (was 0.76, +2.6%)
- hard_disc_texture: 0.73 (was 0.71, +2.8%)

Strategy: Maximum strictness for 95%+ both metrics
Target: 95%+ negative AND 95%+ positive
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

import hard_discriminators_variant0_iter4
sys.modules['hard_discriminators'] = hard_discriminators_variant0_iter4

import run_test

if __name__ == "__main__":
    print("="*80)
    print("VARIANT 0 - ITERATION 4: EVOLUTIONARY OPTIMIZATION")
    print("="*80)
    print()
    print("Configuration:")
    print("  - hard_disc_color: 0.78 (baseline: 0.70, +11.4%)")
    print("  - hard_disc_texture: 0.73 (baseline: 0.65, +12.3%)")
    print()
    print("Strategy: Maximum strictness")
    print("Target: 95%+ negative AND 95%+ positive")
    print("="*80)
    print()
    run_test.main()
