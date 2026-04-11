"""
Example: Using progress_callback with the archaeological fragment reconstruction pipeline

This example demonstrates how to use the optional progress_callback parameter
to monitor pipeline execution progress.
"""

import argparse
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def simple_progress_callback(message, percent=None):
    """Simple callback that prints progress to console"""
    if percent is not None:
        print(f"[{percent:3d}%] {message}")
    else:
        print(f"[INFO] {message}")


def gui_style_progress_callback(message, percent=None):
    """Callback that could be adapted for GUI progress bars"""
    # In a real GUI application, you would update a progress bar widget here
    if percent is not None:
        # Update progress bar to percent
        bar_length = 40
        filled = int(bar_length * percent / 100)
        bar = '=' * filled + '-' * (bar_length - filled)
        print(f"[{bar}] {percent}% - {message}")
    else:
        print(f"Processing: {message}")


def detailed_progress_callback(message, percent=None):
    """Callback with detailed logging including timestamps"""
    from datetime import datetime
    timestamp = datetime.now().strftime('%H:%M:%S')

    if percent is not None:
        print(f"[{timestamp}] Progress: {percent:3d}% | {message}")
    else:
        print(f"[{timestamp}] Status: {message}")


def example_1_simple():
    """Example 1: Simple progress reporting"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Simple Progress Reporting")
    print("="*70 + "\n")

    # Simulate what would happen during pipeline execution
    print("When you run the pipeline with simple_progress_callback:\n")

    simple_progress_callback("Loading fragments... (1/8)", percent=12)
    simple_progress_callback("Loading fragments... (2/8)", percent=25)
    simple_progress_callback("Loading fragments... (3/8)", percent=37)
    simple_progress_callback("Extracting contours...")
    simple_progress_callback("Computing compatibility scores...", percent=0)
    simple_progress_callback("Computing compatibility scores... (100%)", percent=100)
    simple_progress_callback("Relaxation iteration 0/50...", percent=0)
    simple_progress_callback("Relaxation iteration 23/50...", percent=100)
    simple_progress_callback("Rendering results...")


def example_2_gui_style():
    """Example 2: GUI-style progress bar"""
    print("\n" + "="*70)
    print("EXAMPLE 2: GUI-Style Progress Bar")
    print("="*70 + "\n")

    print("This style could be adapted for graphical user interfaces:\n")

    gui_style_progress_callback("Loading fragments... (1/8)", percent=12)
    gui_style_progress_callback("Loading fragments... (5/8)", percent=62)
    gui_style_progress_callback("Extracting contours...")
    gui_style_progress_callback("Computing compatibility scores...", percent=50)
    gui_style_progress_callback("Relaxation iteration 15/50...", percent=75)
    gui_style_progress_callback("Rendering results...")


def example_3_detailed():
    """Example 3: Detailed logging with timestamps"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Detailed Progress with Timestamps")
    print("="*70 + "\n")

    print("Useful for logging and debugging:\n")

    detailed_progress_callback("Loading fragments... (1/8)", percent=12)
    detailed_progress_callback("Loading fragments... (8/8)", percent=100)
    detailed_progress_callback("Extracting contours...")
    detailed_progress_callback("Computing compatibility scores...", percent=100)
    detailed_progress_callback("Relaxation iteration 50/50...", percent=100)
    detailed_progress_callback("Rendering results...")


def example_4_actual_usage():
    """Example 4: How to use it in real code"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Actual Usage Code")
    print("="*70 + "\n")

    code_example = '''
# Import required modules
from main import run_pipeline
import argparse

# Define your progress callback
def my_progress_callback(message, percent=None):
    """Custom progress handler"""
    if percent is not None:
        print(f"Progress: {percent}% - {message}")
    else:
        print(f"Status: {message}")

# Create arguments
args = argparse.Namespace(
    input='data/sample',
    output='outputs/results',
    log='outputs/logs'
)

# Run pipeline with progress callback
run_pipeline(args, progress_callback=my_progress_callback)

# Or run without progress callback (original behavior)
run_pipeline(args)  # progress_callback defaults to None
'''

    print("Python code:")
    print(code_example)


def example_5_cli_unchanged():
    """Example 5: CLI usage remains unchanged"""
    print("\n" + "="*70)
    print("EXAMPLE 5: CLI Usage (Unchanged)")
    print("="*70 + "\n")

    print("The command-line interface works exactly as before:")
    print()
    print("  python src/main.py --input data/sample --output outputs/results --log outputs/logs")
    print()
    print("No progress callbacks are triggered when using CLI (backward compatible).")
    print("The progress_callback parameter defaults to None, so no callbacks occur.")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("PROGRESS CALLBACK EXAMPLES")
    print("Archaeological Fragment Reconstruction Pipeline")
    print("="*70)

    example_1_simple()
    example_2_gui_style()
    example_3_detailed()
    example_4_actual_usage()
    example_5_cli_unchanged()

    print("\n" + "="*70)
    print("KEY POINTS:")
    print("="*70)
    print()
    print("1. Progress callbacks are OPTIONAL (default=None)")
    print("2. CLI usage is UNCHANGED (backward compatible)")
    print("3. Core algorithm logic is UNCHANGED")
    print("4. Callbacks follow format: callback(message, percent=None)")
    print("5. Callbacks are invoked at key progress points:")
    print("   - After each fragment load")
    print("   - During compatibility computation")
    print("   - During relaxation labeling")
    print("   - During result rendering")
    print()
    print("="*70 + "\n")
