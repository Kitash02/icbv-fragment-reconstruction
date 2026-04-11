#!/usr/bin/env python3
"""
Run all 10 variants in TRUE parallel using Python multiprocessing.
"""

import subprocess
import sys
import time
from pathlib import Path
from multiprocessing import Process, Queue

def run_single_variant(variant_id, result_queue):
    """Run a single variant and put results in queue."""
    print(f"[Variant {variant_id}] Starting...")

    start_time = time.time()

    try:
        result = subprocess.run(
            [sys.executable, f"run_variant{variant_id}.py", "--no-rotate"],
            capture_output=True,
            text=True,
            timeout=600  # 10 min timeout
        )

        elapsed = time.time() - start_time
        output = result.stdout

        # Parse results
        lines = output.split('\n')
        positive_pass = positive_total = 0
        negative_pass = negative_total = 0

        for line in lines:
            if '[P]' in line:
                positive_total += 1
                if 'PASS' in line:
                    positive_pass += 1
            elif '[N]' in line:
                negative_total += 1
                if 'PASS' in line:
                    negative_pass += 1

        pos_acc = (positive_pass / positive_total * 100) if positive_total > 0 else 0
        neg_acc = (negative_pass / negative_total * 100) if negative_total > 0 else 0
        overall_acc = ((positive_pass + negative_pass) / (positive_total + negative_total) * 100) if (positive_total + negative_total) > 0 else 0

        # Save full output
        with open(f"outputs/variant{variant_id}_full.txt", 'w') as f:
            f.write(output)

        result_data = {
            'variant_id': variant_id,
            'positive_pass': positive_pass,
            'positive_total': positive_total,
            'positive_acc': pos_acc,
            'negative_pass': negative_pass,
            'negative_total': negative_total,
            'negative_acc': neg_acc,
            'overall_acc': overall_acc,
            'time': elapsed,
            'success': result.returncode == 0
        }

        result_queue.put(result_data)
        print(f"[Variant {variant_id}] DONE: {overall_acc:.1f}% in {elapsed:.1f}s")

    except Exception as e:
        print(f"[Variant {variant_id}] ERROR: {e}")
        result_queue.put({'variant_id': variant_id, 'success': False, 'error': str(e)})

def main():
    print("="*80)
    print("PARALLEL VARIANT TESTING - Python Multiprocessing")
    print("="*80)
    print("Running all 10 variants in parallel...")
    print()

    result_queue = Queue()
    processes = []

    # Launch all 10 processes
    for vid in range(10):
        p = Process(target=run_single_variant, args=(vid, result_queue))
        p.start()
        processes.append(p)

    # Wait for all to complete
    for p in processes:
        p.join()

    # Collect results
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())

    results.sort(key=lambda x: x['variant_id'])

    # Print summary
    print()
    print("="*80)
    print("FINAL RESULTS")
    print("="*80)
    print()
    print(f"{'ID':<4} {'Positive':<15} {'Negative':<15} {'Overall':<10} {'Time':<8}")
    print(f"{'-'*4} {'-'*15} {'-'*15} {'-'*10} {'-'*8}")

    for r in results:
        if r.get('success') and 'positive_acc' in r:
            pos_str = f"{r['positive_pass']}/{r['positive_total']} ({r['positive_acc']:.1f}%)"
            neg_str = f"{r['negative_pass']}/{r['negative_total']} ({r['negative_acc']:.1f}%)"
            overall_str = f"{r['overall_acc']:.1f}%"
            time_str = f"{r['time']:.1f}s"
        else:
            pos_str = "ERROR"
            neg_str = "ERROR"
            overall_str = "ERROR"
            time_str = "-"

        print(f"{r['variant_id']:<4} {pos_str:<15} {neg_str:<15} {overall_str:<10} {time_str:<8}")

    # Best performers
    successful = [r for r in results if r.get('success') and 'overall_acc' in r]
    if successful:
        best = max(successful, key=lambda x: x['overall_acc'])

        print()
        print("="*80)
        print("BEST PERFORMER")
        print("="*80)
        print(f"Variant {best['variant_id']}: {best['overall_acc']:.1f}% overall")
        print(f"  Positive: {best['positive_acc']:.1f}%")
        print(f"  Negative: {best['negative_acc']:.1f}%")

        # Check target
        if best['positive_acc'] >= 95 and best['negative_acc'] >= 95:
            print("\n*** SUCCESS! Achieved 95%+ target!")
        elif best['positive_acc'] >= 90 and best['negative_acc'] >= 90:
            print("\n*** GOOD! Achieved 90%+ (Tier 2)")
        else:
            print(f"\n*** Best result: {best['overall_acc']:.1f}% (target: 95%+)")

    print("="*80)

if __name__ == "__main__":
    main()
