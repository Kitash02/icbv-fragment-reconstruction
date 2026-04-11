# QUICK REFERENCE - Code Changes Summary

**Date:** 2026-04-08
**Session:** ece07127-20d3-460a-a966-c2c82ecfcf43

---

## TL;DR - What Changed

### Before (Baseline)
```python
# src/compatibility.py - Subtractive penalty
color_penalty = (1.0 - bc) * COLOR_PENALTY_WEIGHT
score = max(0.0, score - color_penalty)

# src/relaxation.py - Low thresholds
MATCH_SCORE_THRESHOLD = 0.55
WEAK_MATCH_SCORE_THRESHOLD = 0.35
ASSEMBLY_CONFIDENCE_THRESHOLD = 0.45
```

**Performance:** 100% positive (9/9), 53% negative (19/36)

### After (Stage 1.6 - Final)
```python
# src/compatibility.py - Multiplicative penalty
bc_color = color_sim_mat[frag_i, frag_j]
bc_texture = texture_sim_mat[frag_i, frag_j]
bc_gabor = gabor_sim_mat[frag_i, frag_j]
bc_haralick = haralick_sim_mat[frag_i, frag_j]

appearance_multiplier = (bc_color ** 4.0) * (bc_texture ** 2.0) * (bc_gabor ** 2.0) * (bc_haralick ** 2.0)
score = score * appearance_multiplier

# src/relaxation.py - Balanced thresholds
MATCH_SCORE_THRESHOLD = 0.75
WEAK_MATCH_SCORE_THRESHOLD = 0.60
ASSEMBLY_CONFIDENCE_THRESHOLD = 0.65
```

**Performance:** 89% positive (8/9), 86% negative (31/36)
**Improvement:** +33 percentage points on negative accuracy

---

## Files Modified

### 1. src/compatibility.py (12 changes)
- **Line 6:** Added `from skimage.feature import local_binary_pattern`
- **Line 98:** Added `compute_texture_signature()` function
- **Line 139:** Added `texture_bhattacharyya()` function
- **Line 159:** Added texture similarity matrix computation
- **Line 425:** Changed color penalty from subtractive to multiplicative
- **Line 425:** Increased penalty power (2.5 → 4.0 → 6.0 → 4.0)
- **Line 425:** Added texture/gabor/haralick combination

### 2. src/relaxation.py (4 changes)
- **Line 47-49:** Adjusted thresholds
  - MATCH: 0.55 → 0.70 → 0.85 → 0.75
  - WEAK: 0.35 → 0.50 → 0.70 → 0.60
  - ASSEMBLY: 0.45 → 0.60 → 0.75 → 0.65

---

## Stage Evolution

| Stage | Key Change | Positive | Negative | Notes |
|-------|-----------|----------|----------|-------|
| Baseline | Subtractive penalty | 100% | 53% | Too permissive |
| Stage 1 | color^6 multiplicative | 33% | 83% | Too harsh |
| Stage 1.5 | color^4 multiplicative | 56% | 94% | Better but low positives |
| Stage 1.6 | color^4 + lower thresholds | **89%** | **86%** | ✅ BALANCED |

---

## Why It Works

### 1. Multiplicative > Subtractive
**Old:** `score - (1-BC)*0.80`
- BC=0.85 → penalty=0.12 (only 12% reduction)

**New:** `score * BC^4`
- BC=0.85 → multiplier=0.52 (48% reduction)
- Compounds dissimilarities across features

### 2. Feature Weighting
- **Color (power=4):** Most discriminative (pigment chemistry)
- **Texture/Gabor/Haralick (power=2):** Material class indicators
- Combined: Artifact-specific signature

### 3. Balanced Thresholds
- Stage 1: Thresholds too high (0.85) → rejected true positives
- Stage 1.6: Lowered to 0.75 → accepts positives while rejecting negatives

---

## Current Code Locations

### Appearance Penalty (src/compatibility.py ~line 425)
```python
if color_sim_mat is not None and texture_sim_mat is not None and \
   gabor_sim_mat is not None and haralick_sim_mat is not None:
    bc_color = color_sim_mat[frag_i, frag_j]
    bc_texture = texture_sim_mat[frag_i, frag_j]
    bc_gabor = gabor_sim_mat[frag_i, frag_j]
    bc_haralick = haralick_sim_mat[frag_i, frag_j]

    appearance_multiplier = (bc_color ** 4.0) * (bc_texture ** 2.0) * \
                           (bc_gabor ** 2.0) * (bc_haralick ** 2.0)
    score = score * appearance_multiplier
```

### Thresholds (src/relaxation.py ~line 47)
```python
MATCH_SCORE_THRESHOLD = 0.75        # Strong match
WEAK_MATCH_SCORE_THRESHOLD = 0.60   # Weak match
ASSEMBLY_CONFIDENCE_THRESHOLD = 0.65  # Assembly acceptance
```

---

## Testing Commands

### Run full benchmark
```bash
python run_test.py
```

### Expected results
```
Positive cases: 8/9 passing (89%)
Negative cases: 31/36 passing (86%)
```

---

## Key Insights

1. **Subtractive penalties are too weak** for similar pottery colors (BC ~0.85)
2. **Power=6 on color is too harsh** (breaks 67% of positives)
3. **Power=4 on color is balanced** (maintains 89% positives, 86% negatives)
4. **Texture features help** but are secondary to color
5. **Thresholds matter** - need to balance precision vs recall

---

## References

- **Full documentation:** `CONVERSATION_CODE_EXTRACTION.md` (645 lines, all 16 edits)
- **Original conversation:** ece07127-20d3-460a-a966-c2c82ecfcf43.jsonl
- **Research:** arXiv:2309.13512 (ensemble pottery classification)
- **Course:** ICBV Lectures 71-72 (color histograms, texture)
