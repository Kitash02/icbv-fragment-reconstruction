#!/usr/bin/env python3
"""
Simple sequential runner for all 10 variants.
Runs variants 0-9 one at a time and extracts key metrics.
"""

import subprocess
import sys
import time
from pathlib import Path

def run_variant(variant_id):
    """Run a single variant and extract results."""
    print(f"\n{'='*80}")
    print(f"RUNNING VARIANT {variant_id}")
    print(f"{'='*80}\n")

    start_time = time.time()

    try:
        result = subprocess.run(
            [sys.executable, f"run_variant{variant_id}.py", "--no-rotate"],
            capture_output=True,
            text=True,
            timeout=300  # 5 min timeout per variant
        )

        elapsed = time.time() - start_time

        # Parse output
        output = result.stdout
        lines = output.split('\n')

        # Count results
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

        # Calculate accuracies
        pos_acc = (positive_pass / positive_total * 100) if positive_total > 0 else 0
        neg_acc = (negative_pass / negative_total * 100) if negative_total > 0 else 0
        overall_acc = ((positive_pass + negative_pass) / (positive_total + negative_total) * 100) if (positive_total + negative_total) > 0 else 0

        print(f"\nVariant {variant_id} Results:")
        print(f"  Positive: {positive_pass}/{positive_total} ({pos_acc:.1f}%)")
        print(f"  Negative: {negative_pass}/{negative_total} ({neg_acc:.1f}%)")
        print(f"  Overall:  {positive_pass + negative_pass}/{positive_total + negative_total} ({overall_acc:.1f}%)")
        print(f"  Time: {elapsed:.1f}s")

        return {
            'variant_id': variant_id,
            'positive_pass': positive_pass,
            'positive_total': positive_total,
            'positive_acc': pos_acc,
            'negative_pass': negative_pass,
            'negative_total': negative_total,
            'negative_acc': neg_acc,
            'overall_acc': overall_acc,
            'time': elapsed,
            'success': result.returncode == 0
        }

    except subprocess.TimeoutExpired:
        print(f"TIMEOUT after {time.time() - start_time:.1f}s")
        return {'variant_id': variant_id, 'success': False, 'error': 'Timeout'}
    except Exception as e:
        print(f"ERROR: {e}")
        return {'variant_id': variant_id, 'success': False, 'error': str(e)}

def main():
    print("="*80)
    print("SEQUENTIAL VARIANT TESTING - All 10 Variants")
    print("="*80)

    results = []
    for vid in range(10):
        result = run_variant(vid)
        results.append(result)

    # Summary table
    print(f"\n\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}\n")

    print(f"{'ID':<4} {'Status':<8} {'Positive':<12} {'Negative':<12} {'Overall':<10} {'Time':<8}")
    print(f"{'-'*4} {'-'*8} {'-'*12} {'-'*12} {'-'*10} {'-'*8}")

    for r in results:
        if r.get('success') and 'positive_acc' in r:
            status = "PASS" if r['success'] else "FAIL"
            pos_str = f"{r['positive_acc']:.1f}%"
            neg_str = f"{r['negative_acc']:.1f}%"
            overall_str = f"{r['overall_acc']:.1f}%"
            time_str = f"{r['time']:.1f}s"
        else:
            status = "FAIL"
            pos_str = "N/A"
            neg_str = "N/A"
            overall_str = "N/A"
            time_str = "N/A"

        print(f"{r['variant_id']:<4} {status:<8} {pos_str:<12} {neg_str:<12} {overall_str:<10} {time_str:<8}")

    # Find best
    successful = [r for r in results if r.get('success') and 'overall_acc' in r]
    if successful:
        best = max(successful, key=lambda x: x['overall_acc'])
        print(f"\n{'='*80}")
        print(f"BEST OVERALL: Variant {best['variant_id']} with {best['overall_acc']:.1f}%")
        print(f"  Positive: {best['positive_acc']:.1f}%")
        print(f"  Negative: {best['negative_acc']:.1f}%")

        # Check if reached target
        if best['positive_acc'] >= 95 and best['negative_acc'] >= 95:
            print(f"\n*** SUCCESS! Achieved 95%+ accuracy target!")
        elif best['positive_acc'] >= 90 and best['negative_acc'] >= 90:
            print(f"\n*** GOOD! Achieved 90%+ accuracy (Tier 2)")
        else:
            print(f"\n*** Further optimization needed for 95%+ target")

    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
