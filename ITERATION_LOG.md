# Variant 1 Weight Optimization - Iteration Log

## Baseline (Iteration 0)
**Weights:**
- color: 0.35
- raw_compat: 0.25
- texture: 0.20
- morphological: 0.15
- gabor: 0.05

**Thresholds:**
- MATCH: 0.75
- WEAK: 0.60

**Observed Issues:**
- High FN rate (at least 1/3 positive cases failed in initial test)
- Processing time: ~60s per test case

**Root Cause Analysis:**
- Color weight (0.35) too dominant
- Causes conservative matching (misses valid matches)
- Need to rebalance toward geometric and texture features

---

## Iteration 1 (CURRENT)
**Strategy:** Reduce color dominance, increase raw_compat and texture

**Weights:**
- color: 0.30 (-0.05 from baseline)
- raw_compat: 0.28 (+0.03)
- texture: 0.23 (+0.03)
- morphological: 0.14 (-0.01)
- gabor: 0.05 (no change)

**Rationale:**
- Decrease color to reduce false negatives
- Increase geometric (raw_compat) for better shape matching
- Increase texture for pottery surface patterns
- Keep gabor low (generic, not pottery-specific)

**Testing:** In progress...
**Expected outcome:** Positive accuracy increase from ~67% to 85-90%

---

## Future Iterations (Planned)

### Iteration 2: If FN still high (pos < 90%)
**More permissive weights:**
- color: 0.28 (-0.02)
- raw_compat: 0.29 (+0.01)
- texture: 0.25 (+0.02)
- morphological: 0.13 (-0.01)
- gabor: 0.05

### Iteration 3: Threshold adjustment if needed
**Lower thresholds:**
- MATCH: 0.72 (-0.03)
- WEAK: 0.57 (-0.03)

Keep Iteration 2 weights

### Iteration 4: Balance for negatives (if pos >= 95% but neg < 95%)
**Slightly increase discrimination:**
- color: 0.32 (+0.04 from iter 2)
- raw_compat: 0.28
- texture: 0.23 (-0.02)
- morphological: 0.13
- gabor: 0.04 (-0.01)

### Iterations 5-10: Micro-adjustments
Adjust by 0.01-0.02 increments based on which metric needs improvement

---

## Success Criteria
- ✓ Positive accuracy >= 95%
- ✓ Negative accuracy >= 95%
- ✓ Overall accuracy >= 95%

## Notes
- Each weight adjustment must keep sum = 1.0
- Prioritize reducing FN first (Phase 1)
- Then fine-tune for FP (Phase 2)
- Finally micro-optimize (Phase 3)
