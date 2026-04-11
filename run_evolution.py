#!/usr/bin/env python3
"""
Master orchestration script for Variant 0 evolutionary optimization.
Runs iterations 2-5 sequentially and analyzes results.
"""

import subprocess
import sys
import json
from pathlib import Path
import re


def parse_test_results(file_path):
    """Parse test results file and extract metrics."""
    if not file_path.exists():
        return None

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except:
        return None

    positive_pass = 0
    positive_fail = 0
    negative_pass = 0
    negative_fail = 0

    lines = content.split('\n')
    for line in lines:
        if not ('> [P]' in line or '> [N]' in line):
            continue

        if '> [P]' in line:
            if 'PASS' in line:
                positive_pass += 1
            elif 'FAIL' in line:
                positive_fail += 1
        elif '> [N]' in line:
            if 'PASS' in line:
                negative_pass += 1
            elif 'FAIL' in line:
                negative_fail += 1

    total_positive = positive_pass + positive_fail
    total_negative = negative_pass + negative_fail

    if total_positive == 0 or total_negative == 0:
        return None

    positive_acc = (positive_pass / total_positive * 100)
    negative_acc = (negative_pass / total_negative * 100)

    return {
        'positive_pass': positive_pass,
        'positive_total': total_positive,
        'positive_accuracy': positive_acc,
        'negative_pass': negative_pass,
        'negative_total': total_negative,
        'negative_accuracy': negative_acc,
    }


def run_iteration(iteration_num, root_dir):
    """Run a single iteration and return metrics."""
    print(f"\n{'='*80}")
    print(f"RUNNING ITERATION {iteration_num}")
    print(f"{'='*80}\n")

    runner_script = root_dir / f"run_variant0_iter{iteration_num}.py"
    output_file = root_dir / "outputs" / "evolution" / f"variant0_iter{iteration_num}.txt"

    if not runner_script.exists():
        print(f"ERROR: Runner script not found: {runner_script}")
        return None

    # Run the test
    try:
        result = subprocess.run(
            [sys.executable, str(runner_script)],
            cwd=str(root_dir),
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )

        # Save output
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n\nSTDERR:\n")
                f.write(result.stderr)

        print(f"Output saved to: {output_file}")

    except subprocess.TimeoutExpired:
        print(f"ERROR: Iteration {iteration_num} timed out")
        return None
    except Exception as e:
        print(f"ERROR: Failed to run iteration {iteration_num}: {e}")
        return None

    # Parse results
    metrics = parse_test_results(output_file)
    if metrics:
        print(f"\nIteration {iteration_num} Results:")
        print(f"  Positive: {metrics['positive_pass']}/{metrics['positive_total']} "
              f"({metrics['positive_accuracy']:.1f}%)")
        print(f"  Negative: {metrics['negative_pass']}/{metrics['negative_total']} "
              f"({metrics['negative_accuracy']:.1f}%)")

        # Check if target reached
        if metrics['positive_accuracy'] >= 95.0 and metrics['negative_accuracy'] >= 95.0:
            print(f"\n*** TARGET REACHED! Both metrics >= 95% ***")
            return metrics, True

    return metrics, False


def main():
    root_dir = Path(__file__).parent

    # Load progress file
    progress_file = root_dir / "outputs" / "evolution" / "variant0_progress.json"
    with open(progress_file, 'r') as f:
        progress = json.load(f)

    print("="*80)
    print("VARIANT 0 EVOLUTIONARY OPTIMIZATION - MASTER ORCHESTRATOR")
    print("="*80)
    print(f"Target: 95%+ positive AND 95%+ negative accuracy")
    print(f"Max iterations: {progress['max_iterations']}")
    print("="*80)

    # Check which iterations have already been run
    completed_iterations = []
    for i in range(6):
        result_file = root_dir / "outputs" / "evolution" / f"variant0_iter{i}.txt"
        if result_file.exists():
            metrics = parse_test_results(result_file)
            if metrics:
                completed_iterations.append((i, metrics))
                print(f"\nIteration {i} already completed:")
                print(f"  Positive: {metrics['positive_accuracy']:.1f}%")
                print(f"  Negative: {metrics['negative_accuracy']:.1f}%")

    # Run remaining iterations
    for iteration_num in range(2, 6):
        # Skip if already completed
        if any(i == iteration_num for i, _ in completed_iterations):
            continue

        metrics, target_reached = run_iteration(iteration_num, root_dir)

        if metrics:
            progress['iterations'].append({
                'iteration': iteration_num,
                'metrics': metrics
            })

            # Save progress
            with open(progress_file, 'w') as f:
                json.dump(progress, f, indent=2)

            if target_reached:
                print(f"\n{'='*80}")
                print(f"SUCCESS: Target reached at iteration {iteration_num}!")
                print(f"{'='*80}")
                break

        # Check for convergence/ceiling
        if len(progress['iterations']) >= 3:
            last_3 = progress['iterations'][-3:]
            neg_accs = [it['metrics']['negative_accuracy'] for it in last_3]
            if max(neg_accs) - min(neg_accs) < 2.0:  # Less than 2% improvement
                print(f"\n{'='*80}")
                print(f"CEILING DETECTED: No significant improvement in last 3 iterations")
                print(f"{'='*80}")
                break

    # Final report
    print(f"\n{'='*80}")
    print(f"EVOLUTIONARY OPTIMIZATION COMPLETE")
    print(f"{'='*80}")

    if progress['iterations']:
        best_iter = max(progress['iterations'],
                       key=lambda x: (x['metrics']['negative_accuracy'] +
                                     x['metrics']['positive_accuracy']))
        metrics = best_iter['metrics']
        print(f"\nBest configuration: Iteration {best_iter['iteration']}")
        print(f"  Positive: {metrics['positive_accuracy']:.1f}%")
        print(f"  Negative: {metrics['negative_accuracy']:.1f}%")

        if metrics['positive_accuracy'] >= 95.0 and metrics['negative_accuracy'] >= 95.0:
            print(f"\n*** TARGET ACHIEVED ***")
        else:
            print(f"\nTarget not fully achieved. Best effort shown above.")

    print(f"\nProgress saved to: {progress_file}")
    print(f"="*80)


if __name__ == "__main__":
    main()
