"""
Comprehensive EXE Testing Script
Tests the built FragmentReconstruction.exe for functionality
"""
import subprocess
import time
import os
import sys
from pathlib import Path

TEST_RESULTS = []

def log_test(test_name, passed, message=""):
    """Log test result"""
    status = "[PASS]" if passed else "[FAIL]"
    result = f"{status}: {test_name}"
    if message:
        result += f" - {message}"
    print(result)
    TEST_RESULTS.append((test_name, passed, message))
    return passed

def test_1_exe_exists():
    """Test 1: Verify EXE file exists"""
    exe_path = Path("dist/FragmentReconstruction/FragmentReconstruction.exe")
    exists = exe_path.exists()
    size = exe_path.stat().st_size if exists else 0
    size_mb = size / (1024 * 1024)
    return log_test(
        "EXE Exists",
        exists,
        f"Size: {size_mb:.2f} MB" if exists else "File not found"
    )

def test_2_package_structure():
    """Test 2: Verify package directory structure"""
    required_items = [
        "dist/FragmentReconstruction/_internal",
        "dist/FragmentReconstruction/_internal/data",
        "dist/FragmentReconstruction/_internal/config",
        "dist/FragmentReconstruction/_internal/base_library.zip",
    ]

    missing = []
    for item in required_items:
        if not Path(item).exists():
            missing.append(item)

    passed = len(missing) == 0
    message = "All required items present" if passed else f"Missing: {', '.join(missing)}"
    return log_test("Package Structure", passed, message)

def test_3_sample_data():
    """Test 3: Verify sample data bundled"""
    sample_dir = Path("dist/FragmentReconstruction/_internal/data/sample")

    if not sample_dir.exists():
        return log_test("Sample Data", False, "Sample directory not found")

    # Check for sample images
    sample_files = list(sample_dir.glob("*.png")) + list(sample_dir.glob("*.jpg"))

    passed = len(sample_files) > 0
    message = f"Found {len(sample_files)} sample files" if passed else "No sample files found"
    return log_test("Sample Data", passed, message)

def test_4_config_files():
    """Test 4: Verify configuration files bundled"""
    config_dir = Path("dist/FragmentReconstruction/_internal/config")

    if not config_dir.exists():
        return log_test("Config Files", False, "Config directory not found")

    config_files = list(config_dir.glob("*.yaml")) + list(config_dir.glob("*.yml"))

    passed = len(config_files) > 0
    message = f"Found {len(config_files)} config files" if passed else "No config files found"
    return log_test("Config Files", passed, message)

def test_5_launch_test():
    """Test 5: Launch EXE and verify it doesn't crash immediately"""
    exe_path = Path("dist/FragmentReconstruction/FragmentReconstruction.exe").resolve()

    if not exe_path.exists():
        return log_test("Launch Test", False, "EXE not found")

    try:
        # Launch the EXE
        proc = subprocess.Popen(
            [str(exe_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(exe_path.parent)
        )

        # Wait a few seconds
        time.sleep(3)

        # Check if still running
        poll_result = proc.poll()

        if poll_result is None:
            # Still running - success
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

            return log_test("Launch Test", True, "EXE launched successfully and stayed running")
        else:
            # Process terminated
            stdout, stderr = proc.communicate()
            error_msg = stderr.decode('utf-8', errors='ignore')[:200] if stderr else "Unknown error"
            return log_test("Launch Test", False, f"EXE crashed with code {poll_result}: {error_msg}")

    except Exception as e:
        return log_test("Launch Test", False, f"Exception: {str(e)}")

def test_6_dependencies():
    """Test 6: Check critical dependencies are bundled"""
    internal_dir = Path("dist/FragmentReconstruction/_internal")

    required_deps = [
        "numpy",
        "cv2",
        "PIL",
        "matplotlib",
        "scipy",
    ]

    missing_deps = []
    for dep in required_deps:
        dep_path = internal_dir / dep
        if not dep_path.exists():
            missing_deps.append(dep)

    passed = len(missing_deps) == 0
    message = "All dependencies present" if passed else f"Missing: {', '.join(missing_deps)}"
    return log_test("Dependencies", passed, message)

def test_7_file_count():
    """Test 7: Verify reasonable file count in package"""
    internal_dir = Path("dist/FragmentReconstruction/_internal")

    if not internal_dir.exists():
        return log_test("File Count", False, "Internal directory not found")

    # Count files
    file_count = sum(1 for _ in internal_dir.rglob("*") if _.is_file())

    # Should have at least 100 files for a proper package
    passed = file_count >= 100
    message = f"{file_count} files in package" + (" (seems too few)" if not passed else "")
    return log_test("File Count", passed, message)

def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed_count = sum(1 for _, passed, _ in TEST_RESULTS if passed)
    total_count = len(TEST_RESULTS)

    print(f"Passed: {passed_count}/{total_count}")
    print(f"Failed: {total_count - passed_count}/{total_count}")

    if passed_count == total_count:
        print("\nAll tests PASSED!")
    else:
        print("\nSome tests FAILED. Review the results above.")

    print("="*60)

if __name__ == "__main__":
    print("="*60)
    print("FRAGMENT RECONSTRUCTION EXE TEST SUITE")
    print("="*60)
    print()

    # Run all tests
    test_1_exe_exists()
    test_2_package_structure()
    test_3_sample_data()
    test_4_config_files()
    test_5_launch_test()
    test_6_dependencies()
    test_7_file_count()

    # Print summary
    print_summary()

    # Exit with appropriate code
    all_passed = all(passed for _, passed, _ in TEST_RESULTS)
    sys.exit(0 if all_passed else 1)
