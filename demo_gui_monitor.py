"""
Example usage demonstration for gui_monitor.py

This script shows how to use PipelineRunner and ProgressCallback
from a GUI context (simulated here with a simple polling loop).
"""

import argparse
import queue
import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import gui_monitor


def simulate_gui_integration():
    """
    Simulate GUI integration with the pipeline runner.

    In a real GUI (tkinter, PyQt, etc.), you would:
    1. Create the runner thread
    2. Start the thread
    3. Poll the queue in your event loop (e.g., tkinter's after())
    4. Update progress bars and handle completion/errors
    """
    print("=== GUI Monitor Demo ===\n")

    # Check if data/sample exists
    sample_dir = os.path.join(os.path.dirname(__file__), 'data', 'sample')
    if not os.path.exists(sample_dir):
        print(f"Error: Sample data directory not found: {sample_dir}")
        print("Please ensure data/sample exists with test fragment images.")
        return

    # Setup pipeline arguments
    args = argparse.Namespace(
        input=sample_dir,
        output='outputs/gui_test',
        log='outputs/gui_test_logs'
    )

    # Create progress queue
    progress_queue = queue.Queue()

    # Create and start pipeline runner
    print(f"Starting pipeline on: {args.input}")
    print(f"Output: {args.output}")
    print(f"Logs: {args.log}\n")

    runner = gui_monitor.PipelineRunner(args, progress_queue)
    runner.start()

    # Simulate GUI event loop polling the queue
    last_percent = -1
    running = True

    while running:
        try:
            # Non-blocking queue check (simulates tkinter's after() callback)
            msg_type, *data = progress_queue.get(timeout=0.1)

            if msg_type == "progress":
                message, percent = data
                if percent is not None:
                    # Only print when percent changes to avoid spam
                    if int(percent) != int(last_percent) if last_percent >= 0 else True:
                        print(f"[{percent:5.1f}%] {message}")
                        last_percent = percent
                else:
                    print(f"[  ...] {message}")

            elif msg_type == "complete":
                results = data[0]
                print(f"\n{'='*60}")
                print("PIPELINE COMPLETED SUCCESSFULLY")
                print(f"{'='*60}")
                print(f"Elapsed time: {results['elapsed_time']:.2f} seconds")
                print(f"Fragments processed: {len(results['fragment_names'])}")
                print(f"Fragment names: {', '.join(results['fragment_names'])}")
                print(f"Assemblies found: {len(results['assemblies'])}")
                print(f"Overall verdict: {results.get('verdict', 'N/A')}")
                print(f"Convergence iterations: {len(results['convergence_trace'])}")

                if results['assemblies']:
                    print(f"\nTop assembly details:")
                    top = results['assemblies'][0]
                    print(f"  Verdict: {top['verdict']}")
                    print(f"  Confidence: {top['confidence']:.4f}")
                    print(f"  MATCH pairs: {top['n_match']}")
                    print(f"  WEAK pairs: {top['n_weak']}")
                    print(f"  NO_MATCH pairs: {top['n_no_match']}")

                print(f"{'='*60}\n")
                running = False

            elif msg_type == "error":
                error_msg = data[0]
                print(f"\n{'='*60}")
                print("PIPELINE ERROR")
                print(f"{'='*60}")
                print(f"Error: {error_msg}")
                print(f"{'='*60}\n")
                running = False

        except queue.Empty:
            # No message available - continue polling
            # In a real GUI, this would be the next after() callback
            pass
        except KeyboardInterrupt:
            print("\n\nCancelling pipeline...")
            runner.request_cancel()
            running = False

    # Wait for thread to finish
    runner.join(timeout=5.0)
    if runner.is_alive():
        print("Warning: Pipeline thread did not terminate cleanly")
    else:
        print("Pipeline thread terminated successfully")


if __name__ == "__main__":
    simulate_gui_integration()
