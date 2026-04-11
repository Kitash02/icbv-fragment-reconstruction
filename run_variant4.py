#!/usr/bin/env python3
"""
Test runner for Variant 4: Relaxed Thresholds

Changes from Stage 1.6:
- Same formula as baseline
- Relaxed thresholds: 0.70 / 0.55 / 0.60 (vs baseline 0.75 / 0.60 / 0.65)
- Target: Higher recall at potential cost of precision
"""

import sys
import os
from pathlib import Path

# Add src to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

# Monkey-patch: Replace relaxation module with variant 4
import relaxation_variant4
sys.modules['relaxation'] = relaxation_variant4

# Now run the standard test suite
import run_test

if __name__ == "__main__":
    print("="*80)
    print("VARIANT 4: RELAXED THRESHOLDS")
    print("="*80)
    print("Configuration:")
    print("  - Formula: Stage 1.6 baseline (color^4 × texture^2 × gabor^2 × haralick^2)")
    print("  - Thresholds: RELAXED 0.70 / 0.55 / 0.60 (vs baseline 0.75 / 0.60 / 0.65)")
    print("    - MATCH: ≥ 0.70 (was 0.75)")
    print("    - WEAK_MATCH: ≥ 0.55 (was 0.60)")
    print("    - ASSEMBLY: ≥ 0.60 (was 0.65)")
    print("  - Ensemble: Baseline (five-way voting)")
    print("  - Target: Higher recall (more matches detected)")
    print("="*80)
    print()

    # Run standard benchmark
    run_test.main()
