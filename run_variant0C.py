#!/usr/bin/env python3
"""
Test runner for Variant 0C: Ensemble Gating to Prevent False Positives

This variant adds safety checks BEFORE upgrading WEAK_MATCH → MATCH:
- After ensemble voting suggests MATCH, verify appearance quality
- If color < 0.75 OR texture < 0.70, downgrade back to WEAK_MATCH
- Prevents cross-source false positives (good geometry, weak appearance)

Key Change:
- Uses ensemble_postprocess_variant0C.py with appearance gating logic
- All other components unchanged (compatibility, relaxation, etc.)

Target: Negative accuracy 80%+ by preventing wrong upgrades
"""

import sys
import os
from pathlib import Path

# Add src to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

# Monkey-patch to use variant 0C ensemble module
import main as pipeline_main

# Replace the ensemble_postprocess import with variant 0C
import ensemble_postprocess_variant0C
sys.modules['ensemble_postprocess'] = ensemble_postprocess_variant0C

# Run the standard test suite
import run_test

if __name__ == "__main__":
    print("="*80)
    print("VARIANT 0C: ENSEMBLE GATING (Prevent False Positive Upgrades)")
    print("="*80)
    print("Configuration:")
    print("  - Formula: color^4 × texture^2 × gabor^2 × haralick^2 (unchanged)")
    print("  - Thresholds: 0.75 / 0.60 / 0.65 (unchanged)")
    print("  - Ensemble: 5-way voting WITH GATING")
    print("  - Gating rule: if ensemble says MATCH but color<0.75 OR texture<0.70:")
    print("                 -> downgrade to WEAK_MATCH")
    print("  - Target: Negative accuracy 80%+ (prevent cross-source false positives)")
    print("="*80)
    print()

    # Run standard benchmark with variant 0C ensemble gating
    run_test.main()
