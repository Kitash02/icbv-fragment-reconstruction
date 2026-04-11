#!/usr/bin/env python3
"""
Results Monitor and Analyzer for Variant 9 Evolution

This script monitors running tests and analyzes results when complete.
It provides real-time progress updates and automatic result extraction.
"""

import sys
import time
import re
from pathlib import Path
from datetime import datetime
import json

ROOT = Path(__file__).parent

# Test output files to monitor
TESTS_TO_MONITOR = {
    '9A': 'outputs/evolution/variant9A_test.txt',
    '9_FINAL': 'outputs/evolution/variant9_FINAL_test.txt',
    '9_baseline': 'outputs/evolution/variant9_baseline.txt'
}


def parse_results(content: str) -> dict:
    """Extract accuracy metrics from test output."""
    results = {
        'complete': False,
        'positive_accuracy': None,
        'negative_accuracy': None,
        'overall_accuracy': None,
        'errors': 0
    }

    # Check if test is complete
    if 'FINAL SUMMARY' in content or 'TEST COMPLETE' in content:
        results['complete'] = True

    # Extract positive accuracy
    pos_match = re.search(r'Positive Tests.*?(\d+)/(\d+).*?\((\d+(?:\.\d+)?)%\)', content, re.DOTALL)
    if pos_match:
        results['positive_correct'] = int(pos_match.group(1))
        results['positive_total'] = int(pos_match.group(2))
        results['positive_accuracy'] = float(pos_match.group(3))

    # Extract negative accuracy
    neg_match = re.search(r'Negative Tests.*?(\d+)/(\d+).*?\((\d+(?:\.\d+)?)%\)', content, re.DOTALL)
    if neg_match:
        results['negative_correct'] = int(neg_match.group(1))
        results['negative_total'] = int(neg_match.group(2))
        results['negative_accuracy'] = float(neg_match.group(3))

    # Calculate overall
    if pos_match and neg_match:
        total_correct = results['positive_correct'] + results['negative_correct']
        total = results['positive_total'] + results['negative_total']
        results['overall_accuracy'] = 100.0 * total_correct / total

    # Count errors
    results['errors'] = len(re.findall(r'! ERROR', content))

    # Count tests completed
    results['tests_completed'] = len(re.findall(r'(PASS|FAIL|ERROR)', content))

    return results


def monitor_tests(max_iterations=120, sleep_interval=30):
    """Monitor test progress and report when complete."""
    print("="*80)
    print("VARIANT 9 EVOLUTION - TEST MONITOR")
    print("="*80)
    print(f"Monitoring {len(TESTS_TO_MONITOR)} test(s)")
    print(f"Max iterations: {max_iterations} × {sleep_interval}s = {max_iterations * sleep_interval / 60:.0f} min")
    print("="*80)
    print()

    all_complete = False
    iteration = 0

    while not all_complete and iteration < max_iterations:
        iteration += 1
        timestamp = datetime.now().strftime("%H:%M:%S")

        print(f"\n[{timestamp}] Iteration {iteration}/{max_iterations}")
        print("-"*80)

        status_summary = []
        all_complete = True

        for test_name, test_file in TESTS_TO_MONITOR.items():
            file_path = ROOT / test_file

            if not file_path.exists():
                print(f"  {test_name:12s}: ⏳ Not started yet")
                all_complete = False
                status_summary.append(f"{test_name}:NOT_STARTED")
                continue

            try:
                content = file_path.read_text()
                results = parse_results(content)

                if results['complete']:
                    status = f"✅ COMPLETE"
                    if results['positive_accuracy'] is not None:
                        status += f" - Pos:{results['positive_accuracy']:.1f}% Neg:{results['negative_accuracy']:.1f}%"
                    print(f"  {test_name:12s}: {status}")
                    status_summary.append(f"{test_name}:COMPLETE")
                else:
                    tests_done = results.get('tests_completed', 0)
                    status = f"🔄 Running ({tests_done}/45 tests)"
                    print(f"  {test_name:12s}: {status}")
                    all_complete = False
                    status_summary.append(f"{test_name}:RUNNING:{tests_done}")

            except Exception as e:
                print(f"  {test_name:12s}: ⚠️ Error reading file - {e}")
                all_complete = False
                status_summary.append(f"{test_name}:ERROR")

        if all_complete:
            print("\n" + "="*80)
            print("✅ ALL TESTS COMPLETE!")
            print("="*80)
            break

        if iteration < max_iterations:
            print(f"\n⏳ Sleeping {sleep_interval}s until next check...")
            time.sleep(sleep_interval)

    return all_complete


def analyze_results():
    """Analyze all completed test results."""
    print("\n" + "="*80)
    print("VARIANT 9 EVOLUTION - RESULTS ANALYSIS")
    print("="*80)
    print()

    all_results = []

    for test_name, test_file in TESTS_TO_MONITOR.items():
        file_path = ROOT / test_file

        if not file_path.exists():
            print(f"⚠️ {test_name}: No results file found")
            continue

        try:
            content = file_path.read_text()
            results = parse_results(content)

            if results['complete']:
                print(f"✅ {test_name}:")
                print(f"   Positive: {results.get('positive_correct', 0)}/{results.get('positive_total', 0)} "
                      f"({results.get('positive_accuracy', 0):.1f}%)")
                print(f"   Negative: {results.get('negative_correct', 0)}/{results.get('negative_total', 0)} "
                      f"({results.get('negative_accuracy', 0):.1f}%)")
                print(f"   Overall: {results.get('overall_accuracy', 0):.1f}%")
                print(f"   Errors: {results.get('errors', 0)}")
                print()

                all_results.append({
                    'variant': test_name,
                    'positive_accuracy': results.get('positive_accuracy', 0),
                    'negative_accuracy': results.get('negative_accuracy', 0),
                    'overall_accuracy': results.get('overall_accuracy', 0)
                })
            else:
                print(f"⏳ {test_name}: Test incomplete")
                print()

        except Exception as e:
            print(f"❌ {test_name}: Error analyzing - {e}")
            print()

    if all_results:
        # Find best configuration
        best = max(all_results, key=lambda x: x['overall_accuracy'])

        print("="*80)
        print("BEST CONFIGURATION")
        print("="*80)
        print(f"Variant: {best['variant']}")
        print(f"Positive Accuracy: {best['positive_accuracy']:.1f}%")
        print(f"Negative Accuracy: {best['negative_accuracy']:.1f}%")
        print(f"Overall Accuracy: {best['overall_accuracy']:.1f}%")
        print()

        # Check if target achieved
        if best['positive_accuracy'] >= 95.0 and best['negative_accuracy'] >= 95.0:
            print("🎯 ✅ TARGET ACHIEVED: 95%+ on both metrics!")
        elif best['overall_accuracy'] >= 92.0:
            print(f"✅ SIGNIFICANT IMPROVEMENT: {best['overall_accuracy']:.1f}% overall")
            print(f"   Gap to 95%: Pos={max(0, 95.0 - best['positive_accuracy']):.1f}%, "
                  f"Neg={max(0, 95.0 - best['negative_accuracy']):.1f}%")
        else:
            print(f"⚠️ MODEST IMPROVEMENT: {best['overall_accuracy']:.1f}% overall")
            print(f"   Gap to 95%: Pos={max(0, 95.0 - best['positive_accuracy']):.1f}%, "
                  f"Neg={max(0, 95.0 - best['negative_accuracy']):.1f}%")

        print()

        # Save results
        results_file = ROOT / "outputs" / "evolution" / f"variant9_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)

        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2)

        print(f"✅ Results saved to: {results_file}")

        # Compare with baseline (Variant 0D: 89%/86%)
        print("\n" + "="*80)
        print("COMPARISON WITH BASELINE (Variant 0D: 89%/86%)")
        print("="*80)

        baseline_pos = 89.0
        baseline_neg = 86.0

        for result in sorted(all_results, key=lambda x: x['overall_accuracy'], reverse=True):
            pos_delta = result['positive_accuracy'] - baseline_pos
            neg_delta = result['negative_accuracy'] - baseline_neg

            print(f"{result['variant']:12s}: ", end="")
            print(f"Pos: {result['positive_accuracy']:5.1f}% ({pos_delta:+.1f}%), ", end="")
            print(f"Neg: {result['negative_accuracy']:5.1f}% ({neg_delta:+.1f}%), ", end="")
            print(f"Overall: {result['overall_accuracy']:5.1f}%")

    else:
        print("❌ No complete results found")

    return all_results


def main():
    """Main monitoring and analysis loop."""
    import argparse

    parser = argparse.ArgumentParser(description="Monitor and analyze Variant 9 test results")
    parser.add_argument('--monitor', action='store_true', help="Monitor tests until complete")
    parser.add_argument('--analyze', action='store_true', help="Analyze completed results")
    parser.add_argument('--max-iterations', type=int, default=120, help="Max monitoring iterations")
    parser.add_argument('--sleep', type=int, default=30, help="Sleep interval between checks (seconds)")

    args = parser.parse_args()

    if args.monitor:
        all_complete = monitor_tests(max_iterations=args.max_iterations, sleep_interval=args.sleep)

        if all_complete:
            print("\n✅ Monitoring complete. Analyzing results...")
            analyze_results()
        else:
            print("\n⚠️ Monitoring timed out. Some tests may still be running.")
            print("Run with --analyze to check current status.")

    elif args.analyze:
        analyze_results()

    else:
        # Default: quick status check
        print("Quick status check (use --monitor to track until complete, --analyze for full analysis)")
        print()

        for test_name, test_file in TESTS_TO_MONITOR.items():
            file_path = ROOT / test_file

            if not file_path.exists():
                print(f"  {test_name:12s}: ⏳ Not started")
                continue

            try:
                content = file_path.read_text()
                results = parse_results(content)

                if results['complete']:
                    print(f"  {test_name:12s}: ✅ Complete - "
                          f"Pos:{results.get('positive_accuracy', 0):.1f}% "
                          f"Neg:{results.get('negative_accuracy', 0):.1f}%")
                else:
                    tests_done = results.get('tests_completed', 0)
                    print(f"  {test_name:12s}: 🔄 Running ({tests_done}/45)")

            except Exception as e:
                print(f"  {test_name:12s}: ⚠️ Error - {e}")


if __name__ == "__main__":
    main()
