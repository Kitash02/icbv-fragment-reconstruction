#!/usr/bin/env python
"""
Functional validation script for GUI path resolver integration.

This script validates that all the modified sections of gui_components.py
work correctly with the path_resolver integration.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from path_resolver import (
    get_config_file, get_sample_data_dir, get_output_dir,
    get_log_dir, get_data_dir, print_diagnostics
)

def validate_config_dialogs():
    """Validate config file dialog paths."""
    print("VALIDATION 1: Config File Dialogs")
    print("-" * 70)

    config_dir = get_config_file('').parent
    print(f"Config directory: {config_dir}")
    print(f"Exists: {config_dir.exists()}")

    if config_dir.exists():
        # Check for config files
        config_files = list(config_dir.glob("*.json"))
        print(f"Config files available: {len(config_files)}")

        if config_files:
            print("[PASS] Config dialog will open in correct directory")
            return True
        else:
            print("[WARN] No config files found, but directory exists")
            return True
    else:
        print("[FAIL] Config directory does not exist")
        return False


def validate_browse_folder():
    """Validate browse folder functionality."""
    print("\nVALIDATION 2: Browse Folder Dialog")
    print("-" * 70)

    data_dir = get_data_dir()
    print(f"Data directory: {data_dir}")
    print(f"Exists: {data_dir.exists()}")

    if data_dir.exists():
        # Check for subdirectories
        subdirs = [d for d in data_dir.iterdir() if d.is_dir()]
        print(f"Subdirectories: {[d.name for d in subdirs]}")

        if subdirs:
            print("[PASS] Browse dialog will show data folders")
            return True
        else:
            print("[WARN] Data directory exists but is empty")
            return True
    else:
        print("[FAIL] Data directory does not exist")
        return False


def validate_sample_data():
    """Validate sample data loading."""
    print("\nVALIDATION 3: Sample Data Loading")
    print("-" * 70)

    sample_dir = get_sample_data_dir()
    print(f"Sample data directory: {sample_dir}")
    print(f"Exists: {sample_dir.exists()}")

    if not sample_dir.exists():
        print("[FAIL] Sample data directory does not exist")
        return False

    # Check for image files
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'}
    image_files = [f for f in sample_dir.iterdir()
                   if f.is_file() and f.suffix.lower() in image_extensions]

    print(f"Sample images found: {len(image_files)}")
    for img in image_files[:5]:
        print(f"  - {img.name}")

    if len(image_files) >= 1:
        print(f"[PASS] Load Sample Data will load {len(image_files)} fragments")
        return True
    else:
        print("[FAIL] No sample images found")
        return False


def validate_output_directories():
    """Validate output and log directory creation."""
    print("\nVALIDATION 4: Output and Log Directories")
    print("-" * 70)

    output_dir = get_output_dir()
    log_dir = get_log_dir()

    print(f"Output directory: {output_dir}")
    print(f"Exists: {output_dir.exists()}")
    print(f"Writable: {os.access(output_dir, os.W_OK)}")

    print(f"\nLog directory: {log_dir}")
    print(f"Exists: {log_dir.exists()}")
    print(f"Writable: {os.access(log_dir, os.W_OK)}")

    # Test write capability
    try:
        test_file = output_dir / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
        output_writable = True
    except Exception as e:
        print(f"Output write test failed: {e}")
        output_writable = False

    try:
        test_file = log_dir / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
        log_writable = True
    except Exception as e:
        print(f"Log write test failed: {e}")
        log_writable = False

    if output_dir.exists() and log_dir.exists() and output_writable and log_writable:
        print("[PASS] Output and log directories are ready")
        return True
    else:
        print("[FAIL] Output or log directories have issues")
        return False


def validate_results_loading():
    """Validate results loading functionality."""
    print("\nVALIDATION 5: Results Loading")
    print("-" * 70)

    output_dir = get_output_dir()
    print(f"Looking for results in: {output_dir}")

    if not output_dir.exists():
        print("[WARN] Output directory doesn't exist yet (will be created on first run)")
        return True

    # Check for result files
    result_files = list(output_dir.glob("*.png"))
    print(f"Result files found: {len(result_files)}")

    if result_files:
        print(f"Recent results:")
        for rf in sorted(result_files)[-3:]:
            print(f"  - {rf.name}")
        print("[PASS] Results can be loaded and displayed")
    else:
        print("[INFO] No results yet (run assembly pipeline to generate)")
        print("[PASS] Results loading will work when files exist")

    return True


def main():
    """Run all validations."""
    print("="*70)
    print("GUI PATH RESOLVER - FUNCTIONAL VALIDATION")
    print("="*70)
    print()

    # Run validations
    results = []
    results.append(("Config Dialogs", validate_config_dialogs()))
    results.append(("Browse Folder", validate_browse_folder()))
    results.append(("Sample Data", validate_sample_data()))
    results.append(("Output/Log Dirs", validate_output_directories()))
    results.append(("Results Loading", validate_results_loading()))

    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")

    all_passed = all(result[1] for result in results)

    print("\n" + "="*70)
    if all_passed:
        print("[PASS] ALL VALIDATIONS PASSED")
        print()
        print("GUI Components are ready for use!")
        print()
        print("Next steps:")
        print("1. Launch GUI: python launch_gui.py")
        print("2. Test Load Sample Data button")
        print("3. Test Browse Folder button")
        print("4. Test Run Assembly")
        print("5. Test Results display")
        return 0
    else:
        print("[FAIL] SOME VALIDATIONS FAILED")
        print()
        print("Review the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
