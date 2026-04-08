#!/usr/bin/env python3
"""
profile_tests.py
----------------
Profiles run_test.py with cProfile to identify performance bottlenecks.

Usage:
    python profile_tests.py [--no-rotate] [--positive-only]
"""

import argparse
import cProfile
import pstats
import io
import time
import sys
from pathlib import Path

def profile_tests(args_list):
    """Run the test suite with profiling enabled."""

    # Save original sys.argv
    original_argv = sys.argv

    # Create profiler
    profiler = cProfile.Profile()

    print("\n" + "="*80)
    print("  PERFORMANCE PROFILING - Fragment Reconstruction Test Suite")
    print("="*80)
    print(f"  Arguments: {' '.join(args_list)}")
    print("="*80 + "\n")

    # Start profiling
    profiler.enable()
    start_time = time.time()

    try:
        # Set up args for run_test
        sys.argv = ['run_test.py'] + args_list

        # Import and run
        import run_test
        run_test.main()

    finally:
        # Stop profiling
        profiler.disable()
        end_time = time.time()

        # Restore original sys.argv
        sys.argv = original_argv

    total_time = end_time - start_time

    # Generate statistics
    stats = pstats.Stats(profiler)

    return stats, total_time


def print_top_functions(stats, n=50):
    """Print top N slowest functions."""
    print("\n" + "="*80)
    print(f"  TOP {n} SLOWEST FUNCTIONS (by cumulative time)")
    print("="*80)
    stats.sort_stats('cumulative')
    stats.print_stats(n)


def print_top_time_functions(stats, n=50):
    """Print top N functions by internal time."""
    print("\n" + "="*80)
    print(f"  TOP {n} FUNCTIONS BY INTERNAL TIME")
    print("="*80)
    stats.sort_stats('time')
    stats.print_stats(n)


def analyze_by_module(stats):
    """Analyze performance by module/stage."""
    print("\n" + "="*80)
    print("  TIME BY MODULE/STAGE")
    print("="*80)

    # Extract all stats
    all_stats = stats.stats

    # Categorize by module
    categories = {
        'preprocessing': 0.0,
        'chain_code': 0.0,
        'shape_descriptors': 0.0,
        'compatibility': 0.0,
        'relaxation': 0.0,
        'hard_discriminators': 0.0,
        'ensemble_voting': 0.0,
        'visualize': 0.0,
        'cv2/opencv': 0.0,
        'numpy': 0.0,
        'other': 0.0,
    }

    for func_info, (cc, nc, tt, ct, callers) in all_stats.items():
        filename, line, funcname = func_info

        if 'preprocessing.py' in filename:
            categories['preprocessing'] += ct
        elif 'chain_code.py' in filename:
            categories['chain_code'] += ct
        elif 'shape_descriptors.py' in filename:
            categories['shape_descriptors'] += ct
        elif 'compatibility.py' in filename:
            categories['compatibility'] += ct
        elif 'relaxation.py' in filename:
            categories['relaxation'] += ct
        elif 'hard_discriminators.py' in filename:
            categories['hard_discriminators'] += ct
        elif 'ensemble_voting.py' in filename:
            categories['ensemble_voting'] += ct
        elif 'visualize.py' in filename or 'assembly_renderer.py' in filename:
            categories['visualize'] += ct
        elif 'cv2' in filename or 'opencv' in filename.lower():
            categories['cv2/opencv'] += ct
        elif 'numpy' in filename:
            categories['numpy'] += ct
        else:
            categories['other'] += ct

    # Sort and print
    total = sum(categories.values())
    sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)

    print(f"\n{'Module/Stage':<30} {'Time (s)':<12} {'Percentage':<12}")
    print("-" * 54)
    for name, time_val in sorted_cats:
        pct = (time_val / total * 100) if total > 0 else 0
        print(f"{name:<30} {time_val:>10.2f}s {pct:>10.1f}%")
    print("-" * 54)
    print(f"{'TOTAL':<30} {total:>10.2f}s {100.0:>10.1f}%")


def get_memory_usage():
    """Get current memory usage."""
    try:
        import psutil
        import os
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return mem_info.rss / 1024 / 1024  # MB
    except ImportError:
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Profile run_test.py to identify performance bottlenecks"
    )
    parser.add_argument('--no-rotate', action='store_true',
                       help='Skip rotation (faster testing)')
    parser.add_argument('--positive-only', action='store_true',
                       help='Run only positive test cases')
    parser.add_argument('--negative-only', action='store_true',
                       help='Run only negative test cases')
    parser.add_argument('--output', default='outputs/implementation/profile_stats.txt',
                       help='Output file for detailed stats')

    args = parser.parse_args()

    # Build argument list for run_test.py
    test_args = []
    if args.no_rotate:
        test_args.append('--no-rotate')
    if args.positive_only:
        test_args.append('--positive-only')
    if args.negative_only:
        test_args.append('--negative-only')

    # Get initial memory
    mem_before = get_memory_usage()

    # Run profiling
    stats, total_time = profile_tests(test_args)

    # Get final memory
    mem_after = get_memory_usage()

    # Print analysis
    print("\n\n")
    print("="*80)
    print("  PROFILING RESULTS SUMMARY")
    print("="*80)
    print(f"  Total wall-clock time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")

    if mem_before is not None and mem_after is not None:
        print(f"  Memory usage: {mem_before:.1f} MB -> {mem_after:.1f} MB (delta: {mem_after - mem_before:.1f} MB)")

    # Analyze by module/stage
    analyze_by_module(stats)

    # Print top functions
    print_top_functions(stats, n=30)

    # Save detailed stats to file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        # Redirect stats to file
        s = pstats.Stats(stats, stream=f)

        f.write("="*80 + "\n")
        f.write("  COMPLETE PROFILING STATISTICS\n")
        f.write("="*80 + "\n\n")
        f.write(f"Total wall-clock time: {total_time:.2f} seconds\n\n")

        f.write("\n" + "="*80 + "\n")
        f.write("  BY CUMULATIVE TIME\n")
        f.write("="*80 + "\n")
        s.sort_stats('cumulative')
        s.print_stats(100)

        f.write("\n" + "="*80 + "\n")
        f.write("  BY INTERNAL TIME\n")
        f.write("="*80 + "\n")
        s.sort_stats('time')
        s.print_stats(100)

        f.write("\n" + "="*80 + "\n")
        f.write("  CALLERS\n")
        f.write("="*80 + "\n")
        s.print_callers(50)

    print(f"\n\n  Detailed statistics saved to: {output_path.resolve()}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
