# Negative Case Testing: Benchmark Comparison

## Test Overview

**Mission:** Measure false positive rate when comparing fragments from different sources (cross-source rejection testing).

**Benchmark Reference:** Previous testing showed 0/36 false positives = 0% negative accuracy issues.

---

## Results Summary

### Test Configuration

| Parameter | Value |
|-----------|-------|
| Test Date | 2026-04-08 |
| Sources Tested | 2 (british_museum, wikimedia_processed) |
| Total Fragments | 27 (1 + 26) |
| Cross-Source Pairs | 26 |
| Test Type | ALL negative cases (different sources) |

### Performance Metrics

| Metric | Benchmark | Current System | Delta |
|--------|-----------|----------------|-------|
| **True Negative Rate** | 100% (36/36) | **0.00% (0/26)** | **-100.0%** |
| **False Positive Rate** | 0% (0/36) | **100.00% (26/26)** | **+100.0%** |
| **Correctly Rejected** | 36 | 0 | -36 |
| **Incorrectly Matched** | 0 | 26 | +26 |

### Verdict Distribution

| Verdict | Count | Percentage |
|---------|-------|------------|
| MATCH | 25 | 96.2% |
| WEAK_MATCH | 1 | 3.8% |
| NO_MATCH | 0 | 0.0% |

**Expected:** 0 MATCH, 0 WEAK_MATCH, 26 NO_MATCH

---

## Detailed Analysis

### Confidence Scores

| Statistic | Value |
|-----------|-------|
| Mean | 0.2567 |
| Median | 0.2560 |
| Min | 0.2525 |
| Max | 0.2666 |
| Std Dev | 0.0035 |

**Note:** Low confidence (0.25) but high verdicts (MATCH) indicates verdicts come from raw compatibility scores, not confidence.

### Color Similarity (Bhattacharyya Coefficient)

| Statistic | Value |
|-----------|-------|
| Mean | 0.8560 |
| Median | 0.8630 |
| Min | 0.7343 |
| Max | 0.9576 |
| Std Dev | 0.0564 |

**Critical Finding:** High color BC (>0.73) means fragments look similar despite being from different sources. This defeats the color penalty mechanism.

---

## Root Cause: Color Penalty Ineffectiveness

### Current Formula
```
score_final = score_geometric * (1 - COLOR_PENALTY_WEIGHT * (1 - color_BC))
```

### Math Example (Typical Case)

```
Given:
- COLOR_PENALTY_WEIGHT = 0.80
- color_BC = 0.86 (typical in our data)
- score_geometric = 0.70 (moderate geometric similarity)

Calculation:
penalty = COLOR_PENALTY_WEIGHT * (1 - color_BC)
        = 0.80 * (1 - 0.86)
        = 0.80 * 0.14
        = 0.112

score_final = score_geometric * (1 - penalty)
            = 0.70 * (1 - 0.112)
            = 0.70 * 0.888
            = 0.622

Verdict: 0.622 > 0.55 (MATCH_SCORE_THRESHOLD)
Result: MATCH ✗ (should be NO_MATCH)
```

### Why High Color BC?

Both sources contain similar brownish pottery sherds:
- Same archaeological period
- Same clay composition
- Same firing technique
- Similar surface weathering

**Lesson:** Color similarity alone cannot distinguish different pottery vessels.

---

## Impact Analysis

### Comparison Table

| Aspect | Benchmark Expectation | Reality | Impact |
|--------|----------------------|---------|--------|
| **Rejection Rate** | 100% | 0% | System accepts all cross-source pairs |
| **Color Filtering** | Effective | Ineffective | High BC defeats penalty |
| **Threshold** | Appropriate | Too low | 0.55 threshold too permissive |
| **Production Ready** | Yes | **NO** | Critical recalibration needed |

### Failure Mode

```
Cross-Source Pair Flow:
1. Preprocessing ✓ (both fragments processed successfully)
2. Color Comparison → BC = 0.86 (high similarity)
3. Color Penalty → 11.2% reduction (weak)
4. Geometric Comparison → score = 0.70
5. Final Score → 0.622
6. Threshold Check → 0.622 > 0.55
7. Verdict → MATCH ✗

Expected Flow:
1-4. Same as above
5. Final Score → 0.622
6. Threshold Check → 0.622 < 0.75 (proposed)
7. Verdict → NO_MATCH ✓
```

---

## Recommendations: Fixing the Gap

### Gap Analysis

| Issue | Current | Target | Approach |
|-------|---------|--------|----------|
| False Positive Rate | 100% | <5% | Increase thresholds + penalty |
| MATCH Threshold | 0.55 | 0.70-0.75 | Conservative matching |
| Color Penalty | Weak (11%) | Strong (40%+) | Exponential formula |
| BC Threshold | None | 0.70-0.75 | Pre-filter |

### Recommended Solution (Multi-Layer Defense)

**Layer 1: Hard Color Filter**
```python
if color_BC < 0.70:
    return 0.0  # Immediate rejection
```

**Layer 2: Exponential Penalty**
```python
score_final = score_geometric * pow(color_BC, 3.0)
# With BC=0.86: 0.86³ = 0.636 (36% penalty)
```

**Layer 3: Raised Thresholds**
```python
MATCH_SCORE_THRESHOLD = 0.70  # was 0.55
WEAK_MATCH_SCORE_THRESHOLD = 0.55  # was 0.35
```

**Expected Outcome:**
```
With BC=0.86, geom=0.70:
score_final = 0.70 * 0.86³ = 0.445
0.445 < 0.70 → NO_MATCH ✓

False Positive Rate: 100% → <5%
True Negative Rate: 0% → >95%
```

---

## Validation Plan

### Phase 1: Negative Case Revalidation
**Rerun this test with updated configuration**
- Target: >95% true negative rate (<2 false positives out of 26)
- Metric: False positive rate drops from 100% to <5%

### Phase 2: Positive Case Testing
**Test on same-source pairs**
- Use 26 wikimedia_processed fragments
- Create adjacent pairs from same artifact
- Target: >80% true positive rate

### Phase 3: ROC Analysis
**Find optimal operating point**
- Sweep thresholds: [0.60, 0.65, 0.70, 0.75, 0.80]
- Sweep COLOR_POWER: [1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
- Plot ROC curve (FPR vs TPR)
- Choose configuration that balances both

---

## Conclusion

### Current Status
❌ **CRITICAL FAILURE:** System cannot distinguish cross-source fragments when they have similar appearance.

### Gap to Benchmark
- **-100 percentage points** on true negative rate
- **+100 percentage points** on false positive rate
- **0/26 correct rejections** (expected 26/26)

### Required Actions
1. **Immediate:** Implement threshold and penalty changes
2. **Validation:** Rerun negative + positive case tests
3. **Optimization:** Parameter sweep for best balance
4. **Deployment:** Update production configuration with validated settings

### Time Estimate
- Implementation: 2-4 hours
- Validation: 2-3 hours
- Documentation: 1 hour
- **Total: 5-8 hours**

---

## Files and Artifacts

All test outputs are in: `C:/Users/I763940/icbv-fragment-reconstruction/outputs/testing/`

**Reports:**
- `negative_case_analysis.md` - Detailed analysis with recommendations
- `negative_case_analysis.json` - Machine-readable test results
- `COMPREHENSIVE_NEGATIVE_CASE_REPORT.md` - Full technical documentation
- `BENCHMARK_COMPARISON.md` - This file
- `QUICK_SUMMARY.md` - Executive summary

**Visualizations:**
- `negative_case_performance.png` - TN vs FP rates
- `confidence_distribution.png` - Score distributions
- `color_bc_distribution.png` - Color similarity analysis
- `color_vs_geometric_scatter.png` - 2D feature space
- `verdict_distribution.png` - Verdict breakdown

**Code:**
- `scripts/test_negative_cases.py` - Test harness (858 lines)

---

*Report Generated: 2026-04-08*
*Test Execution Time: ~5 seconds*
*Analysis Time: ~15 minutes*
*Total Pairs Tested: 26 (all cross-source)*
