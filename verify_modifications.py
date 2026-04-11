#!/usr/bin/env python
"""
Verify that gui_components.py has been correctly modified with path_resolver.

This script checks the exact line numbers and content to ensure all modifications
were applied correctly.
"""

import sys
from pathlib import Path

def check_modifications():
    """Check that all required modifications are present."""
    gui_file = Path(__file__).parent / "src" / "src" / "gui_components.py"

    if not gui_file.exists():
        print(f"[FAIL] File not found: {gui_file}")
        return False

    print("="*70)
    print("GUI COMPONENTS MODIFICATION VERIFICATION")
    print("="*70)
    print()

    with open(gui_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    total_lines = len(lines)
    print(f"Total lines in gui_components.py: {total_lines}")
    print()

    checks = []

    # Check 1: Import statements (lines 24-29)
    print("CHECK 1: Import Statements")
    print("-" * 70)
    import_found = False
    for i in range(20, 35):
        if i < len(lines) and 'from path_resolver import' in lines[i]:
            import_found = True
            print(f"Line {i+1}: {lines[i].strip()}")
            if i+1 < len(lines):
                print(f"Line {i+2}: {lines[i+1].strip()}")
            break

    if import_found:
        print("[PASS] Import statements found")
        checks.append(True)
    else:
        print("[FAIL] Import statements not found")
        checks.append(False)
    print()

    # Check 2: Config file usage
    print("CHECK 2: Config File Functions")
    print("-" * 70)
    config_count = 0
    for i, line in enumerate(lines):
        if 'get_config_file' in line:
            config_count += 1
            print(f"Line {i+1}: {line.strip()}")

    if config_count >= 3:  # Import + 2 uses
        print(f"[PASS] Found {config_count} uses of get_config_file()")
        checks.append(True)
    else:
        print(f"[FAIL] Expected 3+ uses, found {config_count}")
        checks.append(False)
    print()

    # Check 3: Sample data directory
    print("CHECK 3: Sample Data Directory")
    print("-" * 70)
    sample_found = False
    for i, line in enumerate(lines):
        if 'get_sample_data_dir()' in line and 'import' not in line:
            sample_found = True
            print(f"Line {i+1}: {line.strip()}")
            break

    if sample_found:
        print("[PASS] get_sample_data_dir() usage found")
        checks.append(True)
    else:
        print("[FAIL] get_sample_data_dir() usage not found")
        checks.append(False)
    print()

    # Check 4: Output directory
    print("CHECK 4: Output Directory")
    print("-" * 70)
    output_count = 0
    for i, line in enumerate(lines):
        if 'get_output_dir()' in line and 'import' not in line:
            output_count += 1
            print(f"Line {i+1}: {line.strip()}")

    if output_count >= 2:  # At least 2 uses
        print(f"[PASS] Found {output_count} uses of get_output_dir()")
        checks.append(True)
    else:
        print(f"[FAIL] Expected 2+ uses, found {output_count}")
        checks.append(False)
    print()

    # Check 5: Log directory
    print("CHECK 5: Log Directory")
    print("-" * 70)
    log_found = False
    for i, line in enumerate(lines):
        if 'get_log_dir()' in line and 'import' not in line:
            log_found = True
            print(f"Line {i+1}: {line.strip()}")
            break

    if log_found:
        print("[PASS] get_log_dir() usage found")
        checks.append(True)
    else:
        print("[FAIL] get_log_dir() usage not found")
        checks.append(False)
    print()

    # Check 6: Data directory (for browse)
    print("CHECK 6: Data Directory")
    print("-" * 70)
    data_found = False
    for i, line in enumerate(lines):
        if 'get_data_dir()' in line and 'import' not in line:
            data_found = True
            print(f"Line {i+1}: {line.strip()}")
            break

    if data_found:
        print("[PASS] get_data_dir() usage found")
        checks.append(True)
    else:
        print("[FAIL] get_data_dir() usage not found")
        checks.append(False)
    print()

    # Check 7: No old hardcoded paths
    print("CHECK 7: Old Path Patterns Removed")
    print("-" * 70)
    old_patterns = [
        'os.path.join(os.path.dirname(__file__), "..", "config")',
        'os.path.join("outputs", "results")',
        'os.path.join("outputs", "logs")'
    ]

    old_found = []
    for pattern in old_patterns:
        for i, line in enumerate(lines):
            if pattern in line:
                old_found.append((i+1, pattern, line.strip()))

    if old_found:
        print("[WARN] Old path patterns still present:")
        for line_num, pattern, line in old_found:
            print(f"  Line {line_num}: {line}")
        checks.append(False)
    else:
        print("[PASS] No old hardcoded path patterns found")
        checks.append(True)
    print()

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)

    check_names = [
        "Import Statements",
        "Config File Functions",
        "Sample Data Directory",
        "Output Directory",
        "Log Directory",
        "Data Directory",
        "Old Patterns Removed"
    ]

    for name, passed in zip(check_names, checks):
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")

    print()
    all_passed = all(checks)

    if all_passed:
        print("[PASS] ALL MODIFICATIONS VERIFIED")
        print()
        print("gui_components.py is correctly using path_resolver!")
        return True
    else:
        print("[FAIL] SOME MODIFICATIONS MISSING OR INCORRECT")
        print()
        print("Review the checks above for details.")
        return False


if __name__ == "__main__":
    success = check_modifications()
    sys.exit(0 if success else 1)
