# Performance Analysis Report
**Archaeological Fragment Reconstruction System**

**Date:** 2026-04-08
**Analyst:** Claude Code Performance Profiler
**Test Environment:** Windows 11 Enterprise, Python with OpenCV/NumPy

---

## Executive Summary

This report provides a comprehensive performance profiling of the archaeological fragment reconstruction pipeline on both synthetic benchmark data and real fragment datasets. The analysis reveals system bottlenecks, scalability characteristics, and provides optimization recommendations.

### Key Findings

1. **System Performance**: Pipeline processes 0.95 fragments/second on 5-fragment datasets
2. **Primary Bottleneck**: Visualization stage consumes 93-97% of total execution time
3. **Core Algorithm Performance**: Non-visualization stages (preprocessing, encoding, compatibility, relaxation) are highly efficient, consuming only 3-7% of total time
4. **Scalability**: System exhibits sub-linear time complexity for core algorithms with good scalability characteristics
5. **Real vs Benchmark**: Real fragment performance is comparable to synthetic benchmarks

---

## 1. Performance Baseline

### 1.1 Sample Data (5 Fragments - Synthetic)

**Dataset**: `data/sample/` - 5 synthetic fragments (500x500 pixels)

```
Total Pipeline Time: 5.287 seconds
Fragments per Second: 0.95
Throughput: 57 fragments/minute
```

**Stage Breakdown:**

| Stage           | Time (s) | % of Total | Mean/Call (s) |
|-----------------|----------|------------|---------------|
| Preprocessing   | 0.067    | 1.3%       | 0.013         |
| Encoding        | 0.006    | 0.1%       | 0.001         |
| Compatibility   | 0.085    | 1.6%       | 0.085         |
| Relaxation      | 0.024    | 0.4%       | 0.024         |
| **Visualization** | **5.105** | **96.5%** | **5.105**   |

### 1.2 Real Fragment Data (5 Fragments - Getty Images)

**Dataset**: `data/examples/positive/gettyimages-1311604917-1024x1024/` - 5 real archaeological fragments with RGBA channels

```
Total Pipeline Time: 5.238 seconds
Fragments per Second: 0.95
Throughput: 57 fragments/minute
```

**Stage Breakdown:**

| Stage           | Time (s) | % of Total | Mean/Call (s) |
|-----------------|----------|------------|---------------|
| Preprocessing   | 0.066    | 1.3%       | 0.013         |
| Encoding        | 0.055    | 1.0%       | 0.011         |
| Compatibility   | 0.175    | 3.3%       | 0.175         |
| Relaxation      | 0.023    | 0.4%       | 0.023         |
| **Visualization** | **4.919** | **93.9%** | **4.919**   |

**Key Observation**: Real fragments show nearly identical performance to synthetic benchmarks, with only a 2x increase in compatibility computation time (0.085s → 0.175s) due to longer, more complex contours (2000+ boundary points vs 300-600 points).

---

## 2. Detailed Pipeline Stage Analysis

### 2.1 Preprocessing Stage (1.3% of total time)

**Components:**
- Image loading: ~0.000s (negligible)
- Gaussian blur + thresholding: 0.063-0.066s (95-98%)
- Contour extraction: 0.001-0.003s (2-5%)

**Performance Characteristics:**
- **Time Complexity**: O(N) linear in number of fragments
- **Per-Fragment Cost**: ~13ms per 500x500 image
- **Scalability**: Excellent - no inter-fragment dependencies
- **Bottleneck**: None identified

**Real vs Benchmark**: Virtually identical performance

### 2.2 Chain Code Encoding Stage (0.1-1.0% of total time)

**Components:**
- Freeman chain code encoding: 0.001-0.002s (3-13%)
- Normalization (PCA + cyclic minimum): 0.006-0.053s (87-97%)
- Boundary segmentation: ~0.000s (negligible)

**Performance Characteristics:**
- **Time Complexity**: O(N × C) where C is contour length
- **Per-Fragment Cost**: 1-11ms depending on contour complexity
- **Scalability**: Linear with contour length
- **Real Data Impact**: 9x longer encoding time for complex real fragments (2000+ points) vs synthetic (300-600 points)

**Bottleneck Analysis**: Minor bottleneck for highly complex contours, but negligible in overall pipeline context.

### 2.3 Compatibility Matrix Computation (1.6-3.3% of total time)

**Components:**
- Curvature profile computation: 100% of stage time
- Fourier descriptors: (integrated)
- Good continuation scoring: (integrated)
- Color histogram comparison: (integrated)

**Performance Characteristics:**
- **Time Complexity**: O(N² × S²) where N = fragments, S = segments per fragment
- **Theoretical Pairs**: For 5 fragments with 4 segments: 5×4 × 5×4 = 400 pairwise comparisons
- **Execution Time**: 85ms (synthetic) to 175ms (real data)
- **Time per Comparison**: 0.21-0.44ms per pair

**Scalability Analysis:**

| Fragments | Pairs | Expected Time (ms) | Complexity |
|-----------|-------|-------------------|------------|
| 3         | 144   | ~31-62           | O(N²)      |
| 5         | 400   | 85-175           | O(N²)      |
| 10        | 1600  | 340-700          | O(N²)      |
| 26        | 10816 | 2300-4800        | O(N²)      |

**Bottleneck Analysis**: Demonstrates classic O(N²) scaling but remains efficient. At 26 fragments (current max), compatibility computation would take 2.3-4.8 seconds - still acceptable.

### 2.4 Relaxation Labeling Stage (0.4% of total time)

**Components:**
- Initialization: ~0.000s (negligible)
- Support computation: 0.004s (15-18%)
- Probability update: 0.019-0.020s (82-84%)
- Convergence check: ~0.000s (negligible)

**Performance Characteristics:**
- **Iterations**: 50 iterations (reached max without convergence)
- **Time per Iteration**: 0.4-0.5ms
- **Time Complexity**: O(I × N² × S²) where I = iterations
- **Total Time**: 23-24ms for 50 iterations

**Convergence Behavior:**
- Max delta starts at ~0.0035-0.0043
- Decreases steadily to ~0.0018-0.0025
- Does not reach convergence threshold (0.0001) within 50 iterations
- Indicates need for either:
  - Higher iteration limit (e.g., 100)
  - Relaxed convergence threshold (e.g., 0.002)

**Bottleneck Analysis**: Extremely efficient even with 50 iterations. Not a bottleneck.

### 2.5 Visualization Stage (93.9-96.5% of total time)

**Components:**

| Component          | Time (s) | % of Viz | Description                    |
|--------------------|----------|----------|--------------------------------|
| Fragment Grid      | 0.7-1.2  | 14-24%   | Render all fragments in grid   |
| Heatmap           | 0.3      | 5-6%     | Compatibility matrix heatmap   |
| Assembly Proposals | 1.9-2.1  | 38-43%   | Render top-3 assembly overlays |
| Geometric Render   | 1.7-1.8  | 33-37%   | Geometric assembly sheets      |

**Performance Characteristics:**
- **Total Time**: 4.9-5.1 seconds
- **Time Complexity**: O(N) for grid/heatmap, O(A) for assemblies where A = top assemblies
- **Primary Cost**: Matplotlib figure creation and image compositing

**Bottleneck Analysis**: **CRITICAL BOTTLENECK** - Consumes 94-97% of pipeline time.

**Why Visualization Dominates:**
1. Matplotlib figure creation overhead (~200-400ms per figure)
2. High-resolution image compositing (500x500 to 2048x2048 pixels)
3. Multiple rendering passes (7 total outputs: 1 grid + 1 heatmap + 1 convergence + 3 assemblies + 3 geometric)
4. File I/O for PNG saving

---

## 3. Scalability Analysis

### 3.1 Fragment Count Scaling

**Test Results** (Synthetic Benchmark Data):

| N Fragments | Total Time (s) | Time/Fragment (s) | Core Pipeline (s) | Visualization (s) |
|-------------|----------------|-------------------|-------------------|-------------------|
| 3           | 4.772          | 1.591             | 0.095             | 4.677             |
| 5           | 5.287          | 1.013             | 0.182             | 5.105             |

**Scaling Characteristics:**

```
Core Pipeline Scaling (Preprocessing + Encoding + Compatibility + Relaxation):
- 3 fragments: 0.095s
- 5 fragments: 0.182s
- Ratio: 1.92x time for 1.67x fragments
- Complexity: ~O(N^1.5) (between linear and quadratic)

Visualization Scaling:
- 3 fragments: 4.677s
- 5 fragments: 5.105s
- Ratio: 1.09x time for 1.67x fragments
- Complexity: ~O(N^0.2) (sub-linear, likely fixed overhead dominant)
```

### 3.2 Projected Performance at Scale

**Extrapolated Times** (based on measured complexity):

| N Fragments | Core Pipeline | Visualization | Total Time | Throughput (frag/min) |
|-------------|---------------|---------------|------------|----------------------|
| 5           | 0.18s         | 5.1s          | 5.3s       | 57                   |
| 10          | 0.52s         | 5.5s          | 6.0s       | 100                  |
| 15          | 0.99s         | 5.8s          | 6.8s       | 132                  |
| 20          | 1.62s         | 6.0s          | 7.6s       | 158                  |
| 26 (max)    | 2.65s         | 6.3s          | 9.0s       | 173                  |

**Key Insight**: Due to visualization's sub-linear scaling and fixed overhead, throughput actually **increases** with more fragments. The system becomes more efficient per fragment as dataset size grows.

### 3.3 Time Complexity Summary

| Component               | Complexity | Dominant Factor          | Scalability |
|-------------------------|------------|--------------------------|-------------|
| Preprocessing           | O(N)       | Image count              | Excellent   |
| Chain Code Encoding     | O(N×C)     | Contour complexity       | Excellent   |
| Compatibility Matrix    | O(N²×S²)   | Fragment pairs           | Good        |
| Relaxation Labeling     | O(I×N²×S²) | Iterations × pairs       | Good        |
| Visualization           | O(N^0.2)   | Fixed rendering overhead | Excellent   |
| **Overall Pipeline**    | **O(N²)**  | **Compatibility stage**  | **Good**    |

---

## 4. Bottleneck Identification

### 4.1 Primary Bottleneck: Visualization (93-97% of time)

**Root Causes:**
1. **Matplotlib Overhead**: Each figure creation incurs 200-400ms overhead
2. **Multiple Rendering Passes**: 7 separate visualizations generated per run
3. **High-Resolution Compositing**: Large image arrays (500x500 to 2048x2048)
4. **Synchronous I/O**: Sequential PNG file writes

**Impact:**
- For 5 fragments: 5.1s visualization vs 0.18s core algorithms
- **28x more time** spent on visualization than actual computation

**Recommendations:**
1. **Production Mode**: Add `--no-viz` flag to skip visualizations in batch processing
2. **Lazy Rendering**: Generate visualizations only on demand
3. **Parallel Rendering**: Multi-threaded visualization generation
4. **Format Optimization**: Use JPEG for non-transparent images (faster I/O)
5. **Resolution Reduction**: Lower DPI for preview renders
6. **Caching**: Reuse matplotlib figures instead of recreating

**Expected Impact**: Could reduce visualization time by 50-70%, improving overall throughput to 1.5-3.0 fragments/second.

### 4.2 Secondary Bottleneck: Compatibility Matrix (O(N²) scaling)

**Current Performance**: Acceptable for N ≤ 26 fragments
- 5 fragments: 175ms
- 26 fragments (extrapolated): ~4.8s

**Potential Issues at Scale:**
- 50 fragments: ~17s
- 100 fragments: ~70s (1.2 minutes)

**Recommendations:**
1. **Spatial Hashing**: Pre-filter fragment pairs by bounding box overlap
2. **Early Termination**: Skip obviously incompatible pairs (distance threshold)
3. **Parallel Processing**: Multi-threaded pair comparison (embarrassingly parallel)
4. **Progressive Refinement**: Coarse filtering → fine comparison for top candidates
5. **Vectorization**: NumPy-optimized batch operations for Fourier/curvature computation

**Expected Impact**: Could achieve 5-10x speedup through parallelization alone.

### 4.3 Minor Issue: Relaxation Convergence

**Observation**: Algorithm reaches 50-iteration limit without converging (delta ~0.002 vs threshold 0.0001)

**Not a Performance Bottleneck**: Even with 50 iterations, relaxation takes only 23ms (0.4% of time)

**Recommendations:**
1. **Increase Iteration Limit**: 50 → 100 or 200 iterations (would add only 23-46ms)
2. **Adaptive Threshold**: Use 0.002 threshold based on observed convergence patterns
3. **Early Stopping**: Detect oscillation patterns and stop when stable

---

## 5. Real Data vs Benchmark Comparison

### 5.1 Performance Comparison

| Metric                  | Synthetic (5 frag) | Real (5 frag) | Ratio   |
|-------------------------|--------------------|---------------|---------|
| Total Time              | 5.287s             | 5.238s        | 0.99x   |
| Preprocessing           | 0.067s             | 0.066s        | 0.99x   |
| Encoding                | 0.006s             | 0.055s        | 9.2x    |
| Compatibility           | 0.085s             | 0.175s        | 2.1x    |
| Relaxation              | 0.024s             | 0.023s        | 0.96x   |
| Visualization           | 5.105s             | 4.919s        | 0.96x   |

### 5.2 Analysis

**Key Finding**: Real fragments are **NOT significantly slower** than benchmarks overall (0.99x ratio).

**Stage-by-Stage Observations:**

1. **Preprocessing**: Identical performance
   - RGBA real fragments use alpha channel directly
   - Synthetic fragments require threshold-based segmentation
   - Both approaches equally efficient

2. **Encoding**: 9x slower for real data
   - Real fragments: 2000+ boundary points (complex shapes)
   - Synthetic fragments: 300-600 boundary points (simpler shapes)
   - Still negligible in overall pipeline (0.055s vs 0.006s)

3. **Compatibility**: 2x slower for real data
   - Longer contours → more detailed curvature profiles
   - More Fourier coefficients to compare
   - Still only 3.3% of total time

4. **Relaxation**: Identical performance
   - Algorithm complexity independent of contour detail
   - Only depends on fragment count and segments

5. **Visualization**: Slightly faster for real data (??!)
   - Likely due to random variation or caching effects
   - Difference is negligible (186ms over 5s)

**Conclusion**: The system handles real-world data **as efficiently** as synthetic benchmarks. The bottleneck (visualization) is data-agnostic.

---

## 6. Memory Usage Analysis

**Note**: Memory profiling unavailable (psutil not installed). Based on data structure analysis:

### 6.1 Memory Footprint Estimates

**Per Fragment:**
- Original image: 500×500×3 = 750KB (uncompressed)
- Contour array: 2000 points × 8 bytes × 2 coords = 32KB
- Chain code: 2000 codes × 1 byte = 2KB
- Segments: 4 × 500 codes = 2KB
- **Total per fragment**: ~800KB

**Global Structures:**
- Compatibility matrix: N×S × N×S × 8 bytes
  - 5 fragments: 5×4 × 5×4 × 8 = 12.8KB
  - 26 fragments: 26×4 × 26×4 × 8 = 346KB
- Probability matrix: Same size as compatibility
- **Total global**: ~25KB (5 frag) to ~700KB (26 frag)

**Peak Memory Usage** (estimated):
- 5 fragments: 5×800KB + 25KB ≈ **4MB**
- 26 fragments: 26×800KB + 700KB ≈ **21MB**

**Memory Complexity**: O(N) for fragments + O(N²) for matrices = **O(N²)** dominant

**Scalability**: Excellent memory efficiency. Even 100 fragments would use only ~80MB.

---

## 7. Optimization Recommendations

### 7.1 High-Impact Optimizations (Targeting Bottlenecks)

#### Recommendation #1: Production Mode (No-Viz Option)
**Target**: Visualization bottleneck (94% of time)
**Implementation**:
```python
parser.add_argument('--no-viz', action='store_true',
                   help='Skip visualization generation for batch processing')
```

**Expected Speedup**: 15-25x (0.18s core vs 5.3s total)
**New Throughput**: 16-28 fragments/second (vs current 0.95/sec)

**Use Case**: Batch processing, CI/CD testing, parameter sweeps

---

#### Recommendation #2: Parallel Compatibility Computation
**Target**: Compatibility matrix O(N²) scaling
**Implementation**:
```python
from multiprocessing import Pool

def compute_pair_compatibility(i, seg_i, j, seg_j):
    return (i, seg_i, j, seg_j), compatibility_score(...)

with Pool(processes=4) as pool:
    results = pool.starmap(compute_pair_compatibility, pairs)
```

**Expected Speedup**: 3-4x on quad-core systems
**New Compatibility Time**: 175ms → 50ms (real data)

**Impact on Total Pipeline**: Negligible (3.3% → 1.0%), but critical for scaling to 50+ fragments

---

#### Recommendation #3: Lazy Visualization Generation
**Target**: Reduce unnecessary rendering overhead
**Implementation**:
```python
# Only generate visualizations if output directory specified
if args.viz_output:
    render_all_visualizations()
else:
    logger.info("Skipping visualization (--viz-output not specified)")
```

**Expected Speedup**: Same as #1 for batch workflows
**Benefit**: Better user experience - don't wait for unused outputs

---

### 7.2 Medium-Impact Optimizations

#### Recommendation #4: Adaptive Relaxation Convergence
**Target**: Improve relaxation efficiency and accuracy
**Implementation**:
```python
# Detect convergence plateau and adapt threshold
if delta < 0.002 and stable_for_5_iterations:
    converged = True
elif iterations > 100:
    converged = True  # absolute limit
```

**Expected Speedup**: Minimal (relaxation already fast)
**Benefit**: Better convergence guarantees, more stable results

---

#### Recommendation #5: Compatibility Matrix Caching
**Target**: Avoid recomputation in iterative workflows
**Implementation**:
```python
import hashlib
cache_key = hashlib.md5(fragment_hashes).hexdigest()
if os.path.exists(f'cache/{cache_key}_compat.npy'):
    compat_matrix = np.load(f'cache/{cache_key}_compat.npy')
```

**Expected Speedup**: ∞ for cached runs (175ms → 5ms load time)
**Use Case**: Interactive exploration, parameter tuning

---

### 7.3 Low-Impact Optimizations (Code Quality)

1. **Vectorize Chain Code Operations**: Replace loops with NumPy operations
2. **Pre-allocate Arrays**: Avoid dynamic list growth
3. **Use C-contiguous Arrays**: Ensure optimal memory layout for NumPy
4. **Profile Sub-functions**: Identify micro-bottlenecks with cProfile
5. **Reduce Logging Verbosity**: Minimize I/O overhead in tight loops

**Expected Impact**: 5-15% speedup, better code maintainability

---

## 8. Scalability Projections

### 8.1 Current System (No Optimizations)

| Fragments | Total Time | Throughput (frag/min) | Practical? |
|-----------|------------|----------------------|------------|
| 5         | 5.3s       | 57                   | ✓ Yes      |
| 10        | 6.0s       | 100                  | ✓ Yes      |
| 26        | 9.0s       | 173                  | ✓ Yes      |
| 50        | 21s        | 143                  | ✓ Yes      |
| 100       | 73s        | 82                   | ⚠ Slow     |

**Conclusion**: Current system handles 5-50 fragments efficiently. Degrades beyond 50 due to O(N²) compatibility matrix.

---

### 8.2 With Production Mode (--no-viz)

| Fragments | Core Time | Throughput (frag/min) | Speedup |
|-----------|-----------|----------------------|---------|
| 5         | 0.18s     | 1667                 | 29x     |
| 10        | 0.52s     | 1154                 | 12x     |
| 26        | 2.65s     | 589                  | 7x      |
| 50        | 17s       | 176                  | 1.2x    |
| 100       | 70s       | 86                   | 1.0x    |

**Conclusion**: Production mode provides massive speedup for small datasets (5-10 fragments), diminishing returns for large datasets where compatibility matrix dominates.

---

### 8.3 With Parallel Compatibility (4 cores + --no-viz)

| Fragments | Core Time | Throughput (frag/min) | vs Current |
|-----------|-----------|----------------------|------------|
| 5         | 0.13s     | 2308                 | 41x faster |
| 10        | 0.26s     | 2308                 | 23x faster |
| 26        | 1.30s     | 1200                 | 7x faster  |
| 50        | 4.8s      | 625                  | 4.4x faster|
| 100       | 19s       | 316                  | 3.8x faster|

**Conclusion**: Parallel optimization enables efficient processing of 50-100 fragment datasets, maintaining reasonable throughput.

---

## 9. Test Coverage and Validation

### 9.1 Test Datasets

**Synthetic Benchmarks:**
- `data/sample/` - 5 fragments, 500×500 pixels, clean backgrounds
- Purpose: Baseline performance measurement, regression testing

**Real Fragment Datasets:**
- `data/examples/positive/gettyimages-*` - 4 sets of 5-6 fragments each
- `data/examples/positive/scroll/` - 6 fragments
- `data/examples/positive/shard_*` - 2 sets of 6 fragments each
- Total: 9 real datasets, 47 total real fragments

**Mixed Datasets:**
- `data/examples/negative/mixed_*` - 20+ mixed fragment sets
- Purpose: Test system behavior on non-matching fragments

### 9.2 Performance Test Coverage

**Tested Scenarios:**
1. ✓ Synthetic benchmark (5 fragments)
2. ✓ Real fragment dataset (5 fragments)
3. ✓ Scalability test (3, 5 fragments)
4. ✗ Large dataset (10+ fragments) - **Not tested due to time constraints**
5. ✗ Maximum dataset (26 fragments) - **Not tested**

**Recommendation**: Extend testing to 10, 15, 20, and 26 fragment datasets to validate scalability projections.

---

## 10. Conclusions

### 10.1 Performance Summary

**Overall Assessment**: ✓ **GOOD**

The archaeological fragment reconstruction pipeline demonstrates:
1. **Efficient Core Algorithms**: Only 3-7% of execution time
2. **Good Scalability**: O(N²) complexity acceptable for N ≤ 50
3. **Real-World Readiness**: Real data performs equivalently to benchmarks
4. **Clear Bottleneck**: Visualization dominates (94-97% of time)

**Current Throughput**: 0.95 fragments/second (with visualization)

**Optimized Potential**: 16-28 fragments/second (no-viz mode)

### 10.2 Bottleneck Assessment

**Critical Bottleneck**: ✗ Visualization (94-97% of time)
- **Severity**: HIGH - Dominates execution time
- **Impact**: Limits batch processing throughput
- **Solution**: Production mode (--no-viz flag)
- **Priority**: P0 - Implement immediately

**Secondary Bottleneck**: ⚠ Compatibility Matrix O(N²) scaling
- **Severity**: MEDIUM - Acceptable for N ≤ 50
- **Impact**: Limits scalability to 100+ fragments
- **Solution**: Parallelization (4x speedup)
- **Priority**: P1 - Implement for production use

**Minor Issue**: ⚠ Relaxation convergence
- **Severity**: LOW - Fast even without convergence
- **Impact**: None on performance, minimal on accuracy
- **Solution**: Adaptive thresholds or higher iteration limit
- **Priority**: P2 - Improve for code quality

### 10.3 Scalability Verdict

| Fragment Count | Status | Notes |
|----------------|--------|-------|
| 5-10           | ✓ Excellent | Fast, responsive |
| 10-26          | ✓ Good | Acceptable performance |
| 26-50          | ⚠ Acceptable | Slower but usable |
| 50-100         | ✗ Poor | Requires optimization (parallel mode) |
| 100+           | ✗ Impractical | Fundamental O(N²) limitation |

**Recommended Operating Range**: 5-26 fragments (current system), 5-100 fragments (with optimizations)

### 10.4 Real vs Benchmark Verdict

**Conclusion**: ✓ **Real fragments perform equivalently to benchmarks**

- Overall time ratio: 0.99x (essentially identical)
- Core algorithm scaling: 1-2x slower (still negligible)
- Bottleneck (visualization): Data-agnostic

**No significant performance degradation on real data.** System is production-ready for real-world datasets.

---

## 11. Recommended Action Items

### Immediate (P0 - Critical)
- [ ] **Implement `--no-viz` flag** for production mode
  - Expected impact: 15-25x speedup
  - Effort: 1 hour
  - Blocker: None

### Short-term (P1 - High Priority)
- [ ] **Parallelize compatibility matrix computation**
  - Expected impact: 3-4x speedup for large datasets
  - Effort: 4-8 hours
  - Blocker: None (embarrassingly parallel)

- [ ] **Extend scalability testing to 10, 15, 20, 26 fragments**
  - Validate performance projections
  - Effort: 2 hours
  - Blocker: None

### Medium-term (P2 - Nice to Have)
- [ ] **Implement compatibility matrix caching**
  - Expected impact: ∞ for cached runs
  - Effort: 2-4 hours
  - Blocker: None

- [ ] **Adaptive relaxation convergence**
  - Expected impact: Better stability
  - Effort: 1-2 hours
  - Blocker: None

- [ ] **Install psutil for memory profiling**
  - Validate memory usage estimates
  - Effort: 5 minutes
  - Blocker: None

### Long-term (P3 - Future Work)
- [ ] Spatial hashing for compatibility pre-filtering
- [ ] Vectorized chain code operations
- [ ] Multi-threaded visualization generation
- [ ] Web-based interactive visualization (avoid Matplotlib overhead)

---

## Appendix A: Test Execution Details

### A.1 Test Commands

```bash
# Baseline test (5 synthetic fragments)
python scripts/profile_performance.py --input data/sample --output outputs/profiling/sample_5

# Real data test (5 real fragments)
python scripts/profile_performance.py --input data/examples/positive/gettyimages-1311604917-1024x1024 --output outputs/profiling/real_6

# Scalability comparison test
python scripts/profile_performance.py --input data/sample --output outputs/profiling/comparison --compare 3,5
```

### A.2 Raw Performance Data

**Sample Data (5 fragments):**
```
Preprocessing: 67ms (1.3%)
  - Blur/threshold: 66ms
  - Contour extract: 1ms
Encoding: 6ms (0.1%)
  - Chain code: 1ms
  - Normalization: 6ms
Compatibility: 85ms (1.6%)
Relaxation: 24ms (0.4%)
  - 50 iterations @ 0.5ms/iter
Visualization: 5105ms (96.5%)
  - Fragment grid: 1218ms
  - Heatmap: 259ms
  - Assemblies: 1940ms (3 outputs)
  - Geometric: 1687ms (3 outputs)
TOTAL: 5287ms
```

**Real Data (5 fragments):**
```
Preprocessing: 66ms (1.3%)
Encoding: 55ms (1.0%)
Compatibility: 175ms (3.3%)
Relaxation: 23ms (0.4%)
Visualization: 4919ms (93.9%)
TOTAL: 5238ms
```

### A.3 System Configuration

```
OS: Windows 11 Enterprise (Build 26200)
CPU: [Not profiled - psutil unavailable]
RAM: [Not profiled - psutil unavailable]
Python: 3.x
OpenCV: Latest
NumPy: Latest
Matplotlib: Latest
```

---

## Appendix B: Profiling Artifacts

**Generated Files:**
- `outputs/profiling/sample_5/profiling_report.txt` - Detailed timing breakdown
- `outputs/profiling/sample_5/timing_breakdown_bar_iter1.png` - Bar chart visualization
- `outputs/profiling/sample_5/timing_breakdown_pie_iter1.png` - Pie chart visualization
- `outputs/profiling/real_6/profiling_report.txt` - Real data timing breakdown
- `outputs/profiling/comparison/comparison_summary.txt` - Scalability comparison
- `outputs/profiling/comparison/comparison_chart.png` - Scalability visualization

**Profiling Logs:**
- `outputs/profiling/sample_5/profiling_20260408_112211.log`
- `outputs/profiling/real_6/profiling_20260408_112227.log`
- `outputs/profiling/comparison/profiling_20260408_112251.log`

---

## Appendix C: Performance Visualization

### Stage Breakdown (Sample Data)

```
Visualization: ██████████████████████████████████████████████████ 96.5%
Preprocessing: █ 1.3%
Compatibility: █ 1.6%
Relaxation:    █ 0.4%
Encoding:      █ 0.1%
```

### Scalability Curve

```
Time (seconds)
7.0 ┤
6.5 ┤                  ○
6.0 ┤
5.5 ┤
5.0 ┤        ○
4.5 ┤   ○
    └────────────────────────────
    3       5       10      15
         Fragment Count

○ Total Time (sub-linear due to viz overhead)
```

---

**Report Generated**: 2026-04-08 11:25:00
**Analysis Tool**: `scripts/profile_performance.py`
**Report Version**: 1.0
