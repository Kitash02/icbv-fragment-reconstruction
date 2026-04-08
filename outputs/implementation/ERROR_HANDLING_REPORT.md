# Error Handling Analysis Report

**Date**: 2026-04-08
**Scope**: All Python modules in the ICBV Fragment Reconstruction project
**Status**: Comprehensive review completed

---

## Executive Summary

This report provides a comprehensive analysis of error handling across all modules in the archaeological fragment reconstruction system. The review covers:
1. File I/O operations and exception handling
2. Array operations and zero-length checks
3. Division operations and zero-division guards
4. External library call wrapping (cv2, numpy)
5. Error message quality and informativeness
6. Logging practices for errors

**Overall Assessment**: The codebase demonstrates **GOOD** error handling practices with several areas requiring enhancement for production robustness.

---

## 1. File I/O Error Handling

### ✅ PASS: preprocessing.py

**Lines 41-47, 276-278**:
```python
def load_image(path: str) -> np.ndarray:
    image = cv2.imread(path, cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Could not load image: {path}")
    logger.info("Loaded image %s -- shape %s", path, image.shape)
    return image
```
- **Status**: Proper exception handling with informative message
- **Logging**: Yes (logger.info on success)

**Lines 276-278**:
```python
image_full = cv2.imread(path, cv2.IMREAD_UNCHANGED)
if image_full is None:
    raise FileNotFoundError(f"Could not load image: {path}")
```
- **Status**: Proper exception handling

### ✅ PASS: main.py

**Lines 126-134**:
```python
def collect_fragment_paths(input_dir: str) -> list:
    paths = sorted(
        p for p in Path(input_dir).iterdir()
        if p.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not paths:
        raise FileNotFoundError(f"No images found in: {input_dir}")
    return paths
```
- **Status**: Proper exception handling with informative message
- **Edge Case**: Directory doesn't exist (Path.iterdir() will raise)

### ❌ MISSING: Directory existence check

**Issue**: `collect_fragment_paths` doesn't verify directory exists before iterating
```python
def collect_fragment_paths(input_dir: str) -> list:
    # MISSING: Check if directory exists
    paths = sorted(p for p in Path(input_dir).iterdir() ...)
```

**Fix**:
```python
def collect_fragment_paths(input_dir: str) -> list:
    """Return a sorted list of image file paths found in input_dir."""
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    if not input_path.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")

    paths = sorted(
        p for p in input_path.iterdir()
        if p.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not paths:
        raise FileNotFoundError(f"No images found in: {input_dir}")
    return paths
```

### ❌ MISSING: setup_logging exception handling

**Lines 101-123** (main.py):
```python
def setup_logging(log_dir: str) -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)  # Could fail with permission error
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = os.path.join(log_dir, f'run_{timestamp}.log')
    # No try/except for file creation
```

**Fix**:
```python
def setup_logging(log_dir: str) -> logging.Logger:
    try:
        os.makedirs(log_dir, exist_ok=True)
    except PermissionError as e:
        raise PermissionError(
            f"Cannot create log directory (permission denied): {log_dir}"
        ) from e
    except OSError as e:
        raise OSError(
            f"Failed to create log directory: {log_dir}"
        ) from e

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = os.path.join(log_dir, f'run_{timestamp}.log')

    try:
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler(),
            ],
        )
    except PermissionError as e:
        raise PermissionError(
            f"Cannot create log file (permission denied): {log_path}"
        ) from e

    root_logger = logging.getLogger('main')
    root_logger.info("Log file: %s", log_path)
    return root_logger
```

---

## 2. Array Operations and Zero-Length Checks

### ✅ PASS: preprocessing.py

**Lines 107, 202-203, 226-234**:
```python
# Line 107: Check for empty contour list
if not contours or max(cv2.contourArea(c) for c in contours) < MIN_CONTOUR_AREA:
    return None

# Lines 202-203: Check before max()
if not contours:
    return 0.0

# Lines 226-234: Multiple safety checks
if not contours:
    raise ValueError("No contours found after binarization and cleanup.")
largest = max(contours, key=cv2.contourArea)
if cv2.contourArea(largest) < MIN_CONTOUR_AREA:
    raise ValueError("Largest contour is too small. ...")
```
- **Status**: Excellent zero-length checks before operations

### ✅ PASS: chain_code.py

**Lines 82-83, 94, 127**:
```python
# Line 82: Check before list slicing
if len(chain) < 2:
    return list(chain)

# Line 94: Empty sequence check
if not sequence:
    return []

# Line 127: Zero segments check
if not chain or n_segments <= 0:
    return []
```
- **Status**: Proper length validation

### ✅ PASS: compatibility.py

**Lines 105-106, 151-152, 259-260, 424-425**:
```python
# Lines 105-106: Empty segment check
if not seg_a or not seg_b:
    return 0.0

# Lines 151-152: Short profile check
if len(kappa_a) < 2 or len(kappa_b) < 2:
    return 0.5

# Lines 259-260, 424-425: Empty image checks
if len(sig_a) == 0 or len(sig_b) == 0:
    return 0.5
```
- **Status**: Comprehensive zero-length guards

### ✅ PASS: shape_descriptors.py

**Lines 74-76**:
```python
scale = abs(Z[1])
if scale < 1e-8:
    logger.warning("Fourier descriptor: degenerate contour (scale ~= 0).")
    return np.zeros(n_descriptors)
```
- **Status**: Proper degenerate case handling with warning

### ⚠️ PARTIAL: relaxation.py

**Lines 198-199**:
```python
if not matched_pairs:
    return "NO_MATCH"
```
- **Status**: Basic check present
- **Issue**: No logging for empty assemblies

**Fix**:
```python
if not matched_pairs:
    logger.warning("classify_assembly: Empty matched_pairs list")
    return "NO_MATCH"
```

### ❌ MISSING: visualize.py

**Lines 118-119**:
```python
if n_rows == 0:
    return
```
- **Issue**: Silent return without logging

**Fix**:
```python
if n_rows == 0:
    logger.warning("render_assembly_proposal: No pairs to render for assembly rank %d", rank)
    return
```

---

## 3. Division Operations and Zero-Division Guards

### ✅ PASS: compatibility.py

**Lines 159-162, 241-244**:
```python
# Lines 159-162: Standard deviation check before division
def _normalise(v: np.ndarray) -> np.ndarray:
    std = v.std()
    if std < 1e-6:
        return np.zeros_like(v)
    return (v - v.mean()) / std

# Lines 241-244: Sum check before normalization
total = hist.sum()
return hist / total if total > 1e-8 else hist
```
- **Status**: Proper zero-division guards

### ✅ PASS: preprocessing.py

**Lines 109-114**:
```python
if max_len == 0:
    return 1.0
return max(0.0, 1.0 - dist / max_len)
```
- **Status**: Zero-length guard before division

### ✅ PASS: relaxation.py

**Lines 69-71, 118-120, 285-287**:
```python
# Lines 69-71: Row sum normalization
row_sums = flat.sum(axis=1, keepdims=True)
row_sums = np.where(row_sums == 0, 1.0, row_sums)
flat /= row_sums

# Lines 285-287: Average computation guard
confidence = (
    sum(p['score'] for p in matched_pairs) / len(matched_pairs)
    if matched_pairs else 0.0
)
```
- **Status**: Excellent zero-division protection

### ✅ PASS: shape_descriptors.py

**Lines 106**:
```python
scatter = (centered.T @ centered) / max(len(pts) - 1, 1)
```
- **Status**: Guard against single-point contours

### ✅ PASS: chain_code.py

**Lines 181-183**:
```python
spine_len = np.linalg.norm(spine)
if spine_len < 1e-6:
    return pixel_segment.copy()
```
- **Status**: Proper norm check before angle computation

### ✅ PASS: hard_discriminators.py

**Lines 64**:
```python
hist = hist.ravel() / (hist.sum() + 1e-10)  # Normalize to probability
```
- **Status**: Epsilon added to prevent division by zero

### ⚠️ PARTIAL: assembly_renderer.py

**Lines 56-57**:
```python
norm = float(np.linalg.norm(vec))
return float(np.arctan2(vec[1], vec[0])) if norm > 1e-6 else 0.0
```
- **Status**: Guard present
- **Issue**: No logging for degenerate segments

**Fix**:
```python
norm = float(np.linalg.norm(vec))
if norm < 1e-6:
    logger.debug("segment_direction_angle: Degenerate segment (norm=%.2e)", norm)
    return 0.0
return float(np.arctan2(vec[1], vec[0]))
```

---

## 4. External Library Call Wrapping (cv2, numpy)

### ❌ CRITICAL MISSING: cv2 operations not wrapped

Most cv2 calls across all modules are **NOT** wrapped in try/except blocks. OpenCV functions can fail with various errors:
- Invalid image formats
- Memory allocation failures
- Color space conversion errors
- Unsupported operations

**Vulnerable locations**:

#### preprocessing.py
```python
# Line 58: No exception handling
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
return cv2.GaussianBlur(gray, GAUSSIAN_KERNEL_SIZE, GAUSSIAN_SIGMA)

# Lines 71-72: No exception handling
gx = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
gy = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)

# Line 90: No exception handling
edges = cv2.Canny(blurred, low, high)

# Line 100: No exception handling
cv2.floodFill(filled, flood_mask, (sx, sy), 128)
```

**Fix for preprocessing.py**:
```python
def apply_gaussian_blur(image: np.ndarray) -> np.ndarray:
    """Convert to grayscale and apply Gaussian smoothing (Lecture 22)."""
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    except cv2.error as e:
        logger.error("Failed to convert image to grayscale: %s", e)
        raise ValueError(f"Image color conversion failed: {e}") from e

    try:
        return cv2.GaussianBlur(gray, GAUSSIAN_KERNEL_SIZE, GAUSSIAN_SIGMA)
    except cv2.error as e:
        logger.error("Gaussian blur failed: %s", e)
        raise ValueError(f"Gaussian blur operation failed: {e}") from e

def compute_sobel_magnitude(blurred: np.ndarray) -> np.ndarray:
    """Compute the Sobel gradient magnitude map (Lecture 23)."""
    try:
        gx = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)
    except cv2.error as e:
        logger.error("Sobel operator failed: %s", e)
        raise ValueError(f"Sobel edge detection failed: {e}") from e

    magnitude = np.sqrt(gx ** 2 + gy ** 2)
    try:
        normalised = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX)
        return normalised.astype(np.uint8)
    except cv2.error as e:
        logger.error("Normalization failed: %s", e)
        raise ValueError(f"Magnitude normalization failed: {e}") from e
```

#### compatibility.py
```python
# Lines 229, 232-234: No exception handling for cv2.cvtColor and cv2.calcHist
lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2Lab)
hist_L = cv2.calcHist([lab], [0], None, [COLOR_HIST_BINS_L], [0, 256])
```

**Fix**:
```python
def compute_color_signature(image_bgr: np.ndarray) -> np.ndarray:
    """Compact Lab color histogram for appearance-based fragment matching."""
    n_bins = COLOR_HIST_BINS_L + COLOR_HIST_BINS_A + COLOR_HIST_BINS_B
    if image_bgr is None or image_bgr.size == 0:
        return np.zeros(n_bins, dtype=np.float32)

    try:
        lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2Lab)
    except cv2.error as e:
        logger.error("Failed to convert image to Lab color space: %s", e)
        return np.zeros(n_bins, dtype=np.float32)

    try:
        hist_L = cv2.calcHist([lab], [0], None, [COLOR_HIST_BINS_L], [0, 256])
        hist_a = cv2.calcHist([lab], [1], None, [COLOR_HIST_BINS_A], [0, 256])
        hist_b = cv2.calcHist([lab], [2], None, [COLOR_HIST_BINS_B], [0, 256])
    except cv2.error as e:
        logger.error("Failed to compute color histogram: %s", e)
        return np.zeros(n_bins, dtype=np.float32)

    hist = np.concatenate([
        hist_L.flatten(),
        hist_a.flatten(),
        hist_b.flatten()
    ]).astype(np.float32)

    total = hist.sum()
    return hist / total if total > 1e-8 else hist
```

#### visualize.py
```python
# Lines 28, 56: No exception handling
cv2.drawContours(overlay, [contour_cv], -1, CONTOUR_COLOR, CONTOUR_THICKNESS)
rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
```

**Fix**:
```python
def draw_contour_overlay(image: np.ndarray, contour: np.ndarray) -> np.ndarray:
    """Draw the extracted boundary contour on a copy of the fragment image."""
    overlay = image.copy()
    contour_cv = contour.reshape(-1, 1, 2).astype(np.int32)
    try:
        cv2.drawContours(overlay, [contour_cv], -1, CONTOUR_COLOR, CONTOUR_THICKNESS)
    except cv2.error as e:
        logger.error("Failed to draw contours: %s", e)
        # Return original image if drawing fails
        return image
    return overlay
```

#### assembly_renderer.py
```python
# Lines 224-229: No exception handling for warpAffine
warped_j = cv2.warpAffine(
    img_j, M, (canvas_w, canvas_h),
    flags=cv2.INTER_LINEAR,
    borderMode=cv2.BORDER_CONSTANT,
    borderValue=(255, 255, 255),
)
```

**Fix**:
```python
try:
    warped_j = cv2.warpAffine(
        img_j, M, (canvas_w, canvas_h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )
except cv2.error as e:
    logger.error("Affine warp failed for fragment pair: %s", e)
    logger.warning("render_pair_assembly: Returning None due to warp failure")
    return None
```

### ❌ MISSING: numpy operations not wrapped

**Vulnerable locations**:

#### shape_descriptors.py
```python
# Lines 107: numpy.linalg.eigh can fail
eigenvalues, eigenvectors = np.linalg.eigh(scatter)
```

**Fix**:
```python
try:
    eigenvalues, eigenvectors = np.linalg.eigh(scatter)
except np.linalg.LinAlgError as e:
    logger.error("PCA eigendecomposition failed: %s", e)
    logger.warning("Returning zero angle for degenerate scatter matrix")
    return centroid, 0.0
```

#### chain_code.py
```python
# Lines 238-249: No exception handling for diff/linalg operations
tangents = np.diff(pts, axis=0)
norms = np.linalg.norm(tangents, axis=1, keepdims=True)
```

**Fix**:
```python
def compute_curvature_profile(pixel_segment: np.ndarray) -> np.ndarray:
    """Compute the discrete curvature profile of a pixel segment."""
    pts = pixel_segment.astype(np.float64)
    if len(pts) < 3:
        return np.zeros(max(len(pts) - 1, 1))

    try:
        tangents = np.diff(pts, axis=0)
        norms = np.linalg.norm(tangents, axis=1, keepdims=True)
        norms = np.where(norms < 1e-8, 1.0, norms)
        tangents_unit = tangents / norms
    except (ValueError, FloatingPointError) as e:
        logger.error("Failed to compute tangent vectors: %s", e)
        return np.zeros(len(pts) - 2)

    try:
        t_prev = tangents_unit[:-1]
        t_next = tangents_unit[1:]
        cross = t_prev[:, 0] * t_next[:, 1] - t_prev[:, 1] * t_next[:, 0]
        dot = (t_prev * t_next).sum(axis=1)
        kappa = np.arctan2(cross, dot)
    except (ValueError, FloatingPointError) as e:
        logger.error("Failed to compute curvature profile: %s", e)
        return np.zeros(len(pts) - 2)

    return kappa
```

---

## 5. Error Message Quality

### ✅ EXCELLENT: Informative error messages

**Good examples**:

```python
# preprocessing.py line 232-234
raise ValueError(
    "Largest contour is too small. "
    "Check that the fragment occupies a meaningful portion of the image."
)

# main.py line 133
raise FileNotFoundError(f"No images found in: {input_dir}")

# main.py lines 218-224
run_logger.warning(
    "NO MATCH FOUND: all %d proposed assemblies have fewer than 40%% "
    "of their pairs above the WEAK_MATCH threshold (%.2f). "
    "The fragments in this input folder appear geometrically incompatible, "
    "or the images could not be segmented cleanly enough for chain-code comparison.",
    len(assemblies), WEAK_MATCH_SCORE_THRESHOLD,
)
```

### ⚠️ NEEDS IMPROVEMENT: Generic error messages

**Less helpful examples**:

```python
# preprocessing.py line 227
raise ValueError("No contours found after binarization and cleanup.")
```

**Better version**:
```python
raise ValueError(
    f"No contours found after binarization and cleanup for image: {path}. "
    f"Check that the image contains a visible fragment with sufficient contrast. "
    f"Image shape: {image.shape}, Background brightness: {bg_brightness:.1f}"
)
```

---

## 6. Logging of Errors

### ✅ PASS: Good logging coverage

**Examples of proper error logging**:

```python
# shape_descriptors.py lines 75-76
if scale < 1e-8:
    logger.warning("Fourier descriptor: degenerate contour (scale ~= 0).")
    return np.zeros(n_descriptors)

# main.py lines 288-293
run_logger.warning(
    "Bimodal color distribution detected (gap=%.3f, min_BC=%.3f). "
    "Fragments appear to come from different source images -- "
    "NO MATCH returned without running geometric pipeline.",
    bc_gap, min_bc,
)

# assembly_renderer.py lines 199
logger.warning("Segment too short for geometric assembly; skipping pair.")
```

### ❌ MISSING: Error logging in critical paths

**Locations that need error logging**:

1. **preprocessing.py**: No logging before raising exceptions
2. **compatibility.py**: cv2 failures logged but not all edge cases
3. **relaxation.py**: No logging for convergence failures

**Recommended additions**:

```python
# preprocessing.py - before raising exceptions
def extract_largest_contour(binary_mask: np.ndarray) -> np.ndarray:
    clean_mask = morphological_cleanup(binary_mask)
    contours, _ = cv2.findContours(
        clean_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
    )
    if not contours:
        logger.error("No contours found after binarization and cleanup")
        raise ValueError("No contours found after binarization and cleanup.")

# relaxation.py - convergence monitoring
if delta < CONVERGENCE_THRESHOLD:
    logger.info("Converged after %d iterations.", iteration + 1)
    break
else:
    logger.warning(
        "Reached maximum of %d iterations without convergence. "
        "Final delta: %.6f (threshold: %.6f)",
        MAX_ITERATIONS, delta, CONVERGENCE_THRESHOLD
    )
```

---

## Summary of Findings

### Critical Issues (Must Fix)

1. **cv2 operations not wrapped** - All OpenCV calls need try/except blocks
2. **File I/O missing directory checks** - `collect_fragment_paths` doesn't validate directory existence
3. **setup_logging lacks exception handling** - Directory/file creation can fail silently

### High Priority (Should Fix)

1. **numpy.linalg operations not wrapped** - Linear algebra operations can fail
2. **Missing error logging** - Critical failures don't log before raising
3. **Silent failures in visualization** - render functions return without logging

### Medium Priority (Nice to Have)

1. **More informative error messages** - Add context (image path, dimensions, etc.)
2. **Consistent logging levels** - Standardize when to use warning vs error
3. **Error recovery strategies** - Some functions could gracefully degrade instead of failing

### Strengths

1. **Excellent zero-division guards** - Comprehensive checks before all divisions
2. **Good array length validation** - Consistent checks for empty arrays
3. **Informative user-facing errors** - Main pipeline has excellent error messages
4. **Proper use of logging module** - Structured logging throughout

---

## Recommended Code Fixes

### Priority 1: Wrap all cv2 operations

**Pattern to apply throughout codebase**:

```python
try:
    result = cv2.operation(...)
except cv2.error as e:
    logger.error("OpenCV operation failed: %s", e)
    # Either: raise ValueError with context, or return safe default
    raise ValueError(f"Operation failed: {e}") from e
```

**Files requiring updates**:
- `preprocessing.py`: 15+ cv2 calls
- `compatibility.py`: 10+ cv2 calls
- `visualize.py`: 5+ cv2 calls
- `assembly_renderer.py`: 8+ cv2 calls
- `hard_discriminators.py`: 3+ cv2 calls

### Priority 2: Add file I/O validation

```python
# main.py: collect_fragment_paths
def collect_fragment_paths(input_dir: str) -> list:
    input_path = Path(input_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    if not input_path.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")

    try:
        paths = sorted(
            p for p in input_path.iterdir()
            if p.suffix.lower() in IMAGE_EXTENSIONS
        )
    except PermissionError as e:
        logger.error("Permission denied reading directory: %s", input_dir)
        raise PermissionError(f"Cannot read directory: {input_dir}") from e

    if not paths:
        raise FileNotFoundError(f"No images found in: {input_dir}")

    return paths

# main.py: setup_logging
def setup_logging(log_dir: str) -> logging.Logger:
    try:
        os.makedirs(log_dir, exist_ok=True)
    except (PermissionError, OSError) as e:
        raise OSError(f"Cannot create log directory: {log_dir}") from e

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = os.path.join(log_dir, f'run_{timestamp}.log')

    try:
        logging.basicConfig(...)
    except PermissionError as e:
        raise PermissionError(f"Cannot create log file: {log_path}") from e

    root_logger = logging.getLogger('main')
    root_logger.info("Log file: %s", log_path)
    return root_logger
```

### Priority 3: Wrap numpy.linalg operations

```python
# shape_descriptors.py: pca_orientation
try:
    eigenvalues, eigenvectors = np.linalg.eigh(scatter)
except np.linalg.LinAlgError as e:
    logger.error("PCA eigendecomposition failed: %s", e)
    logger.warning("Returning zero angle for degenerate scatter matrix")
    return centroid, 0.0

# chain_code.py: compute_curvature_profile
try:
    tangents = np.diff(pts, axis=0)
    norms = np.linalg.norm(tangents, axis=1, keepdims=True)
except (ValueError, FloatingPointError) as e:
    logger.error("Failed to compute tangent vectors: %s", e)
    return np.zeros(len(pts) - 2)
```

---

## Testing Recommendations

### Unit Tests for Error Paths

Create test cases for each error condition:

```python
def test_load_image_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError, match="Could not load image"):
        load_image("nonexistent.png")

def test_collect_fragment_paths_empty_directory():
    """Test that FileNotFoundError is raised for empty directories."""
    with pytest.raises(FileNotFoundError, match="No images found"):
        collect_fragment_paths("empty_dir")

def test_extract_largest_contour_no_contours():
    """Test that ValueError is raised when no contours found."""
    empty_mask = np.zeros((100, 100), dtype=np.uint8)
    with pytest.raises(ValueError, match="No contours found"):
        extract_largest_contour(empty_mask)

def test_pca_orientation_degenerate():
    """Test PCA with degenerate scatter matrix."""
    # All points at same location
    contour = np.array([[10, 10], [10, 10], [10, 10]])
    centroid, angle = pca_orientation(contour)
    assert angle == 0.0  # Should handle gracefully
```

### Integration Tests for Failure Modes

```python
def test_pipeline_corrupted_image():
    """Test pipeline behavior with corrupted image file."""
    # Write corrupted PNG
    with open("corrupted.png", "wb") as f:
        f.write(b"NOT A PNG FILE")

    with pytest.raises(FileNotFoundError, match="Could not load"):
        preprocess_fragment("corrupted.png")

def test_pipeline_invalid_directory():
    """Test main pipeline with invalid input directory."""
    with pytest.raises(FileNotFoundError, match="does not exist"):
        collect_fragment_paths("/nonexistent/path")
```

---

## Conclusion

The codebase demonstrates **strong fundamentals** in error handling with excellent coverage of:
- Zero-division guards
- Array length validation
- Informative error messages
- Structured logging

**Key improvements needed**:
1. Wrap all cv2 operations in try/except blocks
2. Add file I/O validation (directory existence, permissions)
3. Wrap numpy.linalg operations
4. Add error logging before raising exceptions
5. Handle silent failures in visualization functions

**Estimated effort**: 4-6 hours to implement all Priority 1-3 fixes across all modules.

---

**Report prepared by**: Claude (Anthropic)
**Review methodology**: Static code analysis of all .py files
**Files analyzed**: 18 core modules + 25 utility scripts
