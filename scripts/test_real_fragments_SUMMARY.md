# Test Real Fragments - Quick Reference

## What It Does

Tests the archaeological fragment reconstruction pipeline on **real-world images** and compares performance against **synthetic benchmarks**.

## Key Features

1. **Preprocessing Validation**
   - Tests each fragment through preprocessing pipeline
   - Reports success/failure rates
   - Identifies problematic images

2. **Pair Testing**
   - **Positive cases**: Fragments from SAME source (should match)
   - **Negative cases**: Fragments from DIFFERENT sources (should reject)
   - Tests geometric + color-based matching

3. **Comprehensive Reporting**
   - JSON (machine-readable)
   - Markdown (human-readable)
   - 4 visualizations (charts and plots)

## Quick Commands

```bash
# Basic test (default paths)
python scripts/test_real_fragments.py

# Custom paths
python scripts/test_real_fragments.py --input data/my_fragments --output outputs/my_test

# Compare with benchmark
python scripts/test_real_fragments.py --compare-benchmark

# Verbose debug mode
python scripts/test_real_fragments.py --verbose
```

## Expected Directory Structure

```
data/raw/real_fragments_validated/
├── source_a/           # First artifact/collection
│   ├── frag_01.jpg
│   ├── frag_02.jpg     # From same artifact as frag_01
│   └── frag_03.jpg     # From same artifact as frag_01, frag_02
└── source_b/           # Second artifact/collection
    ├── frag_04.jpg
    └── frag_05.jpg     # From same artifact as frag_04
```

**Result**: Creates positive pairs within each source, negative pairs across sources.

## Output Files

```
outputs/real_fragment_analysis/
├── real_fragment_test_report.md              # Human-readable report
├── real_fragment_test_report.json            # Machine-readable results
├── preprocessing_comparison.png              # Success rate chart
├── accuracy_comparison.png                   # Accuracy metrics
├── confidence_distribution.png               # Score histograms
├── color_vs_geometric.png                    # 2D scatter plot
└── test_real_fragments_YYYYMMDD_HHMMSS.log  # Detailed log
```

## Success Criteria

| Metric | Target | Benchmark (Synthetic) | Typical Real Performance |
|--------|--------|----------------------|--------------------------|
| Preprocessing Success | ≥80% | 100% | 70-90% |
| Positive Accuracy (TP) | ≥70% | 100% | 60-85% |
| Negative Accuracy (TN) | ≥70% | 100% | 70-95% |
| Overall Accuracy | ≥70% | 100% | 65-90% |

## Interpreting Results

### High Preprocessing Failures (< 80%)
**Problem**: Images can't be preprocessed (no contour extracted)

**Causes**:
- Poor image quality (low resolution, blur)
- Complex backgrounds not removed
- Fragment too small in image

**Solutions**:
- Improve image capture (better lighting, higher resolution)
- Manual background removal
- Adjust preprocessing parameters (Canny thresholds)

### Low Positive Accuracy (< 70%)
**Problem**: Fragments from same source not matched (false negatives)

**Causes**:
- Real fragment edges too damaged/eroded
- Preprocessing losing edge details
- Thresholds too strict

**Solutions**:
- Relax `MATCH_SCORE_THRESHOLD` (0.55 → 0.45)
- Improve preprocessing to preserve edges
- Add texture/appearance features

### Low Negative Accuracy (< 70%)
**Problem**: Fragments from different sources incorrectly matched (false positives)

**Causes**:
- Accidental geometric similarity
- Color filtering not discriminative
- Thresholds too permissive

**Solutions**:
- Tighten `MATCH_SCORE_THRESHOLD` (0.55 → 0.65)
- Improve color histogram comparison
- Add more appearance features

## Troubleshooting

### "No fragments found"
```bash
# Check directory exists and has images
ls data/raw/real_fragments_validated/

# Should show subdirectories or image files
```

### "All preprocessing failed"
```bash
# Test single image manually
python -c "
import sys; sys.path.insert(0, 'src')
from preprocessing import preprocess_fragment
img, contour = preprocess_fragment('path/to/fragment.jpg')
print(f'{len(contour)} contour points extracted')
"
```

### "All pairs no match"
```bash
# Run with verbose to see confidence scores
python scripts/test_real_fragments.py --verbose

# Check if scores are close to threshold
# Consider relaxing threshold if scores are 0.45-0.54
```

## Related Scripts

- `download_real_fragments.py` - Download real fragment images
- `analyze_benchmark_results.py` - Analyze benchmark test logs
- `generate_benchmark_data.py` - Create synthetic test data

## Full Documentation

- **Detailed README**: `scripts/README_test_real_fragments.md`
- **Usage Examples**: `scripts/USAGE_test_real_fragments.md`

---

**Status**: Ready to use (tested on Python 3.11, Windows 11)

**Last Updated**: 2026-04-08
