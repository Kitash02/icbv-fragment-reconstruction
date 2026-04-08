# EVIDENCE: No Regression - Side-by-Side Comparison

**Investigation Date:** 2026-04-08

---

## Key Finding

**THERE IS NO REGRESSION. The system has consistently shown 0% negative accuracy since the initial implementation.**

---

## Side-by-Side Test Results

### Overall Statistics

| Metric | Baseline (baseline_test_results.txt) | Re-run Today | Change |
|--------|-------------------------------------|--------------|--------|
| Total test cases | 45 | 45 | 0 |
| Positive cases tested | 9 | 9 | 0 |
| Positive cases PASS | 9/9 (100%) | 9/9 (100%) | 0% |
| Negative cases tested | 36 | 36 | 0 |
| Negative cases PASS | 0/36 (0%) | 0/36 (0%) | **0%** |
| False positives | 36 | 36 | 0 |
| True negatives | 0 | 0 | 0 |

**Conclusion:** Identical performance - NO REGRESSION

---

## Negative Case Results (All 36 Cases)

| Case | Baseline Verdict | Re-run Verdict | Difference |
|------|------------------|----------------|------------|
| mixed_gettyimages-13116049_gettyimages-17009652 | OK MATCH (FAIL) | OK MATCH (FAIL) | None |
| mixed_gettyimages-13116049_gettyimages-21778090 | OK MATCH (FAIL) | OK MATCH (FAIL) | None |
| mixed_gettyimages-13116049_gettyimages-47081632 | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |
| mixed_gettyimages-13116049_high-res-antique-clo | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |
| mixed_gettyimages-13116049_scroll | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |
| mixed_gettyimages-13116049_shard_01_british | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |
| mixed_gettyimages-13116049_shard_02_cord_marked | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |
| mixed_gettyimages-17009652_gettyimages-21778090 | OK MATCH (FAIL) | OK MATCH (FAIL) | None |
| mixed_gettyimages-17009652_gettyimages-47081632 | OK MATCH (FAIL) | OK MATCH (FAIL) | None |
| mixed_gettyimages-17009652_high-res-antique-clo | OK MATCH (FAIL) | OK MATCH (FAIL) | None |
| mixed_gettyimages-17009652_scroll | OK MATCH (FAIL) | OK MATCH (FAIL) | None |
| mixed_gettyimages-17009652_shard_01_british | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |
| mixed_gettyimages-17009652_shard_02_cord_marked | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |
| mixed_gettyimages-21778090_gettyimages-47081632 | OK MATCH (FAIL) | OK MATCH (FAIL) | None |
| mixed_gettyimages-21778090_high-res-antique-clo | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |
| mixed_gettyimages-21778090_scroll | OK MATCH (FAIL) | OK MATCH (FAIL) | None |
| mixed_gettyimages-21778090_shard_01_british | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |
| mixed_gettyimages-21778090_shard_02_cord_marked | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |
| mixed_gettyimages-47081632_high-res-antique-clo | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |
| mixed_gettyimages-47081632_scroll | OK MATCH (FAIL) | OK MATCH (FAIL) | None |
| mixed_gettyimages-47081632_shard_01_british | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |
| mixed_gettyimages-47081632_shard_02_cord_marked | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |
| mixed_high-res-antique-clo_scroll | OK MATCH (FAIL) | OK MATCH (FAIL) | None |
| mixed_high-res-antique-clo_shard_01_british | OK MATCH (FAIL) | OK MATCH (FAIL) | None |
| mixed_high-res-antique-clo_shard_02_cord_marked | OK MATCH (FAIL) | OK MATCH (FAIL) | None |
| mixed_scroll_shard_01_british | OK MATCH (FAIL) | OK MATCH (FAIL) | None |
| mixed_scroll_shard_02_cord_marked | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |
| mixed_shard_01_british_shard_02_cord_marked | OK MATCH (FAIL) | OK MATCH (FAIL) | None |
| mixed_Wall painting from R_gettyimages-13116049 | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |
| mixed_Wall painting from R_gettyimages-17009652 | OK MATCH (FAIL) | OK MATCH (FAIL) | None |
| mixed_Wall painting from R_gettyimages-21778090 | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |
| mixed_Wall painting from R_gettyimages-47081632 | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |
| mixed_Wall painting from R_high-res-antique-clo | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |
| mixed_Wall painting from R_scroll | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |
| mixed_Wall painting from R_shard_01_british | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |
| mixed_Wall painting from R_shard_02_cord_marked | ~ WEAK_MATCH (FAIL) | ~ WEAK_MATCH (FAIL) | None |

**Summary:**
- **36/36 cases: Identical verdicts**
- **0/36 cases: Changed behavior**
- **100% match rate**

---

## Verdict Distribution

| Verdict Type | Baseline Count | Re-run Count | Difference |
|--------------|---------------|--------------|------------|
| OK MATCH (strong false positive) | 20 | 20 | 0 |
| ~ WEAK_MATCH (weak false positive) | 16 | 16 | 0 |
| NO_MATCH (correct rejection) | 0 | 0 | 0 |

**Note:** Both MATCH and WEAK_MATCH are failures for negative cases (should be NO_MATCH)

---

## Git History Evidence

```bash
$ git log --oneline --all
65cfeab Initial commit: ICBV fragment reconstruction pipeline
```

**Finding:** Only ONE commit exists in the repository. No code changes have been made since initial implementation.

---

## Real Fragment Test Consistency

### Real Fragment Test (British Museum + Wikimedia Pottery)

```
Dataset: 1 British Museum fragment + 26 Wikimedia fragments
Negative pairs tested: 26 (all cross-source)
True negatives: 0/26 (0%)
False positives: 26/26 (100%)
Average Color BC: 0.856
```

**Consistency check:**
- Benchmark negative accuracy: 0%
- Real data negative accuracy: 0%
- **Difference: 0 percentage points** ✓

---

## Code Analysis: No Changes to Scoring Logic

### Color Penalty Weight

**File:** `/src/compatibility.py`

```python
# Line 53 (unchanged since initial commit)
COLOR_PENALTY_WEIGHT = 0.80
```

### Compatibility Matrix Calculation

**File:** `/src/compatibility.py` (lines 383-390)

```python
# Color penalty (unchanged since initial commit)
if color_sim_mat is not None:
    bc = color_sim_mat[frag_i, frag_j]
    color_penalty = (1.0 - bc) * COLOR_PENALTY_WEIGHT
    score = max(0.0, score - color_penalty)
```

**Verification:** No modifications to this code since initial commit 65cfeab

---

## Where is the "53%" Claim?

### Searched All Output Files

```bash
$ grep -r "53" outputs/
$ grep -r "19/36" outputs/
$ grep -r "19 out of 36" outputs/
```

**Result:** No matches found for "19/36" or "53%" in any baseline documentation

### Possible Explanations

1. **Misinterpretation:** Someone confused "16/36 WEAK_MATCH" (44%) with "19/36 correct" (53%)
2. **Different test:** The 53% might refer to a completely different test not in this repository
3. **Target/Goal:** The 53% might be a goal or milestone, not an actual result
4. **External claim:** The 53% might come from external documentation not in this codebase

### What We Know For Certain

- **Baseline negative accuracy: 0%** (documented in BASELINE_REPORT.md)
- **Re-run negative accuracy: 0%** (verified today)
- **Real fragment negative accuracy: 0%** (consistent with baseline)
- **No code changes:** Only one git commit exists

---

## Conclusion

### Evidence Summary

1. ✓ **Test results are identical** (36/36 cases match exactly)
2. ✓ **Git history shows no changes** (only one commit)
3. ✓ **Code is unchanged** (no modifications to src/)
4. ✓ **Real data matches baseline** (both 0% negative accuracy)
5. ✓ **Documentation confirms 0%** (BASELINE_REPORT.md)

### Final Determination

**NO REGRESSION OCCURRED**

The system has consistently demonstrated **0% negative accuracy** since its initial implementation. The reported "53% to 0% drop" appears to be based on incorrect information or a misunderstanding of the metrics.

### What Actually Needs to Be Done

This is not a regression to fix, but a **fundamental design limitation** that requires system improvements:

1. Strengthen color penalty (increase weight or use exponential formula)
2. Raise match thresholds (0.55 → 0.70+ for MATCH)
3. Add hard color threshold (reject if BC < 0.75)
4. Consider texture features beyond color histograms

---

*Report generated: 2026-04-08*
*Files compared:*
- `/outputs/baseline_test_results.txt`
- `/outputs/testing/rerun_benchmark_output.txt`
- `/outputs/baseline_analysis/BASELINE_REPORT.md`
- `/outputs/testing/negative_case_analysis.md`
