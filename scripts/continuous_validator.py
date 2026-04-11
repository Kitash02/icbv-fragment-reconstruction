#!/usr/bin/env python3
"""
continuous_validator.py
-----------------------
Quick smoke tests that run after every code change.

This script performs fast validation:
- Imports work correctly
- Functions are callable
- No immediate crashes
- Basic sanity checks

Runs in < 10 seconds for rapid feedback during development.

Usage:
    python scripts/continuous_validator.py
    python scripts/continuous_validator.py --quick
    python scripts/continuous_validator.py --watch  # (future: watch mode)

Author: Automated Testing Framework
Date: 2026-04-08
"""

import argparse
import importlib
import sys
import time
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


class ContinuousValidator:
    """Performs fast smoke tests."""

    def __init__(self, quick: bool = False):
        self.quick = quick
        self.tests_passed = 0
        self.tests_failed = 0
        self.start_time = time.time()

    def test_result(self, test_name: str, passed: bool, message: str = "") -> None:
        """Record and print test result."""
        if passed:
            self.tests_passed += 1
            print(f"  ✓ {test_name}")
            if message:
                print(f"    {message}")
        else:
            self.tests_failed += 1
            print(f"  ✗ {test_name}")
            if message:
                print(f"    ERROR: {message}")

    def test_imports(self) -> bool:
        """Test that all modules can be imported."""
        print("\n[1/5] Testing imports...")

        modules = [
            "preprocessing",
            "chain_code",
            "compatibility",
            "relaxation",
            "visualize",
            "main",
            "assembly_renderer",
            "shape_descriptors",
        ]

        all_passed = True

        for module_name in modules:
            try:
                module = importlib.import_module(module_name)
                self.test_result(f"Import {module_name}", True)
            except Exception as e:
                self.test_result(f"Import {module_name}", False, str(e))
                all_passed = False

        return all_passed

    def test_function_signatures(self) -> bool:
        """Test that key functions exist and are callable."""
        print("\n[2/5] Testing function signatures...")

        all_passed = True

        tests = [
            ("preprocessing", "extract_fragments"),
            ("chain_code", "compute_chain_code"),
            ("chain_code", "compute_curvature_profile"),
            ("compatibility", "compute_color_signature"),
            ("compatibility", "segment_compatibility"),
            ("relaxation", "relaxation_labeling"),
            ("visualize", "plot_assembly"),
        ]

        for module_name, function_name in tests:
            try:
                module = importlib.import_module(module_name)
                if not hasattr(module, function_name):
                    self.test_result(f"{module_name}.{function_name}", False, "Function not found")
                    all_passed = False
                elif not callable(getattr(module, function_name)):
                    self.test_result(f"{module_name}.{function_name}", False, "Not callable")
                    all_passed = False
                else:
                    self.test_result(f"{module_name}.{function_name}", True)
            except Exception as e:
                self.test_result(f"{module_name}.{function_name}", False, str(e))
                all_passed = False

        return all_passed

    def test_basic_functionality(self) -> bool:
        """Test basic functionality with minimal inputs."""
        print("\n[3/5] Testing basic functionality...")

        all_passed = True

        # Test 1: Chain code with simple contour
        try:
            import numpy as np
            from chain_code import compute_chain_code

            simple_contour = np.array([[10, 10], [10, 20], [20, 20], [20, 10]])
            chain = compute_chain_code(simple_contour)

            if chain and isinstance(chain, list):
                self.test_result("compute_chain_code", True, f"Returns list of length {len(chain)}")
            else:
                self.test_result("compute_chain_code", False, "Invalid return type")
                all_passed = False
        except Exception as e:
            self.test_result("compute_chain_code", False, str(e))
            all_passed = False

        # Test 2: Color signature with simple image
        try:
            import cv2
            import numpy as np
            from compatibility import compute_color_signature

            # Create simple test image
            test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            signature = compute_color_signature(test_image)

            if signature is not None and len(signature) > 0:
                self.test_result("compute_color_signature", True, f"Returns array of length {len(signature)}")
            else:
                self.test_result("compute_color_signature", False, "Invalid return")
                all_passed = False
        except Exception as e:
            self.test_result("compute_color_signature", False, str(e))
            all_passed = False

        # Test 3: Edit distance
        try:
            from compatibility import edit_distance

            seq_a = [1, 2, 3, 4, 5]
            seq_b = [1, 2, 4, 5]
            dist = edit_distance(seq_a, seq_b)

            if isinstance(dist, int) and dist >= 0:
                self.test_result("edit_distance", True, f"Returns {dist}")
            else:
                self.test_result("edit_distance", False, "Invalid return type")
                all_passed = False
        except Exception as e:
            self.test_result("edit_distance", False, str(e))
            all_passed = False

        return all_passed

    def test_file_structure(self) -> bool:
        """Test that required files and directories exist."""
        print("\n[4/5] Testing file structure...")

        all_passed = True

        required_files = [
            "src/preprocessing.py",
            "src/chain_code.py",
            "src/compatibility.py",
            "src/relaxation.py",
            "src/visualize.py",
            "src/main.py",
            "run_test.py",
        ]

        required_dirs = [
            "src",
            "data",
            "outputs",
            "scripts",
        ]

        for file_path in required_files:
            full_path = ROOT / file_path
            if full_path.exists():
                self.test_result(f"File: {file_path}", True)
            else:
                self.test_result(f"File: {file_path}", False, "Not found")
                all_passed = False

        for dir_path in required_dirs:
            full_path = ROOT / dir_path
            if full_path.exists() and full_path.is_dir():
                self.test_result(f"Dir: {dir_path}", True)
            else:
                self.test_result(f"Dir: {dir_path}", False, "Not found")
                all_passed = False

        return all_passed

    def test_constants_and_config(self) -> bool:
        """Test that key constants are defined properly."""
        print("\n[5/5] Testing constants and configuration...")

        all_passed = True

        # Check compatibility.py constants
        try:
            import compatibility

            constants = [
                "COLOR_PENALTY_WEIGHT",
                "COLOR_HIST_BINS_HUE",
                "COLOR_HIST_BINS_SAT",
            ]

            for const in constants:
                if hasattr(compatibility, const):
                    value = getattr(compatibility, const)
                    self.test_result(f"compatibility.{const}", True, f"= {value}")
                else:
                    self.test_result(f"compatibility.{const}", False, "Not defined")
                    all_passed = False

        except Exception as e:
            self.test_result("compatibility constants", False, str(e))
            all_passed = False

        # Check if OpenCV is available
        try:
            import cv2
            version = cv2.__version__
            self.test_result("OpenCV", True, f"version {version}")
        except Exception as e:
            self.test_result("OpenCV", False, str(e))
            all_passed = False

        # Check NumPy
        try:
            import numpy as np
            version = np.__version__
            self.test_result("NumPy", True, f"version {version}")
        except Exception as e:
            self.test_result("NumPy", False, str(e))
            all_passed = False

        return all_passed

    def run_all_tests(self) -> bool:
        """Run all smoke tests."""
        print("\n" + "="*80)
        print("CONTINUOUS VALIDATION - SMOKE TESTS")
        print("="*80)

        results = [
            self.test_imports(),
            self.test_function_signatures(),
            self.test_basic_functionality(),
            self.test_file_structure(),
            self.test_constants_and_config(),
        ]

        all_passed = all(results)

        # Summary
        elapsed = time.time() - self.start_time
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"  Tests Passed:  {self.tests_passed}")
        print(f"  Tests Failed:  {self.tests_failed}")
        print(f"  Total Time:    {elapsed:.2f}s")
        print()

        if all_passed:
            print("✓ ALL SMOKE TESTS PASSED")
            print("  Code is ready for testing")
        else:
            print("✗ SOME TESTS FAILED")
            print("  Fix issues before running full test suite")

        print("="*80 + "\n")

        return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="Continuous validation smoke tests",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only quick tests (imports and file structure)"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch mode: re-run tests when files change (not implemented)"
    )

    args = parser.parse_args()

    if args.watch:
        print("✗ Watch mode not yet implemented")
        print("  For now, run this script manually after code changes")
        sys.exit(1)

    validator = ContinuousValidator(quick=args.quick)
    success = validator.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
