#!/usr/bin/env python3
"""
Test runner for Variant 0D: ALL FIXES COMBINED

This variant combines ALL three fixes that showed promise individually:

1. STRICTER HARD DISCRIMINATORS (from previous testing)
   - MATCH_SCORE_THRESHOLD: 0.75 (was 0.55, +36%)
   - WEAK_MATCH_SCORE_THRESHOLD: 0.70 (was 0.35, +100%)

2. ENSEMBLE GATING (new approach)
   - Only upgrade WEAK_MATCH → MATCH if BOTH:
     * bc_color > 0.75
     * bc_texture > 0.70
   - Prevents false positive upgrades on cross-artifact pairs
   - Downgrades are NOT gated (asymmetric filter)

3. CURRENT COLOR PRE-CHECK (already in main.py)
   - COLOR_PRECHECK_GAP_THRESH: 0.15
   - COLOR_PRECHECK_LOW_MAX: 0.75
   - Rejects mixed-source datasets before expensive processing

Expected Results:
- Target: 85%+ negative accuracy, 75%+ positive accuracy
- This should be the optimal baseline configuration
- Should outperform any single fix alone

Strategy:
- Use stricter thresholds to reduce false positives at the hard discriminator level
- Add ensemble gating to catch remaining false positives at the upgrade stage
- Maintain current color pre-check for early rejection of mixed-source cases
- This creates a multi-layered defense against false positives
"""

import sys
import os
from pathlib import Path

# Add src to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

# Monkey-patch: Replace BOTH relaxation AND ensemble_postprocess modules with variant 0D
import relaxation_variant0D
import ensemble_postprocess_variant0D
sys.modules['relaxation'] = relaxation_variant0D
sys.modules['ensemble_postprocess'] = ensemble_postprocess_variant0D

# Now run the standard test suite
import run_test

if __name__ == "__main__":
    print("="*80)
    print("VARIANT 0D: ALL FIXES COMBINED")
    print("="*80)
    print()
    print("Configuration:")
    print("  1. STRICTER HARD DISCRIMINATORS")
    print("     - MATCH_SCORE_THRESHOLD: 0.75 (baseline: 0.55, +36%)")
    print("     - WEAK_MATCH_SCORE_THRESHOLD: 0.70 (baseline: 0.35, +100%)")
    print("     - ASSEMBLY_CONFIDENCE_THRESHOLD: 0.65 (unchanged)")
    print()
    print("  2. ENSEMBLE GATING (new)")
    print("     - Upgrade gate: bc_color > 0.75 AND bc_texture > 0.70")
    print("     - Only WEAK_MATCH -> MATCH upgrades are gated")
    print("     - Downgrades (WEAK_MATCH -> NO_MATCH) are NOT gated")
    print("     - Rationale: True matches have high color+texture similarity")
    print()
    print("  3. CURRENT COLOR PRE-CHECK (already in main.py)")
    print("     - COLOR_PRECHECK_GAP_THRESH: 0.15")
    print("     - COLOR_PRECHECK_LOW_MAX: 0.75")
    print("     - Rejects mixed-source datasets early")
    print()
    print("Expected Results:")
    print("  - Target: 85%+ negative accuracy (vs 73.1% baseline)")
    print("  - Target: 75%+ positive accuracy (vs 96.0% baseline)")
    print("  - This should be the optimal baseline configuration")
    print()
    print("Strategy:")
    print("  - Multi-layered defense against false positives:")
    print("    1. Color pre-check catches obvious mixed-source cases")
    print("    2. Stricter hard discriminators reduce false MATCH classifications")
    print("    3. Ensemble gating prevents false positive upgrades")
    print("  - Each layer is independent and addresses different failure modes")
    print("="*80)
    print()

    # Run standard benchmark
    run_test.main()
