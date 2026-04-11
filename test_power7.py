#!/usr/bin/env python3
"""
Single test for Variant 5 with POWER_COLOR = 7.0
"""

import subprocess
import re
import sys
from pathlib import Path

def update_power_color(value):
    """Update POWER_COLOR in compatibility_variant5.py"""
    variant_path = Path("src/compatibility_variant5.py")

    with open(variant_path, 'r') as f:
        content = f.read()

    # Replace POWER_COLOR value
    content = re.sub(
        r'(POWER_COLOR\s*=\s*)[\d.]+',
        f'\\g<1>{value}',
        content
    )

    with open(variant_path, 'w') as f:
        f.write(content)

    print(f"Updated POWER_COLOR to {value}")

def main():
    power = 7.0

    print("="*60)
    print(f"VARIANT 5 TEST: POWER_COLOR = {power}")
    print("="*60)

    # Update configuration
    update_power_color(power)

    # Run tests
    print("\nRunning full 45-case test suite...")
    print("(This will take approximately 3-5 minutes)\n")

    result = subprocess.run(
        ['python', 'run_variant5.py', '--no-rotate'],
        text=True
    )

    print("\n" + "="*60)
    print(f"Test completed with return code: {result.returncode}")
    print("="*60)

    return result.returncode

if __name__ == '__main__':
    sys.exit(main())
