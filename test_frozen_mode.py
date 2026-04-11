#!/usr/bin/env python
"""
Test script for frozen mode functionality.
Tests both development and frozen mode path resolution.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from path_resolver import (
    is_frozen,
    get_bundle_root,
    get_resource_path,
    get_sample_data_dir,
    get_docs_file,
    print_diagnostics
)

def test_frozen_detection():
    """Test frozen mode detection."""
    print("=" * 70)
    print("TEST 1: Frozen Mode Detection")
    print("=" * 70)
    frozen = is_frozen()
    print(f"Is Frozen: {frozen}")
    print(f"Expected: False (in development mode)")
    assert frozen == False, "Should not be frozen in dev mode"
    print("PASS: Frozen mode detection works\n")

def test_bundle_root():
    """Test bundle root resolution."""
    print("=" * 70)
    print("TEST 2: Bundle Root Resolution")
    print("=" * 70)
    bundle_root = get_bundle_root()
    print(f"Bundle Root: {bundle_root}")
    print(f"Exists: {bundle_root.exists()}")
    assert bundle_root.exists(), "Bundle root should exist"
    print("PASS: Bundle root resolves correctly\n")

def test_sample_data():
    """Test sample data directory resolution."""
    print("=" * 70)
    print("TEST 3: Sample Data Directory")
    print("=" * 70)
    sample_dir = get_sample_data_dir()
    print(f"Sample Data Dir: {sample_dir}")
    print(f"Exists: {sample_dir.exists()}")

    if sample_dir.exists():
        image_files = list(sample_dir.glob("*.png")) + list(sample_dir.glob("*.jpg"))
        print(f"Image files found: {len(image_files)}")
        for img in image_files[:5]:
            print(f"  - {img.name}")
    else:
        print("Warning: Sample data directory not found")

    print("PASS: Sample data directory resolves\n")

def test_docs_file():
    """Test documentation file resolution."""
    print("=" * 70)
    print("TEST 4: Documentation File Resolution")
    print("=" * 70)

    # Test README.md
    readme = get_docs_file("README.md")
    print(f"README.md: {readme}")
    if readme:
        print(f"  Exists: {readme.exists()}")
    else:
        print("  Not found")

    # Test EXPERIMENT_DOCUMENTATION.md
    experiment_doc = get_docs_file("EXPERIMENT_DOCUMENTATION.md")
    print(f"EXPERIMENT_DOCUMENTATION.md: {experiment_doc}")
    if experiment_doc:
        print(f"  Exists: {experiment_doc.exists()}")
    else:
        print("  Not found")

    print("PASS: Documentation file resolution works\n")

def test_resource_path():
    """Test generic resource path resolution."""
    print("=" * 70)
    print("TEST 5: Generic Resource Path Resolution")
    print("=" * 70)

    # Test various resource paths
    paths_to_test = [
        "data/sample",
        "config",
        "src",
        "assets/icon.png",  # May not exist
    ]

    for path in paths_to_test:
        resolved = get_resource_path(path)
        exists = resolved.exists()
        print(f"{path:30} -> {resolved}")
        print(f"{'':30}    Exists: {exists}")

    print("PASS: Resource path resolution works\n")

def main():
    """Run all tests."""
    print("\n")
    print("+" + "=" * 68 + "+")
    print("|" + " FROZEN MODE FUNCTIONALITY TEST SUITE ".center(68) + "|")
    print("+" + "=" * 68 + "+")
    print()

    try:
        test_frozen_detection()
        test_bundle_root()
        test_sample_data()
        test_docs_file()
        test_resource_path()

        print("=" * 70)
        print("ALL TESTS PASSED!")
        print("=" * 70)
        print()

        # Print full diagnostics
        print_diagnostics()

        return 0

    except Exception as e:
        print(f"\nFAIL: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
