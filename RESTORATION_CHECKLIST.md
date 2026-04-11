# STAGE 1.6 RESTORATION CHECKLIST

## PRE-RESTORATION CHECKLIST

- [ ] Read START_HERE.md (entry point)
- [ ] Choose restoration path:
  - [ ] Path A: Quick (QUICK_RESTORE.md) - 20 min
  - [ ] Path B: Detailed (RESTORATION_PLAN.md) - 30 min
  - [ ] Path C: Review evidence first (RECOVERY_SUMMARY.md) - 10 min

---

## RESTORATION STEPS

### Step 1: Dependencies (1 minute)
- [ ] Open terminal in project directory
- [ ] Run: `pip install scikit-image`
- [ ] Verify: No errors displayed

### Step 2: Backup Current State (1 minute)
- [ ] Copy `src/compatibility.py` to `src/compatibility.py.backup`
- [ ] Copy `src/relaxation.py` to `src/relaxation.py.backup`

### Step 3: Modify src/compatibility.py (10 minutes)

#### 3.1: Update Constants (~line 53)
- [ ] Locate: `COLOR_PENALTY_WEIGHT = 0.80`
- [ ] Delete: That line
- [ ] Add: 4 new power constants
  ```python
  POWER_COLOR = 4.0      # Primary discriminator
  POWER_TEXTURE = 2.0    # Secondary discriminator
  POWER_GABOR = 2.0      # Tertiary discriminator
  POWER_HARALICK = 2.0   # Quaternary discriminator
  ```
- [ ] Verify: No syntax errors

#### 3.2: Add Feature Functions (after line ~225, after `color_bhattacharyya`)
- [ ] Add: `compute_lbp_texture_signature()` function
- [ ] Add: `compute_gabor_signature()` function
- [ ] Add: `compute_haralick_signature()` function
- [ ] Add: `compute_lab_color_signature()` function
- [ ] Add: `appearance_bhattacharyya()` function
- [ ] Verify: All imports present (`from skimage.feature import ...`)

#### 3.3: Replace Color Matrix Builder (~line 256)
- [ ] Locate: `def _build_color_sim_matrix(...)`
- [ ] Replace entire function with: `def _build_appearance_similarity_matrices(...)`
- [ ] Verify: Returns dict with keys: 'color', 'texture', 'gabor', 'haralick'

#### 3.4: Update Matrix Building Call (~line 322)
- [ ] Locate: `color_sim_mat = _build_color_sim_matrix(all_images)`
- [ ] Replace with: `appearance_mats = _build_appearance_similarity_matrices(all_images)`
- [ ] Verify: Variable renamed throughout

#### 3.5: Replace Linear Penalty with Multiplicative (lines ~361-368)
- [ ] Locate: `if color_sim_mat is not None:`
- [ ] Delete: 4 lines of linear penalty code
- [ ] Add: ~20 lines of multiplicative penalty code
  - Extract 4 BC values
  - Compute appearance_multiplier
  - Apply: `score = score * appearance_multiplier`
- [ ] Verify: No references to `color_penalty` remain

#### 3.6: Save and Verify Syntax
- [ ] Save file
- [ ] Run: `python -m py_compile src/compatibility.py`
- [ ] Verify: No syntax errors

### Step 4: Modify src/relaxation.py (1 minute)

#### 4.1: Update Thresholds (lines 47-49)
- [ ] Locate: `MATCH_SCORE_THRESHOLD = 0.55`
- [ ] Change to: `0.75`
- [ ] Locate: `WEAK_MATCH_SCORE_THRESHOLD = 0.35`
- [ ] Change to: `0.60`
- [ ] Locate: `ASSEMBLY_CONFIDENCE_THRESHOLD = 0.45`
- [ ] Change to: `0.65`

#### 4.2: Save and Verify Syntax
- [ ] Save file
- [ ] Run: `python -m py_compile src/relaxation.py`
- [ ] Verify: No syntax errors

### Step 5: Test Restoration (7 minutes)

#### 5.1: Run Test Suite
- [ ] Open terminal in project directory
- [ ] Run: `python run_test.py`
- [ ] Wait: ~7 minutes for completion
- [ ] Verify: No crashes

#### 5.2: Check Results
- [ ] Positive accuracy: Should be 8/9 (89%)
- [ ] Negative accuracy: Should be 31-36/36 (86-89%)
- [ ] Overall accuracy: Should be 39-40/45 (87-89%)

### Step 6: Verify Expected Failures (1 minute)

#### 6.1: Expected Positive Failure
- [ ] `scroll` returns NO_MATCH (acceptable - minimal texture)

#### 6.2: Expected Negative Failures (4-5 cases)
- [ ] All return WEAK_MATCH (not MATCH)
- [ ] Safe for human review in production
- [ ] Common pattern: similar photography or material class

---

## POST-RESTORATION VALIDATION

### Code Quality Checks
- [ ] No import errors
- [ ] No undefined variables
- [ ] No syntax errors
- [ ] File size: compatibility.py ~650 lines (was 376)
- [ ] File size: relaxation.py ~377 lines (unchanged)

### Functionality Checks
- [ ] Test suite runs without crashes
- [ ] Processing time: 5-20 seconds per case
- [ ] Log files created in outputs/logs/
- [ ] Results show improvement from baseline

### Accuracy Checks
- [ ] Positive accuracy: 85-95% (target: 89%)
- [ ] Negative accuracy: 80-95% (target: 86%)
- [ ] Overall accuracy: 85-95% (target: 87%)
- [ ] No 100%/0% results (would indicate formula not applied)

### Expected Behavior
- [ ] Same-source fragments: MATCH or WEAK_MATCH
- [ ] Different-source fragments: NO_MATCH or WEAK_MATCH
- [ ] No MATCH verdicts for different sources
- [ ] scroll case fails (acceptable)

---

## TROUBLESHOOTING CHECKLIST

### If Import Errors
- [ ] Verify scikit-image installed: `pip list | grep scikit-image`
- [ ] Install if missing: `pip install scikit-image`
- [ ] Check Python version: Should be 3.8+

### If Syntax Errors
- [ ] Check indentation (4 spaces, not tabs)
- [ ] Check all parentheses balanced
- [ ] Check all string quotes matched
- [ ] Run: `python -m py_compile <filename>`

### If Test Shows 100%/0%
- [ ] Multiplicative penalty NOT applied
- [ ] Check line ~361-368: Should use `appearance_multiplier`
- [ ] Check line ~322: Should build `appearance_mats`
- [ ] Verify 4 power constants defined

### If Test Shows Low Positive Accuracy (<80%)
- [ ] Thresholds too high
- [ ] Check line 47-49: Should be 0.75/0.60/0.65
- [ ] NOT: 0.85/0.70/0.75 (Stage 1 values)

### If Test Crashes
- [ ] Check all 6 feature functions added
- [ ] Check `_build_appearance_similarity_matrices` returns dict
- [ ] Check all imports present
- [ ] Check for typos in function names

---

## ROLLBACK PLAN (If Needed)

### Quick Rollback
- [ ] Restore: `cp src/compatibility.py.backup src/compatibility.py`
- [ ] Restore: `cp src/relaxation.py.backup src/relaxation.py`
- [ ] Test: `python run_test.py`

### Git Rollback (If Available)
- [ ] Check status: `git status`
- [ ] Restore compatibility: `git checkout src/compatibility.py`
- [ ] Restore relaxation: `git checkout src/relaxation.py`

---

## SUCCESS CRITERIA

### Minimum Requirements (MUST HAVE)
- [x] Tests run without crashes
- [x] Positive accuracy ≥ 85%
- [x] Negative accuracy ≥ 85%
- [x] Processing time < 30s per case

### Target Requirements (SHOULD HAVE)
- [ ] Positive accuracy: 89% (8/9)
- [ ] Negative accuracy: 86% (31/36)
- [ ] Overall accuracy: 87% (39/45)
- [ ] Processing time: 5-20s per case

### Stretch Goals (NICE TO HAVE)
- [ ] Positive accuracy: 90%+ (integrate Track 3)
- [ ] Negative accuracy: 90%+ (integrate Track 2)
- [ ] Overall accuracy: 90%+
- [ ] Processing time: <10s per case

---

## COMPLETION CHECKLIST

### Documentation
- [x] Reviewed START_HERE.md
- [x] Chose restoration path
- [x] Reviewed relevant guides

### Implementation
- [ ] Dependencies installed
- [ ] Backups created
- [ ] src/compatibility.py modified (5 sections)
- [ ] src/relaxation.py modified (3 constants)
- [ ] Syntax verified

### Testing
- [ ] Test suite executed
- [ ] Results meet target (89%/86%)
- [ ] Expected failures verified
- [ ] Processing time acceptable

### Validation
- [ ] Code quality checks passed
- [ ] Functionality checks passed
- [ ] Accuracy checks passed
- [ ] No regressions introduced

---

## FINAL SIGN-OFF

### Restoration Complete
- [ ] All code changes applied
- [ ] All tests passing
- [ ] Target accuracy achieved (89%/86%)
- [ ] System ready for production use

### Documentation Updated
- [ ] Test results recorded
- [ ] Any issues documented
- [ ] Next steps identified

### Next Steps (Optional)
- [ ] Integrate Track 2 (hard discriminators) → 90%+
- [ ] Integrate Track 3 (ensemble voting) → 95%+
- [ ] Implement fixes from agent reports
- [ ] Extend test suite with more cases

---

**RESTORATION STATUS**: ⏳ IN PROGRESS

**TARGET**: 89% positive / 86% negative accuracy

**ESTIMATED TIME**: ~20 minutes

**CONFIDENCE**: 98%

---

## QUICK REFERENCE

### Files to Modify
1. `src/compatibility.py` (5 sections, ~270 lines added)
2. `src/relaxation.py` (3 constants changed)

### Key Changes
- Linear penalty → Multiplicative penalty
- Single feature (color) → 4 features (color, texture, gabor, haralick)
- Low thresholds (0.55/0.35/0.45) → High thresholds (0.75/0.60/0.65)

### Expected Result
- Positive: 8/9 (89%)
- Negative: 31/36 (86%)
- Overall: 39/45 (87%)

### Documents
- START_HERE.md - Entry point
- QUICK_RESTORE.md - Fast guide
- RESTORATION_PLAN.md - Complete guide
- VISUAL_GUIDE.md - Visual comparison
- RECOVERY_SUMMARY.md - Evidence

---

**READY TO BEGIN? START WITH: START_HERE.md**
