#!/usr/bin/env python3
"""
Test script to verify config.py frozen mode compatibility.

This script tests that:
1. Config module can be imported
2. Config class can be instantiated
3. Default config path is resolved correctly
4. Config can load the YAML file
5. Config sections are accessible
6. Path resolver is working correctly
"""

import sys
from pathlib import Path

# Add src directories to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'src'))

def test_config_frozen_compatibility():
    """Test config.py with path_resolver integration."""

    print("=" * 70)
    print("CONFIG FROZEN MODE COMPATIBILITY TEST")
    print("=" * 70)
    print()

    # Test 1: Import path_resolver
    print("[1/7] Testing path_resolver import...")
    try:
        from path_resolver import get_config_file, is_frozen
        print("      [OK] path_resolver imported successfully")
        print(f"      - Running in {'FROZEN' if is_frozen() else 'DEVELOPMENT'} mode")
    except Exception as e:
        print(f"      [FAIL] Failed to import path_resolver: {e}")
        return False
    print()

    # Test 2: Test get_config_file function
    print("[2/7] Testing get_config_file function...")
    try:
        config_path = get_config_file('default_config.yaml')
        print(f"      [OK] Config path resolved: {config_path}")
        print(f"      - File exists: {config_path.exists()}")
    except Exception as e:
        print(f"      [FAIL] Failed to resolve config path: {e}")
        return False
    print()

    # Test 3: Import config module
    print("[3/7] Testing config module import...")
    try:
        from config import Config
        print("      [OK] config module imported successfully")
    except Exception as e:
        print(f"      [FAIL] Failed to import config module: {e}")
        return False
    print()

    # Test 4: Check Config.DEFAULT_CONFIG_PATH
    print("[4/7] Testing Config.DEFAULT_CONFIG_PATH...")
    try:
        default_path = Config.DEFAULT_CONFIG_PATH
        print(f"      [OK] DEFAULT_CONFIG_PATH: {default_path}")
        print(f"      - File exists: {default_path.exists()}")
        if not default_path.exists():
            print(f"      [FAIL] Config file not found at: {default_path}")
            return False
    except Exception as e:
        print(f"      [FAIL] Failed to access DEFAULT_CONFIG_PATH: {e}")
        return False
    print()

    # Test 5: Instantiate Config
    print("[5/7] Testing Config instantiation...")
    try:
        config = Config()
        print("      [OK] Config instantiated successfully")
    except Exception as e:
        print(f"      [FAIL] Failed to instantiate Config: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()

    # Test 6: Access config sections
    print("[6/7] Testing config section access...")
    try:
        sections = ['preprocessing', 'chain_code', 'shape_descriptors',
                   'compatibility', 'relaxation', 'hard_discriminators']
        for section_name in sections:
            section = getattr(config, section_name)
            print(f"      [OK] {section_name}: accessible")

        # Test parameter access
        sigma = config.preprocessing.gaussian_sigma
        print(f"      [OK] Sample parameter: gaussian_sigma = {sigma}")
    except Exception as e:
        print(f"      [FAIL] Failed to access config sections: {e}")
        return False
    print()

    # Test 7: Verify path_resolver integration
    print("[7/7] Testing path_resolver integration...")
    try:
        from path_resolver import get_path_diagnostics
        diagnostics = get_path_diagnostics()
        print(f"      [OK] Bundle root: {diagnostics['bundle_root']}")
        print(f"      [OK] Config dir exists: {diagnostics['config_dir_exists']}")
        print(f"      [OK] Config dir: {diagnostics['config_dir']}")
    except Exception as e:
        print(f"      [FAIL] Failed path_resolver diagnostics: {e}")
        return False
    print()

    # All tests passed
    print("=" * 70)
    print("ALL TESTS PASSED [OK]")
    print("=" * 70)
    print()
    print("Summary:")
    print("  - Config module uses path_resolver for frozen mode compatibility")
    print("  - Config path resolves correctly in development mode")
    print("  - Config file loads and validates successfully")
    print("  - All config sections are accessible")
    print()
    print("Next steps:")
    print("  - Build EXE with PyInstaller to test frozen mode")
    print("  - Verify config loads correctly in frozen executable")
    print()

    return True


if __name__ == "__main__":
    success = test_config_frozen_compatibility()
    sys.exit(0 if success else 1)
