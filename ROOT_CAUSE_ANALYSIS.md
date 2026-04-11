# ROOT CAUSE ANALYSIS: Baseline False Positives

## Problem Statement
Variant 0 (Stage 1.6 Baseline) achieves only **55.6% negative accuracy** (20/36) instead of the claimed 86%.
**16 false positives** occur where cross-source fragments are incorrectly matched.

## Root Cause Identified

**File**: `src/main.py` lines 60-61, 97-98

**The Issue**: Color pre-check thresholds are TOO LENIENT

```python
COLOR_PRECHECK_GAP_THRESH = 0.25    # Requires 25% gap (TOO HIGH)
COLOR_PRECHECK_LOW_MAX = 0.62       # Low group max 0.62 (TOO HIGH)
```

The `detect_mixed_source_fragments()` function is supposed to reject cross-source pairs early based on bimodal color distribution. However:

1. **Getty images + scroll/pottery** have BC ~0.65-0.75 (moderately similar colors)
2. This PASSES the threshold (0.65 > 0.62) so pre-check doesn't reject
3. Pairs proceed to geometric matching where they match on curvature
4. Result: FALSE POSITIVE

## Evidence from False Positives

All 16 false positives are cross-source matches:
- Getty image 17009652 ↔ Getty 21778090
- Getty 21778090 ↔ scroll
- Getty 21778090 ↔ british shard
- Wall painting ↔ scroll
- etc.

These should be caught by color pre-check but aren't.

## Proposed Fixes

### Fix 1: TIGHTEN Color Pre-check Thresholds (Recommended)

**File**: `src/main.py` lines 60-61

```python
# BEFORE (current - too lenient):
COLOR_PRECHECK_GAP_THRESH = 0.25
COLOR_PRECHECK_LOW_MAX = 0.62

# AFTER (stricter):
COLOR_PRECHECK_GAP_THRESH = 0.15    # Lower gap requirement (more sensitive)
COLOR_PRECHECK_LOW_MAX = 0.75       # Higher threshold (catches more cross-source)
```

**Expected Impact**:
- Catches BC pairs in 0.62-0.75 range
- Should eliminate 10-12 of the 16 false positives
- Target: 75-80% negative accuracy (vs current 55.6%)

### Fix 2: STRENGTHEN Hard Discriminators (Alternative)

**File**: `src/hard_discriminators.py` lines 124

```python
# BEFORE:
if bc_color < 0.60 or bc_texture < 0.55:

# AFTER:
if bc_color < 0.70 or bc_texture < 0.65:  # Stricter thresholds
```

**Expected Impact**:
- Rejects more pairs during compatibility computation
- Catches cases that slip through pre-check
- Target: 70-75% negative accuracy

### Fix 3: LOWER Relaxation Thresholds (Conservative)

**File**: `src/relaxation.py` lines 47-49

```python
# BEFORE:
MATCH_SCORE_THRESHOLD = 0.75
WEAK_MATCH_SCORE_THRESHOLD = 0.60
ASSEMBLY_CONFIDENCE_THRESHOLD = 0.65

# AFTER:
MATCH_SCORE_THRESHOLD = 0.80  # Require higher confidence for MATCH
WEAK_MATCH_SCORE_THRESHOLD = 0.65
ASSEMBLY_CONFIDENCE_THRESHOLD = 0.70
```

**Expected Impact**:
- Reduces false positives by requiring higher scores
- May also reduce true positives (trade-off)
- Target: 65-70% negative accuracy, 80-85% positive

## Recommended Approach

**Phase 1**: Apply Fix 1 (color pre-check) first
- Most targeted fix
- Affects only cross-source detection
- Minimal risk to true positives

**Phase 2**: If still < 80% negative accuracy, add Fix 2 (hard discriminators)
- Provides additional safety net
- Catches cases that slip through pre-check

**Phase 3**: If needed, carefully tune Fix 3 (relaxation thresholds)
- Last resort as it affects all cases
- Risk of reducing true positive rate

## Testing Plan

1. Create `src/main_variant_fixed.py` with Fix 1 applied
2. Run Variant 0 with fixed thresholds
3. Measure: Positive accuracy, Negative accuracy
4. If negative < 80%, apply Fix 2
5. Iterate until 85%+ negative, 85%+ positive achieved

## Success Criteria

- **Minimum**: 75%+ negative accuracy (vs 55.6% current)
- **Target**: 85%+ negative accuracy (close to claimed 86%)
- **Preserve**: 85%+ positive accuracy (current 88.9%)
