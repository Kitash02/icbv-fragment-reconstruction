#!/usr/bin/env python3
"""
Quick evolution test for Variant 5
Tests POWER_COLOR = 6.0, 7.0, 8.0 sequentially
"""

import subprocess
import re
import sys
from pathlib import Path

POWER_VALUES = [6.0, 7.0, 8.0]

def update_power_color(value):
    """Update POWER_COLOR in compatibility_variant5.py"""
    variant_path = Path("src/compatibility_variant5.py")

    with open(variant_path, 'r') as f:
        content = f.read()

    # Replace POWER_COLOR value
    content = re.sub(
        r'POWER_COLOR\s*=\s*[\d.]+',
        f'POWER_COLOR = {value}',
        content
    )

    with open(variant_path, 'w') as f:
        f.write(content)

    print(f"Updated POWER_COLOR to {value}")

def run_tests():
    """Run tests with --no-rotate"""
    result = subprocess.run(
        ['python', 'run_variant5.py', '--no-rotate'],
        capture_output=True,
        text=True,
        timeout=600
    )
    return result.stdout + result.stderr

def parse_results(output):
    """Parse test results from output"""
    lines = output.split('\n')

    positive_pass = 0
    positive_total = 0
    negative_pass = 0
    negative_total = 0

    for line in lines:
        if '[P]' in line:
            positive_total += 1
            if 'PASS' in line:
                positive_pass += 1
        elif '[N]' in line:
            negative_total += 1
            if 'PASS' in line:
                negative_pass += 1

    return {
        'positive_pass': positive_pass,
        'positive_total': positive_total,
        'negative_pass': negative_pass,
        'negative_total': negative_total,
        'positive_acc': (positive_pass / positive_total * 100) if positive_total > 0 else 0,
        'negative_acc': (negative_pass / negative_total * 100) if negative_total > 0 else 0,
        'overall_acc': ((positive_pass + negative_pass) / (positive_total + negative_total) * 100)
                       if (positive_total + negative_total) > 0 else 0
    }

def main():
    print("="*60)
    print("VARIANT 5 EVOLUTION TEST")
    print("="*60)
    print(f"Testing POWER_COLOR values: {POWER_VALUES}")
    print("Baseline (POWER_COLOR=4.0): ~77.8% overall")
    print()

    all_results = []

    for power in POWER_VALUES:
        print(f"\n{'='*60}")
        print(f"Testing POWER_COLOR = {power}")
        print(f"{'='*60}")

        try:
            # Update configuration
            update_power_color(power)

            # Run tests
            print("Running tests (this may take 3-5 minutes)...")
            output = run_tests()

            # Parse results
            results = parse_results(output)
            results['power_color'] = power
            all_results.append(results)

            print(f"\nResults for POWER_COLOR = {power}:")
            print(f"  Positive: {results['positive_pass']}/{results['positive_total']} = {results['positive_acc']:.1f}%")
            print(f"  Negative: {results['negative_pass']}/{results['negative_total']} = {results['negative_acc']:.1f}%")
            print(f"  Overall:  {results['overall_acc']:.1f}%")

        except subprocess.TimeoutExpired:
            print(f"  TIMEOUT after 10 minutes")
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    # Final report
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)

    if not all_results:
        print("No results obtained")
        return 1

    print(f"\n{'Power':<8} {'Positive':<12} {'Negative':<12} {'Overall':<10}")
    print(f"{'-'*8} {'-'*12} {'-'*12} {'-'*10}")

    for r in all_results:
        print(f"{r['power_color']:<8.1f} {r['positive_acc']:>6.1f}%     {r['negative_acc']:>6.1f}%     {r['overall_acc']:>6.1f}%")

    # Find best
    best = max(all_results, key=lambda x: x['overall_acc'])
    print(f"\nBest overall: POWER_COLOR = {best['power_color']} ({best['overall_acc']:.1f}%)")

    # Check targets
    print("\n" + "="*60)
    print("ANALYSIS")
    print("="*60)

    for r in all_results:
        power = r['power_color']
        pos = r['positive_acc']
        neg = r['negative_acc']

        print(f"\nPOWER_COLOR = {power}:")
        print(f"  Positive: {pos:.1f}%")
        print(f"  Negative: {neg:.1f}%")

        if pos >= 90 and neg >= 90:
            print(f"  ✓ ACHIEVES 90%+ on BOTH metrics!")
        elif pos >= 70 and neg >= 95:
            print(f"  ✓ Acceptable: 70%+ positive, 95%+ negative")
        else:
            print(f"  ✗ Below targets")

    # Expected vs actual
    expectations = {
        6.0: (70, 75, 92, 95),
        7.0: (65, 70, 95, 97),
        8.0: (60, 65, 97, 99)
    }

    print("\n" + "="*60)
    print("EXPECTED vs ACTUAL")
    print("="*60)

    for r in all_results:
        power = r['power_color']
        if power in expectations:
            exp = expectations[power]
            pos_actual = r['positive_acc']
            neg_actual = r['negative_acc']

            print(f"\nPOWER_COLOR = {power}:")
            print(f"  Expected: {exp[0]}-{exp[1]}% pos, {exp[2]}-{exp[3]}% neg")
            print(f"  Actual:   {pos_actual:.1f}% pos, {neg_actual:.1f}% neg")

            pos_ok = exp[0] <= pos_actual <= exp[1]
            neg_ok = exp[2] <= neg_actual <= exp[3]

            if pos_ok and neg_ok:
                print(f"  Status: ✓ Matches expectations")
            else:
                print(f"  Status: ✗ Outside expected range")

    return 0

if __name__ == '__main__':
    sys.exit(main())
