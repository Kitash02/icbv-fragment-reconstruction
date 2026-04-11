#!/usr/bin/env python3
"""
Streamlined Evolutionary Optimizer for Variant 6
=================================================

Systematically tests color power values: 2.0, 2.5, 3.0, 3.5, 4.0
to find the optimal balance between positive and negative accuracy.
"""

import sys
import subprocess
import json
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"

def update_color_power(power: float):
    """Update POWER_COLOR in compatibility_variant6.py"""
    variant6_file = SRC / "compatibility_variant6.py"

    with open(variant6_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    with open(variant6_file, 'w', encoding='utf-8') as f:
        for line in lines:
            if line.startswith('POWER_COLOR = '):
                f.write(f'POWER_COLOR = {power}      # Evolutionary optimization\n')
            else:
                f.write(line)

    print(f"Updated POWER_COLOR = {power}")

def run_test(power: float) -> dict:
    """Run test with given color power and return metrics."""
    print(f"\n{'='*80}")
    print(f"Testing POWER_COLOR = {power}")
    print(f"{'='*80}\n")

    # Update configuration
    update_color_power(power)

    # Run test
    try:
        result = subprocess.run(
            [sys.executable, 'test_variant6_simple.py', '--no-rotate'],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=300
        )
        output = result.stdout + result.stderr

        # Parse results
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

        print(f"\nResults:")
        print(f"  Positive: {pos_pass}/{pos_total} ({pos_acc:.1f}%)")
        print(f"  Negative: {neg_pass}/{neg_total} ({neg_acc:.1f}%)")

        # Save output
        output_file = ROOT / "outputs" / f"variant6_power{power}.txt"
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
            'success': pos_acc >= 95 and neg_acc >= 95
        }

    except subprocess.TimeoutExpired:
        print("TEST TIMEOUT")
        return {
            'power': power,
            'pos_acc': 0, 'neg_acc': 0,
            'pos_pass': 0, 'pos_total': 0,
            'neg_pass': 0, 'neg_total': 0,
            'success': False
        }
    except Exception as e:
        print(f"TEST ERROR: {e}")
        return {
            'power': power,
            'pos_acc': 0, 'neg_acc': 0,
            'pos_pass': 0, 'pos_total': 0,
            'neg_pass': 0, 'neg_total': 0,
            'success': False
        }

def main():
    """Run evolutionary search."""
    print("="*80)
    print("EVOLUTIONARY OPTIMIZATION: Variant 6")
    print("="*80)
    print("Strategy: Test color powers 2.0, 2.5, 3.0, 3.5, 4.0")
    print("Target: 95%+ positive AND 95%+ negative accuracy")
    print("="*80)

    powers = [2.0, 2.5, 3.0, 3.5, 4.0]
    results = []

    for i, power in enumerate(powers, 1):
        print(f"\n[Iteration {i}/{len(powers)}]")
        metrics = run_test(power)
        results.append(metrics)

        if metrics['success']:
            print(f"\n*** TARGET ACHIEVED with POWER_COLOR = {power} ***")
            break

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"{'Power':<8} {'Positive':<12} {'Negative':<12} {'Status'}")
    print("-"*80)

    for r in results:
        pos = r['pos_acc']
        neg = r['neg_acc']
        status = "[PASS]" if r['success'] else "  "
        print(f"{r['power']:<8.1f} {pos:<12.1f} {neg:<12.1f} {status}")

    print("-"*80)

    # Find best
    best = max(results, key=lambda x: min(x['pos_acc'], x['neg_acc']))
    print(f"\nBest configuration: POWER_COLOR = {best['power']}")
    print(f"  Positive: {best['pos_acc']:.1f}%")
    print(f"  Negative: {best['neg_acc']:.1f}%")

    if best['success']:
        print(f"  [SUCCESS] Target achieved!")
    else:
        print(f"  [PARTIAL] Target not achieved, but best effort")

    # Save results
    results_file = ROOT / "outputs" / "variant6_evolution.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {results_file}")
    print("="*80)

if __name__ == "__main__":
    main()
