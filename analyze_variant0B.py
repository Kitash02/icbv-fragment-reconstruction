#!/usr/bin/env python3
"""
Analyze Variant 0B test results
"""
import re
import sys

def analyze_results(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return

    # Parse test results
    lines = content.split('\n')

    positive_tests = []
    negative_tests = []

    for line in lines:
        if '[P]' in line and ('PASS' in line or 'FAIL' in line):
            positive_tests.append(line)
        elif '[N]' in line and ('PASS' in line or 'FAIL' in line):
            negative_tests.append(line)

    # Count results
    pos_pass = sum(1 for l in positive_tests if 'PASS' in l)
    pos_fail = sum(1 for l in positive_tests if 'FAIL' in l)
    neg_pass = sum(1 for l in negative_tests if 'PASS' in l)
    neg_fail = sum(1 for l in negative_tests if 'FAIL' in l)

    total_pass = pos_pass + neg_pass
    total_tests = len(positive_tests) + len(negative_tests)

    print("\n" + "=" * 80)
    print("VARIANT 0B TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"\nPositive Tests (should MATCH):")
    print(f"  PASS: {pos_pass}/9 ({pos_pass/9*100:.1f}%)")
    print(f"  FAIL: {pos_fail}/9 ({pos_fail/9*100:.1f}%)")

    print(f"\nNegative Tests (should NOT MATCH):")
    print(f"  PASS: {neg_pass}/36 ({neg_pass/36*100:.1f}%)")
    print(f"  FAIL: {neg_fail}/36 ({neg_fail/36*100:.1f}%)")

    print(f"\nOverall Accuracy: {total_pass}/{total_tests} ({total_pass/total_tests*100:.1f}%)")

    print("\n" + "-" * 80)
    print("POSITIVE TEST FAILURES (False Negatives):")
    print("-" * 80)
    for line in positive_tests:
        if 'FAIL' in line:
            # Extract test name
            match = re.search(r'\[P\]\s+(\S+)', line)
            if match:
                print(f"  - {match.group(1)}")

    print("\n" + "-" * 80)
    print("NEGATIVE TEST FAILURES (False Positives):")
    print("-" * 80)
    false_positives = []
    for line in negative_tests:
        if 'FAIL' in line:
            match = re.search(r'\[N\]\s+(\S+)', line)
            if match:
                false_positives.append(match.group(1))

    for fp in false_positives:
        print(f"  - {fp}")

    print(f"\nTotal False Positives: {len(false_positives)}")

    # Key targets check
    print("\n" + "=" * 80)
    print("KEY TARGETS CHECK:")
    print("=" * 80)

    targets = [
        'mixed_gettyimages-13116049_gettyimages-17009652',
        'mixed_gettyimages-13116049_gettyimages-21778090',
        'mixed_gettyimages-17009652_gettyimages-21778090'
    ]

    for target in targets:
        found = False
        for line in negative_tests:
            if target in line:
                if 'PASS' in line:
                    print(f"  ✓ {target}: CORRECTLY REJECTED")
                    found = True
                elif 'FAIL' in line:
                    print(f"  ✗ {target}: FALSE POSITIVE")
                    found = True
                break
        if not found:
            print(f"  ? {target}: NOT FOUND IN RESULTS")

    print("=" * 80)

    return {
        'pos_pass': pos_pass,
        'pos_fail': pos_fail,
        'neg_pass': neg_pass,
        'neg_fail': neg_fail,
        'false_positives': false_positives
    }

if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else "outputs/variant0B_results_full.txt"
    analyze_results(filepath)
