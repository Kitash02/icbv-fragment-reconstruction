#!/usr/bin/env python3
"""
parallel_variant_tester.py
--------------------------
Master coordinator to launch all 10 variants in parallel for systematic testing.

This script spawns 10 independent Python processes, each running a different variant
configuration on the 45-case benchmark. Results are collected and compared at the end.
"""

import subprocess
import time
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List


def run_variant(variant_id: int, output_dir: Path) -> Dict:
    """
    Run a single variant test in a subprocess.

    Args:
        variant_id: Variant number (0-9)
        output_dir: Where to save results

    Returns:
        Dictionary with results summary
    """
    script = f"run_variant{variant_id}.py" if variant_id > 0 else "run_test.py"
    variant_out = output_dir / f"variant_{variant_id}"
    variant_out.mkdir(parents=True, exist_ok=True)

    log_file = variant_out / "test_output.txt"

    print(f"[Variant {variant_id}] Starting...")

    start_time = time.time()

    try:
        # Run the variant test
        result = subprocess.run(
            ["python", script],
            cwd=Path.cwd() / "icbv-fragment-reconstruction",
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout per variant
        )

        elapsed = time.time() - start_time

        # Save output
        with open(log_file, 'w') as f:
            f.write(f"=== VARIANT {variant_id} TEST OUTPUT ===\n\n")
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\n\nSTDERR:\n")
            f.write(result.stderr)
            f.write(f"\n\nReturn code: {result.returncode}\n")
            f.write(f"Elapsed time: {elapsed:.1f}s\n")

        # Parse results from output
        output_text = result.stdout

        # Extract accuracy metrics
        positive_acc = None
        negative_acc = None
        overall_acc = None

        for line in output_text.split('\n'):
            if "Positive accuracy:" in line:
                try:
                    positive_acc = float(line.split(':')[1].strip().rstrip('%'))
                except:
                    pass
            elif "Negative accuracy:" in line:
                try:
                    negative_acc = float(line.split(':')[1].strip().rstrip('%'))
                except:
                    pass
            elif "Overall accuracy:" in line or "OVERALL:" in line:
                try:
                    overall_acc = float(line.split(':')[1].strip().split()[0].rstrip('%'))
                except:
                    pass

        return {
            "variant_id": variant_id,
            "success": result.returncode == 0,
            "elapsed_time": elapsed,
            "positive_accuracy": positive_acc,
            "negative_accuracy": negative_acc,
            "overall_accuracy": overall_acc,
            "log_file": str(log_file)
        }

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"[Variant {variant_id}] TIMEOUT after {elapsed:.1f}s")
        return {
            "variant_id": variant_id,
            "success": False,
            "elapsed_time": elapsed,
            "error": "Timeout"
        }
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[Variant {variant_id}] ERROR: {e}")
        return {
            "variant_id": variant_id,
            "success": False,
            "elapsed_time": elapsed,
            "error": str(e)
        }


def main():
    print("="*80)
    print("PARALLEL VARIANT TESTING - 10 Variants")
    print("="*80)
    print("Testing configurations:")
    print("  Variant 0: Stage 1.6 Baseline (control)")
    print("  Variant 1: Weighted Ensemble (arXiv:2510.17145)")
    print("  Variant 2: Hierarchical Ensemble")
    print("  Variant 3: Tuned Weighted Ensemble")
    print("  Variant 4: Relaxed Thresholds")
    print("  Variant 5: Color-Dominant (color^6)")
    print("  Variant 6: Balanced Powers (all^2)")
    print("  Variant 7: Optimized Powers (color^5, texture^2.5)")
    print("  Variant 8: Adaptive Thresholds")
    print("  Variant 9: Full Research Stack (99.3% target)")
    print("="*80)
    print()

    output_dir = Path("icbv-fragment-reconstruction/outputs/variant_testing")
    output_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()

    # Launch all 10 variants in parallel
    with ProcessPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(run_variant, vid, output_dir): vid
            for vid in range(10)
        }

        results = []
        for future in as_completed(futures):
            variant_id = futures[future]
            try:
                result = future.result()
                results.append(result)

                if result.get('success'):
                    print(f"[Variant {variant_id}] COMPLETED: "
                          f"Overall={result.get('overall_accuracy', 'N/A')}%, "
                          f"Time={result['elapsed_time']:.1f}s")
                else:
                    print(f"[Variant {variant_id}] FAILED: {result.get('error', 'Unknown error')}")

            except Exception as e:
                print(f"[Variant {variant_id}] EXCEPTION: {e}")
                results.append({
                    "variant_id": variant_id,
                    "success": False,
                    "error": str(e)
                })

    total_time = time.time() - start_time

    # Sort results by variant ID
    results.sort(key=lambda r: r['variant_id'])

    # Generate summary report
    print("\n" + "="*80)
    print("SUMMARY REPORT")
    print("="*80)
    print(f"Total execution time: {total_time:.1f}s")
    print()

    print(f"{'ID':<4} {'Status':<10} {'Overall':<10} {'Positive':<10} {'Negative':<10} {'Time':<10}")
    print(f"{'-'*4} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")

    for r in results:
        vid = r['variant_id']
        status = "PASS" if r.get('success') else "FAIL"
        overall = f"{r['overall_accuracy']:.1f}%" if r.get('overall_accuracy') is not None else "N/A"
        positive = f"{r['positive_accuracy']:.1f}%" if r.get('positive_accuracy') is not None else "N/A"
        negative = f"{r['negative_accuracy']:.1f}%" if r.get('negative_accuracy') is not None else "N/A"
        elapsed = f"{r['elapsed_time']:.1f}s" if 'elapsed_time' in r else "N/A"

        print(f"{vid:<4} {status:<10} {overall:<10} {positive:<10} {negative:<10} {elapsed:<10}")

    # Find best performers
    successful = [r for r in results if r.get('success') and r.get('overall_accuracy') is not None]

    if successful:
        best_overall = max(successful, key=lambda r: r.get('overall_accuracy', 0))
        best_positive = max(successful, key=lambda r: r.get('positive_accuracy', 0))
        best_negative = max(successful, key=lambda r: r.get('negative_accuracy', 0))

        print("\n" + "="*80)
        print("BEST PERFORMERS")
        print("="*80)
        print(f"Best Overall: Variant {best_overall['variant_id']} "
              f"({best_overall['overall_accuracy']:.1f}%)")
        print(f"Best Positive: Variant {best_positive['variant_id']} "
              f"({best_positive['positive_accuracy']:.1f}%)")
        print(f"Best Negative: Variant {best_negative['variant_id']} "
              f"({best_negative['negative_accuracy']:.1f}%)")

        # Check if any reached target
        tier1 = [r for r in successful
                if r.get('positive_accuracy', 0) >= 95 and r.get('negative_accuracy', 0) >= 95]

        if tier1:
            print("\n🎉 SUCCESS: Achieved 95%+ accuracy target!")
            print("Tier 1 variants (95%+ both metrics):")
            for r in tier1:
                print(f"  Variant {r['variant_id']}: "
                      f"{r['positive_accuracy']:.1f}% pos, "
                      f"{r['negative_accuracy']:.1f}% neg")
        else:
            print("\n⚠ Target not reached. Best overall: {:.1f}%".format(
                best_overall['overall_accuracy']))
            print("  Consider Phase 4: Hybrid configurations combining best aspects")

    # Save results to JSON
    results_file = output_dir / "parallel_test_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "total_time": total_time,
            "results": results
        }, f, indent=2)

    print(f"\nResults saved to: {results_file}")
    print("="*80)


if __name__ == "__main__":
    main()
