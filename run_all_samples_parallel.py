#!/usr/bin/env python
"""
Run the pipeline on all sample/example datasets in parallel using multiple processes.
This demonstrates the system's capability to handle multiple reconstruction tasks simultaneously.
"""

import os
import subprocess
import multiprocessing
from pathlib import Path
from datetime import datetime
import time

# Configuration
MAX_PARALLEL_AGENTS = 10  # Number of parallel processes
TIMEOUT_MINUTES = 10      # Timeout per dataset

def find_all_datasets():
    """Find all fragment datasets in data folder."""
    datasets = []

    # Add main sample dataset
    sample_dir = "data/sample"
    if os.path.exists(sample_dir):
        datasets.append({
            'name': 'sample',
            'path': sample_dir,
            'category': 'sample'
        })

    # Add all positive examples
    positive_dir = "data/examples/positive"
    if os.path.exists(positive_dir):
        for item in sorted(os.listdir(positive_dir)):
            item_path = os.path.join(positive_dir, item)
            if os.path.isdir(item_path):
                datasets.append({
                    'name': item,
                    'path': item_path,
                    'category': 'positive'
                })

    return datasets

def count_fragments(dataset_path):
    """Count PNG/JPG images in a dataset folder."""
    if not os.path.exists(dataset_path):
        return 0

    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'}
    count = 0

    for filename in os.listdir(dataset_path):
        filepath = os.path.join(dataset_path, filename)
        if os.path.isfile(filepath):
            ext = Path(filename).suffix.lower()
            if ext in image_extensions:
                count += 1

    return count

def run_pipeline_on_dataset(dataset_info):
    """
    Run the reconstruction pipeline on a single dataset.
    Returns dict with results.
    """
    dataset_name = dataset_info['name']
    dataset_path = dataset_info['path']
    category = dataset_info['category']

    print(f"\n{'='*70}")
    print(f"AGENT: Starting reconstruction for '{dataset_name}'")
    print(f"{'='*70}")

    start_time = time.time()

    # Count fragments
    fragment_count = count_fragments(dataset_path)

    # Create output directories specific to this dataset
    output_dir = os.path.join("outputs", "parallel_results", dataset_name)
    log_dir = os.path.join("outputs", "parallel_logs", dataset_name)

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    # Build command
    cmd = [
        "python",
        "src/main.py",
        "--input", dataset_path,
        "--output", output_dir,
        "--log", log_dir
    ]

    result = {
        'name': dataset_name,
        'category': category,
        'path': dataset_path,
        'fragments': fragment_count,
        'success': False,
        'exit_code': None,
        'duration_seconds': 0,
        'error': None,
        'output_dir': output_dir,
        'log_dir': log_dir
    }

    try:
        # Run pipeline with timeout
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_MINUTES * 60,  # Convert to seconds
            cwd=os.getcwd()
        )

        duration = time.time() - start_time
        result['duration_seconds'] = round(duration, 2)
        result['exit_code'] = process.returncode

        if process.returncode == 0:
            result['success'] = True
            print(f"[SUCCESS] '{dataset_name}' completed in {duration:.1f}s")
        else:
            result['success'] = False
            result['error'] = process.stderr[:500] if process.stderr else "Unknown error"
            print(f"[FAILED] '{dataset_name}' (exit code {process.returncode})")

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        result['duration_seconds'] = round(duration, 2)
        result['error'] = f"Timeout after {TIMEOUT_MINUTES} minutes"
        print(f"[TIMEOUT] '{dataset_name}' exceeded {TIMEOUT_MINUTES} minutes")

    except Exception as e:
        duration = time.time() - start_time
        result['duration_seconds'] = round(duration, 2)
        result['error'] = str(e)
        print(f"[ERROR] '{dataset_name}' - {e}")

    return result

def print_summary(results):
    """Print summary table of all results."""
    print("\n" + "="*90)
    print(" PARALLEL EXECUTION SUMMARY")
    print("="*90)
    print(f"{'Dataset':<35} {'Frags':<7} {'Status':<10} {'Time (s)':<10} {'Category':<10}")
    print("-"*90)

    total_success = 0
    total_failed = 0
    total_time = 0

    for result in results:
        name = result['name'][:33]  # Truncate long names
        frags = result['fragments']
        status = "[OK]" if result['success'] else "[FAIL]"
        duration = f"{result['duration_seconds']:.1f}"
        category = result['category']

        print(f"{name:<35} {frags:<7} {status:<10} {duration:<10} {category:<10}")

        if result['success']:
            total_success += 1
        else:
            total_failed += 1
        total_time += result['duration_seconds']

    print("-"*90)
    print(f"Total: {len(results)} datasets | Success: {total_success} | Failed: {total_failed} | Total time: {total_time:.1f}s")
    print("="*90)

    # Print failures with details
    if total_failed > 0:
        print("\n" + "="*90)
        print(" FAILED DATASETS - DETAILS")
        print("="*90)
        for result in results:
            if not result['success']:
                print(f"\n[X] {result['name']}")
                print(f"   Path: {result['path']}")
                print(f"   Error: {result['error'][:200]}")

    # Print output locations
    print("\n" + "="*90)
    print(" OUTPUT LOCATIONS")
    print("="*90)
    print(f"Results: outputs/parallel_results/<dataset_name>/")
    print(f"Logs:    outputs/parallel_logs/<dataset_name>/")

def main():
    """Main entry point."""
    print("="*90)
    print(" Archaeological Fragment Reconstruction - Parallel Batch Processing")
    print("="*90)
    print(f"Configuration:")
    print(f"  - Max parallel agents: {MAX_PARALLEL_AGENTS}")
    print(f"  - Timeout per dataset: {TIMEOUT_MINUTES} minutes")
    print(f"  - Working directory: {os.getcwd()}")
    print("="*90)

    # Find all datasets
    datasets = find_all_datasets()

    if not datasets:
        print("[ERROR] No datasets found in data/ folder!")
        return 1

    print(f"\nFound {len(datasets)} datasets to process:")
    for i, dataset in enumerate(datasets, 1):
        frags = count_fragments(dataset['path'])
        print(f"  {i:2d}. {dataset['name']:<40} ({frags} fragments) [{dataset['category']}]")

    print(f"\nStarting parallel execution with {MAX_PARALLEL_AGENTS} agents...")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    start_time = time.time()

    # Run in parallel using multiprocessing pool
    with multiprocessing.Pool(processes=MAX_PARALLEL_AGENTS) as pool:
        results = pool.map(run_pipeline_on_dataset, datasets)

    total_duration = time.time() - start_time

    print(f"\nAll agents completed!")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total wall-clock time: {total_duration:.1f}s ({total_duration/60:.1f} minutes)")

    # Print summary
    print_summary(results)

    # Calculate speedup
    total_sequential_time = sum(r['duration_seconds'] for r in results)
    speedup = total_sequential_time / total_duration if total_duration > 0 else 0

    print("\n" + "="*90)
    print(" PARALLELIZATION EFFICIENCY")
    print("="*90)
    print(f"Sequential time (estimated): {total_sequential_time:.1f}s ({total_sequential_time/60:.1f} min)")
    print(f"Parallel time (actual):      {total_duration:.1f}s ({total_duration/60:.1f} min)")
    print(f"Speedup:                     {speedup:.2f}x")
    print(f"Efficiency:                  {(speedup/MAX_PARALLEL_AGENTS)*100:.1f}%")
    print("="*90)

    return 0 if all(r['success'] for r in results) else 1

if __name__ == "__main__":
    exit(main())
