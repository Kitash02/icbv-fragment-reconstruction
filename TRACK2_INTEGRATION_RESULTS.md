# TRACK 2 INTEGRATION RESULTS
## Archaeological Fragment Reconstruction System - Track 2 Hard Discriminators

**Date**: 2026-04-08
**Mission**: Integrate and Test Track 2 Hard Discriminators
**Status**: ❌ **FAILED - REGRESSION**

---

## Executive Summary

Track 2 (Hard Discriminators) has been integrated and tested against the full 45-case benchmark. **CRITICAL FINDING**: Track 2 integration has caused a **SEVERE REGRESSION** in system performance across all metrics.

### Results Comparison

| Configuration | Positive Accuracy | Negative Accuracy | Overall Accuracy |
|---------------|-------------------|-------------------|------------------|
| **Stage 1.6 Baseline** | **89%** (8/9) | **86%** (31/36) | **87%** (39/45) |
| **Stage 1.6 + Track 2** | **78%** (7/9) | **56%** (20/36) | **60%** (27/45) |
| **CHANGE** | **-11%** ❌ | **-30%** ❌ | **-27%** ❌ |

### Verdict

**❌ DO NOT DEPLOY TRACK 2** - Revert to Stage 1.6 baseline immediately.

Track 2 has:
- ✗ **REDUCED positive accuracy** by 11% (lost "Wall painting" match)
- ✗ **REDUCED negative accuracy** by 30% (16 false positives remain)
- ✗ **FAILED to deliver** on promised improvements

---

## 1. Integration Details

### 1.1 Code Changes

**File Modified**: `src/compatibility.py`

**Changes Made**:
1. Added import: `from hard_discriminators import hard_reject_check`
2. Added early rejection check at line 514-518:
```python
# Apply hard rejection check
if hard_reject_check(all_images[frag_i], all_images[frag_j],
                   bc_color, bc_texture):
    # Skip this pair - early rejection
    continue
```

### 1.2 Hard Discriminator Criteria

From `src/hard_discriminators.py`:

1. **Edge Density Check**: Reject if `|density_i - density_j| > 0.15` (15%)
2. **Texture Entropy Check**: Reject if `|entropy_i - entropy_j| > 0.5`
3. **Appearance Gate**: Reject if `color < 0.60 OR texture < 0.55`

---

## 2. Test Results - Detailed Analysis

### 2.1 Positive Test Results (9 cases)

| Test Case | Baseline Result | Track 2 Result | Status |
|-----------|----------------|----------------|--------|
| gettyimages-1311604917 | WEAK_MATCH ✓ | WEAK_MATCH ✓ | Same |
| gettyimages-170096524 | WEAK_MATCH ✓ | WEAK_MATCH ✓ | Same |
| gettyimages-2177809001 | WEAK_MATCH ✓ | WEAK_MATCH ✓ | Same |
| gettyimages-470816328 | WEAK_MATCH ✓ | WEAK_MATCH ✓ | Same |
| high-res-antique-close-up | MATCH ✓ | MATCH ✓ | Same |
| shard_01_british | WEAK_MATCH ✓ | WEAK_MATCH ✓ | Same |
| shard_02_cord_marked | WEAK_MATCH ✓ | WEAK_MATCH ✓ | Same |
| **scroll** | NO_MATCH ✗ | NO_MATCH ✗ | **Same failure** |
| **Wall painting** | **WEAK_MATCH ✓** | **NO_MATCH ✗** | **NEW FAILURE** ❌ |

**Summary**:
- ✓ **Passed**: 7/9 (78%)
- ✗ **Failed**: 2/9 (22%)
- **Baseline**: 8/9 (89%)
- **Delta**: -1 test (-11%)

**Critical Issue**: Track 2 REJECTED the "Wall painting" positive match that was working in Stage 1.6!

### 2.2 Negative Test Results (36 cases)

| Result Type | Baseline | Track 2 | Change |
|-------------|----------|---------|--------|
| ✓ **Correctly Rejected** (NO_MATCH) | 31 | 20 | **-11** ❌ |
| ✗ **False Positives** (WEAK_MATCH) | 4 | 14 | **+10** ❌ |
| ✗ **False Positives** (MATCH) | 0 | 2 | **+2** ❌ |
| **Errors** | 1 | 0 | -1 ✓ |

**Summary**:
- ✓ **Passed**: 20/36 (56%)
- ✗ **Failed**: 16/36 (44%)
- **Baseline**: 31/36 (86%)
- **Delta**: -11 tests (-30%)

**Critical Issue**: Track 2 is NOT reducing false positives - it's actually making them WORSE!

### 2.3 False Positive Analysis

**Track 2 False Positives** (16 total):

**MATCH level** (2):
1. `mixed_gettyimages-13116049_high-res-antique-clo` → MATCH (should be NO_MATCH)
2. `mixed_gettyimages-21778090_gettyimages-47081632` → MATCH (should be NO_MATCH)

**WEAK_MATCH level** (14):
1. `mixed_gettyimages-13116049_gettyimages-21778090`
2. `mixed_gettyimages-17009652_gettyimages-47081632`
3. `mixed_gettyimages-17009652_high-res-antique-clo`
4. `mixed_gettyimages-17009652_scroll`
5. `mixed_gettyimages-17009652_shard_02_cord_marked`
6. `mixed_gettyimages-47081632_scroll`
7. `mixed_gettyimages-47081632_shard_01_british`
8. `mixed_scroll_shard_01_british`
9. `mixed_shard_01_british_shard_02_cord_marked`
10. `mixed_Wall painting from R_gettyimages-13116049`
11. `mixed_Wall painting from R_gettyimages-47081632`
12. `mixed_Wall painting from R_high-res-antique-clo`
13. `mixed_Wall painting from R_shard_01_british`
14. `mixed_Wall painting from R_shard_02_cord_marked`

**Baseline had only 4 false positives**:
1. `mixed_gettyimages-17009652_high-res-antique-clo`
2. `mixed_shard_01_british_shard_02_cord_marked`
3. `mixed_Wall painting from R_gettyimages-17009652` (×2)

**New false positives in Track 2**: 12 additional failures!

---

## 3. Root Cause Analysis

### 3.1 Why Did Track 2 Fail?

**Problem 1: Thresholds Too Strict for Positive Matches**

The "Wall painting" positive test is now failing because Track 2's hard discriminators are rejecting it. This suggests the thresholds are too conservative:
- Edge density threshold (0.15) might be too tight for fragments with varying edge patterns
- Appearance gate (color < 0.60 OR texture < 0.55) is rejecting valid matches

**Problem 2: Thresholds Too Loose for Negative Matches**

Track 2 is NOT improving negative accuracy because the thresholds are not strict enough to reject the false positives that matter. The 16 false positives in Track 2 are passing through the hard discriminators, which means:
- These fragment pairs have similar edge density (< 0.15 difference)
- They have similar texture entropy (< 0.5 difference)
- Their appearance features pass the gate (color ≥ 0.60 AND texture ≥ 0.55)

**Problem 3: Hard Discriminators vs. Soft Appearance Penalty**

In Stage 1.6, the appearance features are applied as a **soft multiplicative penalty**:
- `score = score × (bc_color^4) × (bc_texture^2) × (bc_gabor^2) × (bc_haralick^2)`
- This gradually reduces scores for dissimilar pairs

In Track 2, the appearance gate is a **hard binary decision**:
- Either REJECT completely (if color < 0.60 OR texture < 0.55)
- Or ACCEPT and continue processing

The hard gate is LESS nuanced than the soft penalty, which explains why Track 2 performs worse.

### 3.2 Why Did Negative Accuracy Drop?

This is counterintuitive - Track 2 should IMPROVE negative accuracy by rejecting more pairs early. But the data shows:
- **Baseline**: 31/36 correct rejections (86%)
- **Track 2**: 20/36 correct rejections (56%)

The issue is that Track 2's hard discriminators are NOT triggering for the pairs that need to be rejected. The 16 false positives are:
1. Passing the edge density check (similar edge patterns)
2. Passing the texture entropy check (similar randomness)
3. Passing the appearance gate (color ≥ 0.60 AND texture ≥ 0.55)

This means these pairs have **moderately similar appearance features** (0.60-0.80 range), which is enough to pass Track 2's gates but not enough for Stage 1.6's exponential penalty to suppress them below threshold.

### 3.3 Mathematical Analysis

**Stage 1.6 Penalty Example**:
```
bc_color = 0.70
bc_texture = 0.65
bc_gabor = 0.60
bc_haralick = 0.55

appearance_multiplier = 0.70^4 × 0.65^2 × 0.60^2 × 0.55^2
                     = 0.2401 × 0.4225 × 0.36 × 0.3025
                     = 0.0111 (98.9% penalty!)

Final score = 0.80 × 0.0111 = 0.0089 << 0.60 threshold
→ NO_MATCH ✓
```

**Track 2 Gate Example** (same pair):
```
bc_color = 0.70 ≥ 0.60 ✓ PASS
bc_texture = 0.65 ≥ 0.55 ✓ PASS

→ NO REJECTION, continue to full scoring
→ If geometric score is high, might still classify as WEAK_MATCH
→ FALSE POSITIVE ✗
```

**Key Insight**: Track 2's linear gates (0.60, 0.55) are MUCH MORE LENIENT than Stage 1.6's exponential penalty (4.0, 2.0, 2.0, 2.0 powers).

---

## 4. Performance Analysis

### 4.1 Processing Time

Unfortunately, we cannot analyze speedup because Track 2 is fundamentally broken. The test shows all scores as 0.00, which indicates most pairs are being rejected entirely.

**Expected**: 2-3x speedup (13m → 4-6m)
**Actual**: Cannot measure - system is not functioning correctly

### 4.2 Rejection Statistics

Based on the low scores (0.00) in the output, it appears Track 2 is rejecting a LARGE FRACTION of fragment pairs. However, this aggressive rejection is:
1. Rejecting valid positive matches (Wall painting)
2. NOT rejecting enough invalid negative matches (16 false positives remain)

---

## 5. Comparison to Predictions

### 5.1 Predicted vs. Actual

| Metric | Prediction | Actual | Verdict |
|--------|-----------|---------|---------|
| Positive Accuracy | ~89% (maintain) | 78% | ❌ **WORSE** (-11%) |
| Negative Accuracy | 90%+ (improve) | 56% | ❌ **WORSE** (-30%) |
| Overall Accuracy | 89-91% | 60% | ❌ **WORSE** (-27%) |
| Processing Time | 2-3x faster | Unknown | ⚠️ **Cannot measure** |
| False Positives | 4 → 0-2 | 4 → 16 | ❌ **WORSE** (+12) |

**All predictions were wrong**. Track 2 made everything worse.

---

## 6. Recommendations

### 6.1 Immediate Action: REVERT TRACK 2

**❌ DO NOT DEPLOY TRACK 2**

**Recommendation**: Revert to Stage 1.6 baseline immediately.

**Rationale**:
1. Track 2 causes severe regression (-27% overall accuracy)
2. Positive accuracy dropped from 89% to 78%
3. Negative accuracy dropped from 86% to 56%
4. System is fundamentally broken - not ready for deployment

**Revert Command**:
```bash
git restore src/compatibility.py
```

Or manually remove the import and hard rejection check.

### 6.2 Why Track 2 Failed

Track 2's design assumptions were incorrect:

**Assumption 1**: "Hard discriminators can reject obvious mismatches early"
- **Reality**: The discriminators are rejecting GOOD matches (Wall painting)

**Assumption 2**: "Edge density and texture entropy differences indicate incompatibility"
- **Reality**: Many false positives have similar edge/entropy (they pass the checks)

**Assumption 3**: "Binary gates (0.60, 0.55) will improve accuracy"
- **Reality**: Binary gates are LESS effective than exponential penalties (^4, ^2)

**Assumption 4**: "Early rejection will improve negative accuracy"
- **Reality**: It made negative accuracy WORSE (86% → 56%)

### 6.3 Threshold Tuning Analysis

**Question**: Can we fix Track 2 by tuning thresholds?

**Answer**: ❌ **NO** - The fundamental approach is flawed.

**Why tuning won't help**:
1. **Conflicting requirements**: To fix positive accuracy (Wall painting), we need to LOOSEN thresholds. To fix negative accuracy (16 false positives), we need to TIGHTEN thresholds. These requirements contradict each other.

2. **Binary gate vs. continuous penalty**: Hard discriminators are binary (pass/fail), while Stage 1.6's exponential penalty is continuous. The binary approach loses information.

3. **Feature interaction**: Track 2 uses OR logic (`color < 0.60 OR texture < 0.55`), which is too strict. Stage 1.6 uses multiplicative logic (`color^4 × texture^2`), which is more nuanced.

**Possible threshold adjustments** (if we wanted to try anyway):

| Threshold | Current | Suggested | Effect |
|-----------|---------|-----------|--------|
| Edge density | 0.15 | 0.25 | More lenient - might fix Wall painting |
| Texture entropy | 0.5 | 0.8 | More lenient - might fix Wall painting |
| Color gate | 0.60 | 0.50 | More lenient - might fix Wall painting |
| Texture gate | 0.55 | 0.45 | More lenient - might fix Wall painting |

**But**: Loosening thresholds will make negative accuracy EVEN WORSE (more false positives).

### 6.4 Alternative Approaches

**Option 1: Hybrid Soft Discriminators** (Recommended)

Instead of hard binary gates, use soft penalties with HIGHER powers:
```python
# Current Stage 1.6
appearance_multiplier = (bc_color ** 4.0) * (bc_texture ** 2.0) * ...

# Proposed: Track 2.5
appearance_multiplier = (bc_color ** 6.0) * (bc_texture ** 3.0) * ...  # Higher powers
```

This increases the penalty gradient without losing nuance.

**Option 2: Adaptive Thresholds**

Use different thresholds for different artifact types:
- Pottery shards: Strict (0.70 color, 0.60 texture)
- Wall paintings: Lenient (0.50 color, 0.45 texture)
- Scrolls: Very lenient (0.40 color, 0.35 texture)

Requires artifact type classification.

**Option 3: Ensemble with Fallback**

Use Track 2 as a SUPPLEMENT, not a REPLACEMENT:
```python
if hard_reject_check(...):
    score *= 0.5  # Penalty, not rejection
else:
    score *= 1.0  # No change
```

This preserves Stage 1.6's behavior while adding Track 2's signal.

**Option 4: Learn Thresholds from Data**

Use the 45 test cases to optimize thresholds:
- Grid search over (edge_density, entropy, color, texture) thresholds
- Maximize F1 score or balanced accuracy
- Validate on held-out data

Requires more test data and tuning time.

---

## 7. Lessons Learned

### 7.1 Why Predictions Failed

The original prediction report (FINAL_INTEGRATION_RESULTS.md) projected:
- Positive: 89% → 89% (maintain)
- Negative: 86% → 90%+ (improve)
- Overall: 87% → 89-91% (improve)

These predictions were based on:
1. Research papers (arXiv:2309.13512 - 99.3% accuracy)
2. Theoretical benefits of early rejection
3. Assumptions about threshold effectiveness

**What went wrong**:
1. **Research paper context**: The 99.3% accuracy was on a DIFFERENT dataset with DIFFERENT fragment types
2. **Early rejection assumptions**: We assumed rejected pairs would be negative cases, but Track 2 also rejects positive cases
3. **Threshold calibration**: We used arbitrary thresholds (0.15, 0.5, 0.60, 0.55) without empirical validation

### 7.2 Red Flags We Missed

In hindsight, there were warning signs:

**Red Flag 1**: Track 2 was not integrated into the validated Stage 1.6 system
- We should have tested Track 2 on a SUBSET first (5-10 cases)
- Instead, we integrated and ran the full 45-case benchmark

**Red Flag 2**: No empirical threshold validation
- The thresholds (0.15, 0.5, 0.60, 0.55) were chosen based on intuition
- We should have tuned them on a validation set first

**Red Flag 3**: No ablation study
- We didn't test each discriminator (edge density, entropy, appearance gate) independently
- We don't know which component is causing the regression

**Red Flag 4**: Binary gates vs. continuous penalties
- We replaced Stage 1.6's proven exponential penalties with unproven binary gates
- This was a fundamental architecture change without validation

### 7.3 Validation Failures

**Failure 1**: No incremental testing
- We should have tested Track 2 on positive cases ONLY first
- Then negative cases ONLY
- Then combined

**Failure 2**: No baseline comparison during development
- We didn't check if Track 2 was improving over Stage 1.6 during integration
- We waited until full benchmark to discover the regression

**Failure 3**: No rollback plan
- We didn't create a feature flag or easy rollback mechanism
- Fortunately, reverting is easy (remove 2 lines of code)

---

## 8. Statistical Summary

### 8.1 Confusion Matrix

**Stage 1.6 Baseline**:
```
                    Predicted:
                    MATCH/WEAK  NO_MATCH  ERROR
Actual: POSITIVE         8          1        0     = 9
Actual: NEGATIVE         4         31        1     = 36
                    ------    ------    ------
                       12         32        1     = 45
```

**Stage 1.6 + Track 2**:
```
                    Predicted:
                    MATCH/WEAK  NO_MATCH  ERROR
Actual: POSITIVE         7          2        0     = 9
Actual: NEGATIVE        16         20        0     = 36
                    ------    ------    ------
                       23         22        0     = 45
```

### 8.2 Performance Metrics

**Stage 1.6 Baseline**:
```
True Positives (TP):   8
False Negatives (FN):  1
True Negatives (TN):  31
False Positives (FP):  4

Precision: 8/(8+4) = 67%
Recall:    8/(8+1) = 89%
Specificity: 31/(31+4) = 89%
F1 Score:  2×(0.67×0.89)/(0.67+0.89) = 0.76
Accuracy:  (8+31)/45 = 87%
```

**Stage 1.6 + Track 2**:
```
True Positives (TP):   7
False Negatives (FN):  2
True Negatives (TN):  20
False Positives (FP): 16

Precision: 7/(7+16) = 30% ⬇ -37%
Recall:    7/(7+2) = 78% ⬇ -11%
Specificity: 20/(20+16) = 56% ⬇ -33%
F1 Score:  2×(0.30×0.78)/(0.30+0.78) = 0.43 ⬇ -0.33
Accuracy:  (7+20)/45 = 60% ⬇ -27%
```

**All metrics got WORSE**.

---

## 9. Conclusion

### 9.1 Final Verdict

**❌ TRACK 2 INTEGRATION FAILED**

Track 2 (Hard Discriminators) has caused a severe regression in system performance:
- Positive accuracy: 89% → 78% (-11%)
- Negative accuracy: 86% → 56% (-30%)
- Overall accuracy: 87% → 60% (-27%)
- Precision: 67% → 30% (-37%)
- F1 Score: 0.76 → 0.43 (-0.33)

### 9.2 Immediate Action

**REVERT TO STAGE 1.6 BASELINE**

1. Remove Track 2 import from `src/compatibility.py`
2. Remove hard rejection check (lines 514-518)
3. Restore Stage 1.6 behavior
4. Validate with full benchmark (should return to 89%/86%)

### 9.3 Path Forward

**Stage 1.6 remains the PRODUCTION system**:
- ✅ Positive: 89% (8/9)
- ✅ Negative: 86% (31/36)
- ✅ Overall: 87% (39/45)

**Future work** (if Track 2 is to be reconsidered):
1. Conduct ablation study (test each discriminator independently)
2. Empirically tune thresholds on validation set
3. Consider hybrid soft discriminators (Option 1)
4. Collect more training data for threshold learning
5. Test on subset before full integration

### 9.4 Net Benefit Analysis

**Net Benefit**: **-27% accuracy** ❌

**Loss**:
- 1 positive match lost (Wall painting)
- 11 negative matches lost (more false positives)
- 12 new false positives introduced
- System confidence destroyed

**Gain**:
- None observed
- Processing time improvement cannot be measured (system broken)

**Recommendation**: **DO NOT KEEP TRACK 2** - Revert immediately.

---

## 10. Technical Appendix

### 10.1 Test Environment

- **Date**: 2026-04-08
- **System**: Windows 11 Enterprise 10.0.26200
- **Python**: 3.x
- **Test Suite**: 45 cases (9 positive, 36 negative)
- **Configuration**: WITH rotation (random 0-360°)
- **Command**: `PYTHONIOENCODING=utf-8 python run_test.py`

### 10.2 Files Modified

1. `src/compatibility.py`:
   - Line 39: Added `from hard_discriminators import hard_reject_check`
   - Lines 514-518: Added hard rejection check

### 10.3 Files Unchanged

- `src/hard_discriminators.py` (implementation exists but thresholds are incorrect)
- `src/relaxation.py` (no changes)
- `src/preprocessing.py` (no changes)
- `run_test.py` (no changes)

### 10.4 Raw Test Output

Full test results saved to:
- `TRACK2_TEST_RESULTS_RAW.txt`

---

**Report Generated**: 2026-04-08
**Total Test Time**: ~18 minutes
**Recommendation**: ❌ **REVERT TRACK 2 IMMEDIATELY**
**Next Steps**: Return to Stage 1.6 baseline (89%/86% accuracy)

---

**End of Track 2 Integration Results Report**
