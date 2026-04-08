# Logging Standard for ICBV Fragment Reconstruction System

**Version:** 1.0
**Date:** 2026-04-08
**Author:** ICBV Development Team

## Executive Summary

This document establishes comprehensive logging standards for the archaeological fragment reconstruction pipeline. The system uses Python's `logging` module with consistent log levels, structured messages, and performance-aware practices across all modules.

---

## 1. Current Logging Architecture

### 1.1 Logger Initialization Pattern

**Standard Pattern (Used in all modules):**
```python
import logging
logger = logging.getLogger(__name__)
```

**Root Logger Setup (main.py only):**
```python
def setup_logging(log_dir: str) -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = os.path.join(log_dir, f'run_{timestamp}.log')

    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(),
        ],
    )
    root_logger = logging.getLogger('main')
    root_logger.info("Log file: %s", log_path)
    return root_logger
```

### 1.2 Current Logging Distribution

**29 modules use logging:**
- **Core modules (7):** preprocessing.py, chain_code.py, compatibility.py, relaxation.py, visualize.py, assembly_renderer.py, shape_descriptors.py
- **Scripts (18):** test_*, profile_performance.py, download_*, validate_*, etc.
- **Analysis (4):** analyze_algorithm_components.py, analyze_mixed_sources.py, etc.

---

## 2. Log Level Standards

### 2.1 Level Definitions and Use Cases

#### DEBUG - Detailed diagnostic information
**When to use:**
- Variable values during computation
- Intermediate calculation results
- Loop iteration details
- Memory snapshots
- Algorithm state transitions

**Examples from codebase:**
```python
# profile_performance.py
self.logger.debug(f"Memory [{label}]: {mem_mb:.1f} MB")

# ACCEPTABLE: Low-frequency debug info
logger.debug("PCA orientation: angle=%.1f deg, ratio=%.3f", angle, ratio)

# AVOID: High-frequency verbose output in tight loops
# DON'T: logger.debug(f"Processing pixel {i} of {n}") inside 10000-iteration loop
```

#### INFO - Standard operational messages
**When to use:**
- Pipeline stage entry/exit
- File loading/saving
- Algorithm completion summaries
- Key parameter values
- Progress milestones
- Performance metrics

**Examples from codebase:**
```python
# preprocessing.py
logger.info("Loaded image %s -- shape %s", path, image.shape)
logger.info("Binarization: selected %s threshold", method)
logger.info("Extracted contour with %d boundary points", len(points))

# main.py
logger.info("Found %d fragment images in %s", len(fragment_paths), args.input)
logger.info("Fragment %-20s  size=%dx%d  contour=%d pts  segments=%d",
            name, image.shape[1], image.shape[0], len(contour), len(segments))

# compatibility.py
logger.info("Color similarity matrix (Bhattacharyya): min=%.3f  mean=%.3f  max=%.3f",
            min_bc, mean_bc, max_bc)
logger.info("Compatibility matrix built: shape=%s, mean=%.4f, max=%.4f",
            compat.shape, compat.mean(), compat.max())

# relaxation.py
logger.info("Relaxation iteration %02d -- max Delta: %.6f", iteration + 1, delta)
logger.info("Converged after %d iterations.", iteration + 1)
```

#### WARNING - Unexpected but recoverable situations
**When to use:**
- Fallback to alternative algorithms
- Data quality issues
- Threshold near-misses
- Configuration issues
- Deprecated functionality

**Examples from codebase:**
```python
# main.py
logger.warning("Bimodal color distribution detected (gap=%.3f, min_BC=%.3f). "
               "Fragments appear to come from different source images -- "
               "NO MATCH returned without running geometric pipeline.",
               bc_gap, min_bc)

logger.warning("NO MATCH FOUND: all %d proposed assemblies have fewer than 40%% "
               "of their pairs above the WEAK_MATCH threshold (%.2f).",
               len(assemblies), WEAK_MATCH_SCORE_THRESHOLD)

# analyze_algorithm_components.py
logger.warning(f"Failed to load {img_file.name}: {e}")

# preprocessing.py (potential addition)
logger.warning("Canny yielded no usable region; falling back to threshold")
```

#### ERROR - Errors that prevent specific operations
**When to use:**
- Algorithm failures
- Invalid input data
- I/O failures (after retries)
- Mathematical singularities
- Assertion failures

**Examples:**
```python
# Current codebase uses exceptions rather than ERROR logs
# RECOMMENDED additions:

# preprocessing.py
try:
    contour = extract_largest_contour(binary_mask)
except ValueError as e:
    logger.error("Contour extraction failed for %s: %s", path, e)
    raise

# compatibility.py
if compat_matrix.shape[0] == 0:
    logger.error("Empty compatibility matrix: no valid fragment pairs")
    raise ValueError("Cannot build compatibility matrix from empty input")
```

#### CRITICAL - System-level failures
**When to use:**
- Unrecoverable errors
- Data corruption
- Resource exhaustion
- Configuration failures preventing startup

**Usage:** Reserved for catastrophic failures only. Current codebase does not use CRITICAL (appropriate for application-level code).

---

## 3. Logging Best Practices

### 3.1 Message Formatting

#### Use f-strings for readability, % formatting for logging
```python
# GOOD: Lazy evaluation with % formatting
logger.info("Processing fragment %d/%d: %s", idx+1, total, name)

# ACCEPTABLE: f-strings for complex expressions
logger.info(f"Compatibility: {frag_i}-{frag_j} = {score:.4f}")

# AVOID: String concatenation
logger.info("Fragment: " + name + " size: " + str(size))  # Bad
```

#### Consistent numeric formatting
```python
# Percentages: 1 decimal place
logger.info("Convergence: %.1f%%", progress * 100)

# Scores/probabilities: 3-4 decimal places
logger.info("Compatibility score: %.4f", score)

# Angles: 1 decimal place
logger.info("Rotation angle: %.1f degrees", angle)

# Timing: 2 decimal places
logger.info("Completed in %.2f seconds", elapsed)

# Counts: integers
logger.info("Processed %d fragments", count)
```

### 3.2 Context and Traceability

#### Include relevant identifiers
```python
# GOOD: Clear context
logger.info("Fragment %s: extracted %d boundary points", name, len(contour))

# BAD: Missing context
logger.info("Extracted %d points", len(contour))  # Which fragment?
```

#### Include parameters that affect behavior
```python
# main.py - shows thresholds used for decisions
logger.info("Color pre-check (Lecture 71): min_BC=%.3f  max_gap=%.3f  is_mixed=%s",
            min_bc, bc_gap, is_mixed)

# preprocessing.py - shows auto-computed thresholds
logger.info("Canny thresholds: low=%d, high=%d", low, high)
```

### 3.3 Performance-Aware Logging

#### Avoid logging in tight loops
```python
# BAD: Logs N times (10,000+ for typical contours)
for idx, point in enumerate(contour_points):
    logger.debug("Point %d: (%d, %d)", idx, point[0], point[1])

# GOOD: Summary after loop
logger.info("Processed %d contour points (range: x[%d,%d] y[%d,%d])",
            len(contour_points), x_min, x_max, y_min, y_max)
```

#### Use conditional logging for expensive operations
```python
# Only compute if DEBUG is enabled
if logger.isEnabledFor(logging.DEBUG):
    histogram_str = format_histogram(data)  # Expensive
    logger.debug("Value distribution: %s", histogram_str)
```

### 3.4 Progress Logging for Long Operations

#### Report progress for operations >2 seconds
```python
# compatibility.py - building N×N matrix
logger.info("Building compatibility matrix: %d fragments, %d segment pairs",
            n_frags, n_frags * n_segs * n_frags * n_segs)

# For very long operations (>10s), consider periodic updates
for i in range(n_frags):
    if i > 0 and i % 10 == 0:
        logger.info("Compatibility matrix: processed %d/%d fragments", i, n_frags)
    # ... matrix computation
```

### 3.5 Error Context and Recovery

#### Log error context before raising
```python
# preprocessing.py
if cv2.contourArea(largest) < MIN_CONTOUR_AREA:
    logger.error("Largest contour area (%.1f) below threshold (%d) for %s",
                 cv2.contourArea(largest), MIN_CONTOUR_AREA, path)
    raise ValueError("Largest contour is too small.")
```

#### Document fallback decisions
```python
# preprocessing.py (current implementation at line 305)
logger.info("Canny yielded no usable region; falling back to threshold")
# RECOMMENDED: Upgrade to WARNING
logger.warning("Canny edge detection failed, falling back to Otsu threshold")
```

---

## 4. Module-Specific Guidelines

### 4.1 preprocessing.py
**Current status:** Good INFO logging coverage
**Recommendations:**
- ✅ **Keep:** Image load, Sobel stats, threshold method selection, contour extraction
- ⚠️ **Upgrade to WARNING:** Canny fallback (line 305)
- ➕ **Add INFO:** Background brightness detection result
- ➕ **Add DEBUG:** Morphological cleanup iteration counts

**Example additions:**
```python
# Line 133 (after bg_brightness calculation)
logger.info("Background brightness: %.1f -> %s background",
            bg_brightness, "light" if light_bg else "dark")

# Line 181 (after morphological cleanup)
logger.debug("Morphological cleanup: closed=%d px, opened=%d px",
             np.sum(closed > 0), np.sum(opened > 0))
```

### 4.2 chain_code.py
**Current status:** Minimal logging (only encode_fragment)
**Recommendations:**
- ✅ **Keep:** Chain code preview (line 277)
- ➕ **Add INFO:** Curvature profile statistics
- ➕ **Add DEBUG:** Segment rotation angles

**Example additions:**
```python
def compute_curvature_profile(pixel_segment: np.ndarray) -> np.ndarray:
    # ... existing code ...
    kappa = np.arctan2(cross, dot)

    logger.debug("Curvature profile: mean=%.3f, std=%.3f, range=[%.3f, %.3f]",
                 kappa.mean(), kappa.std(), kappa.min(), kappa.max())
    return kappa
```

### 4.3 compatibility.py
**Current status:** Excellent INFO logging for all matrix builds
**Recommendations:**
- ✅ **Keep:** Color/texture/Gabor/Haralick similarity matrices
- ✅ **Keep:** Final compatibility matrix summary
- ➕ **Add DEBUG:** Per-segment Fourier descriptor distances (sample only)
- ⚠️ **Consider reducing:** Detailed similarity matrices could be DEBUG level

**Example optimization:**
```python
# Lines 503-508: Could be DEBUG instead of INFO
logger.debug("Color similarity matrix: min=%.3f  mean=%.3f  max=%.3f", ...)

# Keep INFO for final compatibility only
logger.info("Compatibility matrix built: shape=%s, mean=%.4f, max=%.4f", ...)
```

### 4.4 relaxation.py
**Current status:** Perfect iteration logging
**Recommendations:**
- ✅ **Keep:** Per-iteration delta (line 148)
- ✅ **Keep:** Convergence message (line 153)
- ➕ **Add INFO:** Initial probability distribution stats
- ➕ **Add DEBUG:** Support matrix statistics per iteration

**Example additions:**
```python
def initialize_probabilities(compat_matrix: np.ndarray) -> np.ndarray:
    # ... existing code ...
    logger.info("Initialized %d×%d probability matrix: mean=%.4f, nonzero=%.1f%%",
                n_frags * n_segs, n_frags * n_segs,
                flat.mean(), 100 * np.count_nonzero(flat) / flat.size)
    return probs
```

### 4.5 visualize.py
**Current status:** Good INFO for all save operations
**Recommendations:**
- ✅ **Keep:** All "Saved X -> path" messages (lines 68, 97, 144, 172)
- ➕ **Add DEBUG:** Image dimensions and rendering parameters

### 4.6 main.py
**Current status:** Comprehensive logging, excellent model
**Recommendations:**
- ✅ **Excellent:** Fragment loading loop (line 273)
- ✅ **Excellent:** Color pre-check diagnostics (line 283)
- ✅ **Excellent:** Assembly match report (lines 156-244)
- ➕ **Add INFO:** Timing breakdown per stage
- ➕ **Add INFO:** Memory usage at key stages (if psutil available)

**Example additions:**
```python
# After compatibility matrix
compat_time = time.time() - stage_start
logger.info("Compatibility matrix computed in %.2f seconds", compat_time)

# After relaxation
relaxation_time = time.time() - stage_start
logger.info("Relaxation labeling completed in %.2f seconds (%d iterations)",
            relaxation_time, len(trace))
```

---

## 5. Anti-Patterns to Avoid

### 5.1 Don't log in tight loops
```python
# BAD: 10,000+ log messages
for i in range(len(contour)):
    logger.info("Processing point %d", i)

# GOOD: Summary
logger.info("Processed %d contour points", len(contour))
```

### 5.2 Don't log sensitive data
```python
# BAD: Potential file paths with usernames
logger.info("Processing: %s", full_path)

# GOOD: Relative or basename only
logger.info("Processing: %s", os.path.basename(full_path))
```

### 5.3 Don't use print() statements
```python
# BAD: Bypasses logging configuration
print(f"Fragment loaded: {name}")

# GOOD: Use logging
logger.info("Fragment loaded: %s", name)

# EXCEPTION: User-facing final results (main.py lines 225-243)
# These are intentional print() for clear UX, not logging
print(f"\n[RESULT] MATCH FOUND verdict={best_verdict} ...")
```

### 5.4 Don't log redundant information
```python
# BAD: Already logged by preprocessing
logger.info("Image shape: %s", image.shape)
logger.info("Image dimensions: %d x %d", image.shape[1], image.shape[0])

# GOOD: Log once with all relevant info
logger.info("Loaded image: shape=%s, dtype=%s, size=%.1f KB",
            image.shape, image.dtype, image.nbytes / 1024)
```

### 5.5 Don't log at wrong levels
```python
# BAD: ERROR for expected conditions
logger.error("No match found")  # This is a valid outcome

# GOOD: INFO for expected outcomes
logger.info("No match found: compatibility below threshold")

# BAD: INFO for debugging details
logger.info("Intermediate value x=%f, y=%f", x, y)

# GOOD: DEBUG for debugging details
logger.debug("Intermediate value x=%f, y=%f", x, y)
```

---

## 6. Performance Impact Assessment

### 6.1 Current Logging Overhead

**Measured impact (from profile_performance.py analysis):**
- **INFO level:** <1% overhead (acceptable)
- **DEBUG level:** 2-5% overhead (acceptable when needed)
- **Logging in loops:** Can add 50-300% overhead (avoid)

### 6.2 Optimization Strategies

#### Strategy 1: Use logger.isEnabledFor()
```python
if logger.isEnabledFor(logging.DEBUG):
    expensive_diagnostic = compute_histogram(data)
    logger.debug("Histogram: %s", expensive_diagnostic)
```

#### Strategy 2: Lazy string formatting
```python
# GOOD: Format string only if logged
logger.debug("Matrix: %s", expensive_matrix)

# BAD: Always formats even if not logged
logger.debug(f"Matrix: {expensive_matrix}")
```

#### Strategy 3: Batch logging for iterations
```python
# Instead of logging every iteration
log_buffer = []
for i in range(n_iterations):
    if i % 10 == 0:
        logger.info("Iteration %d/%d", i, n_iterations)
```

---

## 7. Testing and Validation

### 7.1 Log Message Checklist

For each log message, verify:
- [ ] **Level:** Appropriate for message importance
- [ ] **Context:** Includes necessary identifiers (fragment name, index, etc.)
- [ ] **Format:** Consistent numeric formatting
- [ ] **Performance:** Not in tight loop
- [ ] **Actionable:** User/developer can act on the information

### 7.2 Module Audit Checklist

For each module, verify:
- [ ] **Import:** `logger = logging.getLogger(__name__)`
- [ ] **Entry points:** Key functions log entry/completion
- [ ] **Progress:** Long operations (>2s) log progress
- [ ] **Errors:** Exceptions logged with context
- [ ] **No print():** Except user-facing results

---

## 8. Log File Format Specification

### 8.1 Standard Format
```
%(asctime)s [%(levelname)s] %(name)s: %(message)s

Example:
2024-04-08 14:30:21,345 [INFO] preprocessing: Loaded image frag_001.png -- shape (800, 600, 3)
2024-04-08 14:30:21,456 [INFO] chain_code: Chain code: length=2847, segments=4, preview=[0, 0, 1, 2, ...]
2024-04-08 14:30:22,123 [WARNING] main: Bimodal color distribution detected (gap=0.342, min_BC=0.287)
```

### 8.2 File Organization
```
outputs/logs/
├── run_20240408_143021.log          # Main pipeline run
├── run_20240408_151234.log          # Another run
└── profiling_20240408_160000.log    # Performance profiling
```

### 8.3 Log Rotation
**Not currently implemented.** For production use, consider:
```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    log_path, maxBytes=10*1024*1024, backupCount=5
)
```

---

## 9. Migration Checklist

### Phase 1: Critical Fixes (Immediate)
- [ ] Add ERROR logging with context before raising exceptions
- [ ] Upgrade WARNING level for fallback decisions (preprocessing.py line 305)
- [ ] Remove any remaining print() statements (except user results)
- [ ] Add progress logging for compatibility matrix build (>2s operation)

### Phase 2: Enhancement (Week 1)
- [ ] Add DEBUG logging for algorithm internals (curvature profiles, etc.)
- [ ] Add INFO timing logs per pipeline stage in main.py
- [ ] Add memory usage logging in main.py (optional, needs psutil)
- [ ] Standardize numeric formatting across all modules

### Phase 3: Optimization (Week 2)
- [ ] Review all INFO logs: move diagnostic details to DEBUG
- [ ] Add logger.isEnabledFor() guards for expensive DEBUG logs
- [ ] Implement log rotation for long-running deployments
- [ ] Add structured logging fields for machine parsing (optional)

### Phase 4: Documentation (Week 3)
- [ ] Update module docstrings with logging expectations
- [ ] Add logging examples to CLAUDE.md
- [ ] Create troubleshooting guide based on common log patterns
- [ ] Document log analysis tools (grep patterns, etc.)

---

## 10. Example Patterns from Codebase

### 10.1 Excellent Examples

#### main.py: Structured compatibility matrix logging
```python
def log_compatibility_matrix(matrix, names, run_logger):
    n_frags = matrix.shape[0]
    summary = matrix.mean(axis=(1, 3))
    run_logger.info("Pairwise compatibility matrix (mean over segments):")
    header = "         " + "  ".join(f"{n:>10}" for n in names)
    run_logger.info(header)
    for row_idx in range(n_frags):
        values = "  ".join(f"{summary[row_idx, col_idx]:10.4f}"
                          for col_idx in range(n_frags))
        run_logger.info("%8s  %s", names[row_idx], values)
```
**Why excellent:** Clear structure, readable table format, proper INFO level.

#### relaxation.py: Convergence tracking
```python
logger.info("Relaxation iteration %02d -- max Delta: %.6f", iteration + 1, delta)

if delta < CONVERGENCE_THRESHOLD:
    logger.info("Converged after %d iterations.", iteration + 1)
```
**Why excellent:** Concise, fixed-width formatting, clear completion message.

#### compatibility.py: Summary statistics
```python
logger.info("Color similarity matrix (Bhattacharyya): min=%.3f  mean=%.3f  max=%.3f",
            min_bc, mean_bc, max_bc)
```
**Why excellent:** Captures distribution in one line, consistent 3-digit precision.

### 10.2 Areas for Improvement

#### preprocessing.py line 305
```python
# CURRENT:
logger.info("Canny yielded no usable region; falling back to threshold")

# RECOMMENDED:
logger.warning("Canny edge detection failed, falling back to Otsu threshold for %s", path)
```
**Reason:** Fallback is unexpected behavior → WARNING level, add context.

#### chain_code.py: Silent operations
```python
def compute_curvature_profile(pixel_segment: np.ndarray) -> np.ndarray:
    # ... 50 lines of computation ...
    return kappa  # No logging at all
```
**Recommended:** Add DEBUG logging for diagnostics:
```python
logger.debug("Curvature profile: %d samples, range=[%.3f, %.3f]",
             len(kappa), kappa.min(), kappa.max())
```

---

## 11. Quick Reference

### Log Level Decision Tree
```
Is it an unrecoverable error?
├─ YES → ERROR
└─ NO ↓

Is it unexpected but handled?
├─ YES → WARNING
└─ NO ↓

Is it an expected outcome or milestone?
├─ YES → INFO
└─ NO ↓

Is it diagnostic detail for debugging?
├─ YES → DEBUG
└─ NO → Don't log it
```

### Formatting Quick Reference
```python
# Standard patterns
logger.info("Fragment %s: %d points", name, count)          # String, int
logger.info("Score: %.4f", score)                           # Float 4 decimals
logger.info("Time: %.2f seconds", elapsed)                  # Time 2 decimals
logger.info("Progress: %.1f%%", progress * 100)             # Percentage 1 decimal
logger.warning("Fallback: %s → %s", original, fallback)     # Transition
logger.error("Failed %s: %s", operation, exception)         # Error with cause
```

---

## 12. Conclusion

The ICBV fragment reconstruction system demonstrates strong logging practices with consistent use of Python's `logging` module across 29 files. The main improvements needed are:

1. **Error handling:** Add ERROR logs before raising exceptions
2. **Progress tracking:** Add timing logs for pipeline stages
3. **Debug detail:** Add DEBUG logs for algorithm internals
4. **Level adjustments:** Upgrade some INFO to WARNING (fallbacks)

The logging architecture is sound and ready for production use with these enhancements.

---

**Document Status:** FINAL
**Review Date:** 2026-04-08
**Next Review:** 2026-07-08 (quarterly)
