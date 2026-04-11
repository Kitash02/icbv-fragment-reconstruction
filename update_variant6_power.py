#!/usr/bin/env python3
"""
Simple Power Updater for Variant 6
===================================

Updates POWER_COLOR and tracks progress through manual testing.
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
PROGRESS_FILE = ROOT / "outputs" / "variant6_manual_progress.json"

# Test sequence
POWERS = [2.0, 2.5, 3.0, 3.5, 4.0]

def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'current_index': 0, 'results': []}

def save_progress(progress):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def update_power(power):
    variant6_file = SRC / "compatibility_variant6.py"

    with open(variant6_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    with open(variant6_file, 'w', encoding='utf-8') as f:
        for line in lines:
            if line.startswith('POWER_COLOR = '):
                f.write(f'POWER_COLOR = {power}      # Iteration test\n')
            else:
                f.write(line)

def record_result(power, pos_acc, neg_acc):
    """Record test results."""
    progress = load_progress()
    progress['results'].append({
        'power': power,
        'pos_acc': pos_acc,
        'neg_acc': neg_acc,
        'success': pos_acc >= 95 and neg_acc >= 95
    })
    progress['current_index'] += 1
    save_progress(progress)
    print(f"\nRecorded result for POWER_COLOR={power}")

def main():
    import sys

    progress = load_progress()
    idx = progress['current_index']

    if idx >= len(POWERS):
        print("="*80)
        print("ALL ITERATIONS COMPLETE!")
        print("="*80)
        print()
        print(f"{'Power':<8} {'Positive':<12} {'Negative':<12} {'Status'}")
        print("-"*80)
        for r in progress['results']:
            status = "[PASS]" if r['success'] else ""
            print(f"{r['power']:<8.1f} {r['pos_acc']:<12.1f} {r['neg_acc']:<12.1f} {status}")
        print("-"*80)

        best = max(progress['results'], key=lambda x: min(x['pos_acc'], x['neg_acc']))
        print(f"\nBest: POWER_COLOR = {best['power']}")
        print(f"  Positive: {best['pos_acc']:.1f}%")
        print(f"  Negative: {best['neg_acc']:.1f}%")
        return

    power = POWERS[idx]

    print("="*80)
    print(f"VARIANT 6 EVOLUTIONARY OPTIMIZATION - ITERATION {idx+1}/{len(POWERS)}")
    print("="*80)
    print(f"\nSetting POWER_COLOR = {power}")

    update_power(power)

    print(f"\nUpdated! Now run:")
    print(f"  python test_variant6_simple.py --no-rotate")
    print()
    print(f"After the test completes, record results with:")
    print(f"  python record_variant6_result.py {power} <pos_acc> <neg_acc>")
    print()
    print(f"Example:")
    print(f"  python record_variant6_result.py {power} 88.9 94.4")
    print("="*80)

if __name__ == "__main__":
    main()
