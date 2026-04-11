#!/usr/bin/env python3
"""
Evolutionary Optimizer for Variant 6: Balanced Powers (all^2)
==============================================================

Mission: Iterate until Variant 6 achieves 95%+ accuracy on BOTH positive and negative tests.

Strategy:
---------
1. Test baseline (all powers = 2.0)
2. Analyze failure patterns
3. If negative accuracy is poor (expected):
   - Gradually increase color power: 2.0 → 2.5 → 3.0 → 3.5 → 4.0
   - Keep other powers at 2.0
4. Find optimal balance point (95%+ both metrics)
5. Fine-tune if needed

Expected Behavior:
------------------
- Baseline (all=2.0): High positive accuracy, poor negative (too permissive)
- As color power increases: negative improves, positive may decline slightly
- Target: Find minimum color power for 95%+ negative while preserving 95%+ positive
"""

import sys
import os
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, Tuple

ROOT = Path(__file__).parent
SRC = ROOT / "src"

def parse_test_output(output: str) -> Dict:
    """Extract accuracy metrics from run_test.py output."""
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

    pos_acc = (positive_pass / positive_total * 100) if positive_total > 0 else 0
    neg_acc = (negative_pass / negative_total * 100) if negative_total > 0 else 0
    overall = ((positive_pass + negative_pass) / (positive_total + negative_total) * 100) \
              if (positive_total + negative_total) > 0 else 0

    return {
        'positive_pass': positive_pass,
        'positive_total': positive_total,
        'positive_acc': pos_acc,
        'negative_pass': negative_pass,
        'negative_total': negative_total,
        'negative_acc': neg_acc,
        'overall_acc': overall,
        'raw_output': output
    }

def update_variant6_powers(power_color: float, power_texture: float = 2.0,
                          power_gabor: float = 2.0, power_haralick: float = 2.0):
    """Update the power values in compatibility_variant6.py"""
    variant6_file = SRC / "compatibility_variant6.py"

    # Read current file
    with open(variant6_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace power values
    lines = content.split('\n')
    new_lines = []

    for line in lines:
        if line.startswith('POWER_COLOR = '):
            new_lines.append(f'POWER_COLOR = {power_color}      # Optimized by evolutionary search')
        elif line.startswith('POWER_TEXTURE = '):
            new_lines.append(f'POWER_TEXTURE = {power_texture}    # Equal weight')
        elif line.startswith('POWER_GABOR = '):
            new_lines.append(f'POWER_GABOR = {power_gabor}      # Equal weight')
        elif line.startswith('POWER_HARALICK = '):
            new_lines.append(f'POWER_HARALICK = {power_haralick}   # Equal weight')
        else:
            new_lines.append(line)

    # Write back
    with open(variant6_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    print(f"  > Updated powers: color={power_color}, texture={power_texture}, "
          f"gabor={power_gabor}, haralick={power_haralick}")

def run_test_iteration(iteration: int, power_color: float) -> Tuple[Dict, str]:
    """Run one test iteration with specified color power."""

    print(f"\n{'-'*80}")
    print(f"ITERATION {iteration}: Testing color_power = {power_color}")
    print(f"{'-'*80}")

    # Update configuration
    update_variant6_powers(power_color)

    # Create monkey patch script
    test_script = ROOT / f"_test_variant6_iter{iteration}.py"

    with open(test_script, 'w', encoding='utf-8') as f:
        f.write(f'''#!/usr/bin/env python3
"""Temporary test script for Variant 6 iteration {iteration}"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Monkey-patch compatibility_variant6 as 'compatibility'
import compatibility_variant6
sys.modules['compatibility'] = compatibility_variant6

# Run standard test
import run_test
run_test.main()
''')

    # Run test
    print(f"  Running test (this may take 2-3 minutes)...")
    start_time = time.time()

    try:
        result = subprocess.run(
            [sys.executable, str(test_script), '--no-rotate'],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=300
        )
        output = result.stdout + result.stderr
        elapsed = time.time() - start_time

        print(f"  Test completed in {elapsed:.1f}s")

        # Parse results
        metrics = parse_test_output(output)

        print(f"  Results:")
        print(f"    Positive: {metrics['positive_pass']}/{metrics['positive_total']} "
              f"({metrics['positive_acc']:.1f}%)")
        print(f"    Negative: {metrics['negative_pass']}/{metrics['negative_total']} "
              f"({metrics['negative_acc']:.1f}%)")
        print(f"    Overall:  {metrics['overall_acc']:.1f}%")

        # Save output
        output_file = ROOT / "outputs" / f"variant6_iter{iteration}_color{power_color}.txt"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)

        return metrics, output

    except subprocess.TimeoutExpired:
        print(f"  ⚠ Test timed out after 5 minutes")
        return {
            'positive_acc': 0, 'negative_acc': 0, 'overall_acc': 0,
            'positive_pass': 0, 'positive_total': 0,
            'negative_pass': 0, 'negative_total': 0,
            'raw_output': 'TIMEOUT'
        }, 'TIMEOUT'
    except Exception as e:
        print(f"  ⚠ Test failed: {e}")
        return {
            'positive_acc': 0, 'negative_acc': 0, 'overall_acc': 0,
            'positive_pass': 0, 'positive_total': 0,
            'negative_pass': 0, 'negative_total': 0,
            'raw_output': f'ERROR: {e}'
        }, f'ERROR: {e}'
    finally:
        # Cleanup
        if test_script.exists():
            test_script.unlink()

def evolutionary_search():
    """
    Main evolutionary optimization loop.

    Tests color powers in sequence: 2.0, 2.5, 3.0, 3.5, 4.0
    Stops when 95%+ achieved on both metrics or all values tested.
    """

    print("="*80)
    print("EVOLUTIONARY OPTIMIZATION: Variant 6 (Balanced Powers)")
    print("="*80)
    print()
    print("Configuration:")
    print("  Starting point: ALL powers = 2.0 (equal weighting)")
    print("  Optimization:   Gradually increase color power")
    print("  Target:         95%+ positive AND 95%+ negative accuracy")
    print("  Strategy:       Find minimum color power for 95%+ negative")
    print("                  while preserving 95%+ positive")
    print("="*80)
    print()

    # Test sequence
    color_powers = [2.0, 2.5, 3.0, 3.5, 4.0]

    history = []
    best_config = None
    best_score = 0

    for iteration, power_color in enumerate(color_powers, start=1):

        # Run test
        metrics, output = run_test_iteration(iteration, power_color)

        # Record history
        history.append({
            'iteration': iteration,
            'power_color': power_color,
            'power_texture': 2.0,
            'power_gabor': 2.0,
            'power_haralick': 2.0,
            'metrics': metrics
        })

        # Check if target achieved
        pos_acc = metrics['positive_acc']
        neg_acc = metrics['negative_acc']

        if pos_acc >= 95 and neg_acc >= 95:
            print(f"\n{'*'*80}")
            print(f"TARGET ACHIEVED!")
            print(f"{'*'*80}")
            print(f"  Optimal color_power = {power_color}")
            print(f"  Positive accuracy:    {pos_acc:.1f}%")
            print(f"  Negative accuracy:    {neg_acc:.1f}%")
            print(f"{'*'*80}")
            best_config = history[-1]
            break

        # Track best overall score
        min_score = min(pos_acc, neg_acc)
        if min_score > best_score:
            best_score = min_score
            best_config = history[-1]

        # Status update
        if pos_acc >= 95:
            print(f"  [+] Positive target met ({pos_acc:.1f}%)")
        else:
            print(f"  [-] Positive below target ({pos_acc:.1f}% < 95%)")

        if neg_acc >= 95:
            print(f"  [+] Negative target met ({neg_acc:.1f}%)")
        else:
            print(f"  [-] Negative below target ({neg_acc:.1f}% < 95%)")

        # Early stopping if both metrics declining
        if iteration >= 3:
            recent = history[-3:]
            pos_trend = [h['metrics']['positive_acc'] for h in recent]
            neg_trend = [h['metrics']['negative_acc'] for h in recent]

            if all(pos_trend[i] <= pos_trend[i-1] for i in range(1, len(pos_trend))):
                if all(neg_trend[i] <= neg_trend[i-1] for i in range(1, len(neg_trend))):
                    print(f"\n  [EARLY STOP] Both metrics declining - stopping early")
                    break

    # Final summary
    print(f"\n{'='*80}")
    print("EVOLUTIONARY OPTIMIZATION COMPLETE")
    print(f"{'='*80}")
    print()
    print("Iteration History:")
    print(f"{'-'*80}")
    print(f"{'Iter':<6} {'Color':<8} {'Positive':<12} {'Negative':<12} {'Overall':<10} {'Status'}")
    print(f"{'-'*80}")

    for h in history:
        pos = h['metrics']['positive_acc']
        neg = h['metrics']['negative_acc']
        overall = h['metrics']['overall_acc']
        color = h['power_color']

        status = "[PASS]" if (pos >= 95 and neg >= 95) else "  ----"

        print(f"{h['iteration']:<6} {color:<8.1f} {pos:<12.1f} {neg:<12.1f} {overall:<10.1f} {status}")

    print(f"{'-'*80}")
    print()

    if best_config:
        print("Best Configuration Found:")
        print(f"  Color Power:      {best_config['power_color']}")
        print(f"  Texture Power:    {best_config['power_texture']}")
        print(f"  Gabor Power:      {best_config['power_gabor']}")
        print(f"  Haralick Power:   {best_config['power_haralick']}")
        print(f"  Positive Acc:     {best_config['metrics']['positive_acc']:.1f}%")
        print(f"  Negative Acc:     {best_config['metrics']['negative_acc']:.1f}%")
        print(f"  Overall Acc:      {best_config['metrics']['overall_acc']:.1f}%")

        if best_config['metrics']['positive_acc'] >= 95 and best_config['metrics']['negative_acc'] >= 95:
            print(f"\n  [SUCCESS] Target of 95%+ on BOTH metrics ACHIEVED!")
        else:
            print(f"\n  [PARTIAL] Target not fully achieved - best effort shown above")

    # Save history
    history_file = ROOT / "outputs" / "variant6_evolution_history.json"
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)

    print(f"\n  Evolution history saved to: {history_file}")
    print(f"{'='*80}")

if __name__ == "__main__":
    evolutionary_search()
