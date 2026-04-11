#!/usr/bin/env python3
"""
Manual Iterative Optimizer for Variant 6
=========================================

Run this script multiple times, each time it tests the next power value.
"""

import sys
import subprocess
import json
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
RESULTS_FILE = ROOT / "outputs" / "variant6_evolution_progress.json"

def load_progress():
    """Load previous test results."""
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_progress(results):
    """Save current progress."""
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)

def get_current_power():
    """Read current POWER_COLOR from variant6 file."""
    variant6_file = SRC / "compatibility_variant6.py"
    with open(variant6_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('POWER_COLOR = '):
                return float(line.split('=')[1].split('#')[0].strip())
    return 2.0

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

def parse_results(output):
    """Parse test output for metrics."""
    pos_pass = pos_total = neg_pass = neg_total = 0

    for line in output.split('\n'):
        if '[P]' in line:
            pos_total += 1
            if 'PASS' in line:
                pos_pass += 1
        elif '[N]' in line:
            neg_total += 1
            if 'PASS' in line:
                neg_pass += 1

    pos_acc = (pos_pass / pos_total * 100) if pos_total > 0 else 0
    neg_acc = (neg_pass / neg_total * 100) if neg_total > 0 else 0

    return {
        'pos_pass': pos_pass,
        'pos_total': pos_total,
        'pos_acc': pos_acc,
        'neg_pass': neg_pass,
        'neg_total': neg_total,
        'neg_acc': neg_acc
    }

def main():
    """Run one iteration of the evolution."""
    # Test sequence
    POWER_SEQUENCE = [2.0, 2.5, 3.0, 3.5, 4.0]

    # Load progress
    results = load_progress()
    tested_powers = [r['power'] for r in results]

    # Find next power to test
    next_power = None
    for power in POWER_SEQUENCE:
        if power not in tested_powers:
            next_power = power
            break

    if next_power is None:
        print("="*80)
        print("ALL ITERATIONS COMPLETE!")
        print("="*80)
        print("\nFinal Results:")
        print(f"{'Power':<8} {'Positive':<12} {'Negative':<12} {'Status'}")
        print("-"*80)
        for r in results:
            status = "[PASS]" if r['pos_acc'] >= 95 and r['neg_acc'] >= 95 else ""
            print(f"{r['power']:<8.1f} {r['pos_acc']:<12.1f} {r['neg_acc']:<12.1f} {status}")
        print("-"*80)

        best = max(results, key=lambda x: min(x['pos_acc'], x['neg_acc']))
        print(f"\nBest: POWER_COLOR = {best['power']}")
        print(f"  Positive: {best['pos_acc']:.1f}%")
        print(f"  Negative: {best['neg_acc']:.1f}%")
        return

    print("="*80)
    print(f"VARIANT 6 EVOLUTIONARY OPTIMIZATION")
    print("="*80)
    print(f"Testing POWER_COLOR = {next_power}")
    print(f"Progress: {len(results)}/{len(POWER_SEQUENCE)} iterations complete")
    print("="*80)
    print()

    # Update power
    update_power(next_power)

    # Run test
    print(f"Running test (this will take 3-5 minutes)...")
    print(f"Using: python test_variant6_simple.py --no-rotate")
    print()

    try:
        result = subprocess.run(
            [sys.executable, 'test_variant6_simple.py', '--no-rotate'],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=600
        )
        output = result.stdout + result.stderr

        # Parse results
        metrics = parse_results(output)
        metrics['power'] = next_power

        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        print(f"POWER_COLOR = {next_power}")
        print(f"  Positive: {metrics['pos_pass']}/{metrics['pos_total']} ({metrics['pos_acc']:.1f}%)")
        print(f"  Negative: {metrics['neg_pass']}/{metrics['neg_total']} ({metrics['neg_acc']:.1f}%)")

        if metrics['pos_acc'] >= 95 and metrics['neg_acc'] >= 95:
            print("\n  *** TARGET ACHIEVED! ***")
        elif metrics['pos_acc'] >= 95:
            print(f"\n  [+] Positive target met")
            print(f"  [-] Negative below target ({metrics['neg_acc']:.1f}% < 95%)")
        elif metrics['neg_acc'] >= 95:
            print(f"\n  [+] Negative target met")
            print(f"  [-] Positive below target ({metrics['pos_acc']:.1f}% < 95%)")
        else:
            print(f"\n  [-] Both metrics below target")

        print("="*80)

        # Save results
        results.append(metrics)
        save_progress(results)

        # Save full output
        output_file = ROOT / "outputs" / f"variant6_power{next_power}.txt"
        with open(output_file, 'w') as f:
            f.write(output)
        print(f"\nFull output saved to: {output_file}")

        # Next steps
        remaining = len(POWER_SEQUENCE) - len(results)
        if remaining > 0:
            print(f"\n{remaining} iteration(s) remaining.")
            print(f"Run this script again to test the next power value.")
        else:
            print(f"\nAll iterations complete! Run again to see final summary.")

    except subprocess.TimeoutExpired:
        print("\nERROR: Test timed out (>10 minutes)")
    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == "__main__":
    main()
