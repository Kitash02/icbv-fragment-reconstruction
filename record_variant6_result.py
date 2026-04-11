#!/usr/bin/env python3
"""Record test results for Variant 6 optimization."""

import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent
PROGRESS_FILE = ROOT / "outputs" / "variant6_manual_progress.json"

def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'current_index': 0, 'results': []}

def save_progress(progress):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def main():
    if len(sys.argv) != 4:
        print("Usage: python record_variant6_result.py <power> <pos_acc> <neg_acc>")
        print("Example: python record_variant6_result.py 2.0 88.9 94.4")
        sys.exit(1)

    power = float(sys.argv[1])
    pos_acc = float(sys.argv[2])
    neg_acc = float(sys.argv[3])

    progress = load_progress()
    progress['results'].append({
        'power': power,
        'pos_acc': pos_acc,
        'neg_acc': neg_acc,
        'success': pos_acc >= 95 and neg_acc >= 95
    })
    progress['current_index'] += 1
    save_progress(progress)

    print(f"\nRecorded:")
    print(f"  POWER_COLOR = {power}")
    print(f"  Positive:    {pos_acc}%")
    print(f"  Negative:    {neg_acc}%")
    print(f"  Status:      {'[PASS]' if pos_acc >= 95 and neg_acc >= 95 else '[PARTIAL]'}")
    print()
    print(f"Run 'python update_variant6_power.py' for next iteration")

if __name__ == "__main__":
    main()
