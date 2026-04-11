#!/usr/bin/env python3
"""
Quick test - Positive cases only
Tests just the 9 positive cases to quickly check FN rate
"""
import subprocess
import sys
import time

print("="*80)
print("VARIANT 1 - QUICK TEST (POSITIVE CASES ONLY)")
print("="*80)
print("Testing only positive cases to measure FN rate")
print("="*80)
print()

start = time.time()

result = subprocess.run(
    [sys.executable, "run_variant1.py", "--positive-only", "--no-rotate"],
    text=True
)

elapsed = time.time() - start

print(f"\nTotal time: {elapsed:.1f}s")
print("="*80)
