"""
Test script for path_resolver.py module.

This script tests the path resolution functionality in development mode.
Run this to verify that all path functions work correctly.
"""

import sys
from pathlib import Path

# Add src to path so we can import path_resolver
sys.path.insert(0, str(Path(__file__).parent / "src"))

import path_resolver


def test_basic_detection():
    """Test basic frozen/dev detection."""
    print("\n" + "=" * 70)
    print("TEST 1: Basic Detection")
    print("=" * 70)

    is_frozen = path_resolver.is_frozen()
    print(f"Is Frozen: {is_frozen}")
    print(f"Expected: False (running in development mode)")

    assert not is_frozen, "Should not be frozen in development mode"
    print("[PASSED] Correctly detected development mode")


def test_bundle_root():
    """Test bundle root resolution."""
    print("\n" + "=" * 70)
    print("TEST 2: Bundle Root")
    print("=" * 70)

    bundle_root = path_resolver.get_bundle_root()
    print(f"Bundle Root: {bundle_root}")
    print(f"Exists: {bundle_root.exists()}")

    # Should point to project root
    expected_root = Path(__file__).parent
    assert bundle_root == expected_root, f"Bundle root should be {expected_root}"
    assert bundle_root.exists(), "Bundle root should exist"

    # Check that src/ directory exists in bundle root
    src_dir = bundle_root / "src"
    print(f"Has src/ directory: {src_dir.exists()}")
    assert src_dir.exists(), "src/ directory should exist in bundle root"

    print("[PASS] PASSED: Bundle root correctly resolved")


def test_resource_paths():
    """Test resource path resolution."""
    print("\n" + "=" * 70)
    print("TEST 3: Resource Paths")
    print("=" * 70)

    # Test config path
    config_path = path_resolver.get_resource_path("config")
    print(f"Config Path: {config_path}")
    print(f"Exists: {config_path.exists()}")

    # Test data path
    data_path = path_resolver.get_resource_path("data")
    print(f"Data Path: {data_path}")
    print(f"Exists: {data_path.exists()}")

    # Test specific file path
    test_file = path_resolver.get_resource_path("src/path_resolver.py")
    print(f"Test File Path: {test_file}")
    print(f"Exists: {test_file.exists()}")
    assert test_file.exists(), "path_resolver.py should exist"

    print("[PASS] PASSED: Resource paths correctly resolved")


def test_user_directories():
    """Test user-writable directory creation."""
    print("\n" + "=" * 70)
    print("TEST 4: User Directories")
    print("=" * 70)

    user_base = path_resolver.get_user_base_dir()
    print(f"User Base Dir: {user_base}")
    print(f"Exists: {user_base.exists()}")

    # In dev mode, should be same as bundle root
    bundle_root = path_resolver.get_bundle_root()
    assert user_base == bundle_root, "In dev mode, user base should equal bundle root"

    output_dir = path_resolver.get_output_dir()
    print(f"\nOutput Dir: {output_dir}")
    print(f"Exists: {output_dir.exists()}")
    assert output_dir.exists(), "Output directory should be created"

    log_dir = path_resolver.get_log_dir()
    print(f"\nLog Dir: {log_dir}")
    print(f"Exists: {log_dir.exists()}")
    assert log_dir.exists(), "Log directory should be created"

    temp_dir = path_resolver.get_temp_dir()
    print(f"\nTemp Dir: {temp_dir}")
    print(f"Exists: {temp_dir.exists()}")
    assert temp_dir.exists(), "Temp directory should be created"

    print("[PASS] PASSED: User directories correctly created")


def test_specific_functions():
    """Test specific helper functions."""
    print("\n" + "=" * 70)
    print("TEST 5: Specific Helper Functions")
    print("=" * 70)

    # Test sample data dir
    sample_dir = path_resolver.get_sample_data_dir()
    print(f"Sample Data Dir: {sample_dir}")
    print(f"Exists: {sample_dir.exists()}")
    if not sample_dir.exists():
        print("  (Note: This is expected if data/sample/ hasn't been created yet)")

    # Test config file
    config_file = path_resolver.get_config_file("settings.json")
    print(f"\nConfig File (settings.json): {config_file}")
    print(f"Exists: {config_file.exists()}")
    if not config_file.exists():
        print("  (Note: This is expected if config/settings.json hasn't been created yet)")

    # Test data dir
    data_dir = path_resolver.get_data_dir()
    print(f"\nData Dir: {data_dir}")
    print(f"Exists: {data_dir.exists()}")

    # Test executable dir
    exe_dir = path_resolver.get_executable_dir()
    print(f"\nExecutable Dir: {exe_dir}")
    print(f"Exists: {exe_dir.exists()}")
    assert exe_dir.exists(), "Executable directory should exist"

    print("[PASS] PASSED: Specific functions work correctly")


def test_ensure_directories():
    """Test ensure_user_directories function."""
    print("\n" + "=" * 70)
    print("TEST 6: Ensure User Directories")
    print("=" * 70)

    # This should create all necessary directories
    path_resolver.ensure_user_directories()
    print("Called ensure_user_directories()")

    # Verify all directories exist
    dirs_to_check = [
        ("Output", path_resolver.get_output_dir()),
        ("Log", path_resolver.get_log_dir()),
        ("Temp", path_resolver.get_temp_dir()),
    ]

    all_exist = True
    for name, dir_path in dirs_to_check:
        exists = dir_path.exists()
        print(f"{name} Dir exists: {exists}")
        all_exist = all_exist and exists

    assert all_exist, "All user directories should exist after ensure_user_directories()"
    print("[PASS] PASSED: All user directories ensured")


def test_diagnostics():
    """Test diagnostic functions."""
    print("\n" + "=" * 70)
    print("TEST 7: Diagnostics")
    print("=" * 70)

    diagnostics = path_resolver.get_path_diagnostics()
    print(f"Got diagnostics dictionary with {len(diagnostics)} entries")

    # Check required keys
    required_keys = [
        "is_frozen", "bundle_root", "output_dir", "log_dir",
        "sample_data_dir", "executable_dir"
    ]

    missing_keys = [key for key in required_keys if key not in diagnostics]
    assert not missing_keys, f"Missing diagnostic keys: {missing_keys}"

    print(f"[PASS] All required keys present: {', '.join(required_keys)}")
    print("[PASS] PASSED: Diagnostics function works correctly")


def test_path_types():
    """Test that all functions return Path objects."""
    print("\n" + "=" * 70)
    print("TEST 8: Return Types")
    print("=" * 70)

    path_functions = [
        ("get_bundle_root", path_resolver.get_bundle_root),
        ("get_user_base_dir", path_resolver.get_user_base_dir),
        ("get_output_dir", path_resolver.get_output_dir),
        ("get_log_dir", path_resolver.get_log_dir),
        ("get_temp_dir", path_resolver.get_temp_dir),
        ("get_sample_data_dir", path_resolver.get_sample_data_dir),
        ("get_data_dir", path_resolver.get_data_dir),
        ("get_executable_dir", path_resolver.get_executable_dir),
    ]

    for name, func in path_functions:
        result = func()
        is_path = isinstance(result, Path)
        print(f"{name}(): {type(result).__name__} - {'[PASS]' if is_path else '[FAIL]'}")
        assert is_path, f"{name} should return a Path object"

    # Test functions with arguments
    resource_path = path_resolver.get_resource_path("test")
    assert isinstance(resource_path, Path), "get_resource_path should return Path"
    print(f"get_resource_path('test'): {type(resource_path).__name__} - [PASS]")

    config_file = path_resolver.get_config_file("test.json")
    assert isinstance(config_file, Path), "get_config_file should return Path"
    print(f"get_config_file('test.json'): {type(config_file).__name__} - [PASS]")

    print("[PASS] PASSED: All functions return Path objects")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("RUNNING PATH_RESOLVER TESTS")
    print("=" * 70)

    tests = [
        test_basic_detection,
        test_bundle_root,
        test_resource_paths,
        test_user_directories,
        test_specific_functions,
        test_ensure_directories,
        test_diagnostics,
        test_path_types,
    ]

    failed_tests = []

    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"\n[FAIL] FAILED: {e}")
            failed_tests.append((test.__name__, str(e)))
        except Exception as e:
            print(f"\n[FAIL] ERROR: {e}")
            failed_tests.append((test.__name__, f"Error: {e}"))

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {len(tests) - len(failed_tests)}")
    print(f"Failed: {len(failed_tests)}")

    if failed_tests:
        print("\nFailed Tests:")
        for test_name, error in failed_tests:
            print(f"  - {test_name}: {error}")
        print("\n[FAIL] SOME TESTS FAILED")
        return False
    else:
        print("\n[PASS] ALL TESTS PASSED")
        return True


if __name__ == "__main__":
    # Run all tests
    success = run_all_tests()

    # Print full diagnostics at the end
    print("\n\n")
    path_resolver.print_diagnostics()

    # Exit with appropriate code
    sys.exit(0 if success else 1)
