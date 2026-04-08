# NEGATIVE TEST CASE FAILURE ANALYSIS
## Why ALL 36 Negative Cases Fail (0% Accuracy)

**Date:** 2026-04-08
**Status:** CRITICAL - Complete failure on negative test cases
**Test Results:** 9/45 PASS (100% positive, 0% negative)

---

## EXECUTIVE SUMMARY

All 36 negative test cases incorrectly predict "MATCH" when they should predict "NO_MATCH". The system successfully matches all 9 positive cases but fails to reject ANY mixed-pottery cases.

### Root Cause
**Geometric features are NOT discriminative enough.** The Lab color + LBP texture + exponential penalty system produces compatibility scores that are TOO HIGH for cross-pottery pairs, causing the system to accept assemblies that should be rejected.

### Critical Statistics from Test Data

From test heatmap visualization (mixed_gettyimages-13116049_gettyimages-17009652):
- **Color BC gap:** 0.194 (within-group: 0.974, cross-group: 0.780)
  - TOO SMALL to trigger pre-check rejection (threshold: gap > 0.25 AND low_max < 0.62)
  - Cross-group BC of 0.78 is still "similar" - pottery fragments often have similar earth tones

- **Geometric compatibility scores:** Visible in heatmap showing extensive red/orange regions (0.4-0.8 range)
  - Even cross-pottery pairs achieve high scores
  - Assembly confidence: **0.69** (exceeds 0.60 threshold)

- **Verdict Logic:** Assembly classified as "MATCH" if ≥60% pairs are MATCH (>0.70) OR ≥40% are valid (>0.50)
  - Current thresholds: MATCH=0.70, WEAK=0.50, ASSEMBLY=0.60
  - These were "raised for pottery" but still insufficient

---

## DETAILED ANALYSIS

### 1. Test Dataset Structure

**Negative test case structure:**
```
data/examples/negative/mixed_[pottery_A]_[pottery_B]/
  A_00_[source_A]_frag_00.png  ← 3 fragments from pottery A
  A_01_[source_A]_frag_01.png
  A_02_[source_A]_frag_02.png
  B_03_[source_B]_frag_00.png  ← 3 fragments from pottery B
  B_04_[source_B]_frag_01.png
  B_05_[source_B]_frag_02.png
```

**Expected behavior:** System should detect these are from different source pottery and return "NO_MATCH"

**Actual behavior:** System finds high-confidence assemblies (0.69+) and returns "OK MATCH"

---

### 2. Why Color Pre-Check Fails

**Color Pre-Check Logic** (main.py lines 63-98):
```python
COLOR_PRECHECK_GAP_THRESH = 0.25    # minimum gap between low and high BC group
COLOR_PRECHECK_LOW_MAX = 0.62       # max allowed BC in the "low" group
```

**Rejection criteria:** BOTH conditions must be true:
1. `max_gap >= 0.25` (clear bimodal separation)
2. `low_group_max <= 0.62` (low group is clearly different)

**Why it fails on negative cases:**

Example (mixed_gettyimages-13116049_gettyimages-17009652):
- Within-group BC: 0.936-0.998 (mean 0.974) ← fragments from same pottery
- Cross-group BC: 0.712-0.822 (mean 0.780) ← fragments from DIFFERENT pottery
- Max gap: 0.115 (FAILS threshold of 0.25)
- Low group max: 0.822 (FAILS threshold of 0.62 - too high!)

**Problem:** Pottery fragments from different sources often have:
- Similar color palettes (earth tones, terracotta, browns)
- BC scores of 0.75-0.85 for cross-pottery pairs
- Not enough separation to detect via color alone

The pre-check is **too conservative** - designed to avoid false positives on positive cases, but misses obvious negative cases.

---

### 3. Why Geometric Features Fail

**Current Feature Pipeline:**
1. **Chain code edit distance** (0.0-1.0)
2. **Good continuation bonus** (0.0-0.10, weight 0.10)
3. **Fourier descriptor score** (0.0-0.15, weight 0.15)
4. **Max possible score:** 1.0 + 0.10 + 0.15 = 1.25

**Thresholds** (relaxation.py lines 47-49):
```python
MATCH_SCORE_THRESHOLD = 0.70        # "raised for pottery"
WEAK_MATCH_SCORE_THRESHOLD = 0.50
ASSEMBLY_CONFIDENCE_THRESHOLD = 0.60
```

**Problem:** Chain codes are TOO SIMILAR across different pottery

Why chain codes fail to discriminate:
1. **Limited vocabulary:** 8-directional Freeman codes have low information content
2. **Pottery shape similarity:** Many pottery fragments share:
   - Curved edges (circular/cylindrical vessels)
   - Similar break patterns (stress fractures tend to have predictable geometry)
   - Roughly similar scale and aspect ratios

3. **Edit distance is forgiving:** Normalized edit distance allows for substantial differences while still producing scores >0.60

4. **Bonuses amplify noise:**
   - Good continuation bonus rewards smooth curves (common in pottery)
   - Fourier descriptors capture low-frequency shape but miss fine details
   - Both bonuses can push marginal pairs (0.55) over threshold (0.70)

**Evidence from heatmap:**
- Extensive regions of 0.4-0.6 scores even for cross-pottery pairs
- Maximum scores reach 0.7-0.8 range
- Enough pairs exceed 0.50 to trigger "MATCH" verdict

---

### 4. Why Assembly Logic Accepts False Positives

**Assembly Classification** (relaxation.py lines 178-215):

```python
def classify_assembly(confidence, matched_pairs):
    frac_strong = n_strong / n_pairs  # pairs with raw_compat >= 0.70
    frac_valid = n_valid / n_pairs    # pairs with raw_compat >= 0.50

    if frac_strong >= 0.60 and frac_valid >= 0.40:
        return "MATCH"      # ← This is too permissive!
    if frac_valid >= 0.40:
        return "WEAK_MATCH"
    return "NO_MATCH"
```

**Problem:** Only need 40% of pairs to be "valid" (>0.50) to get WEAK_MATCH, and relaxation labeling will concentrate probability on the best pairs.

**What happens on negative cases:**
1. 6 fragments × 4 segments = 24 segments
2. Even with mostly random pairings, some pairs will score 0.50-0.70 by chance
3. Relaxation labeling amplifies these "best of bad" pairs
4. Result: 40-60% of pairs exceed 0.50 → "MATCH" or "WEAK_MATCH"
5. Assembly confidence 0.60-0.70 → accepted

---

## QUANTITATIVE BREAKDOWN

### Threshold Analysis

| Threshold | Value | Purpose | Problem |
|-----------|-------|---------|---------|
| COLOR_PRECHECK_GAP | 0.25 | Detect bimodal BC distribution | Pottery pairs show gap ~0.10-0.20 (MISS) |
| COLOR_PRECHECK_LOW_MAX | 0.62 | Max BC in "different" group | Pottery pairs have BC ~0.75-0.85 (TOO HIGH) |
| MATCH_SCORE | 0.70 | Raw compatibility for confident match | Many cross-pottery pairs reach 0.60-0.75 (PASS) |
| WEAK_MATCH_SCORE | 0.50 | Raw compatibility for possible match | Most pairs exceed this (NOT SELECTIVE) |
| ASSEMBLY_CONFIDENCE | 0.60 | Mean probability across pairs | Relaxation easily reaches this (TOO LOW) |

### Expected vs Actual Scores

| Metric | Expected (Negative) | Actual (Negative) | Gap |
|--------|---------------------|-------------------|-----|
| Color BC (cross-pottery) | 0.30-0.50 | 0.75-0.85 | **+0.35** |
| Max geometric compat | <0.40 | 0.65-0.80 | **+0.35** |
| Assembly confidence | <0.40 | 0.60-0.75 | **+0.30** |

**Conclusion:** All scores are systematically 0.30-0.35 points too high for negative cases.

---

## ROOT CAUSE SUMMARY

### Primary Cause: Feature Weakness
**Chain codes cannot discriminate between pottery fragments from different sources.**

- Freeman 8-direction codes are too coarse
- Pottery geometry (curves, breaks) is too similar across artifacts
- Edit distance metric is too forgiving
- Current bonuses (good continuation, Fourier) add noise rather than signal

### Secondary Cause: Threshold Miscalibration
**Thresholds were tuned for positive cases, not validated on negatives.**

- Color pre-check: Conservative (avoid false positives)
- Geometric thresholds: Too low (accept marginal matches)
- Assembly logic: Too permissive (40% valid pairs → MATCH)

### Tertiary Cause: Missing Discriminative Features
**The system lacks features that would separate similar-looking pottery:**

- No texture detail beyond coarse LBP
- No material/surface properties
- No thickness or 3D geometry
- No detailed edge rugosity/complexity measures

---

## PLAN B: SOLUTION OPTIONS

### Option 1: AGGRESSIVE THRESHOLD INCREASE (Quick Fix)
**Approach:** Raise all thresholds to force rejection of marginal cases

**Changes:**
```python
# Current
MATCH_SCORE_THRESHOLD = 0.70
WEAK_MATCH_SCORE_THRESHOLD = 0.50
ASSEMBLY_CONFIDENCE_THRESHOLD = 0.60

# Proposed
MATCH_SCORE_THRESHOLD = 0.85        # +0.15 (few pairs will pass)
WEAK_MATCH_SCORE_THRESHOLD = 0.70   # +0.20 (only strong pairs)
ASSEMBLY_CONFIDENCE_THRESHOLD = 0.75 # +0.15 (high bar)

# Assembly logic
frac_strong >= 0.80  # Need 80% of pairs to be MATCH (was 60%)
frac_valid >= 0.60   # Need 60% to be valid (was 40%)
```

**Expected Impact:**
- Negative accuracy: 0% → **60-80%** (should reject most mixed cases)
- Positive accuracy: 100% → **70-90%** (may lose some weak true matches)
- Trade-off: **False negatives on positive cases**

**Risk:** May be too aggressive, rejecting valid but noisy positive matches.

**Effort:** 5 minutes to implement, 30 minutes to validate

---

### Option 2: STRENGTHEN COLOR PRE-CHECK (Medium Fix)
**Approach:** Make color rejection more sensitive

**Changes:**
```python
# Current
COLOR_PRECHECK_GAP_THRESH = 0.25
COLOR_PRECHECK_LOW_MAX = 0.62

# Proposed
COLOR_PRECHECK_GAP_THRESH = 0.15    # Detect smaller gaps
COLOR_PRECHECK_LOW_MAX = 0.75       # Accept that pottery is similar
# AND change logic to single condition (not both required)

# New logic: Reject if gap >= 0.15 OR low_max <= 0.75
```

**Expected Impact:**
- Catches bimodal cases with gap 0.15-0.25 (many negative cases)
- Still allows unimodal positive cases to proceed
- Negative accuracy: 0% → **40-60%**
- Positive accuracy: Unchanged (100%)

**Risk:** Medium - may still miss cases where pottery is very similar

**Effort:** 10 minutes to implement, 20 minutes to validate

---

### Option 3: ADD DISCRIMINATIVE FEATURES (Best Fix, Longer)
**Approach:** Add features that capture pottery-specific differences

**New Features:**

1. **Edge Complexity Score**
   - Measure contour roughness/jaggedness
   - Break patterns differ between pottery types
   - Implementation: Curvature variance, wavelet energy

2. **Multi-Scale Texture**
   - Use Gabor filters at multiple scales
   - Capture fine surface texture detail
   - Current LBP is too coarse

3. **Statistical Shape Context**
   - Histogram of relative positions of contour points
   - More discriminative than chain codes
   - Captures global shape structure

4. **Thickness Estimation**
   - Estimate vessel wall thickness from edges
   - Different pottery types have different thicknesses
   - Implementation: Detect inner/outer contours

**Expected Impact:**
- Negative accuracy: 0% → **80-95%**
- Positive accuracy: Maintained at **95-100%**
- True discriminative power rather than just threshold adjustment

**Risk:** Low - adds genuine signal

**Effort:** 4-6 hours implementation, 2 hours validation

---

### Option 4: ENSEMBLE VOTING (Robust Fix)
**Approach:** Require multiple independent signals to agree

**Strategy:**
```python
# Match decision requires 3 of 4 criteria:
1. Color BC median > 0.85 (within-group similarity)
2. Geometric score > 0.75 (strong shape match)
3. Texture BC > 0.80 (detailed texture match)  ← NEW
4. No bimodal color distribution (gap < 0.15)
```

**Expected Impact:**
- Negative accuracy: 0% → **70-85%**
- Positive accuracy: 100% → **95%** (slight loss on noisy cases)
- More robust than single-feature threshold

**Risk:** Low-Medium - conservative, may miss some valid matches

**Effort:** 2-3 hours to implement, 1 hour to validate

---

## RECOMMENDATIONS (PRIORITIZED)

### IMMEDIATE (Next 30 Minutes)
**Option 1 + Option 2 Hybrid:** Moderate threshold increase + improved color pre-check

```python
# Balanced adjustment
MATCH_SCORE_THRESHOLD = 0.78        # +0.08 (more selective)
WEAK_MATCH_SCORE_THRESHOLD = 0.60   # +0.10 (higher bar)
ASSEMBLY_CONFIDENCE_THRESHOLD = 0.68 # +0.08 (stricter)

# Assembly logic
frac_strong >= 0.70  # Need 70% MATCH pairs
frac_valid >= 0.50   # Need 50% valid pairs

# Color pre-check
COLOR_PRECHECK_GAP_THRESH = 0.18    # More sensitive
COLOR_PRECHECK_LOW_MAX = 0.72       # More realistic
```

**Expected Result:**
- Negative: 0% → 50-70%
- Positive: 100% → 90-95%
- **Total accuracy: 80-85%** (acceptable for course project)

**Validation:** Run `python run_test.py` and check results

---

### SHORT-TERM (Next 2-4 Hours)
**Option 3: Add Edge Complexity Feature**

Implement single most discriminative feature:
```python
def compute_edge_complexity(contour):
    """Measure contour roughness via curvature variance."""
    curvatures = compute_curvature(contour)
    return np.std(curvatures) / (np.mean(np.abs(curvatures)) + 1e-6)

# Add to compatibility scoring:
complexity_i = compute_edge_complexity(contour_i)
complexity_j = compute_edge_complexity(contour_j)
complexity_score = 1.0 - abs(complexity_i - complexity_j) / max(complexity_i, complexity_j)

# Weight: 0.20 (significant contribution)
total_score = 0.60 * edit_score + 0.10 * continuation + 0.10 * fourier + 0.20 * complexity
```

**Expected Result:**
- Adds genuine discriminative power
- Negative: 0% → 70-85%
- Positive: Maintained at 95-100%

---

### LONG-TERM (Next Session)
**Option 4: Full Ensemble System**

Implement multi-feature voting with proper validation:
1. Keep existing features
2. Add edge complexity + multi-scale texture
3. Implement voting logic
4. Cross-validate on held-out test set

**Expected Result:**
- Negative: 85-95%
- Positive: 95-100%
- **Total: 90-97%** (publication-quality)

---

## VALIDATION PLAN

After implementing fixes:

### 1. Spot Check (5 negative cases)
```bash
python run_test.py --negative-only --examples data/examples
# Check first 5 results - should see some NO_MATCH verdicts
```

### 2. Full Test Suite
```bash
python run_test.py
# Target: 9/9 positive + 25/36 negative = 34/45 (75%+)
```

### 3. Detailed Analysis
- Check BC distributions for rejected cases
- Verify geometric scores are below new thresholds
- Ensure no false negatives on positive cases

---

## CRITICAL INSIGHTS

### What We Learned

1. **Color similarity is NOT enough for pottery discrimination**
   - Different pottery can have very similar color palettes
   - BC scores 0.75-0.85 are common for cross-pottery pairs

2. **Chain codes have fundamental limitations**
   - Too coarse for fine shape discrimination
   - Pottery geometry is surprisingly similar across artifacts

3. **Threshold tuning requires negative validation**
   - Tuning on only positive cases leads to over-permissive system
   - Need balanced validation set from the start

4. **Relaxation labeling amplifies best pairs**
   - Even with weak overall compatibility, RL finds "best of bad" matches
   - Makes threshold choice even more critical

### What Would Work Better

1. **Learning-based features** (if allowed by course requirements)
   - Learned CNN features would capture subtle pottery differences
   - But this is a classical CV course project

2. **3D geometry** (if available)
   - Thickness, curvature profiles, surface normals
   - But we only have 2D images

3. **Higher-resolution chain codes** (practical improvement)
   - 16 or 32 directions instead of 8
   - Capture finer geometric detail

4. **Material-specific features** (domain knowledge)
   - Pottery has specific properties: glaze, firing marks, clay texture
   - Could design features specifically for pottery discrimination

---

## CONCLUSION

**Current State:** System cannot discriminate negative cases (0% accuracy)

**Root Cause:** Geometric features too weak + thresholds too low

**Immediate Fix:** Raise thresholds (MATCH=0.78, WEAK=0.60, ASSEMBLY=0.68, assembly logic 70/50)

**Expected Impact:** Negative accuracy 50-70%, Positive accuracy 90-95%, Total 75-85%

**Better Fix:** Add edge complexity feature → 80-90% total accuracy

**Best Fix:** Full ensemble with multiple features → 90-95% total accuracy

**Action Required:** Implement immediate fix (30 min) → validate → iterate if needed

---

**Status:** Analysis complete. Ready for implementation.
**Next Step:** Implement hybrid threshold + color pre-check fix and run validation.
