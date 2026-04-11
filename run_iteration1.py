#!/usr/bin/env python3
"""
Iteration 1 Test - Apply weights and test
"""
import subprocess
import sys
import re
from pathlib import Path

# Iteration 1 weights
WEIGHTS = {
    'color': 0.30,
    'raw_compat': 0.28,
    'texture': 0.23,
    'morphological': 0.14,
    'gabor': 0.05
}

def apply_weights():
    """Apply weights to ensemble_voting.py"""
    voting_file = Path("src/ensemble_voting.py")
    content = voting_file.read_text()

    # Create weights string
    weights_str = f"""weights = {{
            'color': {WEIGHTS['color']},
            'raw_compat': {WEIGHTS['raw_compat']},
            'texture': {WEIGHTS['texture']},
            'morphological': {WEIGHTS['morphological']},
            'gabor': {WEIGHTS['gabor']}
        }}"""

    # Replace
    pattern = r"if weights is None:\s*weights = \{[^}]+\}"
    replacement = f"if weights is None:\n        {weights_str}"

    new_content = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)

    if new_content != content:
        voting_file.write_text(new_content)
        print("✓ Applied Iteration 1 weights")
        return True
    else:
        print("✗ WARNING: Could not apply weights!")
        return False

print("="*80)
print("ITERATION 1: Reduced Color Dominance")
print("="*80)
print("\nWeights:")
for k, v in WEIGHTS.items():
    print(f"  {k:15s}: {v:.2f}")
print()

# Apply weights
if not apply_weights():
    sys.exit(1)

# Run test
print("\nRunning test (positive only, no rotation)...")
print("="*80)

result = subprocess.run(
    [sys.executable, "run_variant1.py", "--positive-only", "--no-rotate"]
)

print("\n" + "="*80)
print("Iteration 1 complete")
print("="*80)

sys.exit(result.returncode)
