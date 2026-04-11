"""
Variant 7: Optimized Powers

Changes from baseline compatibility.py:
- POWER_COLOR: 5.0 (was 4.0)
- POWER_TEXTURE: 2.5 (was 2.0)

Goal: Optimized balance between color and texture discrimination.
Slightly more emphasis on color, and increased texture contribution.
"""

# Import everything from baseline
from compatibility import *

# Override powers for optimized discrimination
POWER_COLOR = 5.0     # Increased from 4.0
POWER_TEXTURE = 2.5   # Increased from 2.0
