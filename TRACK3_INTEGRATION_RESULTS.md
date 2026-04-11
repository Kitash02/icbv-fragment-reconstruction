# TRACK 3 (ENSEMBLE VOTING) INTEGRATION RESULTS

## Executive Summary

Track 3 integration is **DEGRADED**. Ensemble voting decreased overall accuracy by 4 percentage points (64% → 60%).

**Verdict: DO NOT DEPLOY Track 3**

The ensemble post-processing filter actually made things worse, converting some correct NO_MATCH verdicts (from Track 2 hard discriminators) into incorrect MATCH/WEAK_MATCH verdicts through the voting mechanism.

---

## Performance Comparison

### Track 2 Only (Hard Discriminators)
```
Overall Accuracy: 29/45 (64%)
├─ Positive Tests: 7/9 (78%)   ← 2 false negatives
└─ Negative Tests: 22/36 (61%) ← 22 true negatives, 14 false positives
```

### Track 2+3 (Hard Discriminators + Ensemble Voting)
```
Overall Accuracy: 27/45 (60%)
├─ Positive Tests: 7/9 (78%)   ← 2 false negatives (no change)
└─ Negative Tests: 20/36 (56%) ← 20 true negatives, 16 false positives
```

**Result**: Ensemble voting WORSENED negative accuracy by 5 percentage points.

---

## Changes Summary

| Metric | Track 2 | Track 2+3 | Change |
|--------|---------|-----------|--------|
| **Overall Accuracy** | 64% | 60% | **-4 points** ❌ |
| **Positive Accuracy** | 78% | 78% | 0 points |
| **Negative Accuracy** | 61% | 56% | **-5 points** ❌ |
| **False Positives** | 14 | 16 | **+2** ❌ |
| **False Negatives** | 2 | 2 | 0 |

---

## What Went Wrong?

### Degraded Tests (2 tests: Track 2 PASS → Track 3 FAIL)

Track 3 broke these tests that Track 2 correctly handled:

1. **`mixed_gettyimages-13116049_gettyimages-17009652`**
   - Track 2: NO_MATCH ✓ (correct rejection)
   - Track 3: WEAK_MATCH ✗ (ensemble upgraded to weak match)
   - Reason: Ensemble voting gave too much weight to geometric similarity despite hard discriminators flagging appearance mismatch

2. **`mixed_gettyimages-21778090_gettyimages-47081632`** (likely based on pattern)
   - Track 2: NO_MATCH ✓ (correct rejection)
   - Track 3: MATCH/WEAK_MATCH ✗ (ensemble upgraded)
   - Reason: Same issue - voting overrode hard discriminator rejection

### Root Cause Analysis

The ensemble post-processing filter has a **fundamental design flaw**:

1. **Hard discriminators (Track 2)** are VERY effective at rejecting incompatible pairs early
   - They look at edge density, texture entropy, and appearance BC
   - They say "NO" to pairs that are clearly incompatible
   - This produces compat_matrix entries of 0.0 for rejected pairs

2. **Ensemble voting (Track 3)** then tries to re-classify WEAK_MATCH cases
   - BUT some pairs that SHOULD be NO_MATCH slipped through Track 2 with low scores
   - The ensemble voters see:
     - Geometric score: Low but non-zero (e.g., 0.3-0.5)
     - Color/texture BC: Moderate (e.g., 0.6-0.7) - passed hard discriminator gates
     - Gabor/morphology: Moderate
   - With 5 voters all giving moderate scores, the ensemble UPGRADES to WEAK_MATCH or MATCH
   - This OVERRIDES the Track 2 rejection logic

3. **The problem**: Track 3 treats all features equally via voting
   - Track 2's hard discriminators are PESSIMISTIC (prefer false negatives)
   - Track 3's ensemble is OPTIMISTIC (3+ MATCH votes = MATCH)
   - This mismatch causes Track 3 to undo Track 2's good work

---

## Analysis: Why Ensemble Voting Failed

### Design Mismatch

**Track 2 (Hard Discriminators)**: Early rejection, pessimistic
- "If edge density differs by >15%, reject immediately"
- "If color BC <0.60 OR texture BC <0.55, reject immediately"
- Philosophy: Better to miss a match than propose a false assembly

**Track 3 (Ensemble Voting)**: Democratic voting, optimistic
- "If 3+ voters say MATCH, it's a match"
- "Only 2+ NO_MATCH votes needed to reject"
- Philosophy: Trust the majority, even if one discriminator disagrees

### The Fatal Flaw

When Track 2 rejects a pair early (e.g., edge density too different), that pair gets:
- compat_matrix score = 0.0 (no curvature computed)
- assembly verdict = NO_MATCH

But if a similar pair BARELY passes Track 2 gates, it gets:
- compat_matrix score = 0.4 (low but non-zero)
- Color BC = 0.62 (just above 0.60 threshold)
- Texture BC = 0.56 (just above 0.55 threshold)
- assembly verdict = WEAK_MATCH

Then Track 3 ensemble sees:
- Voter 1 (raw_compat=0.4): NO_MATCH
- Voter 2 (color=0.62): WEAK_MATCH
- Voter 3 (texture=0.56): WEAK_MATCH
- Voter 4 (gabor=0.65): WEAK_MATCH
- Voter 5 (morphology=0.60): WEAK_MATCH

Result: 1 NO_MATCH, 4 WEAK_MATCH → **Ensemble verdict: WEAK_MATCH** (upgrades from Track 2's intended rejection)

---

## Positive Tests: No Change

Track 3 did NOT help recover the 2 false negatives from Track 2:
- **scroll**: Still NO_MATCH (Track 2 hard discriminators too aggressive)
- **Wall painting**: Still NO_MATCH (Track 2 hard discriminators too aggressive)

Why? The ensemble only re-classifies WEAK_MATCH pairs. These pairs were already NO_MATCH after Track 2, so the ensemble never got a chance to reconsider them.

---

## Recommendation

### REJECT TRACK 3 ❌

**Reasons**:
1. **Degrades performance**: -4 percentage points overall, -5 points on negatives
2. **Design mismatch**: Optimistic voting contradicts pessimistic hard discriminators
3. **No benefit on positives**: Didn't recover any of the 2 false negatives
4. **Added complexity**: New file, modified call chain, more computational cost
5. **Philosophical conflict**: Archaeology prefers false negatives; ensemble prefers false positives

### Alternative: Stick with Track 2 Only ✅

Track 2 (Hard Discriminators) achieved:
- 64% overall accuracy (+44 points from baseline 20%)
- 78% positive accuracy (7/9 pass)
- 61% negative accuracy (22/36 pass)
- Clear improvement over Stage 1.6

**Track 2 is the winner. Stop here.**

---

## If We Wanted to Fix Track 3 (Not Recommended)

To make ensemble voting work, we would need to:

1. **Change voting rule to be pessimistic**:
   - MATCH: Require 4+ MATCH votes (80% confidence) instead of 3+
   - NO_MATCH: Require only 1+ NO_MATCH vote (20% rejection) instead of 2+
   - This would align with archaeological pessimistic bias

2. **Give hard discriminators veto power**:
   - If Track 2 says NO_MATCH, don't let ensemble override
   - Only use ensemble for genuine WEAK_MATCH cases, not rejected pairs

3. **Use ensemble BEFORE hard discriminators**:
   - Flip the order: ensemble first, hard discriminators as final filter
   - This way hard discriminators get the last word

But none of these are worth it - **Track 2 alone is already good enough**.

---

## Detailed Test Results

### Positive Tests (Same-Source Fragments)
Both Track 2 and Track 2+3: 7/9 pass (78%)

**Passing**:
- gettyimages-1311604917-1024x1024
- gettyimages-170096524-1024x1024
- gettyimages-2177809001-1024x1024
- gettyimages-470816328-2048x2048
- high-res-antique-close-up-earth-muted-tones-geom
- shard_01_british
- shard_02_cord_marked

**Failing** (both Track 2 and Track 2+3):
- scroll (hard discriminators too aggressive)
- Wall painting from Room H of the Villa of P. Fan (hard discriminators too aggressive)

### Negative Tests (Cross-Source Fragments)
- Track 2: 22/36 pass (61%)
- Track 2+3: 20/36 pass (56%) ← **2 more failures**

**Tests degraded by Track 3**:
1. mixed_gettyimages-13116049_gettyimages-17009652 (NO_MATCH → WEAK_MATCH)
2. One other test (likely mixed_gettyimages-21778090_gettyimages-47081632)

---

## Implementation Details

### Files Created/Modified

1. **`src/ensemble_postprocess.py`** (NEW - 200+ lines)
   - Function: `reclassify_borderline_cases()`
   - Re-classifies WEAK_MATCH pairs using 5-way voting
   - Recomputes assembly verdicts after re-classification

2. **`src/main.py`** (MODIFIED)
   - Added import: `from ensemble_postprocess import reclassify_borderline_cases`
   - Added post-processing call after relaxation labeling
   - Added logging for ensemble statistics

3. **`src/compatibility.py`** (MODIFIED)
   - Changed return value: `return compat, appearance_mats` (was: `return compat`)
   - Now returns both compatibility matrix and appearance matrices

### How It Works

1. Relaxation labeling produces assemblies with MATCH/WEAK_MATCH/NO_MATCH verdicts
2. Ensemble post-processor iterates through all assemblies
3. For each WEAK_MATCH pair, compute 5 votes:
   - Voter 1: Raw compatibility (geometric)
   - Voter 2: Color BC (Lab histogram)
   - Voter 3: Texture BC (LBP histogram)
   - Voter 4: Gabor BC (frequency-domain)
   - Voter 5: Morphological (edge density + entropy)
4. Apply voting rule: 3+ MATCH = MATCH, 2+ NO_MATCH = NO_MATCH, else WEAK_MATCH
5. Update pair verdict and recompute assembly verdict

### Computational Cost

- Negligible: Only re-classifies existing pairs, no new feature computation
- Pre-computes edge density and entropy for all fragments once
- Typical overhead: <1% of total pipeline time

### Statistics Logged

From ensemble post-processing:
- Total pairs re-classified
- Upgraded (WEAK → MATCH)
- Downgraded (WEAK → NO_MATCH)
- Assemblies with verdict changes

---

## Conclusion

**Track 3 (Ensemble Voting) FAILED to improve performance.**

- Overall accuracy: 64% → 60% (-4 points)
- Negative accuracy: 61% → 56% (-5 points)
- Added 2 false positives
- Recovered 0 false negatives

**Root cause**: Optimistic voting contradicts pessimistic hard discriminators, causing Track 3 to upgrade pairs that Track 2 correctly wanted to reject.

**Final recommendation**:
1. **REVERT Track 3 changes** - undo modifications to main.py and compatibility.py
2. **KEEP Track 2 (Hard Discriminators)** - this is the winner (64% accuracy, +44 points from baseline)
3. **DO NOT attempt ensemble voting again** - design mismatch is fundamental

---

## Files Modified (to be reverted)

- `src/ensemble_postprocess.py` - DELETE this file
- `src/main.py` - REVERT to Track 2-only version
- `src/compatibility.py` - REVERT return value to `return compat` only
- `outputs/track3_integrated.txt` - Test results (keep for reference)
- `TRACK3_INTEGRATION_RESULTS.md` - This report (keep for documentation)

---

**Report Generated**: 2026-04-08
**Integration Status**: ❌ FAILED - DO NOT DEPLOY
**Final Recommendation**: Stick with Track 2 only (64% accuracy)
