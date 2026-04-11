#!/usr/bin/env python3
"""
Quick Variant 9 Optimizer - Tests key configurations in sequence

Strategy:
1. Start with baseline Variant 9
2. Test 3-4 promising weight configurations
3. Test 2-3 threshold configurations with best weights
4. Report best configuration

This is faster than full grid search.
"""

import sys
import subprocess
from pathlib import Path
import re
import json

ROOT = Path(__file__).parent

def run_quick_test(variant_name, description):
    """Run a quick test and return results."""
    print(f"\n{'='*80}")
    print(f"Testing: {variant_name}")
    print(f"Description: {description}")
    print(f"{'='*80}")

    cmd = [sys.executable, f"run_{variant_name}.py"]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=400
        )
        output = result.stdout + result.stderr

        # Extract accuracy
        pos_match = re.search(r'Positive Tests.*?(\d+)/(\d+).*?\((\d+(?:\.\d+)?)%\)', output, re.DOTALL)
        neg_match = re.search(r'Negative Tests.*?(\d+)/(\d+).*?\((\d+(?:\.\d+)?)%\)', output, re.DOTALL)

        if pos_match and neg_match:
            pos_acc = float(pos_match.group(3))
            neg_acc = float(neg_match.group(3))
            overall = (int(pos_match.group(1)) + int(neg_match.group(1))) / \
                     (int(pos_match.group(2)) + int(neg_match.group(2))) * 100

            print(f"\n✓ Results: Pos={pos_acc:.1f}%, Neg={neg_acc:.1f}%, Overall={overall:.1f}%")

            return {
                'variant': variant_name,
                'description': description,
                'positive_accuracy': pos_acc,
                'negative_accuracy': neg_acc,
                'overall_accuracy': overall
            }
        else:
            print(f"\n✗ Failed to parse results")
            return None

    except subprocess.TimeoutExpired:
        print(f"\n✗ Test timed out")
        return None
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None


def main():
    """Run quick optimization tests."""
    print("="*80)
    print("QUICK VARIANT 9 OPTIMIZER")
    print("Testing key configurations to find best setup")
    print("="*80)

    results = []

    # Test existing variants to establish baseline
    variants_to_test = [
        ('variant9', 'Baseline: Weighted ensemble + adaptive thresholds'),
        ('variant8', 'Comparison: Hierarchical routing'),
        ('variant7', 'Comparison: Relaxed thresholds only'),
        ('variant0D', 'Comparison: Latest Stage 1.6 baseline'),
    ]

    for variant, desc in variants_to_test:
        result = run_quick_test(variant, desc)
        if result:
            results.append(result)

    # Find best
    if results:
        best = max(results, key=lambda x: x['overall_accuracy'])

        print("\n" + "="*80)
        print("QUICK OPTIMIZATION RESULTS")
        print("="*80)

        print("\nAll Results:")
        for r in sorted(results, key=lambda x: x['overall_accuracy'], reverse=True):
            print(f"  {r['variant']:15s}: Pos={r['positive_accuracy']:5.1f}% "
                  f"Neg={r['negative_accuracy']:5.1f}% Overall={r['overall_accuracy']:5.1f}%")

        print(f"\n{'='*80}")
        print(f"BEST CONFIGURATION: {best['variant']}")
        print(f"{'='*80}")
        print(f"Description: {best['description']}")
        print(f"Positive Accuracy: {best['positive_accuracy']:.1f}%")
        print(f"Negative Accuracy: {best['negative_accuracy']:.1f}%")
        print(f"Overall Accuracy: {best['overall_accuracy']:.1f}%")

        if best['positive_accuracy'] >= 95.0 and best['negative_accuracy'] >= 95.0:
            print("\n✅ TARGET ACHIEVED: 95%+ accuracy on both metrics!")
        else:
            print(f"\n⚠️ Gap to 95%: Pos={95.0 - best['positive_accuracy']:.1f}%, "
                  f"Neg={95.0 - best['negative_accuracy']:.1f}%")

        # Save results
        output_file = ROOT / "outputs" / "evolution" / "quick_optimization_results.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✓ Results saved to: {output_file}")

    else:
        print("\n✗ No results obtained")


if __name__ == "__main__":
    main()
