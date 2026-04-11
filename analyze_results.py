#!/usr/bin/env python3
"""
Analyze results from all 10 variants that just completed.
"""

import re
from pathlib import Path

def parse_variant_output(variant_id):
    """Parse output file and extract metrics."""
    file_path = Path(f"outputs/variant{variant_id}.txt")

    if not file_path.exists():
        return None

    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except:
        return None

    lines = content.split('\n')

    # Count PASS/FAIL
    positive_pass = positive_total = 0
    negative_pass = negative_total = 0

    for line in lines:
        if '[P]' in line:
            positive_total += 1
            if 'PASS' in line:
                positive_pass += 1
        elif '[N]' in line:
            negative_total += 1
            if 'PASS' in line:
                negative_pass += 1

    if positive_total == 0 and negative_total == 0:
        return None

    pos_acc = (positive_pass / positive_total * 100) if positive_total > 0 else 0
    neg_acc = (negative_pass / negative_total * 100) if negative_total > 0 else 0
    overall_acc = ((positive_pass + negative_pass) / (positive_total + negative_total) * 100) if (positive_total + negative_total) > 0 else 0

    return {
        'variant_id': variant_id,
        'positive_pass': positive_pass,
        'positive_total': positive_total,
        'positive_acc': pos_acc,
        'negative_pass': negative_pass,
        'negative_total': negative_total,
        'negative_acc': neg_acc,
        'overall_acc': overall_acc
    }

def main():
    print("="*80)
    print("VARIANT TESTING RESULTS - ANALYSIS")
    print("="*80)
    print()

    results = []
    for vid in range(10):
        result = parse_variant_output(vid)
        if result:
            results.append(result)

    if not results:
        print("ERROR: No results found!")
        print("Tests may still be running or output files are incomplete.")
        return

    # Summary table
    print(f"{'ID':<4} {'Positive':<15} {'Negative':<15} {'Overall':<10}")
    print(f"{'-'*4} {'-'*15} {'-'*15} {'-'*10}")

    for r in results:
        pos_str = f"{r['positive_pass']}/{r['positive_total']} ({r['positive_acc']:.1f}%)"
        neg_str = f"{r['negative_pass']}/{r['negative_total']} ({r['negative_acc']:.1f}%)"
        overall_str = f"{r['overall_acc']:.1f}%"

        print(f"{r['variant_id']:<4} {pos_str:<15} {neg_str:<15} {overall_str:<10}")

    # Find best
    if results:
        best_overall = max(results, key=lambda x: x['overall_acc'])
        best_positive = max(results, key=lambda x: x['positive_acc'])
        best_negative = max(results, key=lambda x: x['negative_acc'])

        print()
        print("="*80)
        print("BEST PERFORMERS")
        print("="*80)
        print(f"Best Overall:  Variant {best_overall['variant_id']} - {best_overall['overall_acc']:.1f}%")
        print(f"Best Positive: Variant {best_positive['variant_id']} - {best_positive['positive_acc']:.1f}%")
        print(f"Best Negative: Variant {best_negative['variant_id']} - {best_negative['negative_acc']:.1f}%")

        # Check target
        print()
        print("="*80)
        print("TARGET ANALYSIS (95%+ both metrics)")
        print("="*80)

        tier1 = [r for r in results if r['positive_acc'] >= 95 and r['negative_acc'] >= 95]
        tier2 = [r for r in results if r['positive_acc'] >= 90 and r['negative_acc'] >= 90 and r not in tier1]

        if tier1:
            print(f"\n*** SUCCESS! {len(tier1)} variant(s) achieved 95%+ target:")
            for r in tier1:
                print(f"  Variant {r['variant_id']}: {r['positive_acc']:.1f}% pos, {r['negative_acc']:.1f}% neg")
        elif tier2:
            print(f"\n*** GOOD! {len(tier2)} variant(s) achieved 90%+ (Tier 2):")
            for r in tier2:
                print(f"  Variant {r['variant_id']}: {r['positive_acc']:.1f}% pos, {r['negative_acc']:.1f}% neg")
        else:
            print("\n*** No variants reached 90%+ target.")
            print(f"Best overall: Variant {best_overall['variant_id']} with {best_overall['overall_acc']:.1f}%")

if __name__ == "__main__":
    main()
