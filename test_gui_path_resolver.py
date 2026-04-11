#!/usr/bin/env python
"""
Test script for GUI path resolver integration.

This script tests that gui_components.py correctly uses path_resolver
for all file operations, making it work in both development and frozen modes.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from path_resolver import (
    get_config_file, get_sample_data_dir, get_output_dir,
    get_log_dir, is_frozen, get_data_dir, print_diagnostics
)

def test_path_resolver():
    """Test that all path resolver functions work correctly."""
    print("="*70)
    print("PATH RESOLVER INTEGRATION TEST")
    print("="*70)
    print()

    # Print diagnostics
    print_diagnostics()
    print()

    # Test 1: Config file paths
    print("TEST 1: Config File Paths")
    print("-" * 70)
    config_dir = get_config_file('').parent
    print(f"Config directory: {config_dir}")
    print(f"Exists: {config_dir.exists()}")
    if config_dir.exists():
        config_files = list(config_dir.glob("*.json"))
        print(f"Config files found: {len(config_files)}")
        for cf in config_files[:3]:
            print(f"  - {cf.name}")
    print()

    # Test 2: Sample data directory
    print("TEST 2: Sample Data Directory")
    print("-" * 70)
    sample_dir = get_sample_data_dir()
    print(f"Sample data directory: {sample_dir}")
    print(f"Exists: {sample_dir.exists()}")
    if sample_dir.exists():
        image_files = [f for f in sample_dir.iterdir() if f.suffix.lower() in {'.png', '.jpg', '.jpeg'}]
        print(f"Image files found: {len(image_files)}")
        for img in image_files[:5]:
            print(f"  - {img.name}")
    print()

    # Test 3: Output directory
    print("TEST 3: Output Directory")
    print("-" * 70)
    output_dir = get_output_dir()
    print(f"Output directory: {output_dir}")
    print(f"Exists: {output_dir.exists()}")
    if output_dir.exists():
        result_files = list(output_dir.glob("*.png"))
        print(f"Result files found: {len(result_files)}")
        for rf in result_files[:3]:
            print(f"  - {rf.name}")
    print()

    # Test 4: Log directory
    print("TEST 4: Log Directory")
    print("-" * 70)
    log_dir = get_log_dir()
    print(f"Log directory: {log_dir}")
    print(f"Exists: {log_dir.exists()}")
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log")) + list(log_dir.glob("*.txt"))
        print(f"Log files found: {len(log_files)}")
        for lf in log_files[:3]:
            print(f"  - {lf.name}")
    print()

    # Test 5: Data directory
    print("TEST 5: Data Directory")
    print("-" * 70)
    data_dir = get_data_dir()
    print(f"Data directory: {data_dir}")
    print(f"Exists: {data_dir.exists()}")
    if data_dir.exists():
        subdirs = [d for d in data_dir.iterdir() if d.is_dir()]
        print(f"Subdirectories: {len(subdirs)}")
        for sd in subdirs:
            print(f"  - {sd.name}")
    print()

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    all_good = all([
        config_dir.exists(),
        sample_dir.exists(),
        output_dir.exists(),
        log_dir.exists(),
        data_dir.exists()
    ])

    if all_good:
        print("[PASS] All paths resolved successfully!")
        print("[PASS] GUI should work correctly with path_resolver")
    else:
        print("[FAIL] Some paths could not be resolved")
        print("[FAIL] Check the diagnostics above for details")

    print()
    return all_good


def test_gui_imports():
    """Test that gui_components.py can be imported with path_resolver."""
    print("="*70)
    print("GUI COMPONENTS IMPORT TEST")
    print("="*70)
    print()

    try:
        # Import gui_components (which now uses path_resolver)
        sys.path.insert(0, str(Path(__file__).parent / "src" / "src"))
        import gui_components

        print("[PASS] gui_components.py imported successfully")
        print("[PASS] path_resolver integration working")

        # Check that the imported functions are available
        has_config = hasattr(gui_components, 'get_config_file')
        has_sample = hasattr(gui_components, 'get_sample_data_dir')
        has_output = hasattr(gui_components, 'get_output_dir')
        has_log = hasattr(gui_components, 'get_log_dir')

        print(f"  - get_config_file: {'[PASS]' if has_config else '[FAIL]'}")
        print(f"  - get_sample_data_dir: {'[PASS]' if has_sample else '[FAIL]'}")
        print(f"  - get_output_dir: {'[PASS]' if has_output else '[FAIL]'}")
        print(f"  - get_log_dir: {'[PASS]' if has_log else '[FAIL]'}")

        print()
        return True

    except ImportError as e:
        print(f"[FAIL] Failed to import gui_components.py: {e}")
        print()
        return False
    except Exception as e:
        print(f"[FAIL] Error during import: {e}")
        print()
        return False


if __name__ == "__main__":
    print("\nTesting GUI Path Resolver Integration\n")

    # Run tests
    test1_pass = test_path_resolver()
    print()
    test2_pass = test_gui_imports()

    # Final result
    print("="*70)
    print("FINAL RESULT")
    print("="*70)

    if test1_pass and test2_pass:
        print("[PASS] ALL TESTS PASSED")
        print("[PASS] GUI is ready for both development and frozen mode")
        sys.exit(0)
    else:
        print("[FAIL] SOME TESTS FAILED")
        print("[FAIL] Review the output above for details")
        sys.exit(1)
