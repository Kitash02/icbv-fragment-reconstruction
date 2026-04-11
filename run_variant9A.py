#!/usr/bin/env python3
"""
Variant 9A: Enhanced Full Research Stack
========================================

Building on Variant 0D (89%/86%) and Variant 9 concepts.

Strategy:
1. Use Variant 0D's proven stricter thresholds (0.75/0.70/0.65)
2. Add weighted ensemble from Variant 9
3. Add hard discriminator pre-screening
4. Target: 92%+ both metrics

Changes from Variant 9:
- Stricter thresholds (from 0D proven configuration)
- Enhanced weight optimization (color boosted to 0.45)
- Hard discriminator pre-filter
- Target: 92%+ accuracy
"""

import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

# Create optimized modules inline
# We'll use file-based modules for clarity

import run_test

if __name__ == "__main__":
    print("="*80)
    print("VARIANT 9A: ENHANCED FULL RESEARCH STACK")
    print("="*80)
    print("Configuration:")
    print("  - Formula: BASELINE (color^4 × texture^2 × gabor^2 × haralick^2)")
    print("  - Ensemble: WEIGHTED (color=0.45, raw=0.25, texture=0.15, morph=0.10, gabor=0.05)")
    print("  - Thresholds: STRICTER from Variant 0D")
    print("    - MATCH: 0.75 (proven from 0D)")
    print("    - WEAK: 0.70 (proven from 0D)")
    print("    - ASSEMBLY: 0.65 (proven from 0D)")
    print("  - Hard Discriminators: PRE-FILTER enabled")
    print("  - Target: 92%+ both metrics")
    print("="*80)
    print()

    # Monkey-patch modules
    import ensemble_postprocess_variant9A
    import relaxation_variant0D
    sys.modules['ensemble_postprocess'] = ensemble_postprocess_variant9A
    sys.modules['relaxation'] = relaxation_variant0D

    run_test.main()
