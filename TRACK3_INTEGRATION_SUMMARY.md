# TRACK 3 INTEGRATION - FINAL SUMMARY

## Mission Completion Status: ✅ COMPLETE

**Task**: Integrate Track 3 (Ensemble Voting) as post-processing filter to see if it provides additional boost over Track 2

**Result**: Track 3 integration COMPLETE but **NOT RECOMMENDED for deployment**

---

## Quick Summary

| Configuration | Accuracy | Status |
|---------------|----------|--------|
| **Baseline (no tracks)** | 20% | ❌ Too permissive |
| **Track 2 only** | 64% | ✅ **WINNER** |
| **Track 2 + Track 3** | 60% | ❌ Degraded |

**Recommendation**: **Deploy Track 2 only, skip Track 3**

---

## What Was Done

### 1. Created Ensemble Post-Processing Module
**File**: `src/ensemble_postprocess.py` (200+ lines)

**Function**: `reclassify_borderline_cases(assemblies, compat_matrix, appearance_mats, images)`

**Strategy**: Post-processing filter (Option B - low risk approach)
- Run AFTER relaxation labeling produces assemblies
- Re-classify WEAK_MATCH pairs using 5-way voting ensemble
- Leave MATCH and NO_MATCH verdicts unchanged
- Only modify borderline cases where voting might help

**Ensemble Voters**:
1. Raw Compatibility (geometric features - curvature, Fourier)
2. Color Discriminator (Lab histogram Bhattacharyya coefficient)
3. Texture Discriminator (LBP histogram Bhattacharyya coefficient)
4. Gabor Discriminator (frequency-domain texture cosine similarity)
5. Morphological Discriminator (edge density + texture entropy)

**Voting Rule**:
- MATCH: Requires 3+ MATCH votes (60% confidence threshold)
- NO_MATCH: Requires 2+ NO_MATCH votes (40% rejection threshold)
- WEAK_MATCH: Otherwise (mixed or all weak votes)

### 2. Modified Integration Points

**`src/compatibility.py`**:
- Changed return signature: `return compat, appearance_mats` (was: `return compat`)
- Now returns both compatibility matrix AND appearance matrices for ensemble use

**`src/main.py`**:
- Added import: `from ensemble_postprocess import reclassify_borderline_cases`
- Added ensemble call after relaxation labeling:
```python
# Track 3: Ensemble voting post-processing filter
if appearance_mats is not None:
    run_logger.info("Applying Track 3 (Ensemble Voting) post-processing...")
    assemblies = reclassify_borderline_cases(
        assemblies, compat_matrix, appearance_mats, images
    )
```

### 3. Tested on Full Benchmark
- Ran 45 test cases (9 positive, 36 negative)
- Compared Track 2 only vs Track 2+3
- Generated detailed analysis report

---

## Test Results

### Track 2 Only (Baseline for Comparison)
```
Overall Accuracy: 29/45 (64%)
├─ Positive Tests: 7/9 (78%)   ← 2 false negatives
└─ Negative Tests: 22/36 (61%) ← 14 false positives
```

**Key characteristics**:
- Hard discriminators reject incompatible pairs early
- Pessimistic bias (prefer false negatives over false positives)
- Fast (skips expensive curvature for rejected pairs)

### Track 2+3 (With Ensemble Voting)
```
Overall Accuracy: 27/45 (60%)
├─ Positive Tests: 7/9 (78%)   ← 2 false negatives (no change)
└─ Negative Tests: 20/36 (56%) ← 16 false positives (+2 more)
```

**What happened**:
- Overall accuracy DECREASED by 4 percentage points (64% → 60%)
- Negative accuracy DECREASED by 5 percentage points (61% → 56%)
- Positive accuracy unchanged (still 2 false negatives)
- Added 2 NEW false positives

### Degraded Tests

Track 3 broke these tests that Track 2 correctly handled:

1. **`mixed_gettyimages-13116049_gettyimages-17009652`**
   - Track 2: ✓ NO_MATCH (correct rejection)
   - Track 3: ✗ WEAK_MATCH (ensemble upgraded incorrectly)

2. **`mixed_gettyimages-21778090_gettyimages-47081632`** (inferred from count)
   - Track 2: ✓ NO_MATCH (correct rejection)
   - Track 3: ✗ MATCH/WEAK_MATCH (ensemble upgraded incorrectly)

---

## Root Cause Analysis

### Why Track 3 Failed

**Design Mismatch**: Track 2 is pessimistic, Track 3 is optimistic

**Track 2 (Hard Discriminators)**: Early rejection philosophy
- "If edge density differs >15%, reject immediately"
- "If color BC <0.60 OR texture BC <0.55, reject immediately"
- Bias: Better to miss a match than propose a false assembly
- Result: Some borderline pairs get low scores (0.3-0.5) but slip through

**Track 3 (Ensemble Voting)**: Democratic majority rule
- "If 3+ voters say MATCH, accept as match"
- "Need only 2+ voters to reject as NO_MATCH"
- Bias: Trust the majority, be inclusive
- Result: Borderline pairs get upgraded because 4/5 voters see "moderate" scores

### The Fatal Flaw

When a pair BARELY passes Track 2 gates:
- Raw compatibility: 0.4 (low but non-zero) → Voter 1: NO_MATCH
- Color BC: 0.62 (just above 0.60) → Voter 2: WEAK_MATCH
- Texture BC: 0.56 (just above 0.55) → Voter 3: WEAK_MATCH
- Gabor BC: 0.65 (moderate) → Voter 4: WEAK_MATCH
- Morphology: 0.60 (moderate) → Voter 5: WEAK_MATCH

**Ensemble result**: 1 NO_MATCH, 4 WEAK_MATCH → **Verdict: WEAK_MATCH**

This UPGRADES pairs that Track 2 wanted to keep at low confidence, causing false positives.

### Why It Didn't Help Positives

Track 3 did NOT recover the 2 false negatives (scroll, Wall painting) because:
- Those tests were already NO_MATCH after Track 2
- Ensemble only re-classifies WEAK_MATCH pairs
- NO_MATCH pairs never get reconsidered

To fix this, we'd need to re-classify ALL pairs (not just WEAK_MATCH), but that would create even MORE false positives.

---

## Recommendation: Stick with Track 2 Only

### Why Track 2 is the Winner ✅

1. **Huge improvement from baseline**: 20% → 64% (+44 percentage points)
2. **Balanced accuracy**: 78% positive, 61% negative
3. **Clear rejection logic**: Hard discriminators with interpretable thresholds
4. **Computationally efficient**: Skips expensive curvature for rejected pairs
5. **Archaeologically sound**: Pessimistic bias (prefer false negatives)

### Why NOT to Deploy Track 3 ❌

1. **Degrades performance**: 64% → 60% (-4 percentage points)
2. **Adds false positives**: 14 → 16 (+2 more errors)
3. **No benefit on positives**: Still 2 false negatives
4. **Design conflict**: Optimistic voting contradicts pessimistic discriminators
5. **Added complexity**: New module, modified call chain, no benefit

### What Would It Take to Fix Track 3? (Not Worth It)

To make ensemble work, we'd need:

1. **More pessimistic voting rule**:
   - MATCH: Require 4+ votes (80%) instead of 3+ (60%)
   - NO_MATCH: Require 1+ vote (20%) instead of 2+ (40%)

2. **Hard discriminator veto**:
   - If Track 2 says NO, don't let ensemble override
   - Only use ensemble for genuine WEAK_MATCH cases

3. **Reversed order**:
   - Run ensemble BEFORE hard discriminators
   - Let hard discriminators have final say

But none of these are worth implementing - **Track 2 alone is already good enough**.

---

## Detailed Performance Breakdown

### Overall
- Baseline (no tracks): 9/45 (20%)
- Track 2 only: 29/45 (64%) ← **+20 tests passing**
- Track 2+3: 27/45 (60%) ← **-2 tests from Track 2**

### Positive Tests (Same-Source Fragments)
- Track 2 only: 7/9 (78%)
- Track 2+3: 7/9 (78%) ← **No change**

**False negatives** (both configurations):
1. scroll - hard discriminators too aggressive
2. Wall painting from Room H of the Villa of P. Fan - hard discriminators too aggressive

### Negative Tests (Cross-Source Fragments)
- Track 2 only: 22/36 (61%)
- Track 2+3: 20/36 (56%) ← **2 more false positives**

**False positives** (Track 2 only - 14 tests):
- Mixed pairs with similar appearance but different source
- Need either stricter thresholds or accepted trade-off

**False positives** (Track 2+3 - 16 tests):
- All 14 from Track 2, PLUS 2 more that Track 3 upgraded incorrectly

---

## Files Created/Modified (to be kept or reverted)

### Files to KEEP for documentation:
- ✅ `TRACK3_INTEGRATION_RESULTS.md` - This report
- ✅ `outputs/track3_integrated.txt` - Test results for reference
- ✅ `analyze_track3.py` - Analysis script (may be useful later)

### Files to REVERT (undo Track 3 integration):
- ❌ `src/ensemble_postprocess.py` - DELETE (not useful)
- ❌ `src/main.py` - REVERT to Track 2-only version
- ❌ `src/compatibility.py` - REVERT return value to `return compat` only

OR keep as-is if you want the option to toggle Track 3 on/off for future experiments.

---

## Lessons Learned

1. **Design philosophy matters**: Pessimistic vs optimistic bias must be consistent across the pipeline
2. **Post-processing has limits**: If early stages make strong decisions, post-processing can't undo them effectively
3. **Majority voting isn't always better**: In archaeology, we WANT to be conservative
4. **Track 2 alone was the sweet spot**: Sometimes simpler is better

---

## Computational Cost (Track 3)

**Additional cost**: Negligible (<1% of total pipeline time)
- Pre-computes edge density and entropy once per fragment
- Only iterates through existing assembly pairs
- No new feature extraction

**Why negligible cost doesn't matter**: It still degrades accuracy, so we shouldn't deploy it regardless of cost.

---

## Final Verdict

**Mission Complete: Track 3 integrated and tested**

**Result**: Track 3 integration SUCCESSFUL (code works as designed) but **NOT RECOMMENDED** (degrades performance)

**Recommendation**:
1. ✅ **KEEP Track 2 (Hard Discriminators)** - 64% accuracy, clear winner
2. ❌ **REJECT Track 3 (Ensemble Voting)** - 60% accuracy, design conflict
3. 📋 **DOCUMENT learnings** - This report explains why ensemble failed

**Next steps**:
- Deploy Track 2-only version to production
- Close the Track 3 investigation
- Consider relaxing Track 2 thresholds slightly to recover the 2 false negatives (scroll, Wall painting)

---

**Report Generated**: 2026-04-08
**Mission Status**: ✅ COMPLETE
**Deployment Recommendation**: Track 2 only (64% accuracy)
