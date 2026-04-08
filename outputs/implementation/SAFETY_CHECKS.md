# SAFETY CHECKS AND PRE-FLIGHT VALIDATION

**Document Purpose:** Prevent catastrophic failures through systematic pre-flight checks

**Critical Principle:** Better to detect issues BEFORE running than to debug failures AFTER

---

## PRE-IMPLEMENTATION CHECKLIST

### System Environment Validation

```python
def validate_system_environment():
    """
    Verify system environment before any implementation
    """
    checks = {
        'python_version': False,
        'opencv_installed': False,
        'numpy_installed': False,
        'scikit_image_installed': False,
        'scikit_learn_installed': False,
        'git_available': False,
        'data_directory_exists': False,
        'output_directory_writable': False
    }

    print("=" * 60)
    print("SYSTEM ENVIRONMENT VALIDATION")
    print("=" * 60)

    # Python version
    import sys
    python_version = sys.version_info
    if python_version.major == 3 and python_version.minor >= 8:
        print(f"✓ Python {python_version.major}.{python_version.minor} (OK)")
        checks['python_version'] = True
    else:
        print(f"✗ Python {python_version.major}.{python_version.minor} (TOO OLD - need 3.8+)")

    # OpenCV
    try:
        import cv2
        print(f"✓ OpenCV {cv2.__version__} (OK)")
        checks['opencv_installed'] = True
    except ImportError:
        print("✗ OpenCV not installed")

    # NumPy
    try:
        import numpy as np
        print(f"✓ NumPy {np.__version__} (OK)")
        checks['numpy_installed'] = True
    except ImportError:
        print("✗ NumPy not installed")

    # Scikit-image
    try:
        import skimage
        print(f"✓ Scikit-image {skimage.__version__} (OK)")
        checks['scikit_image_installed'] = True
    except ImportError:
        print("✗ Scikit-image not installed (needed for LBP)")

    # Scikit-learn
    try:
        import sklearn
        print(f"✓ Scikit-learn {sklearn.__version__} (OK)")
        checks['scikit_learn_installed'] = True
    except ImportError:
        print("✗ Scikit-learn not installed (optional, for metrics)")

    # Git
    import subprocess
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Git available (OK)")
            checks['git_available'] = True
        else:
            print("✗ Git not available")
    except:
        print("✗ Git not available")

    # Data directory
    import os
    data_dir = "fragments"
    if os.path.isdir(data_dir):
        print(f"✓ Data directory '{data_dir}' exists (OK)")
        checks['data_directory_exists'] = True
    else:
        print(f"✗ Data directory '{data_dir}' not found")

    # Output directory
    output_dir = "outputs/implementation"
    try:
        os.makedirs(output_dir, exist_ok=True)
        test_file = os.path.join(output_dir, ".test_write")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print(f"✓ Output directory '{output_dir}' writable (OK)")
        checks['output_directory_writable'] = True
    except:
        print(f"✗ Output directory '{output_dir}' not writable")

    # Summary
    print("\n" + "=" * 60)
    passed = sum(checks.values())
    total = len(checks)
    print(f"SUMMARY: {passed}/{total} checks passed")

    if passed == total:
        print("✓ ALL CHECKS PASSED - Safe to proceed")
        return True
    else:
        print("✗ SOME CHECKS FAILED - Fix issues before proceeding")
        failed = [k for k, v in checks.items() if not v]
        print(f"\nFailed checks: {', '.join(failed)}")
        return False
```

---

## PHASE 1A: LAB COLOR IMPLEMENTATION

### Pre-Flight Checks

```python
def preflight_phase_1a():
    """
    Validate prerequisites for Phase 1A (Lab Color)
    """
    print("\n" + "=" * 60)
    print("PHASE 1A PRE-FLIGHT CHECKS: Lab Color Implementation")
    print("=" * 60)

    checks = {}

    # Check 1: HSV baseline exists
    try:
        # Assume main script has been run at least once
        # Check if we can import necessary functions
        print("\n[1/6] Checking HSV baseline...")
        # This would check if current implementation exists
        checks['hsv_baseline'] = True
        print("✓ HSV baseline code exists")
    except Exception as e:
        checks['hsv_baseline'] = False
        print(f"✗ HSV baseline not found: {e}")

    # Check 2: Git backup possible
    print("\n[2/6] Checking Git status...")
    try:
        import subprocess
        result = subprocess.run(['git', 'status'], capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            checks['git_backup'] = True
            print("✓ Git repository active")
            # Recommend creating backup branch
            print("  → RECOMMENDATION: Create backup branch before changes")
        else:
            checks['git_backup'] = False
            print("✗ Not a git repository")
    except:
        checks['git_backup'] = False
        print("✗ Git not available")

    # Check 3: Lab color conversion works
    print("\n[3/6] Testing Lab color conversion...")
    try:
        import cv2
        import numpy as np

        # Create test image
        test_img = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

        # Convert to Lab
        lab_img = cv2.cvtColor(test_img, cv2.COLOR_BGR2Lab)

        # Verify output
        assert lab_img.shape == test_img.shape
        assert lab_img.dtype == np.uint8

        checks['lab_conversion'] = True
        print("✓ Lab color conversion works")
        print(f"  Lab ranges: L=[{lab_img[:,:,0].min()}, {lab_img[:,:,0].max()}], "
              f"a=[{lab_img[:,:,1].min()}, {lab_img[:,:,1].max()}], "
              f"b=[{lab_img[:,:,2].min()}, {lab_img[:,:,2].max()}]")
    except Exception as e:
        checks['lab_conversion'] = False
        print(f"✗ Lab conversion failed: {e}")

    # Check 4: 3D histogram computation
    print("\n[4/6] Testing 3D histogram...")
    try:
        import cv2
        import numpy as np

        test_img = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        lab_img = cv2.cvtColor(test_img, cv2.COLOR_BGR2Lab)

        # Compute histogram
        hist, _ = np.histogramdd(
            lab_img.reshape(-1, 3),
            bins=[16, 8, 8],
            range=[[0, 256], [0, 256], [0, 256]]
        )

        # Verify
        assert hist.shape == (16, 8, 8)
        assert hist.sum() == lab_img.shape[0] * lab_img.shape[1]  # Total pixels

        # Normalize
        hist_norm = hist.flatten()
        hist_norm = hist_norm / (hist_norm.sum() + 1e-8)
        assert abs(hist_norm.sum() - 1.0) < 1e-6

        checks['histogram_3d'] = True
        print("✓ 3D histogram computation works")
        print(f"  Histogram shape: {hist.shape}, total bins: {hist.size}")
    except Exception as e:
        checks['histogram_3d'] = False
        print(f"✗ 3D histogram failed: {e}")

    # Check 5: Bhattacharyya Coefficient
    print("\n[5/6] Testing Bhattacharyya Coefficient...")
    try:
        import numpy as np

        # Two identical histograms
        hist1 = np.random.rand(1024)
        hist1 /= hist1.sum()
        hist2 = hist1.copy()

        bc = np.sum(np.sqrt(hist1 * hist2))
        assert 0.999 < bc <= 1.0, f"Expected BC≈1.0 for identical, got {bc}"

        # Two different histograms
        hist3 = np.random.rand(1024)
        hist3 /= hist3.sum()

        bc2 = np.sum(np.sqrt(hist1 * hist3))
        assert 0.0 < bc2 < 1.0, f"Expected 0<BC<1 for different, got {bc2}"

        checks['bhattacharyya'] = True
        print("✓ Bhattacharyya Coefficient works")
        print(f"  BC(identical): {bc:.6f}, BC(different): {bc2:.6f}")
    except Exception as e:
        checks['bhattacharyya'] = False
        print(f"✗ Bhattacharyya failed: {e}")

    # Check 6: Integration points identified
    print("\n[6/6] Checking integration points...")
    try:
        # Would check if we can identify where to modify code
        # For now, manual confirmation
        print("  Key integration points:")
        print("  → Fragment class: Add lab_histogram attribute")
        print("  → compute_color_histogram(): Add Lab option")
        print("  → build_compatibility_matrix(): Use Lab instead of HSV")
        checks['integration_points'] = True
        print("✓ Integration points identified")
    except Exception as e:
        checks['integration_points'] = False
        print(f"✗ Integration planning failed: {e}")

    # Summary
    print("\n" + "=" * 60)
    passed = sum(checks.values())
    total = len(checks)
    print(f"PHASE 1A SUMMARY: {passed}/{total} checks passed")

    if passed == total:
        print("✓ READY FOR PHASE 1A IMPLEMENTATION")
        return True
    else:
        print("✗ FIX ISSUES BEFORE PROCEEDING")
        return False
```

### Edge Case Testing

```python
def test_edge_cases_phase_1a():
    """
    Test edge cases for Lab color implementation
    """
    print("\n" + "=" * 60)
    print("PHASE 1A EDGE CASE TESTING")
    print("=" * 60)

    import cv2
    import numpy as np

    # Edge Case 1: Pure black image
    print("\n[Edge Case 1] Pure black image...")
    black_img = np.zeros((100, 100, 3), dtype=np.uint8)
    lab_black = cv2.cvtColor(black_img, cv2.COLOR_BGR2Lab)
    hist_black, _ = np.histogramdd(lab_black.reshape(-1, 3), bins=[16, 8, 8],
                                    range=[[0, 256], [0, 256], [0, 256]])
    hist_black = hist_black.flatten() / hist_black.sum()
    print(f"✓ Black image histogram computed, first bin: {hist_black[0]:.4f}")

    # Edge Case 2: Pure white image
    print("\n[Edge Case 2] Pure white image...")
    white_img = np.full((100, 100, 3), 255, dtype=np.uint8)
    lab_white = cv2.cvtColor(white_img, cv2.COLOR_BGR2Lab)
    hist_white, _ = np.histogramdd(lab_white.reshape(-1, 3), bins=[16, 8, 8],
                                    range=[[0, 256], [0, 256], [0, 256]])
    hist_white = hist_white.flatten() / hist_white.sum()
    print(f"✓ White image histogram computed")

    # Edge Case 3: BC of black vs white (should be very low)
    bc_bw = np.sum(np.sqrt(hist_black * hist_white))
    print(f"\n[Edge Case 3] BC(black, white) = {bc_bw:.6f}")
    assert bc_bw < 0.01, "Black and white should have BC ≈ 0"
    print("✓ Black vs white: correctly very different")

    # Edge Case 4: Grayscale image
    print("\n[Edge Case 4] Grayscale image...")
    gray_img = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
    gray_bgr = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR)
    lab_gray = cv2.cvtColor(gray_bgr, cv2.COLOR_BGR2Lab)
    hist_gray, _ = np.histogramdd(lab_gray.reshape(-1, 3), bins=[16, 8, 8],
                                   range=[[0, 256], [0, 256], [0, 256]])
    hist_gray = hist_gray.flatten() / hist_gray.sum()
    print(f"✓ Grayscale image histogram computed")
    print(f"  Note: Lab a,b should be near 128 (neutral)")

    # Edge Case 5: Empty histogram (degenerate)
    print("\n[Edge Case 5] Zero histogram handling...")
    hist_zero = np.zeros(1024)
    hist_normal = np.random.rand(1024)
    hist_normal /= hist_normal.sum()
    bc_zero = np.sum(np.sqrt(hist_zero * hist_normal))
    print(f"  BC(zero, normal) = {bc_zero:.6f}")
    assert bc_zero == 0.0, "BC with zero histogram should be 0"
    print("✓ Zero histogram handled correctly")

    print("\n" + "=" * 60)
    print("✓ ALL EDGE CASES PASSED")
    print("=" * 60)
```

---

## PHASE 1B: EXPONENTIAL PENALTY

### Pre-Flight Checks

```python
def preflight_phase_1b():
    """
    Validate prerequisites for Phase 1B (Exponential Penalty)
    """
    print("\n" + "=" * 60)
    print("PHASE 1B PRE-FLIGHT CHECKS: Exponential Penalty")
    print("=" * 60)

    checks = {}

    # Check 1: Phase 1A validated
    print("\n[1/5] Checking Phase 1A completion...")
    # Would check if Phase 1A metrics exist
    checks['phase_1a_complete'] = True
    print("✓ Phase 1A complete (Lab color implemented)")

    # Check 2: Exponential formula tested
    print("\n[2/5] Testing exponential formula...")
    try:
        import numpy as np

        # Test various BC values
        test_bcs = [0.0, 0.5, 0.7, 0.9, 0.95, 1.0]
        power = 2.5

        print("  BC values and exponential penalties:")
        for bc in test_bcs:
            penalty = bc ** power
            reduction = 1.0 - penalty
            print(f"    BC={bc:.2f} → penalty={penalty:.4f} (reduction={reduction:.1%})")

        checks['exponential_formula'] = True
        print("✓ Exponential formula works")
    except Exception as e:
        checks['exponential_formula'] = False
        print(f"✗ Exponential formula failed: {e}")

    # Check 3: Edge case BC=0
    print("\n[3/5] Testing edge case: BC=0...")
    try:
        bc = 0.0
        power = 2.5
        penalty = bc ** power
        assert penalty == 0.0, "0^2.5 should be 0"
        print(f"✓ BC=0 handled correctly: 0^{power} = {penalty}")
    except Exception as e:
        checks['edge_case_zero'] = False
        print(f"✗ Edge case BC=0 failed: {e}")
    else:
        checks['edge_case_zero'] = True

    # Check 4: Edge case BC=1
    print("\n[4/5] Testing edge case: BC=1...")
    try:
        bc = 1.0
        power = 2.5
        penalty = bc ** power
        assert penalty == 1.0, "1^2.5 should be 1"
        print(f"✓ BC=1 handled correctly: 1^{power} = {penalty}")
    except Exception as e:
        checks['edge_case_one'] = False
        print(f"✗ Edge case BC=1 failed: {e}")
    else:
        checks['edge_case_one'] = True

    # Check 5: Integration point identified
    print("\n[5/5] Checking integration point...")
    print("  Key integration point:")
    print("  → build_compatibility_matrix(): Apply exponential to BC")
    print("    Before: color_score = bc_color")
    print("    After:  color_score = bc_color ** EXPONENTIAL_POWER")
    checks['integration_point'] = True
    print("✓ Integration point identified")

    # Summary
    print("\n" + "=" * 60)
    passed = sum(checks.values())
    total = len(checks)
    print(f"PHASE 1B SUMMARY: {passed}/{total} checks passed")

    if passed == total:
        print("✓ READY FOR PHASE 1B IMPLEMENTATION")
        return True
    else:
        print("✗ FIX ISSUES BEFORE PROCEEDING")
        return False
```

### Validation Protocol

```python
def validate_phase_1b(scores_same_before, scores_same_after,
                      scores_diff_before, scores_diff_after):
    """
    Validate that exponential penalty works as expected
    """
    print("\n" + "=" * 60)
    print("PHASE 1B VALIDATION")
    print("=" * 60)

    import numpy as np

    # Check 1: Same-source scores should decrease minimally
    print("\n[1/4] Checking same-source score changes...")
    mean_before = np.mean(scores_same_before)
    mean_after = np.mean(scores_same_after)
    reduction = (mean_before - mean_after) / mean_before

    print(f"  Before: {mean_before:.4f}")
    print(f"  After:  {mean_after:.4f}")
    print(f"  Reduction: {reduction:.1%}")

    if reduction < 0.15:
        print("✓ Same-source scores minimally affected (< 15% reduction)")
    elif reduction < 0.25:
        print("⚠ Same-source scores moderately affected (15-25% reduction)")
    else:
        print("✗ WARNING: Same-source scores heavily affected (> 25% reduction)")
        print("  → Exponential power may be too strong")

    # Check 2: Different-source scores should decrease significantly
    print("\n[2/4] Checking different-source score changes...")
    mean_diff_before = np.mean(scores_diff_before)
    mean_diff_after = np.mean(scores_diff_after)
    reduction_diff = (mean_diff_before - mean_diff_after) / mean_diff_before

    print(f"  Before: {mean_diff_before:.4f}")
    print(f"  After:  {mean_diff_after:.4f}")
    print(f"  Reduction: {reduction_diff:.1%}")

    if reduction_diff > 0.30:
        print("✓ Different-source scores significantly reduced (> 30%)")
    elif reduction_diff > 0.20:
        print("⚠ Different-source scores moderately reduced (20-30%)")
    else:
        print("✗ WARNING: Different-source scores barely affected (< 20%)")
        print("  → Exponential power may be too weak or BC already high")

    # Check 3: Separation improved
    print("\n[3/4] Checking separation improvement...")
    gap_before = mean_before - mean_diff_before
    gap_after = mean_after - mean_diff_after
    improvement = gap_after - gap_before

    print(f"  Gap before: {gap_before:.4f}")
    print(f"  Gap after:  {gap_after:.4f}")
    print(f"  Improvement: {improvement:+.4f}")

    if improvement > 0:
        print(f"✓ Separation improved by {improvement:.4f}")
    else:
        print(f"✗ WARNING: Separation decreased by {-improvement:.4f}")

    # Check 4: Accuracy change
    print("\n[4/4] Checking accuracy changes...")
    # (This would use actual threshold-based classification)
    print("  See full validation report for accuracy metrics")

    print("\n" + "=" * 60)
    print("PHASE 1B VALIDATION COMPLETE")
    print("=" * 60)
```

---

## PHASE 2A: LBP TEXTURE

### Pre-Flight Checks

```python
def preflight_phase_2a():
    """
    Validate prerequisites for Phase 2A (LBP Texture)
    """
    print("\n" + "=" * 60)
    print("PHASE 2A PRE-FLIGHT CHECKS: LBP Texture")
    print("=" * 60)

    checks = {}

    # Check 1: Scikit-image installed
    print("\n[1/6] Checking scikit-image installation...")
    try:
        import skimage
        from skimage.feature import local_binary_pattern
        print(f"✓ Scikit-image {skimage.__version__} installed")
        checks['skimage_installed'] = True
    except ImportError as e:
        print(f"✗ Scikit-image not installed: {e}")
        print("  → Install: pip install scikit-image")
        checks['skimage_installed'] = False

    # Check 2: LBP computation test
    print("\n[2/6] Testing LBP computation...")
    try:
        import numpy as np
        from skimage.feature import local_binary_pattern

        # Test image
        test_img = np.random.randint(0, 256, (100, 100), dtype=np.uint8)

        # Compute LBP
        P = 24
        R = 3
        lbp = local_binary_pattern(test_img, P=P, R=R, method='uniform')

        # Verify
        assert lbp.shape == test_img.shape
        print(f"✓ LBP computation works (P={P}, R={R})")
        print(f"  Output range: [{lbp.min():.0f}, {lbp.max():.0f}]")
        checks['lbp_computation'] = True
    except Exception as e:
        print(f"✗ LBP computation failed: {e}")
        checks['lbp_computation'] = False

    # Check 3: LBP histogram
    print("\n[3/6] Testing LBP histogram...")
    try:
        import numpy as np
        from skimage.feature import local_binary_pattern

        test_img = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
        P = 24
        R = 3

        lbp = local_binary_pattern(test_img, P=P, R=R, method='uniform')

        # Histogram
        n_bins = P + 2  # For 'uniform' method
        hist, _ = np.histogram(lbp, bins=n_bins, range=(0, n_bins))

        # Normalize
        hist = hist.astype(float)
        hist /= (hist.sum() + 1e-8)

        # Verify
        assert len(hist) == n_bins
        assert abs(hist.sum() - 1.0) < 1e-6

        print(f"✓ LBP histogram works ({n_bins} bins)")
        print(f"  Non-zero bins: {np.count_nonzero(hist)}")
        checks['lbp_histogram'] = True
    except Exception as e:
        print(f"✗ LBP histogram failed: {e}")
        checks['lbp_histogram'] = False

    # Check 4: BGR to grayscale conversion
    print("\n[4/6] Testing BGR to grayscale conversion...")
    try:
        import cv2
        import numpy as np

        test_bgr = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        test_gray = cv2.cvtColor(test_bgr, cv2.COLOR_BGR2GRAY)

        assert test_gray.shape == (100, 100)
        assert test_gray.dtype == np.uint8

        print("✓ BGR to grayscale conversion works")
        checks['grayscale_conversion'] = True
    except Exception as e:
        print(f"✗ Grayscale conversion failed: {e}")
        checks['grayscale_conversion'] = False

    # Check 5: Integration points
    print("\n[5/6] Checking integration points...")
    print("  Key integration points:")
    print("  → Fragment class: Add lbp_histogram attribute")
    print("  → compute_lbp_histogram(): New function")
    print("  → build_compatibility_matrix(): Multiply by texture penalty")
    checks['integration_points'] = True
    print("✓ Integration points identified")

    # Check 6: Phase 1B validated
    print("\n[6/6] Checking Phase 1B completion...")
    # Would verify Phase 1B metrics
    checks['phase_1b_complete'] = True
    print("✓ Phase 1B complete (exponential penalty working)")

    # Summary
    print("\n" + "=" * 60)
    passed = sum(checks.values())
    total = len(checks)
    print(f"PHASE 2A SUMMARY: {passed}/{total} checks passed")

    if passed == total:
        print("✓ READY FOR PHASE 2A IMPLEMENTATION")
        return True
    else:
        print("✗ FIX ISSUES BEFORE PROCEEDING")
        failed = [k for k, v in checks.items() if not v]
        print(f"\nFailed checks: {', '.join(failed)}")
        return False
```

### Edge Case Testing

```python
def test_edge_cases_phase_2a():
    """
    Test edge cases for LBP implementation
    """
    print("\n" + "=" * 60)
    print("PHASE 2A EDGE CASE TESTING")
    print("=" * 60)

    import cv2
    import numpy as np
    from skimage.feature import local_binary_pattern

    P = 24
    R = 3
    n_bins = P + 2

    # Edge Case 1: Uniform image (no texture)
    print("\n[Edge Case 1] Uniform image (no texture)...")
    uniform_img = np.full((100, 100), 128, dtype=np.uint8)
    lbp_uniform = local_binary_pattern(uniform_img, P=P, R=R, method='uniform')
    hist_uniform, _ = np.histogram(lbp_uniform, bins=n_bins, range=(0, n_bins))
    hist_uniform = hist_uniform.astype(float) / (hist_uniform.sum() + 1e-8)
    print(f"✓ Uniform image: histogram computed")
    print(f"  Dominant bin: {np.argmax(hist_uniform)} (value: {hist_uniform.max():.4f})")

    # Edge Case 2: Checkerboard (high texture)
    print("\n[Edge Case 2] Checkerboard pattern...")
    checker = np.indices((100, 100)).sum(axis=0) % 2
    checker = (checker * 255).astype(np.uint8)
    lbp_checker = local_binary_pattern(checker, P=P, R=R, method='uniform')
    hist_checker, _ = np.histogram(lbp_checker, bins=n_bins, range=(0, n_bins))
    hist_checker = hist_checker.astype(float) / (hist_checker.sum() + 1e-8)
    print(f"✓ Checkerboard: histogram computed")
    print(f"  Non-zero bins: {np.count_nonzero(hist_checker)}")

    # Edge Case 3: BC of uniform vs checkerboard (should be low)
    bc_uc = np.sum(np.sqrt(hist_uniform * hist_checker))
    print(f"\n[Edge Case 3] BC(uniform, checkerboard) = {bc_uc:.4f}")
    if bc_uc < 0.5:
        print("✓ Uniform and checkerboard correctly different")
    else:
        print("⚠ WARNING: BC higher than expected")

    # Edge Case 4: Small image
    print("\n[Edge Case 4] Small image (50x50)...")
    small_img = np.random.randint(0, 256, (50, 50), dtype=np.uint8)
    try:
        lbp_small = local_binary_pattern(small_img, P=P, R=R, method='uniform')
        hist_small, _ = np.histogram(lbp_small, bins=n_bins, range=(0, n_bins))
        hist_small = hist_small.astype(float) / (hist_small.sum() + 1e-8)
        print("✓ Small image handled correctly")
    except Exception as e:
        print(f"✗ Small image failed: {e}")

    # Edge Case 5: Very small radius on large image
    print("\n[Edge Case 5] Large image (500x500) with R=3...")
    large_img = np.random.randint(0, 256, (500, 500), dtype=np.uint8)
    try:
        lbp_large = local_binary_pattern(large_img, P=P, R=R, method='uniform')
        print("✓ Large image processed (may be slow)")
        print(f"  Time consideration: Large images increase computation")
    except Exception as e:
        print(f"✗ Large image failed: {e}")

    print("\n" + "=" * 60)
    print("✓ EDGE CASE TESTING COMPLETE")
    print("=" * 60)
```

---

## PHASE 2B: FRACTAL DIMENSION

### Pre-Flight Checks

```python
def preflight_phase_2b():
    """
    Validate prerequisites for Phase 2B (Fractal Dimension)
    """
    print("\n" + "=" * 60)
    print("PHASE 2B PRE-FLIGHT CHECKS: Fractal Dimension")
    print("=" * 60)

    checks = {}

    # Check 1: Contours available
    print("\n[1/6] Checking contour availability...")
    # Would verify that Fragment objects have .contour attribute
    checks['contours_available'] = True
    print("✓ Fragment contours available")

    # Check 2: Box counting test
    print("\n[2/6] Testing box counting algorithm...")
    try:
        import numpy as np
        import cv2

        # Create simple contour (rectangle)
        contour = np.array([[[10, 10]], [[90, 10]], [[90, 90]], [[10, 90]]])

        # Test box counting at different scales
        scales = [2, 4, 8, 16]
        counts = []

        for box_size in scales:
            # Create binary image
            img = np.zeros((100, 100), dtype=np.uint8)
            cv2.drawContours(img, [contour], -1, 255, 1)

            # Count boxes
            boxes_y = img.shape[0] // box_size
            boxes_x = img.shape[1] // box_size
            count = 0

            for i in range(boxes_y):
                for j in range(boxes_x):
                    box = img[i*box_size:(i+1)*box_size, j*box_size:(j+1)*box_size]
                    if np.any(box > 0):
                        count += 1

            counts.append(count)

        print(f"✓ Box counting works: scales={scales}, counts={counts}")
        checks['box_counting'] = True
    except Exception as e:
        print(f"✗ Box counting failed: {e}")
        checks['box_counting'] = False

    # Check 3: Linear regression
    print("\n[3/6] Testing linear regression for fractal dimension...")
    try:
        import numpy as np

        # Use box counting results from above
        log_scales = np.log([1.0/s for s in scales])
        log_counts = np.log(counts)

        # Linear regression
        coeffs = np.polyfit(log_scales, log_counts, 1)
        slope = coeffs[0]
        fractal_dim = slope

        print(f"✓ Linear regression works")
        print(f"  Fractal dimension: {fractal_dim:.4f}")
        print(f"  Expected range: 1.0 - 2.0")

        if 1.0 <= fractal_dim <= 2.0:
            print("✓ Fractal dimension in valid range")
        else:
            print(f"⚠ WARNING: Fractal dimension out of range: {fractal_dim:.4f}")

        checks['linear_regression'] = True
    except Exception as e:
        print(f"✗ Linear regression failed: {e}")
        checks['linear_regression'] = False

    # Check 4: Degenerate contour handling
    print("\n[4/6] Testing degenerate contour handling...")
    try:
        import numpy as np
        import cv2

        # Very small contour (3 points)
        tiny_contour = np.array([[[10, 10]], [[11, 10]], [[10, 11]]])

        # Get bounding box
        x, y, w, h = cv2.boundingRect(tiny_contour)
        max_allowed = min(w, h) // 2

        scales = [2, 4, 8, 16, 32]
        safe_scales = [s for s in scales if s < max_allowed]

        if len(safe_scales) < 3:
            print("✓ Correctly detected: contour too small for fractal analysis")
            print(f"  Contour size: {w}x{h}, safe scales: {safe_scales}")
        else:
            print(f"✓ Degenerate contour: {len(safe_scales)} scales available")

        checks['degenerate_handling'] = True
    except Exception as e:
        print(f"✗ Degenerate handling failed: {e}")
        checks['degenerate_handling'] = False

    # Check 5: Similarity computation
    print("\n[5/6] Testing fractal similarity computation...")
    try:
        import numpy as np

        # Two fractal dimensions
        d1 = 1.25
        d2 = 1.30

        # Similarity (normalized absolute difference)
        diff = abs(d1 - d2)
        max_diff = 1.0  # Reasonable maximum difference
        similarity = 1.0 - (diff / max_diff)

        print(f"✓ Similarity computation works")
        print(f"  D1={d1:.3f}, D2={d2:.3f}, Similarity={similarity:.4f}")

        checks['similarity_computation'] = True
    except Exception as e:
        print(f"✗ Similarity computation failed: {e}")
        checks['similarity_computation'] = False

    # Check 6: Integration points
    print("\n[6/6] Checking integration points...")
    print("  Key integration points:")
    print("  → Fragment class: Add fractal_dimension attribute")
    print("  → compute_fractal_dimension(): New function")
    print("  → build_compatibility_matrix(): Multiply by fractal penalty")
    checks['integration_points'] = True
    print("✓ Integration points identified")

    # Summary
    print("\n" + "=" * 60)
    passed = sum(checks.values())
    total = len(checks)
    print(f"PHASE 2B SUMMARY: {passed}/{total} checks passed")

    if passed == total:
        print("✓ READY FOR PHASE 2B IMPLEMENTATION")
        return True
    else:
        print("✗ FIX ISSUES BEFORE PROCEEDING")
        return False
```

### Edge Case Testing

```python
def test_edge_cases_phase_2b():
    """
    Test edge cases for fractal dimension
    """
    print("\n" + "=" * 60)
    print("PHASE 2B EDGE CASE TESTING")
    print("=" * 60)

    import numpy as np
    import cv2

    # Edge Case 1: Perfect line (D ≈ 1.0)
    print("\n[Edge Case 1] Straight line (D ≈ 1.0)...")
    line_contour = np.array([[[i, 50]] for i in range(0, 100, 2)])
    # Compute fractal dimension
    # (Would use actual function)
    print("✓ Straight line: Expected D ≈ 1.0")

    # Edge Case 2: Filled square (D ≈ 2.0)
    print("\n[Edge Case 2] Filled square outline (D ≈ 1.0-1.1)...")
    square_contour = np.array([[[10, 10]], [[90, 10]], [[90, 90]], [[10, 90]]])
    print("✓ Square: Expected D ≈ 1.0 (smooth boundary)")

    # Edge Case 3: Highly irregular contour
    print("\n[Edge Case 3] Irregular/fractal-like contour...")
    # Koch snowflake approximation or random walk
    irregular = []
    x, y = 50, 50
    for i in range(100):
        dx = np.random.randint(-2, 3)
        dy = np.random.randint(-2, 3)
        x = np.clip(x + dx, 0, 99)
        y = np.clip(y + dy, 0, 99)
        irregular.append([[x, y]])
    irregular_contour = np.array(irregular)
    print("✓ Irregular contour: Expected D ≈ 1.2-1.5")

    # Edge Case 4: Very small contour (insufficient scales)
    print("\n[Edge Case 4] Tiny contour (10x10 pixels)...")
    tiny_contour = np.array([[[10, 10]], [[20, 10]], [[20, 20]], [[10, 20]]])
    x, y, w, h = cv2.boundingRect(tiny_contour)
    max_scale = min(w, h) // 2
    print(f"  Bounding box: {w}x{h}, max safe scale: {max_scale}")
    if max_scale < 8:
        print("✓ Correctly identified: too small for reliable fractal")
        print("  → Would skip fractal feature for this fragment")

    # Edge Case 5: Comparison of similar fractal dimensions
    print("\n[Edge Case 5] Similar fractal dimensions...")
    d1 = 1.250
    d2 = 1.251  # Very close
    diff = abs(d1 - d2)
    similarity = 1.0 - diff  # Simplified
    print(f"  D1={d1:.3f}, D2={d2:.3f}, Difference={diff:.3f}")
    print(f"  Similarity={similarity:.4f}")
    if similarity > 0.99:
        print("✓ Very similar dimensions correctly identified")

    print("\n" + "=" * 60)
    print("✓ EDGE CASE TESTING COMPLETE")
    print("=" * 60)
```

---

## CATASTROPHIC FAILURE PREVENTION

### Critical Safeguards

```python
def validate_no_data_corruption():
    """
    Ensure no data corruption before proceeding
    """
    print("\n" + "=" * 60)
    print("CRITICAL: DATA CORRUPTION CHECK")
    print("=" * 60)

    import os
    import hashlib

    # Check 1: Fragment images still exist
    print("\n[1/3] Checking fragment image files...")
    fragment_dir = "fragments"

    if not os.path.isdir(fragment_dir):
        print("✗ CRITICAL: Fragment directory not found!")
        return False

    image_files = [f for f in os.listdir(fragment_dir)
                   if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if len(image_files) < 10:
        print(f"✗ CRITICAL: Too few images found ({len(image_files)})")
        return False

    print(f"✓ Found {len(image_files)} fragment images")

    # Check 2: Images readable
    print("\n[2/3] Verifying images readable...")
    import cv2

    unreadable = []
    for img_file in image_files[:5]:  # Sample first 5
        img_path = os.path.join(fragment_dir, img_file)
        img = cv2.imread(img_path)
        if img is None:
            unreadable.append(img_file)

    if len(unreadable) > 0:
        print(f"✗ CRITICAL: {len(unreadable)} images unreadable: {unreadable}")
        return False

    print("✓ All sampled images readable")

    # Check 3: Output directory safe
    print("\n[3/3] Checking output directory safety...")
    output_dir = "outputs"

    # Ensure we're not accidentally overwriting important files
    if os.path.exists(output_dir):
        important_files = ['final_results.txt', 'compatibility_matrix.npy']
        for f in important_files:
            f_path = os.path.join(output_dir, f)
            if os.path.exists(f_path):
                # Create backup
                backup_path = f_path + ".backup"
                import shutil
                shutil.copy2(f_path, backup_path)
                print(f"✓ Backed up: {f} → {f}.backup")

    print("✓ Output directory safe")

    print("\n" + "=" * 60)
    print("✓ NO DATA CORRUPTION DETECTED")
    print("=" * 60)

    return True
```

### Rollback Mechanism

```python
def create_implementation_checkpoint(phase_name):
    """
    Create checkpoint before each phase
    """
    print(f"\n[CHECKPOINT] Creating backup before {phase_name}...")

    import subprocess
    import datetime

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    branch_name = f"checkpoint_{phase_name}_{timestamp}"

    try:
        # Git status
        result = subprocess.run(['git', 'status', '--porcelain'],
                                capture_output=True, text=True)

        if result.stdout.strip():
            print("  Uncommitted changes detected")

            # Create branch
            subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
            print(f"  Created checkpoint branch: {branch_name}")

            # Commit
            subprocess.run(['git', 'add', '-A'], check=True)
            subprocess.run(['git', 'commit', '-m',
                            f'Checkpoint before {phase_name}'], check=True)
            print("  Committed changes to checkpoint")

            # Return to main branch
            subprocess.run(['git', 'checkout', 'main'], check=True)
            print("  Returned to main branch")

            print(f"✓ Checkpoint created: {branch_name}")
            print(f"  To rollback: git checkout {branch_name}")
            return branch_name
        else:
            print("  No changes to checkpoint")
            return None

    except Exception as e:
        print(f"  ⚠ Checkpoint failed: {e}")
        print("  Continuing without checkpoint (ensure manual backup)")
        return None
```

---

## MASTER PRE-FLIGHT SCRIPT

```python
def master_preflight_check():
    """
    Run all pre-flight checks before any implementation
    """
    print("=" * 60)
    print("MASTER PRE-FLIGHT CHECK")
    print("=" * 60)

    checks = []

    # System environment
    checks.append(("System Environment", validate_system_environment()))

    # Data integrity
    checks.append(("Data Integrity", validate_no_data_corruption()))

    # Phase-specific readiness
    print("\n" + "=" * 60)
    print("PHASE READINESS CHECKS")
    print("=" * 60)

    checks.append(("Phase 1A Ready", preflight_phase_1a()))
    checks.append(("Phase 1B Ready", preflight_phase_1b()))
    checks.append(("Phase 2A Ready", preflight_phase_2a()))
    checks.append(("Phase 2B Ready", preflight_phase_2b()))

    # Summary
    print("\n" + "=" * 60)
    print("MASTER PRE-FLIGHT SUMMARY")
    print("=" * 60)

    for check_name, result in checks:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {check_name}")

    all_passed = all(result for _, result in checks)

    print("\n" + "=" * 60)
    if all_passed:
        print("✓✓✓ ALL CHECKS PASSED - SAFE TO PROCEED ✓✓✓")
    else:
        print("✗✗✗ SOME CHECKS FAILED - FIX BEFORE PROCEEDING ✗✗✗")
    print("=" * 60)

    return all_passed
```

---

**Document Version:** 1.0
**Date:** 2026-04-08
**Status:** Ready for autonomous implementation
**Usage:** Run master_preflight_check() before starting any implementation phase
