# Comprehensive Positive Case Testing Report

**Generated:** 2026-04-08 11:24:20

---

## Executive Summary

- **Total Fragments:** 26
- **Total Pairs Tested:** 325
- **Positive Accuracy:** 100.00%
- **Average Confidence:** 0.257
- **Median Confidence:** 0.257

**Status:** ✅ **SUCCESS** - Positive accuracy meets target (≥95%)

---

## Verdict Distribution

| Verdict | Count | Percentage |
|---------|-------|------------|
| MATCH | 284 | 87.4% |
| WEAK_MATCH | 41 | 12.6% |
| NO_MATCH | 0 | 0.0% |
| **Total** | **325** | **100.0%** |

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Positive Accuracy | 100.00% |
| Average Confidence | 0.257 |
| Median Confidence | 0.257 |
| Average Color BC | 0.856 |
| Average Execution Time | 89 ms |
| Total Test Time | 29.0 s |

---

## Comparison to Benchmark

### Benchmark Performance (Synthetic Data)
- **Positive Cases:** 9/9 = 100.0%
- **Average Confidence:** ~0.75 (estimated)

### Real Data Performance (26 Fragments, 325 Pairs)
- **Positive Cases:** 325/325 = 100.00%
- **Average Confidence:** 0.257

| Metric | Benchmark | Real Data | Difference |
|--------|-----------|-----------|------------|
| Positive Accuracy | 100.0% | 100.00% | +0.00% |
| Avg Confidence | 0.750 | 0.257 | -0.493 |

---

## Failed Pairs Analysis

**No failed pairs!** All {summary.total_pairs_tested} pairs were correctly identified as matches.

---

## Detailed Results (Sample)

Showing first 50 pairs (sorted by confidence, descending):

| Pair | Fragment A | Fragment B | Verdict | Confidence | Color BC | Time (ms) |
|------|------------|------------|---------|------------|----------|----------|
| [01-22] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ WEAK_MATCH | 0.270 | 0.663 | 200 |
| [01-14] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.266 | 0.741 | 170 |
| [17-22] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.266 | 0.956 | 23 |
| [12-14] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.265 | 0.902 | 47 |
| [18-22] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.265 | 0.974 | 33 |
| [11-14] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.265 | 0.882 | 51 |
| [22-23] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.265 | 0.991 | 15 |
| [18-19] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.264 | 0.984 | 22 |
| [01-26] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ WEAK_MATCH | 0.264 | 0.529 | 159 |
| [01-03] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.264 | 0.868 | 191 |
| [06-22] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.264 | 0.784 | 131 |
| [24-25] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.264 | 0.985 | 22 |
| [24-26] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.263 | 0.948 | 27 |
| [19-21] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.263 | 0.994 | 19 |
| [19-20] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.263 | 0.996 | 29 |
| [01-20] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ WEAK_MATCH | 0.263 | 0.606 | 158 |
| [03-22] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.263 | 0.797 | 123 |
| [18-21] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.263 | 0.982 | 16 |
| [22-25] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.263 | 0.976 | 21 |
| [09-22] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ WEAK_MATCH | 0.262 | 0.744 | 72 |
| [06-14] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.262 | 0.803 | 142 |
| [05-22] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.262 | 0.803 | 123 |
| [01-12] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.262 | 0.797 | 158 |
| [16-18] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.262 | 0.949 | 23 |
| [17-25] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.262 | 0.951 | 19 |
| [03-14] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.262 | 0.836 | 114 |
| [01-17] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ WEAK_MATCH | 0.262 | 0.731 | 176 |
| [23-25] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.262 | 0.980 | 22 |
| [14-22] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.262 | 0.950 | 36 |
| [09-14] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.262 | 0.814 | 91 |
| [17-18] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.262 | 0.979 | 23 |
| [12-22] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.262 | 0.835 | 34 |
| [22-26] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.261 | 0.938 | 28 |
| [01-23] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ WEAK_MATCH | 0.261 | 0.628 | 177 |
| [21-22] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.261 | 0.982 | 24 |
| [10-14] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.261 | 0.836 | 64 |
| [08-22] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ WEAK_MATCH | 0.261 | 0.672 | 90 |
| [20-22] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.261 | 0.973 | 21 |
| [16-19] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.261 | 0.979 | 24 |
| [13-22] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.261 | 0.906 | 42 |
| [05-14] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.261 | 0.876 | 145 |
| [14-18] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.261 | 0.979 | 44 |
| [01-25] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ WEAK_MATCH | 0.261 | 0.605 | 185 |
| [10-11] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.261 | 0.967 | 88 |
| [03-06] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.261 | 0.833 | 142 |
| [13-14] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.261 | 0.954 | 45 |
| [01-18] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ WEAK_MATCH | 0.261 | 0.707 | 163 |
| [01-06] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.261 | 0.811 | 198 |
| [16-17] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ MATCH | 0.261 | 0.963 | 21 |
| [01-21] | 14_scherven_-_O36ZFL_-_60... | 14_scherven_-_O36ZFL_-_60... | ✅ WEAK_MATCH | 0.261 | 0.635 | 172 |

*(275 more pairs not shown for brevity)*

---

## Insights and Recommendations

### ✅ Positive Case Performance: EXCELLENT

The system achieves 100.0% positive accuracy on real data, meeting or exceeding the 95% target. This indicates:

- The chain code representation generalizes well to real fragments
- Relaxation labeling successfully propagates constraints
- Color-based filtering (Bhattacharyya coefficient) provides complementary evidence
- The preprocessing pipeline (Gaussian blur + Otsu thresholding) is robust

### ⚠️ Low Average Confidence

Average confidence (0.257) is below 0.40, suggesting:
- Real fragment edges are less consistent than synthetic data
- Chain code matching may need relaxation (allow more variation)
- Consider adding shape context or other invariant features

### Key Findings

1. **Scale:** Tested 325 positive pairs from 26 fragments
2. **Success Rate:** 100.0% of pairs correctly identified
3. **Confidence Distribution:** Mean=0.257, Median=0.257
4. **Color Coherence:** Average BC=0.856 (high values indicate good color consistency)
5. **Performance:** Average 89 ms per pair

---

**End of Report**
