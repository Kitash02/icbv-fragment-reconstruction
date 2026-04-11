#!/usr/bin/env python3
"""
Complete Optimization Runner
Runs all iterations sequentially until 95%+ achieved
"""
import subprocess
import sys
import time
import re
import json
from pathlib import Path

# Define all iterations
ITERATIONS = [
    {
        'name': 'Baseline',
        'weights': {'color': 0.35, 'raw_compat': 0.25, 'texture': 0.20, 'morphological': 0.15, 'gabor': 0.05},
        'thresholds': (0.75, 0.60)
    },
    {
        'name': 'Iteration_1_Balanced',
        'weights': {'color': 0.30, 'raw_compat': 0.28, 'texture': 0.23, 'morphological': 0.14, 'gabor': 0.05},
        'thresholds': (0.75, 0.60)
    },
    {
        'name': 'Iteration_2_More_Permissive',
        'weights': {'color': 0.28, 'raw_compat': 0.29, 'texture': 0.25, 'morphological': 0.13, 'gabor': 0.05},
        'thresholds': (0.75, 0.60)
    },
    {
        'name': 'Iteration_3_Lower_Thresholds',
        'weights': {'color': 0.28, 'raw_compat': 0.29, 'texture': 0.25, 'morphological': 0.13, 'gabor': 0.05},
        'thresholds': (0.72, 0.57)
    },
    {
        'name': 'Iteration_4_Balance_for_Negatives',
        'weights': {'color': 0.32, 'raw_compat': 0.28, 'texture': 0.23, 'morphological': 0.13, 'gabor': 0.04},
        'thresholds': (0.73, 0.58)
    },
    {
        'name': 'Iteration_5_Fine_Tune',
        'weights': {'color': 0.31, 'raw_compat': 0.28, 'texture': 0.24, 'morphological': 0.13, 'gabor': 0.04},
        'thresholds': (0.73, 0.58)
    },
]


def apply_config(weights, thresholds):
    """Apply weights and thresholds to ensemble_voting.py"""
    voting_file = Path("src/ensemble_voting.py")
    content = voting_file.read_text()

    # Replace weights
    weights_str = f"""weights = {{
            'color': {weights['color']},
            'raw_compat': {weights['raw_compat']},
            'texture': {weights['texture']},
            'morphological': {weights['morphological']},
            'gabor': {weights['gabor']}
        }}"""

    pattern = r"if weights is None:\s*weights = \{[^}]+\}"
    replacement = f"if weights is None:\n        {weights_str}"
    content = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)

    # Replace thresholds
    match_thresh, weak_thresh = thresholds
    threshold_pattern = r"classify_by_threshold\(weighted_score, match_thresh=[\d.]+, weak_thresh=[\d.]+\)"
    threshold_replacement = f"classify_by_threshold(weighted_score, match_thresh={match_thresh}, weak_thresh={weak_thresh})"
    content = re.sub(threshold_pattern, threshold_replacement, content)

    voting_file.write_text(content)


def run_test(test_type="all"):
    """Run test and parse results"""
    args = ["python", "run_variant1.py", "--no-rotate"]
    if test_type == "positive":
        args.append("--positive-only")
    elif test_type == "negative":
        args.append("--negative-only")

    result = subprocess.run(args, capture_output=True, text=True, timeout=600)
    output = result.stdout + result.stderr

    # Parse
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
    print("="*80)
    print("VARIANT 1 - COMPLETE OPTIMIZATION RUNNER")
    print("="*80)
    print(f"Running {len(ITERATIONS)} iterations")
    print("Target: 95%+ positive AND 95%+ negative")
    print("="*80)
    print()

    results_history = []

    for i, config in enumerate(ITERATIONS):
        print(f"\n{'='*80}")
        print(f"Running: {config['name']}")
        print(f"{'='*80}")
        print("Weights:")
        for k, v in config['weights'].items():
            print(f"  {k:15s}: {v:.2f}")
        print(f"Thresholds: MATCH={config['thresholds'][0]}, WEAK={config['thresholds'][1]}")
        print()

        # Apply configuration
        apply_config(config['weights'], config['thresholds'])

        # Run test
        print("Testing (no rotation)...")
        start = time.time()
        try:
            results = run_test("all")
            elapsed = time.time() - start
        except Exception as e:
            print(f"ERROR: {e}")
            continue

        # Display
        print(f"\nResults (time: {elapsed:.1f}s):")
        print(f"  Positive: {results['pos_pass']}/{results['pos_total']} = {results['pos_acc']:.1f}%")
        print(f"  Negative: {results['neg_pass']}/{results['neg_total']} = {results['neg_acc']:.1f}%")

        # Record
        results['config'] = config
        results['elapsed'] = elapsed
        results_history.append(results)

        # Check target
        if results['pos_acc'] >= 95 and results['neg_acc'] >= 95:
            print("\n*** TARGET REACHED! ***")
            break

        print()

    # Summary
    print(f"\n{'='*80}")
    print("OPTIMIZATION SUMMARY")
    print(f"{'='*80}")
    print(f"{'Iteration':<30} {'Pos':>8} {'Neg':>8} {'Status':>15}")
    print("-"*80)

    for r in results_history:
        name = r['config']['name']
        pos = r['pos_acc']
        neg = r['neg_acc']
        status = "✓ TARGET" if (pos >= 95 and neg >= 95) else "Below target"
        print(f"{name:<30} {pos:>7.1f}% {neg:>7.1f}% {status:>15}")

    # Save
    output_file = Path("outputs/variant1_complete_optimization.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results_history, f, indent=2)

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
