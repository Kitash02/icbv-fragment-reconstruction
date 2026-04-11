#!/usr/bin/env python3
"""
Monitor optimization progress
"""
import time
import subprocess
from pathlib import Path

print("Monitoring Variant 1 optimization progress...")
print("Press Ctrl+C to stop monitoring")
print("="*80)

try:
    while True:
        # Check if JSON results file exists
        results_file = Path("outputs/variant1_complete_optimization.json")

        if results_file.exists():
            import json
            with open(results_file, 'r') as f:
                data = json.load(f)

            print(f"\n[{time.strftime('%H:%M:%S')}] Progress: {len(data)} iterations completed")

            if data:
                latest = data[-1]
                print(f"  Latest: {latest['config']['name']}")
                print(f"    Positive: {latest['pos_acc']:.1f}%")
                print(f"    Negative: {latest['neg_acc']:.1f}%")

                if latest['pos_acc'] >= 95 and latest['neg_acc'] >= 95:
                    print("\n*** TARGET REACHED! ***")
                    break
        else:
            print(f"[{time.strftime('%H:%M:%S')}] Waiting for results file...")

        time.sleep(30)

except KeyboardInterrupt:
    print("\n\nMonitoring stopped")
