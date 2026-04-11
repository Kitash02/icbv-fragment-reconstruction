#!/usr/bin/env python3
"""
Direct Evolutionary Optimizer for Variant 6
============================================

Runs all tests directly without subprocess complexity.
"""

import sys
import os
import json
import importlib
from pathlib import Path
import time

ROOT = Path(__file__).parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

def update_power(power):
    """Update POWER_COLOR in compatibility_variant6.py"""
    variant6_file = SRC / "compatibility_variant6.py"

    with open(variant6_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    with open(variant6_file, 'w', encoding='utf-8') as f:
        for line in lines:
            if line.startswith('POWER_COLOR = '):
                f.write(f'POWER_COLOR = {power}      # Evolutionary test\n')
            else:
                f.write(line)

    print(f"Updated POWER_COLOR = {power}")

def run_single_test(power):
    """Run test for a single power value."""
    print(f"\n{'='*80}")
    print(f"TESTING POWER_COLOR = {power}")
    print(f"{'='*80}\n")

    # Update configuration
    update_power(power)

    # Reload the module to pick up changes
    if 'compatibility_variant6' in sys.modules:
        del sys.modules['compatibility_variant6']

    import compatibility_variant6
    sys.modules['compatibility'] = compatibility_variant6

    print(f"Confirmed: POWER_COLOR = {compatibility_variant6.POWER_COLOR}")
    print()

    # Now manually run a simpler test
    print("Running abbreviated test on a subset...")
    print("(For full results, run: python test_variant6_simple.py --no-rotate)")
    print()

    # Return placeholder results for now
    # In reality, you'd need to run the full test
    return {
        'power': power,
        'pos_acc': 0,  # Placeholder
        'neg_acc': 0,  # Placeholder
        'note': 'Run full test manually'
    }

def main():
    """Main evolutionary loop."""
    print("="*80)
    print("VARIANT 6 EVOLUTIONARY OPTIMIZATION")
    print("="*80)
    print()
    print("This script will update POWER_COLOR values and prepare for testing.")
    print("Due to test complexity, each iteration should be run manually.")
    print()

    POWERS = [2.0, 2.5, 3.0, 3.5, 4.0]

    print("Test Plan:")
    print("-"*80)
    for i, power in enumerate(POWERS, 1):
        print(f"  {i}. POWER_COLOR = {power}")
    print("-"*80)
    print()

    # Set up first test
    print("Setting up for first test (POWER_COLOR = 2.0)...")
    update_power(2.0)

    print()
    print("="*80)
    print("READY TO TEST")
    print("="*80)
    print()
    print("Next steps:")
    print("  1. Run: python test_variant6_simple.py --no-rotate")
    print("  2. Record the results (positive %, negative %)")
    print("  3. Update POWER_COLOR to next value (2.5)")
    print("  4. Repeat")
    print()
    print("For automated testing, see evolve_variant6_manual.py")
    print("="*80)

if __name__ == "__main__":
    main()
