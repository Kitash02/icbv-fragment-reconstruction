#!/usr/bin/env python3
"""
Quick test runner for Variant 1 - shows current performance
"""
import subprocess
import sys
import time
from pathlib import Path

def run_test():
    """Run Variant 1 test and parse results."""
    print("Running Variant 1 test...")
    print("="*80)

    start = time.time()
    result = subprocess.run(
        [sys.executable, "run_variant1.py"],
        capture_output=True,
        text=True
    )
    elapsed = time.time() - start

    output = result.stdout + result.stderr

    # Parse results
    lines = output.split('\n')

    # Find summary table
    in_summary = False
    summary_lines = []

    for line in lines:
        if 'RECONSTRUCTION TEST RESULTS' in line:
            in_summary = True
        if in_summary:
            summary_lines.append(line)
            if 'TOTAL' in line and '/' in line:
                # Print a few more lines and stop
                for i, next_line in enumerate(lines[lines.index(line):lines.index(line)+5]):
                    summary_lines.append(next_line)
                break

    # Print summary
    for line in summary_lines:
        print(line)

    # Parse metrics
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

    if positive_total > 0 or negative_total > 0:
        pos_acc = (positive_pass / positive_total * 100) if positive_total > 0 else 0
        neg_acc = (negative_pass / negative_total * 100) if negative_total > 0 else 0
        overall = ((positive_pass + negative_pass) / (positive_total + negative_total) * 100)

        print("\n" + "="*80)
        print("ACCURACY METRICS")
        print("="*80)
        print(f"Positive Cases: {positive_pass}/{positive_total} = {pos_acc:.1f}%")
        print(f"Negative Cases: {negative_pass}/{negative_total} = {neg_acc:.1f}%")
        print(f"Overall:        {positive_pass+negative_pass}/{positive_total+negative_total} = {overall:.1f}%")
        print("="*80)
        print(f"Time: {elapsed:.1f}s")

        # Status
        if pos_acc >= 95 and neg_acc >= 95:
            print("\n✓ TARGET REACHED! (95%+ both metrics)")
        else:
            gap_pos = max(0, 95 - pos_acc)
            gap_neg = max(0, 95 - neg_acc)
            print(f"\n✗ Need improvement:")
            if gap_pos > 0:
                print(f"  - Positive: {gap_pos:.1f}% below target")
            if gap_neg > 0:
                print(f"  - Negative: {gap_neg:.1f}% below target")
    else:
        print("\nERROR: Could not parse test results")
        print("\nFull output:")
        print(output[-2000:])  # Last 2000 chars

    return output

if __name__ == "__main__":
    run_test()
