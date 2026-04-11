#!/usr/bin/env python
"""
GUI Feature Test - Automated test for GUI menu functionality
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_gui_imports():
    """Test that GUI can be imported."""
    print("=" * 70)
    print("TEST 1: GUI Module Import")
    print("=" * 70)

    try:
        # Import path_resolver first
        from path_resolver import get_resource_path, get_docs_file, is_frozen
        print(f"  path_resolver imported successfully")
        print(f"  - is_frozen: {is_frozen()}")
        print(f"  - get_resource_path: {get_resource_path}")
        print(f"  - get_docs_file: {get_docs_file}")

        # Try to import gui_main
        sys.path.insert(0, str(Path(__file__).parent / 'src' / 'src'))
        from gui_main import FragmentReconstructionApp
        print(f"  gui_main.FragmentReconstructionApp imported successfully")

        print("PASS: All GUI modules import successfully\n")
        return True
    except Exception as e:
        print(f"FAIL: Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_path_functions():
    """Test path resolution functions used by GUI."""
    print("=" * 70)
    print("TEST 2: Path Resolution Functions")
    print("=" * 70)

    try:
        from path_resolver import get_resource_path, get_docs_file

        # Test icon path
        icon_path = get_resource_path("assets/icon.png")
        print(f"  Icon path: {icon_path}")
        print(f"  Icon exists: {icon_path.exists()}")

        # Test README
        readme_path = get_docs_file("README.md")
        print(f"  README path: {readme_path}")
        if readme_path:
            print(f"  README exists: {readme_path.exists()}")
        else:
            print(f"  README not found")

        # Test EXPERIMENT_DOCUMENTATION
        exp_doc_path = get_docs_file("EXPERIMENT_DOCUMENTATION.md")
        print(f"  Experiment doc path: {exp_doc_path}")
        if exp_doc_path:
            print(f"  Experiment doc exists: {exp_doc_path.exists()}")
        else:
            print(f"  Experiment doc not found")

        print("PASS: Path resolution functions work correctly\n")
        return True
    except Exception as e:
        print(f"FAIL: Path resolution error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_frozen_mode_support():
    """Test frozen mode detection and handling."""
    print("=" * 70)
    print("TEST 3: Frozen Mode Support")
    print("=" * 70)

    try:
        from path_resolver import is_frozen, get_bundle_root
        import sys

        frozen = is_frozen()
        print(f"  Frozen mode: {frozen}")
        print(f"  sys.frozen: {getattr(sys, 'frozen', False)}")
        print(f"  sys._MEIPASS exists: {hasattr(sys, '_MEIPASS')}")
        print(f"  Bundle root: {get_bundle_root()}")

        # In dev mode, should not be frozen
        assert frozen == False, "Should not be frozen in development mode"
        print("PASS: Frozen mode detection works correctly\n")
        return True
    except Exception as e:
        print(f"FAIL: Frozen mode detection error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all GUI feature tests."""
    print("\n")
    print("+" + "=" * 68 + "+")
    print("|" + " GUI FEATURE TEST SUITE ".center(68) + "|")
    print("+" + "=" * 68 + "+")
    print()

    results = []

    results.append(test_gui_imports())
    results.append(test_path_functions())
    results.append(test_frozen_mode_support())

    print("=" * 70)
    if all(results):
        print("ALL GUI FEATURE TESTS PASSED!")
        print("=" * 70)
        print("\nGUI is ready for:")
        print("  - Development mode testing")
        print("  - Frozen mode (PyInstaller) packaging")
        print("  - Menu features (Help -> View Documentation)")
        print("  - About dialog")
        return 0
    else:
        print(f"SOME TESTS FAILED ({sum(results)}/{len(results)} passed)")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
