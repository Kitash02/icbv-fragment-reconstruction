# CODE EXTRACTION - INDEX AND SUMMARY

**Date:** 2026-04-08
**Session:** ece07127-20d3-460a-a966-c2c82ecfcf43
**Total Edits:** 16 operations across 2 files
**Outcome:** Improved negative accuracy from 53% → 86% (+33 pp)

---

## DOCUMENTS CREATED

### 1. CONVERSATION_CODE_EXTRACTION.md (645 lines)
**Purpose:** Complete detailed documentation of all 16 code changes

**Contents:**
- Executive summary with stage evolution table
- Detailed chronological changes by stage
- Final configuration code
- Full appendix with all 16 edits (before/after code)

**Use this for:** Understanding what changed and why

### 2. QUICK_REFERENCE_CODE_CHANGES.md
**Purpose:** Fast lookup for key changes and current code

**Contents:**
- TL;DR before/after comparison
- Files modified with line numbers
- Stage evolution table
- Current code locations
- Key insights

**Use this for:** Quick reference when coding or debugging

### 3. VISUAL_TIMELINE.txt
**Purpose:** ASCII visualization of change progression

**Contents:**
- Timeline with all 16 edits in chronological order
- Performance graphs (positive/negative accuracy)
- Threshold evolution diagram
- Formula comparison
- Key learnings

**Use this for:** Understanding the iterative improvement process

### 4. USER_CONTEXT_EXTRACTION.md
**Purpose:** User messages and context from conversation

**Contents:**
- 24 relevant user messages
- Stage descriptions
- Performance discussions
- Testing results

**Use this for:** Understanding user requirements and feedback

---

## QUICK NAVIGATION

### Need to know what the final code looks like?
→ **QUICK_REFERENCE_CODE_CHANGES.md** (Section: "Current Code Locations")

### Need to see all changes in detail?
→ **CONVERSATION_CODE_EXTRACTION.md** (Section: "APPENDIX: All 16 Edits")

### Need to understand the progression?
→ **VISUAL_TIMELINE.txt** (Full timeline visualization)

### Need to see user context?
→ **USER_CONTEXT_EXTRACTION.md** (All relevant messages)

---

## KEY FINDINGS

### Problem
Fragment reconstruction system had 53% negative accuracy due to weak color penalty:
```python
# OLD (Baseline)
color_penalty = (1.0 - bc) * COLOR_PENALTY_WEIGHT  # Only 12% reduction for BC=0.85
score = max(0.0, score - color_penalty)
```

### Solution
Multiplicative penalty with balanced thresholds:
```python
# NEW (Stage 1.6 - Final)
appearance_multiplier = (bc_color ** 4.0) * (bc_texture ** 2.0) * (bc_gabor ** 2.0) * (bc_haralick ** 2.0)
score = score * appearance_multiplier  # 48% reduction for BC=0.85

# Thresholds
MATCH_SCORE_THRESHOLD = 0.75        # was 0.55
WEAK_MATCH_SCORE_THRESHOLD = 0.60   # was 0.35
ASSEMBLY_CONFIDENCE_THRESHOLD = 0.65 # was 0.45
```

### Results
| Metric | Baseline | Stage 1.6 | Change |
|--------|----------|-----------|--------|
| Positive Accuracy | 100% (9/9) | 89% (8/9) | -11 pp |
| Negative Accuracy | 53% (19/36) | 86% (31/36) | **+33 pp** |
| Overall Balance | Unbalanced | Balanced | ✓ |

---

## CHANGE STAGES

### Stage 0: Cosmetic Fixes
- **Edit 1:** Unicode arrow fix (→ to ->)
- **Impact:** None (display only)

### Stage 1: Aggressive Penalty (FAILED)
- **Edits 2-13:** Changed to multiplicative penalty, added features, raised thresholds
- **Result:** 33% positive, 83% negative
- **Problem:** Power=6 on color too harsh

### Stage 1.5: Reduce Color Power (BETTER)
- **Edits 14-15:** Reduced color power from 6 → 4
- **Result:** 56% positive, 94% negative
- **Problem:** Thresholds still too high (0.85)

### Stage 1.6: Lower Thresholds (SUCCESS)
- **Edit 16:** Lowered thresholds to 0.75/0.60/0.65
- **Result:** **89% positive, 86% negative**
- **Status:** ✓ BALANCED

---

## FILES MODIFIED

### src/compatibility.py
**Line counts:** ~458 lines
**Total edits:** 12 operations

**Changes:**
1. Added LBP texture signature computation (Edit 3-4)
2. Added texture similarity matrix (Edit 5)
3. Changed penalty from subtractive to multiplicative (Edit 2, 6-7)
4. Tuned exponential powers (2.5 → 4.0 → 6.0 → 4.0)
5. Combined color + texture + gabor + haralick features (Edits 10-12, 14-15)

**Key lines:**
- ~Line 6: Import LBP
- ~Line 98: `compute_texture_signature()`
- ~Line 139: `texture_bhattacharyya()`
- ~Line 159: Texture matrix computation
- ~Line 425: Appearance penalty formula

### src/relaxation.py
**Line counts:** ~327 lines
**Total edits:** 4 operations

**Changes:**
1. Raised thresholds 0.55→0.70→0.85 (Edits 8-9, 13)
2. Lowered thresholds 0.85→0.75 (Edit 16)

**Key lines:**
- Line 47-49: Threshold constants

---

## FORMULA EVOLUTION

```
Baseline:
  score - (1 - BC) * 0.80

Stage 1 (initial):
  score * (BC ** 2.5)

Stage 1 (with texture):
  score * (sqrt(BC_color * BC_texture) ** 2.5)
  score * (sqrt(BC_color * BC_texture) ** 4.0)

Stage 1 (final - power=6):
  score * (BC_color ** 6.0) * (BC_texture ** 2.0) * (BC_gabor ** 2.0) * (BC_haralick ** 2.0)

Stage 1.5 (power=4):
  score * (BC_color ** 4.0) * (BC_texture ** 2.0) * (BC_gabor ** 2.0) * (BC_haralick ** 2.0)

Stage 1.6 (FINAL - same formula, lower thresholds):
  score * (BC_color ** 4.0) * (BC_texture ** 2.0) * (BC_gabor ** 2.0) * (BC_haralick ** 2.0)
```

---

## WHY IT WORKS

### 1. Multiplicative Compounds Dissimilarities
**Subtractive:** BC=0.85 → penalty=0.12 (12% reduction)
**Multiplicative:** BC=0.85 → multiplier=0.52 (48% reduction)

### 2. Power=4 is Balanced
- Power=6: Too harsh (broke 67% of positives)
- Power=4: Balanced (maintains 89% positives, 86% negatives)

### 3. Feature Weighting Reflects Importance
- **Color (power=4):** Artifact-specific (pigment chemistry)
- **Texture/Gabor/Haralick (power=2):** Material class indicators

### 4. Thresholds Tuned for Balance
- High thresholds (0.85): Good negatives, poor positives
- Balanced thresholds (0.75): Good both positives and negatives

---

## TESTING

### Run benchmark
```bash
python run_test.py
```

### Expected output
```
Processing positive test cases...
  fragment_004b_pos: MATCH FOUND ✓
  fragment_012_pos: MATCH FOUND ✓
  fragment_023_pos: MATCH FOUND ✓
  ...
  Results: 8/9 passing (89%)

Processing negative test cases...
  fragment_004b_008b_neg: NO MATCH ✓
  fragment_012_023_neg: NO MATCH ✓
  ...
  Results: 31/36 passing (86%)

Overall: 89% positive, 86% negative
```

---

## NEXT STEPS

### To verify current state
1. Check `src/compatibility.py` line ~425 for appearance multiplier
2. Check `src/relaxation.py` lines 47-49 for thresholds
3. Run `python run_test.py` to verify performance

### To revert to baseline
1. Restore compatibility.py line ~425:
   ```python
   color_penalty = (1.0 - bc) * COLOR_PENALTY_WEIGHT
   score = max(0.0, score - color_penalty)
   ```
2. Restore relaxation.py lines 47-49:
   ```python
   MATCH_SCORE_THRESHOLD = 0.55
   WEAK_MATCH_SCORE_THRESHOLD = 0.35
   ASSEMBLY_CONFIDENCE_THRESHOLD = 0.45
   ```

### To tune further
- Adjust color power (try 3.5, 4.5)
- Adjust texture power (try 1.5, 2.5)
- Adjust thresholds in small increments (±0.05)
- Run `python run_test.py` after each change

---

## REFERENCES

- **arXiv:2309.13512:** Ensemble pottery classification (99.3% accuracy)
- **ICBV Lecture 71:** Bhattacharyya coefficient for histogram similarity
- **ICBV Lecture 72:** Chain codes, shape descriptors, texture features
- **Conversation transcript:** ece07127-20d3-460a-a966-c2c82ecfcf43.jsonl (7079 lines)

---

## DOCUMENT METADATA

**Created:** 2026-04-08
**Primary source:** Conversation transcript ece07127-20d3-460a-a966-c2c82ecfcf43.jsonl
**Extraction method:** Parsed JSONL for Edit tool operations
**Verification:** All 16 edits cross-referenced with user messages
**Total documentation:** ~1500 lines across 4 files

---

**END OF INDEX**
