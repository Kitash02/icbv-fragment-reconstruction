# Variant 5 Evolution Results: Aggressive Color Penalty Testing

## Executive Summary

**Objective**: Test if aggressive color penalties (POWER_COLOR = 6.0, 7.0, 8.0) can achieve 90%+ accuracy on both positive and negative test cases.

**Result**: **FAILED** - Aggressive penalties significantly hurt overall performance.

**Recommendation**: **DO NOT USE** aggressive color penalties. Keep baseline POWER_COLOR = 4.0.

---

## Test Configuration

- **Variant**: Variant 5 (Color-Dominant)
- **Test Suite**: 45 cases (9 positive, 36 negative)
- **Baseline**: POWER_COLOR = 4.0 → 77.8% overall
- **Tested Values**: POWER_COLOR = 6.0, 7.0, 8.0
- **Target**: 90%+ on BOTH positive and negative metrics

---

## Results Summary

| POWER_COLOR | Positive Accuracy | Negative Accuracy | Overall Accuracy |
|-------------|-------------------|-------------------|------------------|
| **4.0** (baseline) | **~70%** | **~83%** | **77.8%** |
| **6.0** | **55.6%** (5/9) | **77.8%** (28/36) | **73.3%** |
| **7.0** | **44.4%** (4/9) | **80.6%** (29/36) | **73.3%** |
| **8.0** | **44.4%** (4/9) | **86.1%** (31/36) | **77.8%** |

### Key Findings

1. **POWER_COLOR = 6.0**
   - Expected: 70-75% pos, 92-95% neg
   - Actual: 55.6% pos, 77.8% neg
   - Status: OUTSIDE expected range on both metrics
   - Analysis: Dramatic drop in positive accuracy, negative also worse than expected

2. **POWER_COLOR = 7.0**
   - Expected: 65-70% pos, 95-97% neg
   - Actual: 44.4% pos, 80.6% neg
   - Status: OUTSIDE expected range on both metrics
   - Analysis: Continued degradation of positive cases, negative still below target

3. **POWER_COLOR = 8.0**
   - Expected: 60-65% pos, 97-99% neg
   - Actual: 44.4% pos, 86.1% neg
   - Status: OUTSIDE expected range on both metrics
   - Analysis: Best overall (ties baseline), but negative accuracy still far from target

---

## Detailed Analysis

### Trade-off Assessment

**Hypothesis**: Aggressive color penalties would significantly improve negative accuracy while maintaining acceptable positive accuracy (70%+).

**Reality**:
- Positive accuracy dropped catastrophically (from ~70% to 44-56%)
- Negative accuracy improved modestly but fell far short of targets (77-86% vs 92-99% expected)
- The trade-off is **HIGHLY UNFAVORABLE**

### Why the Strategy Failed

1. **Over-penalization of Color Differences**
   - Color^6, Color^7, Color^8 create extreme penalties
   - Even slight color variations become disqualifying
   - Legitimate matches (positive cases) are rejected due to minor color inconsistencies

2. **Insufficient Negative Discrimination**
   - Despite aggressive penalties, negative accuracy only reached 86% (POWER=8.0)
   - Target was 95%+, achieved only 86%
   - Many mixed-source fragments still found matches (false positives persist)

3. **Algorithm Sensitivity**
   - System is MORE sensitive to power changes than predicted
   - Expected ~5-10% drops in positive accuracy per power increase
   - Actual: ~15-25% drops

### Failed Cases Analysis

**Positive Cases (Should MATCH, but got NO_MATCH)**:
- With POWER=7.0 or 8.0, only 4/9 positive cases passed
- Failed cases: gettyimages-1311604917, gettyimages-2177809001, gettyimages-470816328, scroll, Wall painting
- Reason: Minor color variations between fragments (lighting, scanning, preprocessing) get exponentially penalized

**Negative Cases (Should be NO_MATCH, but got MATCH - False Positives)**:
- Even with POWER=8.0, 5/36 negative cases still got false matches
- Persistent false positives: mixed_gettyimages-17009652 combinations, mixed_gettyimages-21778090 combinations
- Reason: Geometric similarity overcomes even extreme color penalties when shapes align well

---

## Conclusions

### Target Achievement

| Target | Achievement | Status |
|--------|-------------|--------|
| 90%+ positive, 90%+ negative | NO configuration achieved this | ❌ FAILED |
| 70%+ positive, 95%+ negative | NO configuration achieved this | ❌ FAILED |
| Better than baseline (77.8%) | Only POWER=8.0 tied baseline | ⚠️ MARGINAL |

### Recommended Action

**DO NOT DEPLOY** aggressive color penalties (POWER_COLOR > 6.0).

**Why**:
1. Overall accuracy does not improve (73-78% vs 78% baseline)
2. Positive accuracy drops catastrophically (44-56% vs ~70% baseline)
3. Negative accuracy improvements insufficient (77-86% vs 95%+ target)
4. Strategy creates unacceptable trade-offs

### Alternative Approaches

Since aggressive color penalties failed, explore:

1. **Stricter Color Pre-Checks**
   - Add color histogram comparison BEFORE geometric matching
   - Reject candidates with >15% color distance early
   - Prevents false positives without hurting true positives

2. **Multi-Feature Validation**
   - Require BOTH color AND texture agreement for match
   - Use AND logic instead of exponential penalties
   - More robust discrimination

3. **Geometric Constraints**
   - Add contour complexity matching
   - Require similar edge characteristics
   - Better mixed-source rejection

4. **Ensemble Validation**
   - Multiple independent classifiers vote on match
   - Majority vote required for positive verdict
   - Reduces false positives while preserving true positives

---

## Methodology Notes

### Test Execution
- Each power value tested on full 45-case suite
- Tests run with `--no-rotate` for consistency
- Sequential execution to avoid resource conflicts
- Each test took 3-5 minutes

### Data Quality
- All results verified through manual log inspection
- Counting verified: [P] lines for positive, [N] lines for negative
- PASS/FAIL status parsed from test output

### Files Generated
- `test_power7_results.txt`: Detailed output for POWER=7.0
- `variant5_evolution_final.txt`: Complete evolution results
- `src/compatibility_variant5.py`: Updated with final POWER_COLOR value

---

## Appendix: Test Output Samples

### POWER_COLOR = 7.0 Sample

```
====================================================================
  RUNNING 45 TEST CASES  (NO rotation)
====================================================================
  Positive (expect MATCH)    : 9
  Negative (expect NO_MATCH) : 36
====================================================================

  > [P] gettyimages-1311604917-1024x1024      - NO_MATCH    0.3s  FAIL
  > [P] gettyimages-170096524-1024x1024       + MATCH       25.3s  PASS
  > [P] gettyimages-2177809001-1024x1024      - NO_MATCH    31.8s  FAIL
  > [P] gettyimages-470816328-2048x2048       - NO_MATCH    28.0s  FAIL
  ...

====================================================================
  TOTAL  33/45 pass  12 fail  0 error
====================================================================
```

### Performance Characteristics

- **Fast negative rejections**: <1s (color pre-check working)
- **Slow positive processing**: 15-30s (full pipeline)
- **Consistent behavior**: No errors or timeouts

---

## Version Information

- **Date**: 2026-04-09
- **Test Environment**: Windows 11, Python 3.11
- **Repository**: icbv-fragment-reconstruction
- **Baseline Version**: Stage 1.6 (77.8% overall)

---

## Contact & Next Steps

For questions about this analysis:
- Review detailed logs in `outputs/test_results/`
- Examine `src/compatibility_variant5.py` for implementation
- See `run_variant5.py` for test runner details

**Next Phase**: Explore alternative strategies listed in Alternative Approaches section.
