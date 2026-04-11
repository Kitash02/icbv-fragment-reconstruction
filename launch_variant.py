#!/usr/bin/env python3
"""
Quick launcher for individual variant testing.

Usage:
    python launch_variant.py 0    # Test baseline only
    python launch_variant.py 5    # Test color^6 variant only
    python launch_variant.py all  # Test all variants in sequence
"""

import sys
import subprocess
from pathlib import Path

def run_single_variant(variant_id):
    """Run a single variant test."""
    script = f"run_variant{variant_id}.py"

    if not Path(script).exists():
        print(f"Error: {script} not found!")
        return False

    print(f"\n{'='*80}")
    print(f"Running Variant {variant_id}")
    print(f"{'='*80}\n")

    result = subprocess.run([sys.executable, script])
    return result.returncode == 0

def main():
    if len(sys.argv) < 2:
        print("Usage: python launch_variant.py <variant_id|all>")
        print("  variant_id: 0-9")
        print("  all: run all variants sequentially")
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "all":
        print("Running all 10 variants sequentially...")
        success_count = 0
        for vid in range(10):
            if run_single_variant(vid):
                success_count += 1

        print(f"\n{'='*80}")
        print(f"Completed: {success_count}/10 variants successful")
        print(f"{'='*80}")
    else:
        try:
            variant_id = int(arg)
            if variant_id < 0 or variant_id > 9:
                print("Error: variant_id must be 0-9")
                sys.exit(1)

            success = run_single_variant(variant_id)
            sys.exit(0 if success else 1)
        except ValueError:
            print("Error: Invalid argument. Use 0-9 or 'all'")
            sys.exit(1)

if __name__ == "__main__":
    main()
