#!/usr/bin/env python3
"""
Quick usage examples for preprocess_complex_images.py

This script demonstrates the three processing modes with practical examples.
Run sections individually by uncommenting them.
"""

import subprocess
import sys
from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPT = PROJECT_ROOT / "scripts" / "preprocess_complex_images.py"
INPUT_DIR = PROJECT_ROOT / "data" / "raw" / "real_fragments" / "wikimedia"
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "real_fragments_validated" / "wikimedia_processed"

def run_command(cmd, description):
    """Run a command and print results."""
    print("\n" + "="*70)
    print(f"EXAMPLE: {description}")
    print("="*70)
    print(f"Command: {' '.join(map(str, cmd))}\n")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print("STDERR:", result.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def example_1_auto_split():
    """Example 1: Auto-split multi-fragment image."""
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--input", str(INPUT_DIR),
        "--output", str(OUTPUT_DIR / "example1_auto"),
        "--mode", "auto",
        "--pattern", "*14_scherven*"
    ]
    return run_command(cmd, "Auto-Split Mode - Detect and separate all fragments")


def example_2_background_removal():
    """Example 2: Background removal with GrabCut."""
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--input", str(INPUT_DIR),
        "--output", str(OUTPUT_DIR / "example2_background"),
        "--mode", "background",
        "--pattern", "*14_scherven*"
    ]
    return run_command(cmd, "Background Removal Mode - Use GrabCut for refinement")


def example_3_manual_mode():
    """Example 3: Manual interactive cropping."""
    print("\n" + "="*70)
    print("EXAMPLE: Manual Mode - Interactive Cropping")
    print("="*70)
    print("""
This mode opens a GUI window where you can:
  1. Click and drag to draw a bounding box around a fragment
  2. Press 's' to save the selection
  3. Press 'r' to reset
  4. Press 'q' to quit

To run this example (requires display):
    """)

    cmd = [
        "python",
        "scripts/preprocess_complex_images.py",
        "--input", "data/raw/real_fragments/wikimedia",
        "--output", "data/processed/manual_example",
        "--mode", "manual",
        "--pattern", "*14_scherven*"
    ]
    print(" ".join(cmd))
    print("\nNote: This mode requires a graphical display (X11/Windows GUI)")


def example_4_batch_processing():
    """Example 4: Batch process entire directory."""
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--input", str(INPUT_DIR),
        "--output", str(OUTPUT_DIR / "example4_batch"),
        "--mode", "auto"
    ]
    return run_command(cmd, "Batch Processing - Process all images in directory")


def example_5_resume_processing():
    """Example 5: Resume interrupted processing."""
    # First run (simulate interruption by only processing one file)
    print("\n" + "="*70)
    print("EXAMPLE: Resume Processing - Skip already-processed images")
    print("="*70)
    print("Scenario: Processing was interrupted, now resuming with --skip-existing")
    print("\nFirst, we'll process some files...")

    cmd1 = [
        sys.executable,
        str(SCRIPT),
        "--input", str(INPUT_DIR),
        "--output", str(OUTPUT_DIR / "example5_resume"),
        "--mode", "auto",
        "--pattern", "*14_scherven*"
    ]

    if not run_command(cmd1, "Initial processing"):
        return False

    print("\n Now running again with --skip-existing (should skip already-processed files)...")

    cmd2 = [
        sys.executable,
        str(SCRIPT),
        "--input", str(INPUT_DIR),
        "--output", str(OUTPUT_DIR / "example5_resume"),
        "--mode", "auto",
        "--skip-existing"
    ]

    return run_command(cmd2, "Resumed processing with --skip-existing")


def show_output_structure():
    """Display the output directory structure."""
    print("\n" + "="*70)
    print("OUTPUT STRUCTURE")
    print("="*70)
    print("""
After processing, your output directory will contain:

output_directory/
+-- manifest.json                    # Processing metadata
|   {
|     "image.jpg": {
|       "mode": "auto",
|       "output_files": ["image_fragment_001.jpg", ...],
|       "fragment_count": 26,
|       "timestamp": "2026-04-08T10:43:09"
|     }
|   }
|
+-- preprocess_YYYYMMDD_HHMMSS.log  # Detailed log with DEBUG info
|
+-- image_fragment_001.jpg           # Extracted fragments
+-- image_fragment_002.jpg           # (white background, 10px border)
+-- image_fragment_003.jpg
+-- ...

The manifest.json tracks all transformations and can be used for:
- Resuming interrupted processing (--skip-existing)
- Auditing what was processed when
- Mapping original files to extracted fragments
    """)


def main():
    """Run examples."""
    print("\n" + "="*70)
    print("PREPROCESS_COMPLEX_IMAGES.PY - USAGE EXAMPLES")
    print("="*70)
    print(f"Script location: {SCRIPT}")
    print(f"Input directory: {INPUT_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")

    # Check if script exists
    if not SCRIPT.exists():
        print(f"\nError: Script not found at {SCRIPT}")
        return 1

    # Check if input directory exists
    if not INPUT_DIR.exists():
        print(f"\nWarning: Input directory not found at {INPUT_DIR}")
        print("The examples below show the command syntax but won't execute.")

    print("\n" + "="*70)
    print("RUNNING EXAMPLES")
    print("="*70)

    # Run examples
    # Uncomment the examples you want to run:

    # Example 1: Auto-split (fast, basic)
    example_1_auto_split()

    # Example 2: Background removal (slower, higher quality)
    # example_2_background_removal()

    # Example 3: Manual mode (requires GUI)
    example_3_manual_mode()

    # Example 4: Batch processing
    # example_4_batch_processing()

    # Example 5: Resume interrupted processing
    # example_5_resume_processing()

    # Show output structure
    show_output_structure()

    print("\n" + "="*70)
    print("EXAMPLES COMPLETE")
    print("="*70)
    print("\nFor full documentation, see:")
    print("  scripts/README_PREPROCESSING.md")
    print("\nFor help:")
    print("  python scripts/preprocess_complex_images.py --help")

    return 0


if __name__ == '__main__':
    sys.exit(main())
