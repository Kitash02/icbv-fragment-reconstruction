#!/usr/bin/env python3
"""
Quick diagnostic: Test a specific false positive case to see what scores it gets.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path("src")))

# Test case: mixed_gettyimages-21778090_scroll (FALSE POSITIVE)
# This should be NO_MATCH but is getting MATCH

test_dir = Path("data/examples/negative/mixed_gettyimages-21778090_scroll")

if test_dir.exists():
    print(f"Testing: {test_dir.name}")
    print("Expected: NO_MATCH (negative case)")
    print("Actual from Variant 0: MATCH (FALSE POSITIVE)")
    print()

    # List fragments
    fragments = sorted([f for f in test_dir.iterdir() if f.suffix.lower() in ['.png', '.jpg', '.jpeg']])
    print(f"Fragments: {[f.name for f in fragments]}")
    print()

    # Run quick compatibility check
    import main as pipeline_main
    import argparse

    args_ns = argparse.Namespace(
        input=str(test_dir),
        output="outputs/diagnostic",
        log="outputs/diagnostic_logs"
    )

    print("Running pipeline...")
    try:
        pipeline_main.run_pipeline(args_ns)
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"Test directory not found: {test_dir}")
