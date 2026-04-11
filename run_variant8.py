#!/usr/bin/env python3
"""
Test runner for Variant 8: Adaptive Thresholds

Changes from Stage 1.6:
- Same formula as baseline
- KEY CHANGE: Different thresholds based on artifact appearance variance
  - High variance artifacts (scroll, wall painting): 0.70 / 0.55
  - Low variance artifacts (pottery sherds): 0.75 / 0.60
  - Detect artifact type by computing appearance variance from compatibility matrix
- Description: "Adaptive thresholds per artifact type"
- Target: Context-aware threshold selection based on artifact characteristics
"""

import sys
import os
from pathlib import Path

# Add src to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

# Monkey-patch: Replace relaxation module with variant 8
import relaxation_variant8
sys.modules['relaxation'] = relaxation_variant8

# Now run the standard test suite
import run_test

if __name__ == "__main__":
    print("="*80)
    print("VARIANT 8: ADAPTIVE THRESHOLDS PER ARTIFACT TYPE")
    print("="*80)
    print("Configuration:")
    print("  - Formula: Stage 1.6 baseline (same as baseline)")
    print("  - Thresholds: ADAPTIVE based on appearance variance")
    print()
    print("  Detection method:")
    print("    - Compute standard deviation of compatibility scores")
    print("    - High variance (std > 0.20): scroll, wall painting")
    print("    - Low variance (std <= 0.20): pottery sherds")
    print()
    print("  Threshold profiles:")
    print("    - High variance artifacts: 0.70 / 0.55 (relaxed)")
    print("      → Scrolls, wall paintings with decorations")
    print("    - Low variance artifacts: 0.75 / 0.60 (stricter)")
    print("      → Plain pottery sherds")
    print()
    print("  - Ensemble: Baseline (five-way voting)")
    print("  - Target: Context-aware classification based on artifact appearance")
    print("="*80)
    print()

    # Run standard benchmark
    run_test.main()
