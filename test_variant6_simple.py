#!/usr/bin/env python3
"""Simple test runner for Variant 6 with monkey-patching."""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Monkey-patch compatibility_variant6 as 'compatibility'
import compatibility_variant6
sys.modules['compatibility'] = compatibility_variant6

print(f"Running Variant 6 test with:")
print(f"  POWER_COLOR = {compatibility_variant6.POWER_COLOR}")
print(f"  POWER_TEXTURE = {compatibility_variant6.POWER_TEXTURE}")
print(f"  POWER_GABOR = {compatibility_variant6.POWER_GABOR}")
print(f"  POWER_HARALICK = {compatibility_variant6.POWER_HARALICK}")
print()

# Run standard test
import run_test
run_test.main()
