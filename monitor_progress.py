#!/usr/bin/env python3
"""
Monitor progress of parallel variant testing.
Shows real-time updates as variants complete.
"""

import json
import time
from pathlib import Path

def check_progress():
    """Check how many variants have completed."""
    output_dir = Path("outputs/variant_testing")

    if not output_dir.exists():
        print("Testing not started yet...")
        return 0, []

    completed = []
    for vid in range(10):
        result_file = output_dir / f"variant_{vid}" / "test_output.txt"
        if result_file.exists():
            completed.append(vid)

    return len(completed), completed

def main():
    print("="*80)
    print("PARALLEL VARIANT TESTING - PROGRESS MONITOR")
    print("="*80)
    print("Monitoring outputs/variant_testing/")
    print("Press Ctrl+C to exit\n")

    last_count = 0

    try:
        while True:
            count, completed = check_progress()

            if count != last_count:
                print(f"[{time.strftime('%H:%M:%S')}] {count}/10 variants completed: {completed}")
                last_count = count

            if count == 10:
                print("\n🎉 All variants completed!")
                print("Check: outputs/variant_testing/parallel_test_results.json")
                break

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
        count, completed = check_progress()
        print(f"Final status: {count}/10 completed")

if __name__ == "__main__":
    main()
