#!/usr/bin/env python3
"""
Rapid Iteration Tester for Variant 1
=====================================
Tests current weights and provides immediate feedback
"""
import subprocess
import sys
import time
import re

def extract_weights_from_file():
    """Read current weights from ensemble_voting.py"""
    with open("src/ensemble_voting.py", 'r') as f:
        content = f.read()

    # Find weights block
    pattern = r"weights = \{[^}]+\}"
    match = re.search(pattern, content)

    if match:
        weights_str = match.group(0)
        # Extract values
        color = float(re.search(r"'color':\s*([\d.]+)", weights_str).group(1))
        raw = float(re.search(r"'raw_compat':\s*([\d.]+)", weights_str).group(1))
        texture = float(re.search(r"'texture':\s*([\d.]+)", weights_str).group(1))
        morph = float(re.search(r"'morphological':\s*([\d.]+)", weights_str).group(1))
        gabor = float(re.search(r"'gabor':\s*([\d.]+)", weights_str).group(1))

        return {
            'color': color,
            'raw_compat': raw,
            'texture': texture,
            'morphological': morph,
            'gabor': gabor
        }
    return None

print("="*80)
print("VARIANT 1 RAPID ITERATION TEST")
print("="*80)

# Show current weights
weights = extract_weights_from_file()
if weights:
    print("\nCurrent Weights:")
    for key, val in weights.items():
        print(f"  {key:15s}: {val:.2f} ({val*100:.0f}%)")
else:
    print("\nWARNING: Could not extract weights from file!")

print("\n" + "="*80)
print("Running test (positive cases only, no rotation)...")
print("="*80)

start = time.time()

try:
    result = subprocess.run(
        [sys.executable, "run_variant1.py", "--positive-only", "--no-rotate"],
        capture_output=True,
        text=True,
        timeout=600  # 10 minute timeout
    )
    output = result.stdout + result.stderr
except subprocess.TimeoutExpired:
    print("\nERROR: Test timed out after 10 minutes")
    sys.exit(1)
except Exception as e:
    print(f"\nERROR: {e}")
    sys.exit(1)

elapsed = time.time() - start

# Parse results
positive_pass = positive_total = 0
failures = []

for line in output.split('\n'):
    if '[P]' in line:
        positive_total += 1
        if 'PASS' in line:
            positive_pass += 1
        elif 'FAIL' in line:
            # Extract case name
            parts = line.split('[P]')
            if len(parts) > 1:
                case_name = parts[1].split()[0]
                failures.append(case_name)

# Calculate accuracy
pos_acc = (positive_pass / positive_total * 100) if positive_total > 0 else 0

# Display results
print("\n" + "="*80)
print("RESULTS")
print("="*80)
print(f"Positive Cases: {positive_pass}/{positive_total} PASS = {pos_acc:.1f}%")
print(f"False Negatives: {positive_total - positive_pass}")
print(f"Test Time: {elapsed:.1f}s (avg {elapsed/max(1,positive_total):.1f}s per case)")

if failures:
    print(f"\nFailed Cases ({len(failures)}):")
    for i, case in enumerate(failures, 1):
        print(f"  {i}. {case}")

print("\n" + "="*80)
print("ANALYSIS")
print("="*80)

if pos_acc >= 95:
    print("✓ POSITIVE TARGET MET (>= 95%)")
    print("\nNext step: Test negative cases")
    print("  Run: python run_variant1.py --negative-only --no-rotate")
else:
    fn_rate = 100 - pos_acc
    print(f"✗ Positive accuracy below target: {95 - pos_acc:.1f}% gap")
    print(f"  False Negative Rate: {fn_rate:.1f}%")
    print("\nSuggested adjustments:")
    if fn_rate > 15:
        print("  - Decrease color weight by 0.03-0.05")
        print("  - Increase texture/raw_compat weights")
    elif fn_rate > 5:
        print("  - Decrease color weight by 0.02")
        print("  - Increase texture weight by 0.02")
    else:
        print("  - Lower thresholds by 0.02-0.03")
        print("  - Or micro-adjust weights by 0.01")

print("="*80)
