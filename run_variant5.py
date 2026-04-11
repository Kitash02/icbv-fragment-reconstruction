"""
Test runner for Variant 5: Color-Dominant (color^6)

VARIANT 5 CONFIGURATION:
- More aggressive color penalty for better negative discrimination
- POWER_COLOR = 6.0 (was 4.0 in baseline)
- POWER_TEXTURE = 2.0
- POWER_GABOR = 2.0
- POWER_HARALICK = 2.0
- Same thresholds: 0.75 / 0.60 / 0.65

This runner monkey-patches compatibility_variant5 into sys.modules
so that run_test.py imports our variant instead of the baseline.
"""

import sys
sys.path.insert(0, "src")

# Monkey-patch: replace compatibility with compatibility_variant5
import compatibility_variant5
sys.modules['compatibility'] = compatibility_variant5

# Now run the test suite
import run_test
run_test.main()
