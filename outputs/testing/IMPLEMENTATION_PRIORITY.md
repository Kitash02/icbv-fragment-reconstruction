# Implementation Priority Guide
## Archaeological Fragment Reconstruction - Actionable Roadmap

**Date:** 2026-04-08
**Based on:** Comprehensive architecture analysis

---

## Quick Reference: What to Fix First

### CRITICAL (Fix Today) - 1-2 Hours
**Goal:** Fix 0% negative accuracy → 40-50%

1. ✅ **Tune color thresholds** (5 min) - Lines to change in `src/main.py`:
   ```python
   COLOR_PRECHECK_GAP_THRESH = 0.15    # Change from 0.25
   COLOR_PRECHECK_LOW_MAX = 0.72       # Change from 0.62
   ```

2. ✅ **Raise geometric thresholds** (15 min) - Lines to change in `src/relaxation.py`:
   ```python
   WEAK_MATCH_SCORE_THRESHOLD = 0.45   # Change from 0.35
   ASSEMBLY_CONFIDENCE_THRESHOLD = 0.55  # Change from 0.45
   ```

3. ✅ **Add explicit rejection** (15 min) - Add to `src/relaxation.py::classify_assembly()`:
   ```python
   def classify_assembly(confidence: float, matched_pairs: List[dict]) -> str:
       if not matched_pairs:
           return "NO_MATCH"

       # NEW: Explicit rejection if no strong evidence
       max_pair_score = max((p['raw_compat'] for p in matched_pairs), default=0.0)
       if max_pair_score < 0.40:
           return "NO_MATCH"

       # ... rest of existing logic
   ```

4. ✅ **Fix unit tests** (20 min) - Update `tests/test_pipeline.py`:
   ```python
   # Replace:
   from compatibility import segment_compatibility

   # With:
   from compatibility import profile_similarity
   from chain_code import compute_curvature_profile

   def test_profile_similarity_identical():
       seg = np.array([[0, 0], [1, 0], [2, 1], [3, 2], [4, 3]])
       kappa = compute_curvature_profile(seg)
       score = profile_similarity(kappa, kappa)
       assert score == pytest.approx(1.0, abs=0.05)
   ```

**Test:** `python run_test.py --no-rotate`
**Expected:** Negative accuracy 0% → 40-50%, positive 100% maintained

---

### HIGH PRIORITY (This Week) - 1 Day
**Goal:** 70-80% negative accuracy

5. ✅ **Add texture descriptor** (2 hours)
   - File: `src/compatibility.py`
   - Add to requirements.txt: `scikit-image`
   - New functions to add:
   ```python
   from skimage.feature import local_binary_pattern

   TEXTURE_PENALTY_WEIGHT = 0.60

   def compute_texture_signature(image_bgr: np.ndarray) -> np.ndarray:
       gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
       lbp = local_binary_pattern(gray, P=8, R=1, method='uniform')
       hist, _ = np.histogram(lbp.ravel(), bins=10, range=(0, 10), density=True)
       return hist

   def texture_bhattacharyya(tex_a: np.ndarray, tex_b: np.ndarray) -> float:
       return float(np.sqrt(np.sum(np.sqrt(tex_a * tex_b))))

   def _build_texture_sim_matrix(all_images: List[np.ndarray]) -> np.ndarray:
       n = len(all_images)
       sigs = [compute_texture_signature(img) for img in all_images]
       mat = np.ones((n, n), dtype=float)
       for i in range(n):
           for j in range(i + 1, n):
               tbc = texture_bhattacharyya(sigs[i], sigs[j])
               mat[i, j] = tbc
               mat[j, i] = tbc
       return mat
   ```

   - Integrate in `build_compatibility_matrix()`:
   ```python
   # After building color_sim_mat:
   texture_sim_mat = _build_texture_sim_matrix(all_images) if all_images else None

   # In scoring loop:
   if texture_sim_mat is not None:
       texture_bc = texture_sim_mat[frag_i, frag_j]
       texture_penalty = (1.0 - texture_bc) * TEXTURE_PENALTY_WEIGHT
       score = max(0.0, score - color_penalty - texture_penalty)
   ```

6. ✅ **Add edge complexity** (1.5 hours)
   - File: `src/compatibility.py`
   - New functions:
   ```python
   COMPLEXITY_WEIGHT = 0.15

   def edge_complexity_score(pixel_segment: np.ndarray) -> float:
       if len(pixel_segment) < 2:
           return 1.0
       contour_length = np.sum(np.linalg.norm(np.diff(pixel_segment, axis=0), axis=1))
       bbox_diag = np.linalg.norm(pixel_segment.max(axis=0) - pixel_segment.min(axis=0))
       if bbox_diag < 1e-6:
           return 1.0
       complexity = np.log(contour_length + 1) / np.log(bbox_diag + 1)
       return float(np.clip(complexity, 1.0, 2.0))

   def complexity_compatibility(seg_a: np.ndarray, seg_b: np.ndarray) -> float:
       comp_a = edge_complexity_score(seg_a)
       comp_b = edge_complexity_score(seg_b)
       diff = abs(comp_a - comp_b)
       return float(np.exp(-diff / 0.2))
   ```

   - Add to scoring in `build_compatibility_matrix()`:
   ```python
   complexity_compat = complexity_compatibility(pix_a, pix_b)
   score = base + FOURIER_WEIGHT * fourier + COMPLEXITY_WEIGHT * complexity_compat
   ```

7. ✅ **Early pruning optimization** (30 min)
   - File: `src/compatibility.py`
   - In `build_compatibility_matrix()` scoring loop:
   ```python
   # Before computing curvature:
   if color_sim_mat is not None:
       bc = color_sim_mat[frag_i, frag_j]
       if bc < 0.40:
           compat[frag_i, seg_a, frag_j, seg_b] = 0.0
           continue  # Skip expensive FFT computation
   ```

**Test:** `python run_test.py --no-rotate`
**Expected:** Negative accuracy 40-50% → 70-80%

---

### MEDIUM PRIORITY (Next 2 Weeks) - 1 Week
**Goal:** Production-ready (85-90% negative accuracy)

8. ✅ **Parallelize compatibility matrix** (2 hours)
   - File: `src/compatibility.py`
   - Create new function:
   ```python
   from multiprocessing import Pool

   def _compute_fragment_pair_compat(args):
       # Extract args
       # Compute compatibility for one (frag_i, frag_j) pair
       # Return (frag_i, frag_j, pair_compat_matrix)

   def build_compatibility_matrix_parallel(all_segments, all_pixel_segments, all_images):
       # Pre-compute curvatures
       # Build task list
       with Pool() as pool:
           results = pool.map(_compute_fragment_pair_compat, tasks)
       # Assemble 4D matrix
       return compat
   ```

   - Add CLI flag in `src/main.py`:
   ```python
   parser.add_argument('--parallel', action='store_true',
                       help='Enable parallel compatibility computation')

   # In run_pipeline():
   if args.parallel:
       compat_matrix = build_compatibility_matrix_parallel(...)
   else:
       compat_matrix = build_compatibility_matrix(...)
   ```

9. ✅ **Negative constraint propagation** (1 day)
   - File: `src/relaxation.py`
   - Modify `compute_support()`:
   ```python
   def compute_support(probs: np.ndarray, compat_matrix: np.ndarray) -> np.ndarray:
       # Existing positive support
       positive_support = probs @ compat_matrix.T

       # NEW: Negative constraints
       negative_compat = np.where(compat_matrix < 0.30, 0.30 - compat_matrix, 0.0)
       negative_support = probs @ negative_compat.T

       return positive_support - 0.5 * negative_support
   ```

10. ✅ **Expand test coverage** (2 days)
    - File: `tests/test_preprocessing.py` (NEW)
    ```python
    def test_alpha_channel_extraction():
    def test_canny_fallback():
    def test_background_detection():
    ```

    - File: `tests/test_shape_descriptors.py` (NEW)
    ```python
    def test_pca_normalization_invariance():
    def test_fourier_descriptors_scale_invariance():
    ```

    - File: `tests/test_curvature.py` (NEW)
    ```python
    def test_curvature_profile_straight_line():
    def test_profile_similarity_anti_parallel():
    ```

**Test:** `python run_test.py` (full suite)
**Expected:** Negative accuracy 70-80% → 85-90%, coverage 40% → 80%

---

## File-by-File Change List

### `src/main.py`
**Lines to modify:** 59-60
```python
# OLD:
COLOR_PRECHECK_GAP_THRESH = 0.25
COLOR_PRECHECK_LOW_MAX = 0.62

# NEW:
COLOR_PRECHECK_GAP_THRESH = 0.15
COLOR_PRECHECK_LOW_MAX = 0.72
```

**Lines to add:** After line 360
```python
parser.add_argument('--parallel', action='store_true',
                    help='Enable parallel compatibility computation (faster on multi-core)')
```

---

### `src/relaxation.py`
**Lines to modify:** 47-49
```python
# OLD:
MATCH_SCORE_THRESHOLD = 0.55
WEAK_MATCH_SCORE_THRESHOLD = 0.35
ASSEMBLY_CONFIDENCE_THRESHOLD = 0.45

# NEW:
MATCH_SCORE_THRESHOLD = 0.55      # Keep same
WEAK_MATCH_SCORE_THRESHOLD = 0.45  # Raise from 0.35
ASSEMBLY_CONFIDENCE_THRESHOLD = 0.55  # Raise from 0.45
```

**Lines to add:** After line 196 in `classify_assembly()`
```python
# NEW: Explicit rejection criterion
max_pair_score = max((p.get('raw_compat', 0.0) for p in matched_pairs), default=0.0)
if max_pair_score < 0.40:
    return "NO_MATCH"
```

**Lines to modify:** 73-97 in `compute_support()`
```python
# Replace entire function with:
def compute_support(probs: np.ndarray, compat_matrix: np.ndarray) -> np.ndarray:
    n_frags, n_segs = compat_matrix.shape[:2]
    n_units = n_frags * n_segs

    probs_flat = probs.reshape(n_units, n_units)
    compat_flat = compat_matrix.reshape(n_units, n_units)

    # Positive support (existing)
    positive_support_flat = probs_flat @ compat_flat.T

    # NEW: Negative constraint propagation
    negative_compat_flat = np.where(compat_flat < 0.30, 0.30 - compat_flat, 0.0)
    negative_support_flat = probs_flat @ negative_compat_flat.T

    # Combine positive and negative evidence
    support_flat = positive_support_flat - 0.5 * negative_support_flat

    return support_flat.reshape(n_frags, n_segs, n_frags, n_segs)
```

---

### `src/compatibility.py`
**Lines to add:** After line 55 (constants section)
```python
TEXTURE_PENALTY_WEIGHT = 0.60
COMPLEXITY_WEIGHT = 0.15
```

**Lines to add:** After line 226 (after `color_bhattacharyya`)
```python
def compute_texture_signature(image_bgr: np.ndarray) -> np.ndarray:
    """Compute LBP texture histogram for appearance-based matching."""
    from skimage.feature import local_binary_pattern

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    lbp = local_binary_pattern(gray, P=8, R=1, method='uniform')
    hist, _ = np.histogram(lbp.ravel(), bins=10, range=(0, 10), density=True)
    return hist.astype(np.float32)

def texture_bhattacharyya(tex_a: np.ndarray, tex_b: np.ndarray) -> float:
    """Bhattacharyya coefficient between texture histograms."""
    return float(np.sqrt(np.sum(np.sqrt(tex_a * tex_b))))

def edge_complexity_score(pixel_segment: np.ndarray) -> float:
    """Fractal dimension approximation for edge irregularity."""
    if len(pixel_segment) < 2:
        return 1.0
    contour_length = np.sum(np.linalg.norm(np.diff(pixel_segment, axis=0), axis=1))
    bbox_diag = np.linalg.norm(pixel_segment.max(axis=0) - pixel_segment.min(axis=0))
    if bbox_diag < 1e-6:
        return 1.0
    complexity = np.log(contour_length + 1) / np.log(bbox_diag + 1)
    return float(np.clip(complexity, 1.0, 2.0))

def complexity_compatibility(seg_a: np.ndarray, seg_b: np.ndarray) -> float:
    """Penalty for mismatched edge complexity (smooth vs jagged)."""
    comp_a = edge_complexity_score(seg_a)
    comp_b = edge_complexity_score(seg_b)
    diff = abs(comp_a - comp_b)
    return float(np.exp(-diff / 0.2))
```

**Lines to modify:** 256-274 in `_build_color_sim_matrix()`
```python
# Add after color matrix:
def _build_texture_sim_matrix(all_images: List[np.ndarray]) -> np.ndarray:
    """Build texture similarity matrix (same structure as color)."""
    n = len(all_images)
    sigs = [compute_texture_signature(img) for img in all_images]
    mat = np.ones((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            tbc = texture_bhattacharyya(sigs[i], sigs[j])
            mat[i, j] = tbc
            mat[j, i] = tbc
    return mat
```

**Lines to modify:** 333-370 in `build_compatibility_matrix()`
```python
# Add after color_sim_mat computation:
texture_sim_mat: Optional[np.ndarray] = None
if all_images is not None:
    texture_sim_mat = _build_texture_sim_matrix(all_images)

# In scoring loop, after line 337:
for seg_b, chain_b in enumerate(segs_j):
    # NEW: Early pruning for low-BC pairs
    if color_sim_mat is not None:
        bc = color_sim_mat[frag_i, frag_j]
        if bc < 0.40:
            compat[frag_i, seg_a, frag_j, seg_b] = 0.0
            continue

    # ... existing curvature computation ...

    # NEW: Add complexity compatibility
    complexity_compat = complexity_compatibility(pix_a, pix_b)
    score = base + FOURIER_WEIGHT * fourier + COMPLEXITY_WEIGHT * complexity_compat

    # Existing good continuation
    cont = good_continuation_bonus(chain_a, chain_b)
    score += GOOD_CONTINUATION_WEIGHT * cont

    # Existing color penalty
    if color_sim_mat is not None:
        bc = color_sim_mat[frag_i, frag_j]
        color_penalty = (1.0 - bc) * COLOR_PENALTY_WEIGHT
        score = max(0.0, score - color_penalty)

    # NEW: Texture penalty
    if texture_sim_mat is not None:
        texture_bc = texture_sim_mat[frag_i, frag_j]
        texture_penalty = (1.0 - texture_bc) * TEXTURE_PENALTY_WEIGHT
        score = max(0.0, score - texture_penalty)

    compat[frag_i, seg_a, frag_j, seg_b] = score
```

---

### `tests/test_pipeline.py`
**Lines to modify:** 23-26
```python
# OLD:
from compatibility import (
    edit_distance,
    segment_compatibility,
    build_compatibility_matrix,
)

# NEW:
from compatibility import (
    edit_distance,
    profile_similarity,
    build_compatibility_matrix,
)
from chain_code import compute_curvature_profile
```

**Lines to replace:** 139-146
```python
# OLD:
def test_segment_compatibility_identical():
    seg = [0, 1, 2, 3, 0, 1]
    assert segment_compatibility(seg, seg) == pytest.approx(1.0)

def test_segment_compatibility_in_unit_interval():
    score = segment_compatibility([0, 1, 2], [3, 4, 5, 6])
    assert 0.0 <= score <= 1.0

# NEW:
def test_profile_similarity_identical():
    seg = np.array([[0, 0], [1, 0], [2, 1], [3, 2], [4, 3]])
    kappa = compute_curvature_profile(seg)
    score = profile_similarity(kappa, kappa)
    assert score == pytest.approx(1.0, abs=0.05)

def test_profile_similarity_in_unit_interval():
    seg_a = np.array([[0, 0], [1, 0], [2, 1], [3, 2]])
    seg_b = np.array([[0, 0], [1, 1], [2, 2], [3, 2]])
    kappa_a = compute_curvature_profile(seg_a)
    kappa_b = compute_curvature_profile(seg_b)
    score = profile_similarity(kappa_a, kappa_b)
    assert 0.0 <= score <= 1.0
```

---

### `requirements.txt`
**Lines to add:**
```
scikit-image>=0.19.0
```

---

## Testing Checklist

### After Each Change
- [ ] Run unit tests: `python -m pytest tests/ -v`
- [ ] Run quick benchmark: `python run_test.py --no-rotate --positive-only`
- [ ] Check logs for errors: `cat outputs/logs/run_*.log | grep ERROR`

### After Phase 1 (Critical)
- [ ] Full benchmark: `python run_test.py --no-rotate`
- [ ] Verify positive accuracy = 100%
- [ ] Verify negative accuracy >= 40%
- [ ] Check no preprocessing failures

### After Phase 2 (High Priority)
- [ ] Full benchmark with rotation: `python run_test.py`
- [ ] Verify negative accuracy >= 70%
- [ ] Verify positive accuracy >= 95%
- [ ] Profile performance: `python -m cProfile -o profile.stats src/main.py --input data/sample`

### Before Production (Medium Priority)
- [ ] Test coverage: `pytest --cov=src tests/`
- [ ] Verify coverage >= 80%
- [ ] Load test: 100 fragments
- [ ] Memory profile: `mprof run src/main.py --input large_dataset`

---

## Rollback Plan

If any change causes positive accuracy to drop below 95%:

1. **Revert threshold changes:**
   ```bash
   git diff src/main.py src/relaxation.py
   git checkout HEAD -- src/main.py src/relaxation.py
   ```

2. **Disable new features:**
   ```python
   TEXTURE_PENALTY_WEIGHT = 0.0  # Disable texture
   COMPLEXITY_WEIGHT = 0.0       # Disable complexity
   ```

3. **Re-run benchmark:**
   ```bash
   python run_test.py --no-rotate --positive-only
   ```

4. **Investigate failure:**
   - Check logs for specific failing case
   - Run single case in isolation: `python src/main.py --input data/examples/positive/failing_case`
   - Examine compatibility matrix: Look for abnormally low scores

---

## Performance Monitoring

### Before Changes (Baseline)
- Negative accuracy: 0%
- Positive accuracy: 100%
- Time per case: ~6.7s

### After Phase 1 (Expected)
- Negative accuracy: 40-50%
- Positive accuracy: 100%
- Time per case: ~5.0s (1.5x speedup from early pruning)

### After Phase 2 (Expected)
- Negative accuracy: 70-80%
- Positive accuracy: 95-100%
- Time per case: ~6.5s (texture/complexity add overhead, offset by pruning)

### After Phase 3 (Expected)
- Negative accuracy: 85-90%
- Positive accuracy: 95-100%
- Time per case: ~2.0s (4x speedup from parallelization)

---

## Validation Criteria

### Phase 1 Success
✅ Negative accuracy >= 40%
✅ Positive accuracy = 100%
✅ Unit tests passing
✅ No preprocessing failures

### Phase 2 Success
✅ Negative accuracy >= 70%
✅ Positive accuracy >= 95%
✅ Time per case <= 7s
✅ No false negatives on benchmark

### Phase 3 Success
✅ Negative accuracy >= 85%
✅ Positive accuracy >= 95%
✅ Test coverage >= 80%
✅ Time per case <= 5s

---

**End of Implementation Guide**
**Generated:** 2026-04-08
**Next Action:** Start with Phase 1 (1-2 hours to fix critical 0% negative accuracy)
