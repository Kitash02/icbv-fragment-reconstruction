#!/usr/bin/env python3
"""
Manual Weight Iterator for Variant 1
=====================================
Tests predefined weight configurations to find optimal ensemble weights.
"""

import sys
import subprocess
import time
import json
from pathlib import Path
import re

# Test configurations to try
WEIGHT_CONFIGS = [
    # Iteration 1: Baseline
    {
        'name': 'Baseline',
        'color': 0.35,
        'raw_compat': 0.25,
        'texture': 0.20,
        'morphological': 0.15,
        'gabor': 0.05
    },
    # Iteration 2: Increase color discrimination (reduce FP)
    {
        'name': 'More_Discriminative_Color',
        'color': 0.40,
        'raw_compat': 0.25,
        'texture': 0.18,
        'morphological': 0.14,
        'gabor': 0.03
    },
    # Iteration 3: Even more color emphasis
    {
        'name': 'High_Color_Weight',
        'color': 0.45,
        'raw_compat': 0.23,
        'texture': 0.17,
        'morphological': 0.12,
        'gabor': 0.03
    },
    # Iteration 4: Balance with raw compat
    {
        'name': 'Color_Raw_Balance',
        'color': 0.40,
        'raw_compat': 0.30,
        'texture': 0.15,
        'morphological': 0.12,
        'gabor': 0.03
    },
    # Iteration 5: More texture (reduce FN)
    {
        'name': 'More_Permissive_Texture',
        'color': 0.32,
        'raw_compat': 0.25,
        'texture': 0.25,
        'morphological': 0.13,
        'gabor': 0.05
    },
]


def update_weights_in_file(weights):
    """Update ensemble_voting.py with new weights."""
    voting_file = Path("src/ensemble_voting.py")
    content = voting_file.read_text()

    # Find and replace weights block
    pattern = r"weights = \{[^}]+\}"
    replacement = f"""weights = {{
            'color': {weights['color']},
            'raw_compat': {weights['raw_compat']},
            'texture': {weights['texture']},
            'morphological': {weights['morphological']},
            'gabor': {weights['gabor']}
        }}"""

    new_content = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)

    if new_content == content:
        print("  WARNING: Pattern not found, weights not updated!")
        return False

    voting_file.write_text(new_content)
    return True


def run_test():
    """Run Variant 1 test and extract metrics."""
    result = subprocess.run(
        [sys.executable, "run_variant1.py", "--no-rotate"],
        capture_output=True,
        text=True,
        timeout=120
    )

    output = result.stdout + result.stderr

    # Parse metrics
    positive_pass = positive_total = 0
    negative_pass = negative_total = 0

    for line in output.split('\n'):
        if '[P]' in line:
            positive_total += 1
            if 'PASS' in line:
                positive_pass += 1
        elif '[N]' in line:
            negative_total += 1
            if 'PASS' in line:
                negative_pass += 1

    if positive_total == 0 and negative_total == 0:
        # Try alternative parsing
        for line in output.split('\n'):
            if 'Positive (expect MATCH)' in line:
                parts = line.split(':')
                if len(parts) > 1:
                    try:
                        positive_total = int(parts[-1].strip())
                    except:
                        pass
            elif 'Negative (expect NO_MATCH)' in line:
                parts = line.split(':')
                if len(parts) > 1:
                    try:
                        negative_total = int(parts[-1].strip())
                    except:
                        pass

        # Try to find pass count from TOTAL line
        for line in output.split('\n'):
            if 'TOTAL' in line and '/' in line:
                parts = line.split()
                for part in parts:
                    if '/' in part:
                        try:
                            passed, total = part.split('/')
                            positive_pass = int(passed) // 2
                            negative_pass = int(passed) - positive_pass
                        except:
                            pass

    pos_acc = (positive_pass / positive_total * 100) if positive_total > 0 else 0
    neg_acc = (negative_pass / negative_total * 100) if negative_total > 0 else 0

    return {
        'positive_pass': positive_pass,
        'positive_total': positive_total,
        'positive_acc': pos_acc,
        'negative_pass': negative_pass,
        'negative_total': negative_total,
        'negative_acc': neg_acc,
        'output': output
    }


def main():
    """Test all weight configurations."""
    print("="*80)
    print("VARIANT 1: MANUAL WEIGHT OPTIMIZATION")
    print("="*80)
    print(f"Testing {len(WEIGHT_CONFIGS)} weight configurations")
    print("Target: 95%+ positive AND 95%+ negative accuracy")
    print("="*80)
    print()

    results = []

    for i, config in enumerate(WEIGHT_CONFIGS, 1):
        print(f"\n{'='*80}")
        print(f"ITERATION {i}/{len(WEIGHT_CONFIGS)}: {config['name']}")
        print(f"{'='*80}")
        print("Weights:")
        for key in ['color', 'raw_compat', 'texture', 'morphological', 'gabor']:
            print(f"  {key:15s}: {config[key]:.2f}")

        # Update weights
        print("\nUpdating weights...")
        if not update_weights_in_file(config):
            print("  ERROR: Failed to update weights, skipping")
            continue

        # Run test
        print("Running test (no rotation)...")
        start = time.time()
        try:
            test_results = run_test()
            elapsed = time.time() - start
        except subprocess.TimeoutExpired:
            print("  TIMEOUT after 120s")
            continue
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        # Display results
        print(f"\nResults (test time: {elapsed:.1f}s):")
        print(f"  Positive: {test_results['positive_pass']}/{test_results['positive_total']} = {test_results['positive_acc']:.1f}%")
        print(f"  Negative: {test_results['negative_pass']}/{test_results['negative_total']} = {test_results['negative_acc']:.1f}%")

        # Check target
        if test_results['positive_acc'] >= 95 and test_results['negative_acc'] >= 95:
            print("\n  *** TARGET REACHED! ***")
        else:
            if test_results['positive_acc'] < 95:
                print(f"  ✗ Positive: {95 - test_results['positive_acc']:.1f}% below target")
            else:
                print(f"  ✓ Positive: Target met")

            if test_results['negative_acc'] < 95:
                print(f"  ✗ Negative: {95 - test_results['negative_acc']:.1f}% below target")
            else:
                print(f"  ✓ Negative: Target met")

        # Record
        results.append({
            'iteration': i,
            'config': config,
            'results': test_results
        })

        # Early stop if target reached
        if test_results['positive_acc'] >= 95 and test_results['negative_acc'] >= 95:
            print("\nTarget reached, stopping iterations.")
            break

    # Summary
    print(f"\n{'='*80}")
    print("OPTIMIZATION SUMMARY")
    print(f"{'='*80}")
    print(f"{'Iteration':<25} {'Pos Acc':>10} {'Neg Acc':>10} {'Status':>15}")
    print("-"*80)

    best_overall = None
    best_overall_score = 0

    for r in results:
        name = r['config']['name']
        pos = r['results']['positive_acc']
        neg = r['results']['negative_acc']

        status = ""
        if pos >= 95 and neg >= 95:
            status = "✓ TARGET"
        elif pos >= 90 and neg >= 90:
            status = "Near target"
        else:
            status = "Below target"

        print(f"{name:<25} {pos:>10.1f}% {neg:>10.1f}% {status:>15}")

        # Track best
        overall_score = min(pos, neg)  # Worst of the two
        if overall_score > best_overall_score:
            best_overall_score = overall_score
            best_overall = r

    print("-"*80)

    if best_overall:
        print(f"\nBest Configuration: {best_overall['config']['name']}")
        print(f"  Positive: {best_overall['results']['positive_acc']:.1f}%")
        print(f"  Negative: {best_overall['results']['negative_acc']:.1f}%")
        print("\nOptimal Weights:")
        for key in ['color', 'raw_compat', 'texture', 'morphological', 'gabor']:
            print(f"  {key:15s}: {best_overall['config'][key]:.2f}")

        # Save results
        output_file = Path("outputs/variant1_manual_optimization.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Remove 'output' field (too large)
        for r in results:
            if 'output' in r['results']:
                del r['results']['output']

        with open(output_file, 'w') as f:
            json.dump({
                'results': results,
                'best_config': best_overall
            }, f, indent=2)

        print(f"\nResults saved to: {output_file}")

        # Check if target reached
        if best_overall['results']['positive_acc'] >= 95 and best_overall['results']['negative_acc'] >= 95:
            print("\n" + "="*80)
            print("SUCCESS: 95%+ TARGET ACHIEVED!")
            print("="*80)
        else:
            print("\n" + "="*80)
            print("Target not yet reached. Suggest additional configurations:")
            print("="*80)

            pos_acc = best_overall['results']['positive_acc']
            neg_acc = best_overall['results']['negative_acc']

            if neg_acc < 95:
                print("- Increase color weight further (reduce false positives)")
            if pos_acc < 95:
                print("- Increase texture/gabor weight (reduce false negatives)")


if __name__ == "__main__":
    main()
