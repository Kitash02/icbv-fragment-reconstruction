#!/usr/bin/env python3
"""
Variant 0B Test Runner - EVEN STRICTER Hard Discriminators

This script monkey-patches the hard_discriminators module with variant0B
that uses EVEN STRICTER thresholds:
- bc_color < 0.75 (was 0.70)
- bc_texture < 0.70 (was 0.65)

TARGET: Eliminate remaining 9 false positives
EXPECTED: Negative accuracy 85%+ (from current 75%)
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Monkey-patch BEFORE importing run_test
import src.hard_discriminators_variant0B as variant0B
sys.modules['src.hard_discriminators'] = variant0B

# Now import and run the test
from run_test import main

if __name__ == "__main__":
    print("=" * 80)
    print("VARIANT 0B: EVEN STRICTER Hard Discriminators")
    print("=" * 80)
    print("Changes:")
    print("  - bc_color threshold: 0.70 -> 0.75")
    print("  - bc_texture threshold: 0.65 -> 0.70")
    print("Target: Eliminate 9 false positives (getty 17009652 & 21778090)")
    print("=" * 80)
    print()

    # Run the test
    main()
