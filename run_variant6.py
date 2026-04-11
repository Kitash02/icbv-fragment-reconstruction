"""
Variant 6: Balanced Powers (all^2) - Equal Feature Weighting Test Runner

This variant tests equal weighting across all appearance features by setting
all power exponents to 2.0. This reduces the dominance of color features and
may improve positive recall at the cost of some cross-source discrimination.

Configuration:
- POWER_COLOR = 2.0 (was 4.0 in baseline)
- POWER_TEXTURE = 2.0
- POWER_GABOR = 2.0
- POWER_HARALICK = 2.0
- Same thresholds: 0.75 / 0.60 / 0.65

Hypothesis: Equal weighting will increase positive recall (fewer missed true
matches) but may allow more false positives. This tests whether the baseline's
color^4 term was too aggressive.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Monkey-patch compatibility_variant6 into sys.modules as 'compatibility'
import compatibility_variant6
sys.modules['compatibility'] = compatibility_variant6

# Now run the standard evaluation
from evaluate_reconstruction import main

if __name__ == '__main__':
    print("=" * 80)
    print("VARIANT 6: Balanced Powers (all^2)")
    print("=" * 80)
    print("Configuration:")
    print("  POWER_COLOR = 2.0 (was 4.0)")
    print("  POWER_TEXTURE = 2.0")
    print("  POWER_GABOR = 2.0")
    print("  POWER_HARALICK = 2.0")
    print("  Thresholds: 0.75 / 0.60 / 0.65 (unchanged)")
    print()
    print("Hypothesis: Equal feature weighting for better positive recall")
    print("=" * 80)
    print()

    main()
