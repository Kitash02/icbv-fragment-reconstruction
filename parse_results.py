#!/usr/bin/env python3
"""
Parse test results and extract metrics for evolutionary optimization.
"""

import re
import sys
from pathlib import Path


def parse_test_results(file_path):
    """Parse test results file and extract metrics."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Extract positive and negative test results
    positive_pass = 0
    positive_fail = 0
    negative_pass = 0
    negative_fail = 0
    false_positives = []
    false_negatives = []

    lines = content.split('\n')
    for line in lines:
        # Skip lines without test results
        if not ('> [P]' in line or '> [N]' in line):
            continue

        # Positive cases
        if '> [P]' in line:
            if 'PASS' in line:
                positive_pass += 1
            elif 'FAIL' in line:
                positive_fail += 1
                # Extract test name
                match = re.search(r'\[P\] ([^\s]+)', line)
                if match:
                    false_negatives.append(match.group(1))

        # Negative cases
        elif '> [N]' in line:
            if 'PASS' in line:
                negative_pass += 1
            elif 'FAIL' in line:
                negative_fail += 1
                # Extract test name
                match = re.search(r'\[N\] ([^\s]+)', line)
                if match:
                    false_positives.append(match.group(1))

    # Calculate metrics
    total_positive = positive_pass + positive_fail
    total_negative = negative_pass + negative_fail

    positive_acc = (positive_pass / total_positive * 100) if total_positive > 0 else 0
    negative_acc = (negative_pass / total_negative * 100) if total_negative > 0 else 0

    return {
        'positive_pass': positive_pass,
        'positive_fail': positive_fail,
        'positive_total': total_positive,
        'positive_accuracy': positive_acc,
        'negative_pass': negative_pass,
        'negative_fail': negative_fail,
        'negative_total': total_negative,
        'negative_accuracy': negative_acc,
        'false_positives': false_positives,
        'false_negatives': false_negatives,
    }


def print_metrics(iteration, metrics):
    """Print metrics in a formatted way."""
    print(f"\n{'='*70}")
    print(f"ITERATION {iteration} RESULTS")
    print(f"{'='*70}")
    print(f"Positive Cases: {metrics['positive_pass']}/{metrics['positive_total']} PASS "
          f"({metrics['positive_accuracy']:.1f}%)")
    print(f"Negative Cases: {metrics['negative_pass']}/{metrics['negative_total']} PASS "
          f"({metrics['negative_accuracy']:.1f}%)")
    print(f"\nFalse Positives (cross-source matched): {len(metrics['false_positives'])}")
    if metrics['false_positives']:
        for fp in metrics['false_positives'][:10]:  # Show first 10
            print(f"  - {fp}")
    print(f"\nFalse Negatives (same-source not matched): {len(metrics['false_negatives'])}")
    if metrics['false_negatives']:
        for fn in metrics['false_negatives']:
            print(f"  - {fn}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_results.py <result_file>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    iteration = "UNKNOWN"
    if "iter0" in str(file_path):
        iteration = "0 (Baseline)"
    elif "iter1" in str(file_path):
        iteration = "1"
    elif "iter2" in str(file_path):
        iteration = "2"
    elif "iter3" in str(file_path):
        iteration = "3"

    metrics = parse_test_results(file_path)
    print_metrics(iteration, metrics)
