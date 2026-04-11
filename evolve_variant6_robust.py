#!/usr/bin/env python3
"""
Robust Evolutionary Optimizer for Variant 6
============================================

Runs complete evolutionary optimization by directly executing test code.
"""

import sys
import os
from pathlib import Path
import json
import time

# Setup paths
ROOT = Path(__file__).parent
SRC = ROOT / "src"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SRC))

def update_power(power: float):
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

    print(f"  > Set POWER_COLOR = {power}")

def parse_summary_line(line: str):
    """Parse a line like '  > [P] case_name  + MATCH  45.2s  PASS'"""
    if '[P]' in line:
        is_positive = True
    elif '[N]' in line:
        is_positive = False
    else:
        return None, None

    is_pass = 'PASS' in line
    return is_positive, is_pass

def count_results(output_lines):
    """Count passes and totals from test output."""
    pos_pass = pos_total = neg_pass = neg_total = 0

    for line in output_lines:
        is_positive, is_pass = parse_summary_line(line)

        if is_positive is None:
            continue

        if is_positive:
            pos_total += 1
            if is_pass:
                pos_pass += 1
        else:
            neg_total += 1
            if is_pass:
                neg_pass += 1

    return pos_pass, pos_total, neg_pass, neg_total

def run_test_with_power(power: float, iteration: int):
    """Run test with specified power value."""

    print(f"\n{'='*80}")
    print(f"ITERATION {iteration}: POWER_COLOR = {power}")
    print(f"{'='*80}")

    # Update configuration
    update_power(power)

    # Force reload of compatibility module
    if 'compatibility_variant6' in sys.modules:
        del sys.modules['compatibility_variant6']
    if 'compatibility' in sys.modules:
        del sys.modules['compatibility']

    # Import and monkey-patch
    import compatibility_variant6
    sys.modules['compatibility'] = compatibility_variant6

    # Verify
    actual_power = compatibility_variant6.POWER_COLOR
    if abs(actual_power - power) > 0.01:
        print(f"  WARNING: Expected {power}, got {actual_power}")

    print(f"  > Running test suite...")
    print(f"  > This will take 3-5 minutes...")
    print()

    # Capture output
    output_lines = []

    # Run the test by importing and executing run_test
    try:
        # Clear any previous run_test module
        if 'run_test' in sys.modules:
            del sys.modules['run_test']

        # Import run_test (which uses our monkey-patched compatibility)
        import run_test

        # Create mock arguments
        class Args:
            examples = "data/examples"
            results = f"outputs/test_results_power{power}"
            logs = f"outputs/test_logs_power{power}"
            rotate = False
            positive_only = False
            negative_only = False
            seed = 42

        # Redirect stdout to capture output
        import io
        from contextlib import redirect_stdout

        captured = io.StringIO()

        with redirect_stdout(captured):
            # Build parser and run
            import argparse
            import numpy as np
            import random

            np.random.seed(42)
            random.seed(42)

            try:
                # Run the main test function
                run_test.main()
            except SystemExit:
                pass  # main() calls sys.exit()

        output = captured.getvalue()
        output_lines = output.split('\n')

        # Parse results
        pos_pass, pos_total, neg_pass, neg_total = count_results(output_lines)

        pos_acc = (pos_pass / pos_total * 100) if pos_total > 0 else 0
        neg_acc = (neg_pass / neg_total * 100) if neg_total > 0 else 0

        print(f"\n{'='*80}")
        print(f"RESULTS FOR POWER_COLOR = {power}")
        print(f"{'='*80}")
        print(f"  Positive: {pos_pass}/{pos_total} ({pos_acc:.1f}%)")
        print(f"  Negative: {neg_pass}/{neg_total} ({neg_acc:.1f}%)")

        success = (pos_acc >= 95 and neg_acc >= 95)

        if success:
            print(f"  [SUCCESS] Target achieved!")
        elif pos_acc >= 95:
            print(f"  [+] Positive target met")
            print(f"  [-] Negative below target")
        elif neg_acc >= 95:
            print(f"  [+] Negative target met")
            print(f"  [-] Positive below target")
        else:
            print(f"  [-] Both below target")

        print(f"{'='*80}")

        # Save output
        output_file = ROOT / "outputs" / f"variant6_power{power}_full.txt"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(output)

        return {
            'power': power,
            'pos_pass': pos_pass,
            'pos_total': pos_total,
            'pos_acc': pos_acc,
            'neg_pass': neg_pass,
            'neg_total': neg_total,
            'neg_acc': neg_acc,
            'success': success
        }

    except Exception as e:
        print(f"\n  ERROR running test: {e}")
        import traceback
        traceback.print_exc()

        return {
            'power': power,
            'pos_acc': 0, 'neg_acc': 0,
            'pos_pass': 0, 'pos_total': 0,
            'neg_pass': 0, 'neg_total': 0,
            'success': False,
            'error': str(e)
        }

def main():
    """Main evolutionary loop."""

    print("="*80)
    print("VARIANT 6 EVOLUTIONARY OPTIMIZATION")
    print("="*80)
    print()
    print("Configuration:")
    print("  Test sequence: POWER_COLOR = 2.0, 2.5, 3.0, 3.5, 4.0")
    print("  Target: 95%+ positive AND 95%+ negative accuracy")
    print("  Strategy: Find minimum power for 95%+ on both metrics")
    print("="*80)

    POWERS = [2.0, 2.5, 3.0, 3.5, 4.0]
    results = []

    for iteration, power in enumerate(POWERS, start=1):
        print(f"\nStarting iteration {iteration}/{len(POWERS)}...")

        metrics = run_test_with_power(power, iteration)
        results.append(metrics)

        # Early stopping if target achieved
        if metrics['success']:
            print(f"\n*** TARGET ACHIEVED AT POWER_COLOR = {power} ***")
            print(f"*** Stopping early (no need to test remaining values) ***")
            break

        # Brief pause between iterations
        if iteration < len(POWERS):
            print(f"\nWaiting 5 seconds before next iteration...")
            time.sleep(5)

    # Final summary
    print(f"\n{'='*80}")
    print("EVOLUTIONARY OPTIMIZATION COMPLETE")
    print(f"{'='*80}")
    print()
    print(f"{'Iter':<6} {'Power':<8} {'Positive':<12} {'Negative':<12} {'Status'}")
    print("-"*80)

    for i, r in enumerate(results, 1):
        status = "[PASS]" if r.get('success', False) else ""
        print(f"{i:<6} {r['power']:<8.1f} {r['pos_acc']:<12.1f} {r['neg_acc']:<12.1f} {status}")

    print("-"*80)
    print()

    # Best configuration
    best = max(results, key=lambda x: min(x['pos_acc'], x['neg_acc']))

    print("Best Configuration:")
    print(f"  POWER_COLOR = {best['power']}")
    print(f"  Positive:    {best['pos_acc']:.1f}%")
    print(f"  Negative:    {best['neg_acc']:.1f}%")

    if best['success']:
        print(f"\n  [SUCCESS] Target of 95%+ on BOTH metrics achieved!")
    else:
        print(f"\n  [PARTIAL] Target not fully achieved - best effort shown")

    # Save results
    results_file = ROOT / "outputs" / "variant6_evolution_final.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n  Results saved to: {results_file}")
    print(f"{'='*80}")

if __name__ == "__main__":
    # Ensure we're in the right directory
    os.chdir(ROOT)
    main()
