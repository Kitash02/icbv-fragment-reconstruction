#!/usr/bin/env python3
"""
Evolutionary testing for Variant 5: Aggressive Color Penalty
Tests color^6, color^7, color^8 to find optimal balance
"""

import subprocess
import json
import sys
from pathlib import Path

# Test configurations
POWER_VALUES = [6.0, 7.0, 8.0]
TARGET_BOTH_METRICS = 0.90  # 90%+ on both positive and negative
ACCEPTABLE_POSITIVE = 0.70  # Minimum acceptable positive accuracy
TARGET_NEGATIVE = 0.95  # Target negative accuracy

def run_test_suite(power_color):
    """Run the full 45-case test suite with given POWER_COLOR value"""
    print(f"\n{'='*60}")
    print(f"Testing POWER_COLOR = {power_color}")
    print(f"{'='*60}")

    # Update the compatibility_variant5.py file with new POWER_COLOR
    variant_path = Path("src/compatibility_variant5.py")

    # Read current file
    with open(variant_path, 'r') as f:
        content = f.read()

    # Replace POWER_COLOR value
    import re
    content = re.sub(
        r'POWER_COLOR\s*=\s*[\d.]+',
        f'POWER_COLOR = {power_color}',
        content
    )

    # Write updated content
    with open(variant_path, 'w') as f:
        f.write(content)

    # Run the test suite
    try:
        result = subprocess.run(
            ['python', 'run_variant5.py', '--no-rotate'],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )

        output = result.stdout + result.stderr

        if result.returncode != 0:
            print(f"Warning: Non-zero return code: {result.returncode}")

        # Parse results from output
        lines = output.split('\n')

        # Count positive and negative results
        positive_correct = 0
        positive_total = 0
        negative_correct = 0
        negative_total = 0

        for line in lines:
            if '[P]' in line and 'PASS' in line:
                positive_correct += 1
                positive_total += 1
            elif '[P]' in line and 'FAIL' in line:
                positive_total += 1
            elif '[N]' in line and 'PASS' in line:
                negative_correct += 1
                negative_total += 1
            elif '[N]' in line and 'FAIL' in line:
                negative_total += 1

        return {
            'positive_correct': positive_correct,
            'positive_total': positive_total,
            'negative_correct': negative_correct,
            'negative_total': negative_total
        }

    except subprocess.TimeoutExpired:
        print(f"Test timed out after 10 minutes")
        return None
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_results(power_color, results):
    """Analyze test results and extract key metrics"""
    if not results:
        return None

    positive_correct = results.get('positive_correct', 0)
    positive_total = results.get('positive_total', 0)
    negative_correct = results.get('negative_correct', 0)
    negative_total = results.get('negative_total', 0)

    positive_acc = positive_correct / positive_total if positive_total > 0 else 0
    negative_acc = negative_correct / negative_total if negative_total > 0 else 0
    overall_acc = (positive_correct + negative_correct) / (positive_total + negative_total)

    analysis = {
        'power_color': power_color,
        'positive_accuracy': positive_acc,
        'negative_accuracy': negative_acc,
        'overall_accuracy': overall_acc,
        'positive_correct': positive_correct,
        'positive_total': positive_total,
        'negative_correct': negative_correct,
        'negative_total': negative_total
    }

    print(f"\nResults for POWER_COLOR = {power_color}:")
    print(f"  Positive: {positive_correct}/{positive_total} = {positive_acc*100:.1f}%")
    print(f"  Negative: {negative_correct}/{negative_total} = {negative_acc*100:.1f}%")
    print(f"  Overall:  {overall_acc*100:.1f}%")

    # Check if meets target
    if positive_acc >= TARGET_BOTH_METRICS and negative_acc >= TARGET_BOTH_METRICS:
        print(f"  *** ACHIEVES 90%+ ON BOTH METRICS! ***")
        analysis['meets_target'] = True
    elif positive_acc >= ACCEPTABLE_POSITIVE and negative_acc >= TARGET_NEGATIVE:
        print(f"  *** ACCEPTABLE: 70%+ positive, 95%+ negative ***")
        analysis['acceptable'] = True
    else:
        print(f"  Does not meet targets")

    return analysis

def main():
    print("="*60)
    print("VARIANT 5 EVOLUTION: AGGRESSIVE COLOR PENALTY")
    print("="*60)
    print(f"\nBaseline (POWER_COLOR=4.0): 77.8% overall")
    print(f"Testing: {POWER_VALUES}")
    print(f"\nTarget: 90%+ on BOTH positive and negative")
    print(f"Acceptable: 70%+ positive, 95%+ negative")

    all_results = []
    best_overall = None
    best_acceptable = None

    for power_color in POWER_VALUES:
        results = run_test_suite(power_color)
        if results:
            analysis = analyze_results(power_color, results)
            if analysis:
                all_results.append(analysis)

                # Check if meets perfect target
                if analysis.get('meets_target'):
                    print(f"\n*** FOUND OPTIMAL CONFIGURATION! ***")
                    print(f"POWER_COLOR = {power_color} achieves 90%+ on both metrics")
                    best_overall = analysis
                    break  # Stop testing

                # Track best acceptable
                if analysis.get('acceptable'):
                    if not best_acceptable or analysis['overall_accuracy'] > best_acceptable['overall_accuracy']:
                        best_acceptable = analysis

                # Track best overall (even if not acceptable)
                if not best_overall or analysis['overall_accuracy'] > best_overall['overall_accuracy']:
                    best_overall = analysis

    # Final report
    print("\n" + "="*60)
    print("FINAL REPORT")
    print("="*60)

    if not all_results:
        print("No valid results obtained")
        return 1

    # Sort by overall accuracy
    all_results.sort(key=lambda x: x['overall_accuracy'], reverse=True)

    print("\nAll Results (sorted by overall accuracy):")
    for r in all_results:
        print(f"\nPOWER_COLOR = {r['power_color']}:")
        print(f"  Positive: {r['positive_accuracy']*100:.1f}%")
        print(f"  Negative: {r['negative_accuracy']*100:.1f}%")
        print(f"  Overall:  {r['overall_accuracy']*100:.1f}%")
        if r.get('meets_target'):
            print(f"  Status: MEETS TARGET (90%+ both)")
        elif r.get('acceptable'):
            print(f"  Status: ACCEPTABLE (70%+ pos, 95%+ neg)")

    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)

    if best_overall and best_overall.get('meets_target'):
        print(f"\n*** OPTIMAL CONFIGURATION FOUND ***")
        print(f"POWER_COLOR = {best_overall['power_color']}")
        print(f"Achieves {best_overall['positive_accuracy']*100:.1f}% positive, {best_overall['negative_accuracy']*100:.1f}% negative")
        print(f"Overall: {best_overall['overall_accuracy']*100:.1f}%")
    elif best_acceptable:
        print(f"\n*** BEST ACCEPTABLE CONFIGURATION ***")
        print(f"POWER_COLOR = {best_acceptable['power_color']}")
        print(f"Achieves {best_acceptable['positive_accuracy']*100:.1f}% positive, {best_acceptable['negative_accuracy']*100:.1f}% negative")
        print(f"Overall: {best_acceptable['overall_accuracy']*100:.1f}%")
        print(f"\nTrade-off: Significantly improved negative accuracy at cost of positive accuracy")
    else:
        print(f"\n*** NO ACCEPTABLE CONFIGURATION FOUND ***")
        print(f"\nBest overall: POWER_COLOR = {best_overall['power_color']}")
        print(f"Positive: {best_overall['positive_accuracy']*100:.1f}%")
        print(f"Negative: {best_overall['negative_accuracy']*100:.1f}%")
        print(f"Overall:  {best_overall['overall_accuracy']*100:.1f}%")
        print(f"\nConclusion: Aggressive color penalty does not achieve target metrics")

    # Expected trade-offs
    print("\n" + "="*60)
    print("EXPECTED vs ACTUAL TRADE-OFFS")
    print("="*60)

    expectations = {
        6.0: "Expected: 70-75% pos, 92-95% neg",
        7.0: "Expected: 65-70% pos, 95-97% neg",
        8.0: "Expected: 60-65% pos, 97-99% neg"
    }

    for r in all_results:
        power = r['power_color']
        if power in expectations:
            print(f"\nPOWER_COLOR = {power}:")
            print(f"  {expectations[power]}")
            print(f"  Actual: {r['positive_accuracy']*100:.1f}% pos, {r['negative_accuracy']*100:.1f}% neg")

            pos_actual = r['positive_accuracy'] * 100
            neg_actual = r['negative_accuracy'] * 100

            # Parse expectations
            if power == 6.0:
                pos_ok = 70 <= pos_actual <= 75
                neg_ok = 92 <= neg_actual <= 95
            elif power == 7.0:
                pos_ok = 65 <= pos_actual <= 70
                neg_ok = 95 <= neg_actual <= 97
            else:  # 8.0
                pos_ok = 60 <= pos_actual <= 65
                neg_ok = 97 <= neg_actual <= 99

            if pos_ok and neg_ok:
                print(f"  Status: Matches expectations")
            else:
                print(f"  Status: Outside expected range")

    # Save results to file
    output_file = "variant5_evolution_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'all_results': all_results,
            'best_overall': best_overall,
            'best_acceptable': best_acceptable
        }, f, indent=2)
    print(f"\nResults saved to: {output_file}")

    return 0

if __name__ == '__main__':
    sys.exit(main())
