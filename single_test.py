#!/usr/bin/env python3
"""
Single test runner - baseline performance check
"""
import subprocess
import sys

print("Testing Variant 1 with current weights (no rotation)...", flush=True)
print("="*80, flush=True)

try:
    result = subprocess.run(
        [sys.executable, "run_variant1.py", "--no-rotate"],
        timeout=120,
        text=True
    )
    print(f"\nTest completed with exit code: {result.returncode}", flush=True)
except subprocess.TimeoutExpired:
    print("\nTest timed out after 120 seconds", flush=True)
except Exception as e:
    print(f"\nError: {e}", flush=True)
