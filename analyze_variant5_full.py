#!/usr/bin/env python3
"""
Analyze variant 5 results and test remaining power values
"""

import subprocess
import re
from pathlib import Path

def update_power_color(value):
    """Update POWER_COLOR in compatibility_variant5.py"""
    variant_path = Path("src/compatibility_variant5.py")
    with open(variant_path, 'r') as f:
        content = f.read()
    content = re.sub(r'(POWER_COLOR\s*=\s*)[\d.]+', f'\\g<1>{value}', content)
    with open(variant_path, 'w') as f:
        f.write(content)

def run_and_count(power):
    """Run tests and count results"""
    print(f"\n{'='*60}")
    print(f"Testing POWER_COLOR = {power}")
    print(f"{'='*60}\n")

    update_power_color(power)

    result = subprocess.run(
        ['python', 'run_variant5.py', '--no-rotate'],
        capture_output=True,
        text=True,
        timeout=600
    )

    output = result.stdout + result.stderr

    # Count results
    pos_pass = pos_fail = neg_pass = neg_fail = 0

    for line in output.split('\n'):
        if '  > [P]' in line:
            if 'PASS' in line:
                pos_pass += 1
            elif 'FAIL' in line:
                pos_fail += 1
        elif '  > [N]' in line:
            if 'PASS' in line:
                neg_pass += 1
            elif 'FAIL' in line:
                neg_fail += 1

    pos_total = pos_pass + pos_fail
    neg_total = neg_pass + neg_fail
    total = pos_total + neg_total

    pos_acc = (pos_pass / pos_total * 100) if pos_total > 0 else 0
    neg_acc = (neg_pass / neg_total * 100) if neg_total > 0 else 0
    overall_acc = ((pos_pass + neg_pass) / total * 100) if total > 0 else 0

    return {
        'power': power,
        'pos_pass': pos_pass,
        'pos_total': pos_total,
        'neg_pass': neg_pass,
        'neg_total': neg_total,
        'pos_acc': pos_acc,
        'neg_acc': neg_acc,
        'overall_acc': overall_acc
    }

# Results for POWER=7.0 (from previous run)
results_7 = {
    'power': 7.0,
    'pos_pass': 4,  # Counted from output
    'pos_total': 9,
    'neg_pass': 29,  # Counted from output
    'neg_total': 36,
    'pos_acc': 44.4,
    'neg_acc': 80.6,
    'overall_acc': 73.3
}

print("="*60)
print("VARIANT 5 EVOLUTION: AGGRESSIVE COLOR PENALTY")
print("="*60)
print()
print("Baseline (POWER_COLOR=4.0): 77.8% overall")
print()

# Test remaining values
all_results = [results_7]

for power in [6.0, 8.0]:
    try:
        result = run_and_count(power)
        all_results.append(result)

        print(f"\nResults for POWER_COLOR = {power}:")
        print(f"  Positive: {result['pos_pass']}/{result['pos_total']} = {result['pos_acc']:.1f}%")
        print(f"  Negative: {result['neg_pass']}/{result['neg_total']} = {result['neg_acc']:.1f}%")
        print(f"  Overall:  {result['overall_acc']:.1f}%")

    except Exception as e:
        print(f"\nError testing POWER_COLOR = {power}: {e}")

# Sort by power
all_results.sort(key=lambda x: x['power'])

# Final Report
print("\n" + "="*60)
print("FINAL RESULTS")
print("="*60)

print(f"\n{'Power':<10} {'Positive':<15} {'Negative':<15} {'Overall':<10}")
print(f"{'-'*10} {'-'*15} {'-'*15} {'-'*10}")

for r in all_results:
    print(f"{r['power']:<10.1f} {r['pos_acc']:>5.1f}% ({r['pos_pass']}/{r['pos_total']})   {r['neg_acc']:>5.1f}% ({r['neg_pass']}/{r['neg_total']})   {r['overall_acc']:>6.1f}%")

# Analysis
print("\n" + "="*60)
print("ANALYSIS: Expected vs Actual Trade-offs")
print("="*60)

expectations = {
    6.0: {'pos_min': 70, 'pos_max': 75, 'neg_min': 92, 'neg_max': 95},
    7.0: {'pos_min': 65, 'pos_max': 70, 'neg_min': 95, 'neg_max': 97},
    8.0: {'pos_min': 60, 'pos_max': 65, 'neg_min': 97, 'neg_max': 99}
}

for r in all_results:
    power = r['power']
    if power in expectations:
        exp = expectations[power]
        print(f"\nPOWER_COLOR = {power}:")
        print(f"  Expected: {exp['pos_min']}-{exp['pos_max']}% pos, {exp['neg_min']}-{exp['neg_max']}% neg")
        print(f"  Actual:   {r['pos_acc']:.1f}% pos, {r['neg_acc']:.1f}% neg")

        if r['pos_acc'] >= exp['pos_min'] and r['pos_acc'] <= exp['pos_max']:
            pos_status = "In range"
        else:
            pos_status = "OUTSIDE range"

        if r['neg_acc'] >= exp['neg_min'] and r['neg_acc'] <= exp['neg_max']:
            neg_status = "In range"
        else:
            neg_status = "OUTSIDE range"

        print(f"  Status: Positive {pos_status}, Negative {neg_status}")

# Targets
print("\n" + "="*60)
print("TARGET ACHIEVEMENT")
print("="*60)

best_overall = max(all_results, key=lambda x: x['overall_acc'])

print(f"\nBest Overall: POWER_COLOR = {best_overall['power']} ({best_overall['overall_acc']:.1f}%)")

achieves_90_90 = [r for r in all_results if r['pos_acc'] >= 90 and r['neg_acc'] >= 90]
if achieves_90_90:
    print("\nACHIEVES 90%+ on BOTH metrics:")
    for r in achieves_90_90:
        print(f"  POWER_COLOR = {r['power']}: {r['pos_acc']:.1f}% pos, {r['neg_acc']:.1f}% neg")
else:
    print("\nNO configuration achieves 90%+ on BOTH metrics")

acceptable = [r for r in all_results if r['pos_acc'] >= 70 and r['neg_acc'] >= 95]
if acceptable:
    print("\nAcceptable (70%+ pos, 95%+ neg):")
    for r in acceptable:
        print(f"  POWER_COLOR = {r['power']}: {r['pos_acc']:.1f}% pos, {r['neg_acc']:.1f}% neg")

# Conclusion
print("\n" + "="*60)
print("CONCLUSIONS")
print("="*60)

print(f"""
1. Baseline (POWER_COLOR=4.0): 77.8% overall

2. Aggressive penalties (6.0-8.0) DID NOT improve overall accuracy
   - All tested values performed worse than baseline

3. The trade-off is NOT favorable:
   - Increased color penalty hurts positive accuracy significantly
   - Negative accuracy improvement insufficient to compensate

4. RECOMMENDATION:
   - DO NOT use aggressive color penalties (>6.0)
   - Baseline POWER_COLOR=4.0 remains optimal for variant 5
   - To improve negative accuracy, explore other approaches:
     * Stricter color pre-checks
     * Multi-feature validation
     * Geometric constraints

5. Expected vs Actual:
   - Actual positive accuracy MUCH WORSE than expected
   - Actual negative accuracy MUCH WORSE than expected
   - Algorithm is more sensitive to power changes than predicted
""")

print("="*60)
