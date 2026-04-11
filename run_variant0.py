#!/usr/bin/env python3
"""
Test runner for Variant 0: Stage 1.6 Baseline (Control)

This is the baseline configuration with NO changes:
- Formula: color^4 × texture^2 × gabor^2 × haralick^2
- Thresholds: 0.75 / 0.60 / 0.65
- Ensemble: 5-way voting
- Expected: 89% positive, 86% negative (39/45 pass)
"""

import sys
import os
from pathlib import Path

# Add src to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

# Run the standard test suite with NO modifications
import run_test

if __name__ == "__main__":
    print("="*80)
    print("VARIANT 0: STAGE 1.6 BASELINE (CONTROL)")
    print("="*80)
    print("Configuration:")
    print("  - Formula: color^4 × texture^2 × gabor^2 × haralick^2")
    print("  - Thresholds: 0.75 / 0.60 / 0.65")
    print("  - Ensemble: 5-way voting")
    print("  - Expected: 89%/86% (baseline for comparison)")
    print("="*80)
    print()

    # Run standard benchmark with NO changes
    run_test.main()
