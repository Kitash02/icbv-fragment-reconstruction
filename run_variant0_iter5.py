#!/usr/bin/env python3
"""
Test runner for Variant 0 Iteration 5
EVOLUTIONARY OPTIMIZATION

Iteration 5 Configuration:
- hard_disc_color: 0.80 (was 0.78, +2.6%)
- hard_disc_texture: 0.75 (was 0.73, +2.7%)

Strategy: Ultra-strict (testing upper bounds)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

import hard_discriminators_variant0_iter5
sys.modules['hard_discriminators'] = hard_discriminators_variant0_iter5

import run_test

if __name__ == "__main__":
    print("="*80)
    print("VARIANT 0 - ITERATION 5: EVOLUTIONARY OPTIMIZATION")
    print("="*80)
    print()
    print("Configuration:")
    print("  - hard_disc_color: 0.80 (baseline: 0.70, +14.3%)")
    print("  - hard_disc_texture: 0.75 (baseline: 0.65, +15.4%)")
    print()
    print("Strategy: Ultra-strict (testing limits)")
    print("Warning: May sacrifice positive accuracy")
    print("="*80)
    print()
    run_test.main()
