# Negative Case Analysis Report

## Cross-Source Fragment Rejection Testing

**Generated:** 2026-04-08 11:25:14

---

## Executive Summary

- **Mission:** Test cross-source fragment rejection (negative cases)
- **Sources Tested:** 2
- **Fragments Collected:** 27
- **Fragments Successfully Preprocessed:** 27
- **Negative Pairs Tested:** 26

### Key Results

- **True Negative Rate (Correctly Rejected):** 0.00%
- **False Positive Rate (Incorrectly Matched):** 100.00%
- **False Positives:** 26/26
- **True Negatives:** 0/26

**NEEDS IMPROVEMENT:** >20% false positive rate - significant issues with rejection.

---

## Data Collection

### Fragments by Source

| Source | Total Fragments | Preprocessed | Failed |
|--------|-----------------|--------------|--------|
| british_museum | 1 | 1 | 0 |
| wikimedia_processed | 26 | 26 | 0 |

### Test Design

All pairs are **negative cases** (cross-source) and should be rejected:
- Total cross-source pairs generated: 26
- Expected result: NO_MATCH verdict for all pairs
- Success metric: High true negative rate (>95%)

---

## Performance Results

### Overall Metrics

- **True Negative Rate:** 0.00% (0/26)
- **False Positive Rate:** 100.00% (26/26)

### Confidence Statistics

- **Average Confidence:** 0.2567
- **Median Confidence:** 0.2560
- **Average Color BC:** 0.8560
- **Median Color BC:** 0.8630

### Comparison to Benchmark

**Benchmark (Expected):**
- Negative accuracy: 100% (0/36 false positives)
- False positive rate: 0%

**Current System:**
- Negative accuracy: 0.00%
- False positive rate: 100.00%

**Gap from benchmark:** 100.00 percentage points

---

## False Positive Analysis

**26 false positives detected** (pairs incorrectly matched):

### False Positive Details

| Fragment A | Fragment B | Source A | Source B | Verdict | Confidence | Color BC |
|------------|------------|----------|----------|---------|------------|----------|
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_022 | british_museum | wikimedia_processed | MATCH | 0.2666 | 0.8746 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_018 | british_museum | wikimedia_processed | MATCH | 0.2615 | 0.9165 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_023 | british_museum | wikimedia_processed | MATCH | 0.2611 | 0.8701 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_026 | british_museum | wikimedia_processed | MATCH | 0.2608 | 0.7481 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_001 | british_museum | wikimedia_processed | WEAK_MATCH | 0.2594 | 0.7343 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_017 | british_museum | wikimedia_processed | MATCH | 0.2593 | 0.9089 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_024 | british_museum | wikimedia_processed | MATCH | 0.2577 | 0.8451 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_014 | british_museum | wikimedia_processed | MATCH | 0.2575 | 0.9576 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_016 | british_museum | wikimedia_processed | MATCH | 0.2574 | 0.8863 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_020 | british_museum | wikimedia_processed | MATCH | 0.2570 | 0.8847 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_012 | british_museum | wikimedia_processed | MATCH | 0.2570 | 0.8641 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_003 | british_museum | wikimedia_processed | MATCH | 0.2564 | 0.8122 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_015 | british_museum | wikimedia_processed | MATCH | 0.2563 | 0.9118 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_021 | british_museum | wikimedia_processed | MATCH | 0.2558 | 0.8834 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_011 | british_museum | wikimedia_processed | MATCH | 0.2556 | 0.8619 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_005 | british_museum | wikimedia_processed | MATCH | 0.2554 | 0.8443 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_009 | british_museum | wikimedia_processed | MATCH | 0.2554 | 0.7996 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_025 | british_museum | wikimedia_processed | MATCH | 0.2549 | 0.8370 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_006 | british_museum | wikimedia_processed | MATCH | 0.2546 | 0.8249 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_010 | british_museum | wikimedia_processed | MATCH | 0.2546 | 0.8018 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_002 | british_museum | wikimedia_processed | MATCH | 0.2545 | 0.8509 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_004 | british_museum | wikimedia_processed | MATCH | 0.2539 | 0.8334 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_019 | british_museum | wikimedia_processed | MATCH | 0.2536 | 0.9029 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_007 | british_museum | wikimedia_processed | MATCH | 0.2531 | 0.9367 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_008 | british_museum | wikimedia_processed | MATCH | 0.2529 | 0.7506 |
| fragment_001_File020240849Identifyingpotterysherdsjpg | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_013 | british_museum | wikimedia_processed | MATCH | 0.2525 | 0.9132 |

### False Positive Patterns

- **Highest false positive confidence:** 0.2666
- **Lowest false positive confidence:** 0.2525
- **Average false positive confidence:** 0.2567
- **Average false positive color BC:** 0.8560

**False positives by verdict:**
- MATCH: 25
- WEAK_MATCH: 1

**False positives by source combination:**
- british_museum vs wikimedia_processed: 26

---

## True Negative Analysis

**0 pairs correctly rejected.**

---

## Color Similarity Analysis

- **Average Color BC (all pairs):** 0.8560
- **Median Color BC (all pairs):** 0.8630
- **Min Color BC:** 0.7343
- **Max Color BC:** 0.9576

**Insight:** Cross-source pairs should have LOW color BC (different appearance). If color BC is high but pairs are correctly rejected, the geometric features are working well to distinguish different sources.

---

## Root Cause Analysis

### Why 100% False Positive Rate?

**CRITICAL FINDING:** The false positives are occurring because:

1. **High Color Similarity:** Color BC ranges from 0.73 to 0.96 (mean 0.856)
   - Cross-source fragments have VERY SIMILAR appearances
   - British Museum fragment and Wikimedia sherds are both brownish pottery
   - Current COLOR_PENALTY_WEIGHT (0.80) is insufficient

2. **Verdict vs Confidence Confusion:**
   - **Confidence scores** (0.25-0.27) are the relaxation probabilities (LOW)
   - **Verdicts** ("MATCH"/"WEAK_MATCH") come from RAW compatibility scores (HIGH)
   - The system checks: `if raw_compat >= 0.55 then verdict="MATCH"`
   - Raw compat scores must be >= 0.55 for "MATCH" verdicts

3. **Why Raw Compat is High:**
   - Geometric similarity: pottery sherds have similar curved edges
   - Color penalty not strong enough: `final_score = geometric_score * (1 - COLOR_WEIGHT * (1 - BC))`
   - With BC=0.86 and COLOR_WEIGHT=0.80: penalty = 0.80 * (1-0.86) = 0.112
   - A score of 0.70 becomes: 0.70 * (1 - 0.112) = 0.622 > 0.55 threshold
   - **MATCH verdict triggered despite being different sources!**

### Color Penalty Math

Current formula: `score_final = score_geom * (1 - COLOR_WEIGHT * (1 - BC))`

With COLOR_WEIGHT = 0.80:
- BC = 0.90 → penalty = 8% → keeps 92% of geometric score
- BC = 0.80 → penalty = 16% → keeps 84% of geometric score
- BC = 0.70 → penalty = 24% → keeps 76% of geometric score

**Problem:** Even with 24% penalty, a geometric score of 0.75 stays above 0.55!

## Recommendations

### Current System Performance: CRITICAL ISSUE - 100% FALSE POSITIVE RATE

The system cannot distinguish cross-source fragments when they have similar colors.

**IMMEDIATE ACTION REQUIRED:**

### Option 1: Increase Thresholds (Conservative)
1. **Increase MATCH_SCORE_THRESHOLD: 0.55 → 0.75**
2. **Increase WEAK_MATCH_SCORE_THRESHOLD: 0.35 → 0.55**
3. **Pro:** Simple, preserves current algorithm
4. **Con:** May hurt true positive rate on damaged edges

### Option 2: Strengthen Color Penalty (Aggressive)
1. **Increase COLOR_PENALTY_WEIGHT: 0.80 → 0.95**
   - With BC=0.86: penalty = 95% * 14% = 13.3% (keeps 86.7%)
   - Geom score 0.70 becomes: 0.70 * 0.867 = 0.607 (still above 0.55!)
2. **Change penalty formula to exponential:**
   - `score_final = score_geom * pow(BC, COLOR_POWER)`
   - With COLOR_POWER=3.0 and BC=0.86: 0.86^3 = 0.636
   - Geom score 0.70 becomes: 0.70 * 0.636 = 0.445 < 0.55 ✓
3. **Pro:** Leverages color effectively
4. **Con:** Requires code changes to compatibility.py

### Option 3: Add Hard Color Threshold (Practical)
1. **Reject pairs with BC < 0.90 immediately**
2. **Rationale:** If colors don't match well, can't be same artifact
3. **Implementation:** Add check before geometric comparison
4. **Pro:** Simple and effective
5. **Con:** May be too strict for weathered artifacts

### Option 4: Hybrid Approach (RECOMMENDED)
1. **Increase MATCH_SCORE_THRESHOLD: 0.55 → 0.70**
2. **Increase COLOR_PENALTY_WEIGHT: 0.80 → 0.90**
3. **Add color pre-filter: reject if BC < 0.70**
4. **Result:** Multi-layer defense against false positives

### Validation Plan

After implementing changes:
1. **Rerun negative case test** - Target: <5% false positive rate
2. **Run positive case test** - Ensure >80% true positive rate
3. **Test on mixed dataset** - Balance false positive / false negative
4. **Document trade-offs** - ROC curve analysis

### General Recommendations

1. **Priority: Fix false positive rate** - Current 100% is unacceptable
2. **Collect more diverse test data** - Need fragments with different colors
3. **Consider texture features** - Color alone may not be sufficient
4. **Implement confidence calibration** - Separate geometric from appearance confidence

---

## Visualizations

Generated plots (see `outputs/testing/` directory):

- `negative_case_performance.png` - True negative vs false positive rates
- `confidence_distribution.png` - Confidence score histogram
- `color_bc_distribution.png` - Color similarity histogram
- `color_vs_geometric_scatter.png` - Color BC vs confidence scatter plot
- `verdict_distribution.png` - Verdict type breakdown

---

*End of Report*
