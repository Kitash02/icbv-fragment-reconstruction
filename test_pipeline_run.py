#!/usr/bin/env python
"""
Quick test to verify the pipeline runs correctly with sample data.
This simulates what the GUI does when you click "Run Assembly".
"""

import subprocess
import sys
import os

print("=" * 70)
print(" Testing Pipeline Execution (What GUI Does)")
print("=" * 70)

# Change to project root
os.chdir(r"C:\Users\I763940\icbv-fragment-reconstruction")
print(f"\nWorking directory: {os.getcwd()}")

# Build command (exactly what GUI uses)
cmd = [
    "python",
    "src/main.py",
    "--input", "data/sample",
    "--output", "outputs/results",
    "--log", "outputs/logs"
]

print(f"\nCommand: {' '.join(cmd)}")
print("\nRunning pipeline...")
print("=" * 70)

# Run command
try:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout
    )

    print(f"\nExit code: {result.returncode}")

    if result.returncode == 0:
        print("\n✅ SUCCESS: Pipeline completed!")
        print("\nOutput (last 20 lines):")
        print("-" * 70)
        stdout_lines = result.stdout.split('\n')
        for line in stdout_lines[-20:]:
            print(line)
    else:
        print("\n❌ FAILED: Pipeline error!")
        print("\nError output:")
        print("-" * 70)
        print(result.stderr[:1000])

except subprocess.TimeoutExpired:
    print("\n❌ TIMEOUT: Pipeline took longer than 5 minutes")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
