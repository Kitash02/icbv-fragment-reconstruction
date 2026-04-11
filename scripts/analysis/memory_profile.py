#!/usr/bin/env python3
"""
memory_profile.py
-----------------
Tracks memory usage during pipeline execution on a single test case.

Usage:
    python memory_profile.py [test_folder_path]
"""

import argparse
import sys
import time
import tracemalloc
from pathlib import Path

# Add src to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

import main as pipeline_main


def format_size(size_bytes):
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def profile_single_case(test_folder):
    """Profile memory usage on a single test case."""

    print("\n" + "="*80)
    print("  MEMORY PROFILING - Single Test Case")
    print("="*80)
    print(f"  Test folder: {test_folder}")
    print("="*80 + "\n")

    # Start memory tracking
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()

    # Run pipeline
    output_dir = ROOT / "outputs" / "memory_profile_test"
    log_dir = ROOT / "outputs" / "memory_profile_logs"

    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    args = argparse.Namespace(
        input=str(test_folder),
        output=str(output_dir),
        log=str(log_dir),
    )

    start_time = time.time()

    try:
        pipeline_main.run_pipeline(args)
    except Exception as e:
        print(f"\nError running pipeline: {e}")
        traceback.print_exc()

    elapsed = time.time() - start_time

    # Take snapshot after
    snapshot_after = tracemalloc.take_snapshot()

    # Get current memory usage
    current, peak = tracemalloc.get_traced_memory()

    # Stop tracking
    tracemalloc.stop()

    # Analyze memory changes
    print("\n" + "="*80)
    print("  MEMORY USAGE SUMMARY")
    print("="*80)
    print(f"  Execution time: {elapsed:.2f} seconds")
    print(f"  Current memory: {format_size(current)}")
    print(f"  Peak memory: {format_size(peak)}")
    print("="*80)

    # Show top memory allocations
    print("\n" + "="*80)
    print("  TOP 20 MEMORY ALLOCATIONS")
    print("="*80)

    top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')

    for stat in top_stats[:20]:
        print(f"{stat}")

    print("\n" + "="*80)
    print("  TOP 10 MEMORY ALLOCATIONS BY FILE")
    print("="*80)

    top_stats_by_file = snapshot_after.compare_to(snapshot_before, 'filename')

    for stat in top_stats_by_file[:10]:
        print(f"{stat}")

    return current, peak, elapsed


def main():
    parser = argparse.ArgumentParser(
        description="Profile memory usage on a single test case"
    )
    parser.add_argument(
        'test_folder',
        nargs='?',
        default='data/examples/positive/abstract_art_3frags',
        help='Path to test case folder (default: data/examples/positive/abstract_art_3frags)'
    )

    args = parser.parse_args()

    test_folder = Path(args.test_folder)

    if not test_folder.exists():
        print(f"Error: Test folder not found: {test_folder}")
        sys.exit(1)

    profile_single_case(test_folder)


if __name__ == "__main__":
    main()
