# Comprehensive Negative Case Testing Report
## Cross-Source Fragment Rejection Analysis

**Generated:** 2026-04-08
**Mission:** Measure false positive rate on real data (cross-source rejection)
**Status:** CRITICAL FINDINGS - 100% FALSE POSITIVE RATE

---

## Executive Summary

### Test Objective
Test the system's ability to reject fragment pairs from different archaeological sources (negative cases). These pairs should be rejected as they cannot physically match.

### Test Configuration
- **Sources:** 2 (british_museum, wikimedia_processed)
- **Fragments Total:** 27 (1 from british_museum, 26 from wikimedia_processed)
- **Cross-Source Pairs Tested:** 26
- **Expected Result:** 0% matches (all should be rejected)

### Critical Results
- **True Negative Rate:** 0.00% (0/26 correctly rejected)
- **False Positive Rate:** 100.00% (26/26 incorrectly matched)
- **Verdict Distribution:** 25 MATCH, 1 WEAK_MATCH, 0 NO_MATCH
- **Average Confidence:** 0.2567 (LOW - but irrelevant to verdict)
- **Average Color BC:** 0.8560 (HIGH - fragments look similar!)

### Comparison to Benchmark
| Metric | Expected | Actual | Gap |
|--------|----------|--------|-----|
| True Negative Rate | 100% | 0% | **-100%** |
| False Positive Rate | 0% | 100% | **+100%** |
| Correctly Rejected | 26/26 | 0/26 | **0/26** |

**VERDICT:** System FAILS to reject cross-source pairs. Current configuration is NOT production-ready for fragment matching.

---

## Detailed Test Results

### Data Collection Summary

| Source | Fragments | Preprocessed | Failed |
|--------|-----------|--------------|--------|
| british_museum | 1 | 1 | 0 |
| wikimedia_processed | 26 | 26 | 0 |

**Preprocessing Success Rate:** 100% (27/27)
All fragments were successfully preprocessed. No preprocessing failures.

### False Positive Analysis

**ALL 26 CROSS-SOURCE PAIRS WERE INCORRECTLY MATCHED.**

Top 10 False Positives (sorted by confidence):

| Fragment A | Fragment B | Verdict | Confidence | Color BC | Gap to Threshold |
|------------|------------|---------|------------|----------|------------------|
| fragment_001... | ...fragment_022 | MATCH | 0.2666 | 0.8746 | N/A (verdict from raw_compat) |
| fragment_001... | ...fragment_018 | MATCH | 0.2615 | 0.9165 | N/A |
| fragment_001... | ...fragment_023 | MATCH | 0.2611 | 0.8701 | N/A |
| fragment_001... | ...fragment_026 | MATCH | 0.2608 | 0.7481 | N/A |
| fragment_001... | ...fragment_001 | WEAK_MATCH | 0.2594 | 0.7343 | N/A |
| fragment_001... | ...fragment_017 | MATCH | 0.2593 | 0.9089 | N/A |
| fragment_001... | ...fragment_024 | MATCH | 0.2577 | 0.8451 | N/A |
| fragment_001... | ...fragment_014 | MATCH | 0.2575 | 0.9576 | N/A |
| fragment_001... | ...fragment_016 | MATCH | 0.2574 | 0.8863 | N/A |
| fragment_001... | ...fragment_020 | MATCH | 0.2570 | 0.8847 | N/A |

### Statistical Analysis

**Confidence Scores (Relaxation Probabilities):**
- Mean: 0.2567
- Median: 0.2560
- Min: 0.2525
- Max: 0.2666
- Range: 0.0141

**Color Bhattacharyya Coefficients:**
- Mean: 0.8560
- Median: 0.8630
- Min: 0.7343
- Max: 0.9576
- Range: 0.2233

**Key Observation:** Confidence scores are LOW (0.25) but verdicts are MATCH/WEAK_MATCH. This indicates that verdicts come from RAW COMPATIBILITY SCORES, not confidence!

---

## Root Cause Analysis

### The Core Problem

**Why does a confidence of 0.25 result in "MATCH" verdict?**

The system has two separate scoring mechanisms:

1. **Relaxation Probability (Confidence):**
   - Iterative constraint propagation score
   - Represents global consistency
   - Ranges 0-1, observed: 0.25-0.27 (LOW)
   - **NOT used for verdicts!**

2. **Raw Compatibility Score:**
   - Direct geometric + color similarity
   - Used to classify pairs: `raw >= 0.55 → MATCH`
   - **This is what determines verdicts!**
   - Observed: Must be >= 0.55 for all these MATCH verdicts

### Why Raw Compatibility is Too High

**Formula:** `score_final = score_geometric * (1 - COLOR_PENALTY_WEIGHT * (1 - color_BC))`

**Current Settings:**
- COLOR_PENALTY_WEIGHT = 0.80
- MATCH_SCORE_THRESHOLD = 0.55
- WEAK_MATCH_SCORE_THRESHOLD = 0.35

**Math Breakdown:**

For a pair with Color BC = 0.86 (typical in our data):
```
color_penalty = COLOR_PENALTY_WEIGHT * (1 - BC)
              = 0.80 * (1 - 0.86)
              = 0.80 * 0.14
              = 0.112 (11.2% penalty)

score_final = score_geom * (1 - 0.112)
            = score_geom * 0.888
```

If geometric score = 0.70 (moderately similar curved pottery edges):
```
score_final = 0.70 * 0.888 = 0.622
```

**0.622 > 0.55 → MATCH verdict! ✗**

### Why Color BC is So High

Both british_museum and wikimedia_processed fragments are:
- Brownish pottery sherds
- Similar HSV color distributions
- Similar surface texture appearance
- From same archaeological period/region

**The color penalty assumes different sources have different colors. This assumption is VIOLATED when comparing similar artifact types.**

---

## Why This Matters

### System Design Assumption
The system was designed with the assumption that fragments from different sources (different original artifacts) would have:
1. Different color palettes → Low color BC → High penalty → Low final score
2. Different edge geometries → Low geometric score

### Reality Check
In archaeological contexts:
- Multiple pottery sherds from different vessels may look similar
- Same clay, same firing technique, same time period
- **Color alone cannot distinguish different sources**
- **Geometric features may also be similar (all have curved edges)**

### Impact
The current system will incorrectly assemble fragments from different artifacts if they look similar, leading to:
- False assemblies
- Wasted time on incorrect reconstructions
- Loss of confidence in the automated system

---

## Threshold Analysis

### Current Thresholds
- MATCH_SCORE_THRESHOLD = 0.55
- WEAK_MATCH_SCORE_THRESHOLD = 0.35
- COLOR_PENALTY_WEIGHT = 0.80

### Scenario Analysis

**Scenario 1: BC = 0.95 (very similar colors)**
```
Penalty = 0.80 * (1 - 0.95) = 0.04 (4%)
Geom = 0.60 → Final = 0.60 * 0.96 = 0.576 → MATCH ✗
```

**Scenario 2: BC = 0.80 (moderately similar colors)**
```
Penalty = 0.80 * (1 - 0.80) = 0.16 (16%)
Geom = 0.70 → Final = 0.70 * 0.84 = 0.588 → MATCH ✗
```

**Scenario 3: BC = 0.60 (dissimilar colors)**
```
Penalty = 0.80 * (1 - 0.60) = 0.32 (32%)
Geom = 0.80 → Final = 0.80 * 0.68 = 0.544 < 0.55 → NO_MATCH ✓
```

**Conclusion:** Color penalty only works when BC < 0.70. Our data has BC > 0.73, so penalty is ineffective.

---

## Recommendations

### Immediate Actions (Priority Order)

#### 1. Increase Match Thresholds (URGENT)
**Target: Reduce false positive rate from 100% to <5%**

**Recommended Changes:**
```python
# Current
MATCH_SCORE_THRESHOLD = 0.55
WEAK_MATCH_SCORE_THRESHOLD = 0.35

# Proposed
MATCH_SCORE_THRESHOLD = 0.75  # +0.20
WEAK_MATCH_SCORE_THRESHOLD = 0.60  # +0.25
```

**Impact:**
- With BC=0.86, geom=0.70: final=0.622 < 0.75 → NO_MATCH ✓
- More conservative matching
- **Trade-off:** May reject some true positives with damaged edges

#### 2. Strengthen Color Penalty
**Target: Make color dissimilarity more impactful**

**Option A: Increase Weight (Simple)**
```python
COLOR_PENALTY_WEIGHT = 0.95  # was 0.80
```
- BC=0.86, geom=0.70: final = 0.70 * (1 - 0.95*0.14) = 0.607
- Still above 0.55 threshold! Need Option B.

**Option B: Change Formula (Better)**
```python
# Current: multiplicative penalty
score_final = score_geom * (1 - COLOR_WEIGHT * (1 - BC))

# Proposed: exponential penalty
score_final = score_geom * pow(BC, COLOR_POWER)
# with COLOR_POWER = 3.0

# Impact:
# BC=0.86: penalty = 0.86^3 = 0.636
# geom=0.70: final = 0.70 * 0.636 = 0.445 < 0.55 ✓
```

**Recommended:** Implement Option B + increase threshold to 0.70.

#### 3. Add Hard Color Filter (Safety Net)
**Pre-filter pairs before geometric comparison**

```python
# Before computing geometric similarity:
if color_BC < COLOR_BC_THRESHOLD:
    return 0.0  # Reject immediately

# Recommended threshold:
COLOR_BC_THRESHOLD = 0.75
```

**Impact:**
- Pairs with BC < 0.75 are rejected without geometric comparison
- Saves computation time
- Acts as a safety net
- **Trade-off:** May be too strict for weathered/damaged artifacts

#### 4. Multi-Threshold Approach (RECOMMENDED - Best Balance)

Implement a cascading decision tree:

```python
def compute_final_score(geom_score, color_bc):
    # Stage 1: Hard color filter
    if color_bc < 0.70:
        return 0.0  # Definitely different sources

    # Stage 2: Exponential color penalty
    color_factor = pow(color_bc, 3.0)
    score = geom_score * color_factor

    # Stage 3: Boosted threshold
    return score

# New thresholds:
MATCH_SCORE_THRESHOLD = 0.70
WEAK_MATCH_SCORE_THRESHOLD = 0.50
```

**Expected Impact:**
- BC=0.86, geom=0.70: score = 0.70 * 0.86^3 = 0.445 < 0.70 → NO_MATCH ✓
- BC=0.65, geom=0.70: score = 0.0 (hard filter) → NO_MATCH ✓
- BC=0.95, geom=0.90: score = 0.90 * 0.95^3 = 0.772 > 0.70 → MATCH ✓

---

## Validation Plan

### Phase 1: Negative Case Validation (This Test)
**Rerun after implementing changes**

Target Metrics:
- True Negative Rate: > 95% (currently 0%)
- False Positive Rate: < 5% (currently 100%)
- Target: 25/26 or 26/26 correctly rejected

### Phase 2: Positive Case Validation
**Test on known matching pairs**

Required Tests:
- Same-source pairs from wikimedia_processed (26 fragments)
- Adjacent fragments from same artifact
- Target: True Positive Rate > 80%

### Phase 3: Mixed Dataset Testing
**Combine positive and negative cases**

Metrics:
- Overall Accuracy
- Precision / Recall
- F1 Score
- ROC Curve Analysis

### Phase 4: Parameter Sweep
**Find optimal balance point**

Test Parameters:
- MATCH_SCORE_THRESHOLD: [0.60, 0.65, 0.70, 0.75, 0.80]
- COLOR_POWER: [1.0, 1.5, 2.0, 2.5, 3.0, 4.0]
- COLOR_BC_THRESHOLD: [0.65, 0.70, 0.75, 0.80, 0.85]

Output:
- Trade-off curves (FPR vs TPR)
- Optimal configuration for production use

---

## Generated Visualizations

The following plots are available in `outputs/testing/`:

1. **negative_case_performance.png**
   - True negative vs false positive rates
   - Shows current 100% FP rate

2. **confidence_distribution.png**
   - Histogram of confidence scores
   - All scores clustered around 0.25

3. **color_bc_distribution.png**
   - Color similarity distribution
   - Shows high BC values (0.73-0.96)

4. **color_vs_geometric_scatter.png**
   - 2D plot: Color BC vs Confidence
   - All points in high-BC, low-confidence region

5. **verdict_distribution.png**
   - Bar chart of verdict types
   - Shows 25 MATCH, 1 WEAK_MATCH, 0 NO_MATCH

---

## Key Takeaways

### What We Learned

1. **Color similarity is necessary but not sufficient**
   - Similar-looking artifacts from different sources exist
   - Color penalty must be much stronger
   - Consider adding texture/surface features

2. **Thresholds matter enormously**
   - Current thresholds (0.55, 0.35) are too permissive
   - Need to balance false positives vs false negatives
   - Production system should err on side of caution (reject borderline cases)

3. **Confidence vs Raw Score distinction is critical**
   - Confidence (relaxation probability) is global consistency measure
   - Raw compatibility (geometric + color) determines verdicts
   - These two metrics serve different purposes

4. **Real-world data challenges assumptions**
   - Synthetic benchmarks may not capture real complexity
   - Need diverse test sets with known ground truth
   - Archaeological context matters

### Next Steps

1. **Implement recommended threshold changes** (1-2 hours)
2. **Rerun negative case test** (validate FP rate drops to <5%)
3. **Run positive case test** (ensure TP rate stays >80%)
4. **Parameter optimization** (find best balance)
5. **Update documentation** (record final configuration)
6. **Deploy with monitoring** (track performance on new data)

---

## Conclusion

This comprehensive negative case testing has revealed a **critical flaw** in the current system configuration:

- ✗ **100% false positive rate** on cross-source pairs
- ✗ **Color penalty insufficient** for similar-looking artifacts
- ✗ **Thresholds too permissive** for production use
- ✓ **Root cause identified** (high color BC, weak penalty formula)
- ✓ **Solutions proposed** (exponential penalty, higher thresholds)
- ✓ **Validation plan defined** (multi-phase testing)

**Status:** System requires recalibration before production deployment.

**Estimated time to fix:** 4-6 hours (implementation + validation)

---

*Report generated by: test_negative_cases.py*
*Date: 2026-04-08 11:25:14*
*Test Duration: ~5 seconds*
*Total Pairs Tested: 26*
