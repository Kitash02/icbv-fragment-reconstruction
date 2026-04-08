"""
Test script for configuration system validation.

This script verifies:
1. Default configuration loads successfully
2. All parameters are accessible
3. Validation catches invalid values
4. Configuration can be saved and reloaded
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import Config, ConfigValidationError, get_config


def test_default_config():
    """Test loading default configuration."""
    print("=" * 60)
    print("TEST 1: Load default configuration")
    print("=" * 60)

    try:
        cfg = Config()
        print("[OK] Default configuration loaded successfully")

        # Test dot notation access
        print(f"  preprocessing.gaussian_sigma = {cfg.preprocessing.gaussian_sigma}")
        print(f"  relaxation.match_score_threshold = {cfg.relaxation.match_score_threshold}")
        print(f"  compatibility.color_power = {cfg.compatibility.color_power}")
        print("[OK] Dot notation access works")

        # Test dictionary access
        sigma = cfg['preprocessing']['gaussian_sigma']
        print(f"  Dictionary access: gaussian_sigma = {sigma}")
        print("[OK] Dictionary access works")

        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        return False


def test_parameter_access():
    """Test accessing all major parameter groups."""
    print("\n" + "=" * 60)
    print("TEST 2: Access all parameter groups")
    print("=" * 60)

    try:
        cfg = Config()

        sections = [
            'preprocessing', 'chain_code', 'shape_descriptors',
            'compatibility', 'relaxation', 'hard_discriminators',
            'ensemble_voting', 'mixed_source_detection', 'pipeline', 'logging'
        ]

        for section in sections:
            assert hasattr(cfg, section), f"Missing section: {section}"
            print(f"[OK] Section '{section}' accessible")

        return True

    except Exception as e:
        print(f"[FAIL] FAILED: {e}")
        return False


def test_validation():
    """Test that validation catches invalid values."""
    print("\n" + "=" * 60)
    print("TEST 3: Validation of invalid values")
    print("=" * 60)

    # Create a temporary invalid config
    import yaml
    import tempfile

    invalid_configs = [
        # Out of range
        {
            'test': 'gaussian_sigma out of range',
            'modifications': {'preprocessing': {'gaussian_sigma': 10.0}}
        },
        # Wrong type
        {
            'test': 'match_score_threshold wrong type',
            'modifications': {'relaxation': {'match_score_threshold': 'invalid'}}
        },
        # Weak >= Match threshold
        {
            'test': 'weak_threshold >= match_threshold',
            'modifications': {
                'relaxation': {
                    'match_score_threshold': 0.60,
                    'weak_match_score_threshold': 0.70
                }
            }
        },
    ]

    passed = 0
    for test_case in invalid_configs:
        # Load default config
        default_cfg = Config()
        config_dict = default_cfg.to_dict()

        # Apply modifications
        for section, params in test_case['modifications'].items():
            config_dict[section].update(params)

        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            temp_path = f.name

        # Try to load (should fail)
        try:
            Config(temp_path)
            print(f"[FAIL] FAILED: {test_case['test']} - validation did not catch error")
        except ConfigValidationError as e:
            print(f"[OK] Caught invalid config: {test_case['test']}")
            passed += 1
        finally:
            os.unlink(temp_path)

    return passed == len(invalid_configs)


def test_update():
    """Test updating configuration parameters."""
    print("\n" + "=" * 60)
    print("TEST 4: Update configuration parameters")
    print("=" * 60)

    try:
        cfg = Config()

        # Valid update
        old_value = cfg.relaxation.match_score_threshold
        cfg.update('relaxation', 'match_score_threshold', 0.80)
        new_value = cfg.relaxation.match_score_threshold
        assert new_value == 0.80, "Update failed to apply"
        print(f"[OK] Valid update: {old_value} -> {new_value}")

        # Invalid update (should rollback)
        try:
            cfg.update('relaxation', 'match_score_threshold', 2.0)  # Out of range
            print("[FAIL] FAILED: Invalid update was not rejected")
            return False
        except ConfigValidationError:
            print("[OK] Invalid update rejected and rolled back")

        # Verify rollback
        assert cfg.relaxation.match_score_threshold == 0.80, "Rollback failed"
        print("[OK] Rollback preserved last valid value")

        return True

    except Exception as e:
        print(f"[FAIL] FAILED: {e}")
        return False


def test_save_load():
    """Test saving and reloading configuration."""
    print("\n" + "=" * 60)
    print("TEST 5: Save and reload configuration")
    print("=" * 60)

    import tempfile

    try:
        cfg = Config()
        cfg.update('relaxation', 'match_score_threshold', 0.78)

        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name

        cfg.save(temp_path)
        print(f"[OK] Configuration saved to: {temp_path}")

        # Reload
        cfg2 = Config(temp_path)
        assert cfg2.relaxation.match_score_threshold == 0.78, "Reloaded value mismatch"
        print("[OK] Configuration reloaded with correct values")

        os.unlink(temp_path)
        return True

    except Exception as e:
        print(f"[FAIL] FAILED: {e}")
        return False


def test_summary():
    """Test configuration summary generation."""
    print("\n" + "=" * 60)
    print("TEST 6: Configuration summary")
    print("=" * 60)

    try:
        cfg = Config()
        summary = cfg.summary()
        print(summary)
        print("\n[OK] Summary generated successfully")
        return True

    except Exception as e:
        print(f"[FAIL] FAILED: {e}")
        return False


def test_global_singleton():
    """Test global configuration singleton."""
    print("\n" + "=" * 60)
    print("TEST 7: Global singleton pattern")
    print("=" * 60)

    try:
        cfg1 = get_config()
        cfg2 = get_config()
        assert cfg1 is cfg2, "get_config() returned different instances"
        print("[OK] Singleton pattern works (same instance returned)")

        return True

    except Exception as e:
        print(f"[FAIL] FAILED: {e}")
        return False


def main():
    """Run all tests."""
    print("\nConfiguration System Validation Tests")
    print("=" * 60)

    tests = [
        test_default_config,
        test_parameter_access,
        test_validation,
        test_update,
        test_save_load,
        test_summary,
        test_global_singleton,
    ]

    results = [test() for test in tests]
    passed = sum(results)
    total = len(results)

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n[OK] All tests passed!")
        return 0
    else:
        print(f"\n[FAIL] {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
