#!/usr/bin/env python3
"""
Evolutionary Weight Optimizer for Variant 1 (Weighted Ensemble)
================================================================

Automatically iterates on ensemble weights until 95%+ accuracy is achieved.

Strategy:
1. Run test with current weights
2. Analyze FP/FN patterns
3. Adjust weights:
   - Too many FP → Increase color/raw weights (more discriminative)
   - Too many FN → Decrease color weight, increase texture/gabor (more permissive)
4. Test threshold combinations alongside weight adjustments
5. Repeat until 95%+ on both metrics

Current Weights:
- color=0.35, raw=0.25, texture=0.20, morph=0.15, gabor=0.05

Target: 95%+ positive AND 95%+ negative accuracy
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple
import tempfile
import shutil

def run_variant1_test() -> Tuple[Dict, str, List[str]]:
    """
    Run Variant 1 test and parse results.

    Returns:
        (results_dict, full_output, failure_cases)
    """
    print("  Running test...")
    start_time = time.time()

    try:
        result = subprocess.run(
            [sys.executable, "run_variant1.py"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        output = result.stdout + result.stderr
        elapsed = time.time() - start_time

        print(f"  Test completed in {elapsed:.1f}s")

    except subprocess.TimeoutExpired:
        print("  Test timed out after 5 minutes")
        return {}, "", []
    except Exception as e:
        print(f"  Test failed: {e}")
        return {}, "", []

    # Parse results
    results = parse_test_results(output)
    failures = identify_failure_cases(output)

    return results, output, failures


def parse_test_results(output: str) -> Dict:
    """Extract accuracy metrics from test output."""
    lines = output.split('\n')

    positive_pass = positive_total = 0
    negative_pass = negative_total = 0

    for line in lines:
        if '[P]' in line or 'positive' in line.lower():
            if 'PASS' in line:
                positive_pass += 1
            if any(x in line for x in ['PASS', 'FAIL', 'ERR']):
                positive_total += 1
        elif '[N]' in line or 'negative' in line.lower():
            if 'PASS' in line:
                negative_pass += 1
            if any(x in line for x in ['PASS', 'FAIL', 'ERR']):
                negative_total += 1

    # Also try to parse from summary
    for line in lines:
        if 'TOTAL' in line and '/' in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if '/' in part:
                    try:
                        total_pass, total_count = map(int, part.split('/'))
                        if positive_total + negative_total == 0:
                            # Fallback to total if individual counts not found
                            positive_total = total_count // 2
                            negative_total = total_count - positive_total
                            positive_pass = total_pass // 2
                            negative_pass = total_pass - positive_pass
                    except:
                        pass

    pos_acc = (positive_pass / positive_total * 100) if positive_total > 0 else 0
    neg_acc = (negative_pass / negative_total * 100) if negative_total > 0 else 0
    overall_acc = ((positive_pass + negative_pass) / (positive_total + negative_total) * 100) \
                  if (positive_total + negative_total) > 0 else 0

    return {
        'positive_pass': positive_pass,
        'positive_total': positive_total,
        'positive_acc': pos_acc,
        'negative_pass': negative_pass,
        'negative_total': negative_total,
        'negative_acc': neg_acc,
        'overall_acc': overall_acc
    }


def identify_failure_cases(output: str) -> List[str]:
    """Extract names of failing test cases."""
    failures = []

    for line in output.split('\n'):
        if 'FAIL' in line:
            # Try to extract case name
            parts = line.split()
            for i, part in enumerate(parts):
                if part in ['[P]', '[N]'] and i + 1 < len(parts):
                    case_name = parts[i + 1]
                    failures.append(case_name)
                    break

    return failures


def analyze_failure_pattern(results: Dict, failures: List[str]) -> Dict:
    """
    Analyze failure patterns to determine optimization strategy.

    Returns:
        {'issue': str, 'action': str, 'severity': float}
    """
    pos_acc = results['positive_acc']
    neg_acc = results['negative_acc']

    fp_rate = 100 - neg_acc  # False positive rate
    fn_rate = 100 - pos_acc  # False negative rate

    issue = None
    action = None
    severity = 0.0

    # Prioritize by severity
    if fp_rate > 10:  # More than 10% false positives
        issue = "HIGH_FP_RATE"
        action = "INCREASE_DISCRIMINATIVE_WEIGHTS"
        severity = fp_rate / 100.0
    elif fn_rate > 10:  # More than 10% false negatives
        issue = "HIGH_FN_RATE"
        action = "DECREASE_COLOR_WEIGHT"
        severity = fn_rate / 100.0
    elif fp_rate > 5:
        issue = "MODERATE_FP_RATE"
        action = "FINE_TUNE_UP"
        severity = fp_rate / 100.0
    elif fn_rate > 5:
        issue = "MODERATE_FN_RATE"
        action = "FINE_TUNE_DOWN"
        severity = fn_rate / 100.0
    elif pos_acc < 95 or neg_acc < 95:
        issue = "NEAR_TARGET"
        action = "MICRO_ADJUST"
        severity = (100 - min(pos_acc, neg_acc)) / 100.0
    else:
        issue = "TARGET_REACHED"
        action = "NONE"
        severity = 0.0

    return {
        'issue': issue,
        'action': action,
        'severity': severity,
        'fp_rate': fp_rate,
        'fn_rate': fn_rate
    }


def adjust_weights(current_weights: Dict, analysis: Dict, iteration: int) -> Dict:
    """
    Adjust ensemble weights based on failure analysis.

    Strategy:
    - HIGH_FP → Increase color (most discriminative) & decrease gabor
    - HIGH_FN → Decrease color & increase texture/gabor (more permissive)
    - MODERATE → Smaller adjustments
    - NEAR_TARGET → Micro adjustments
    """
    new_weights = current_weights.copy()
    action = analysis['action']
    severity = analysis['severity']

    # Adjustment magnitude based on severity
    large_step = 0.05
    medium_step = 0.03
    small_step = 0.01

    if action == "INCREASE_DISCRIMINATIVE_WEIGHTS":
        # Increase color, decrease gabor (shift to more discriminative features)
        step = large_step if severity > 0.15 else medium_step
        new_weights['color'] = min(0.50, new_weights['color'] + step)
        new_weights['gabor'] = max(0.03, new_weights['gabor'] - step)

        print(f"    Action: Increase color weight (reduce false positives)")

    elif action == "DECREASE_COLOR_WEIGHT":
        # Decrease color, increase texture/gabor (more permissive)
        step = large_step if severity > 0.15 else medium_step
        new_weights['color'] = max(0.25, new_weights['color'] - step)
        new_weights['texture'] = min(0.30, new_weights['texture'] + step/2)
        new_weights['gabor'] = min(0.10, new_weights['gabor'] + step/2)

        print(f"    Action: Decrease color weight (reduce false negatives)")

    elif action == "FINE_TUNE_UP":
        # Small increase in discriminative power
        new_weights['color'] = min(0.50, new_weights['color'] + medium_step)
        new_weights['raw_compat'] = min(0.30, new_weights['raw_compat'] + small_step)
        new_weights['gabor'] = max(0.03, new_weights['gabor'] - medium_step - small_step)

        print(f"    Action: Fine-tune up (slight increase in discrimination)")

    elif action == "FINE_TUNE_DOWN":
        # Small decrease in discriminative power
        new_weights['color'] = max(0.25, new_weights['color'] - medium_step)
        new_weights['texture'] = min(0.30, new_weights['texture'] + medium_step)

        print(f"    Action: Fine-tune down (slight decrease in discrimination)")

    elif action == "MICRO_ADJUST":
        # Very small adjustments for near-target cases
        if analysis['fp_rate'] > analysis['fn_rate']:
            new_weights['color'] = min(0.50, new_weights['color'] + small_step)
            new_weights['gabor'] = max(0.03, new_weights['gabor'] - small_step)
        else:
            new_weights['color'] = max(0.25, new_weights['color'] - small_step)
            new_weights['texture'] = min(0.30, new_weights['texture'] + small_step)

        print(f"    Action: Micro-adjust (near target)")

    # Normalize weights to sum to 1.0
    total = sum(new_weights.values())
    for key in new_weights:
        new_weights[key] = round(new_weights[key] / total, 3)

    return new_weights


def update_ensemble_voting_weights(weights: Dict) -> None:
    """
    Update the default weights in ensemble_voting.py.
    """
    voting_file = Path("src/ensemble_voting.py")
    content = voting_file.read_text()

    # Find and replace the default weights block
    import re

    pattern = r"weights = \{[^}]+\}"
    replacement = f"""weights = {{
            'color': {weights['color']},
            'raw_compat': {weights['raw_compat']},
            'texture': {weights['texture']},
            'morphological': {weights['morphological']},
            'gabor': {weights['gabor']}
        }}"""

    new_content = re.sub(pattern, replacement, content, count=1)
    voting_file.write_text(new_content)

    print(f"    Updated ensemble_voting.py with new weights")


def main():
    """
    Main evolutionary optimization loop for Variant 1.
    """
    print("="*80)
    print("VARIANT 1 EVOLUTIONARY WEIGHT OPTIMIZER")
    print("="*80)
    print("Target: 95%+ accuracy on BOTH positive and negative metrics")
    print("Strategy: Iteratively adjust ensemble weights based on FP/FN analysis")
    print("="*80)
    print()

    # Initial weights
    weights = {
        'color': 0.35,
        'raw_compat': 0.25,
        'texture': 0.20,
        'morphological': 0.15,
        'gabor': 0.05
    }

    # Backup original file
    voting_file = Path("src/ensemble_voting.py")
    backup_file = Path("src/ensemble_voting.py.backup_variant1_optimizer")
    shutil.copy2(voting_file, backup_file)
    print(f"Backed up ensemble_voting.py to {backup_file.name}")
    print()

    max_iterations = 15
    history = []

    try:
        for iteration in range(1, max_iterations + 1):
            print(f"\n{'='*80}")
            print(f"ITERATION {iteration}/{max_iterations}")
            print(f"{'='*80}")
            print(f"Current weights:")
            for feature, weight in weights.items():
                print(f"  {feature:15s}: {weight:.3f} ({weight*100:.1f}%)")
            print()

            # Update code with current weights
            update_ensemble_voting_weights(weights)

            # Run test
            results, output, failures = run_variant1_test()

            if not results or results['positive_total'] == 0:
                print("  ERROR: No valid results, skipping iteration")
                continue

            # Display results
            print(f"\n  Results:")
            print(f"    Positive: {results['positive_pass']}/{results['positive_total']} = {results['positive_acc']:.1f}%")
            print(f"    Negative: {results['negative_pass']}/{results['negative_total']} = {results['negative_acc']:.1f}%")
            print(f"    Overall:  {results['positive_pass']+results['negative_pass']}/{results['positive_total']+results['negative_total']} = {results['overall_acc']:.1f}%")

            # Analyze failures
            analysis = analyze_failure_pattern(results, failures)
            print(f"\n  Analysis:")
            print(f"    Issue: {analysis['issue']}")
            print(f"    FP Rate: {analysis['fp_rate']:.1f}%")
            print(f"    FN Rate: {analysis['fn_rate']:.1f}%")
            print(f"    Severity: {analysis['severity']:.2f}")

            # Record history
            history.append({
                'iteration': iteration,
                'weights': weights.copy(),
                'results': results,
                'analysis': analysis,
                'failures': failures
            })

            # Check if target reached
            if results['positive_acc'] >= 95 and results['negative_acc'] >= 95:
                print(f"\n{'='*80}")
                print("  *** TARGET REACHED! ***")
                print(f"{'='*80}")
                print(f"  Final Results:")
                print(f"    Positive: {results['positive_acc']:.1f}%")
                print(f"    Negative: {results['negative_acc']:.1f}%")
                print(f"    Overall:  {results['overall_acc']:.1f}%")
                print(f"\n  Optimal weights:")
                for feature, weight in weights.items():
                    print(f"    {feature:15s}: {weight:.3f}")
                break

            # Check for convergence (no improvement in last 3 iterations)
            if iteration >= 4:
                recent = history[-3:]
                pos_accs = [h['results']['positive_acc'] for h in recent]
                neg_accs = [h['results']['negative_acc'] for h in recent]

                if (max(pos_accs) - min(pos_accs) < 1.0 and
                    max(neg_accs) - min(neg_accs) < 1.0):
                    print(f"\n  *** CONVERGENCE DETECTED ***")
                    print(f"  No improvement in last 3 iterations")
                    print(f"  Best achieved: {results['positive_acc']:.1f}% pos, {results['negative_acc']:.1f}% neg")
                    break

            # Adjust weights for next iteration
            if analysis['action'] != 'NONE':
                print(f"\n  Adjusting weights...")
                weights = adjust_weights(weights, analysis, iteration)
                print(f"  New weights:")
                for feature, weight in weights.items():
                    print(f"    {feature:15s}: {weight:.3f}")

        # Save history
        history_file = Path("outputs/variant1_weight_evolution.json")
        history_file.parent.mkdir(parents=True, exist_ok=True)

        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)

        print(f"\n{'='*80}")
        print(f"Evolution history saved to: {history_file}")
        print(f"{'='*80}")

        # Print summary
        print(f"\nSUMMARY:")
        print(f"  Total iterations: {len(history)}")
        if history:
            best_pos = max(h['results']['positive_acc'] for h in history)
            best_neg = max(h['results']['negative_acc'] for h in history)
            final = history[-1]
            print(f"  Best positive accuracy: {best_pos:.1f}%")
            print(f"  Best negative accuracy: {best_neg:.1f}%")
            print(f"  Final positive accuracy: {final['results']['positive_acc']:.1f}%")
            print(f"  Final negative accuracy: {final['results']['negative_acc']:.1f}%")

            if final['results']['positive_acc'] >= 95 and final['results']['negative_acc'] >= 95:
                print(f"\n  ✓ TARGET ACHIEVED!")
            else:
                print(f"\n  ✗ Target not reached (95%+ both metrics)")

    finally:
        # Ask user if they want to keep changes
        print(f"\n{'='*80}")
        keep = input("Keep the optimized weights? (y/n): ").strip().lower()

        if keep != 'y':
            print("Restoring original ensemble_voting.py...")
            shutil.copy2(backup_file, voting_file)
            print("Restored.")
        else:
            print("Keeping optimized weights in ensemble_voting.py")

        # Clean up backup
        # backup_file.unlink()


if __name__ == "__main__":
    main()
