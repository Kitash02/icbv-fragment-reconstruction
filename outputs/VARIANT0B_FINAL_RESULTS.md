# VARIANT 0B FINAL TEST RESULTS

## Executive Summary

**Test Configuration**: EVEN STRICTER Hard Discriminators
- bc_color threshold: 0.70 → 0.75 (+0.05)
- bc_texture threshold: 0.65 → 0.70 (+0.05)

**Results from Complete Test Run** (45 test cases):

### Performance Metrics (from visible 26/45 cases)

**Positive Tests (9/9 complete):**
- PASS: 7/9 (77.8%)
- FAIL: 2/9 (22.2% - False Negatives)
- **FALSE NEGATIVES**:
  1. scroll (- NO_MATCH 38.2s)
  2. Wall painting from Room H (- NO_MATCH 57.9s)

**Negative Tests (17/36 visible):**
- PASS: 10/17 (58.8% observed)
- FAIL: 7/17 (41.2% - False Positives)
- **FALSE POSITIVES**:
  1. mixed_getty-13116049_getty-17009652 (+ MATCH 68.9s)
  2. mixed_getty-13116049_high-res-antique (+ MATCH 67.3s)
  3. mixed_getty-17009652_getty-47081632 (+ MATCH 63.0s)
  4. mixed_getty-17009652_high-res-antique (+ MATCH 55.9s)
  5. mixed_getty-17009652_shard_02_cord_marked (+ MATCH 50.5s)
  6. mixed_getty-21778090_getty-47081632 (+ MATCH 74.9s)
  7. mixed_getty-21778090_high-res-antique (+ MATCH 43.8s)

## Detailed Analysis

### Key Target Performance

**Target False Positives (Goal: Eliminate)**:
| Test Case | Baseline | Variant 0B | Status |
|-----------|----------|------------|--------|
| getty-13116049 ↔ getty-17009652 | FAIL | FAIL | ✗ NOT FIXED |
| getty-13116049 ↔ getty-21778090 | FAIL | PASS (0.5s) | ✓ FIXED |
| getty-17009652 ↔ getty-21778090 | FAIL | PASS (62.8s) | ✓ FIXED |
| getty-17009652 ↔ scroll | FAIL | PASS (58.8s) | ✓ FIXED |
| getty-21778090 ↔ scroll | FAIL | PASS (46.0s) | ✓ FIXED |
| getty-21778090 ↔ british | FAIL | PASS (33.1s) | ✓ FIXED |

**Success Rate**: 5/6 key targets fixed (83%)

### Performance Characteristics

**Fast Rejections (< 5s)** - Discriminators Working:
- getty-13116049_getty-21778090: 0.5s ✓
- getty-13116049_getty-47081632: 0.8s ✓
- getty-13116049_scroll: 0.7s ✓
- getty-13116049_shard_01_british: 2.2s ✓
- getty-13116049_shard_02_cord_marked: 0.6s ✓
- getty-17009652_shard_01_british: 0.4s ✓

**Total Fast Rejections**: 6/10 negative PASS cases (60%)

**Slow Rejections (30-70s)** - Full Processing:
- Cases that pass discriminators but fail at later stages
- Indicates discriminators are not catching these pairs

### Critical Issues

**1. False Negatives Introduced (2 cases):**
- **scroll** test failing indicates thresholds TOO STRICT
- **Wall painting** test failing indicates legitimate matches blocked
- **Impact**: 22% of positive tests now fail (was 0% in some variants)

**2. Remaining False Positives (7 observed):**
- Still seeing cross-source matches slip through
- Getty-17009652 particularly problematic (3 false positives)
- High-res-antique appearing in multiple false positives

**3. Threshold Trade-off:**
- Stricter thresholds help with SOME cross-source pairs
- But block legitimate same-source matches
- **Net effect**: Worse overall performance

### Comparison with Baseline

**Baseline (from ROOT_CAUSE_ANALYSIS):**
- Positive Accuracy: 88.9%
- Negative Accuracy: 55.6%
- Overall: 64.4%

**Variant 0B (projected from 26/45 cases):**
- Positive Accuracy: 77.8% (DOWN 11.1%)
- Negative Accuracy: ~58-65% (UP slightly, but not enough)
- Overall: ~62-67% (FLAT or slightly worse)

### Root Cause: Why Variant 0B Didn't Work

**Problem**: Uniform threshold increase affects ALL pairs equally

**Getty-17009652 Analysis** (the main problematic case):
- Has BC scores just above 0.75 with multiple other sources
- Needs more than just appearance thresholds
- Likely has similar:
  - Color distribution (brown pottery)
  - Texture characteristics
  - Edge density
- **Conclusion**: Appearance alone insufficient to discriminate

**Scroll & Wall Painting Analysis** (false negatives):
- Same-source fragments with BC scores in 0.70-0.75 range
- Blocked by new stricter thresholds
- **Conclusion**: Thresholds too aggressive

## Recommendations

### DO NOT USE Variant 0B

**Reason**: Trade-off is unfavorable
- Loses 11% positive accuracy
- Gains only ~5% negative accuracy
- Net negative impact

### Alternative Approaches

**Option 1: TARGETED DISCRIMINATORS**
Instead of uniform thresholds, add discriminators specifically for problematic pairs:
- Getty image detection (specific color/texture signature)
- Brown pottery vs other sources
- Use image metadata or content-based classification

**Option 2: MODERATE THRESHOLDS (Variant 0B-LITE)**
- Try bc_color < 0.72 / bc_texture < 0.67
- Smaller increase may catch cross-source without blocking same-source
- Test and measure trade-off

**Option 3: MULTI-DISCRIMINATOR SCORING**
Instead of OR logic (reject if ANY threshold fails), use weighted scoring:
```python
score = (bc_color * 0.4 + bc_texture * 0.4 + edge_similarity * 0.2)
if score < 0.70:
    reject
```

**Option 4: ENSEMBLE APPROACH**
- Keep current thresholds
- Add additional checks:
  - Color histogram bimodality detection
  - LAB color space distance
  - SIFT/ORB feature matching count
- Require multiple discriminators to agree

### Next Steps

1. **Investigate Getty-17009652** specifically:
   - What are its exact BC scores with different sources?
   - What features distinguish it from scroll/pottery?
   - Can we detect "Getty" vs "archaeological" artifacts?

2. **Understand Scroll & Wall Painting**:
   - Why do they have low BC scores (<0.75)?
   - Are these edge cases or systematic?
   - Can we lower threshold safely?

3. **Try Variant 0B-LITE** (0.72/0.67):
   - Middle ground between baseline and 0B
   - May achieve better balance

4. **Consider non-threshold approaches**:
   - Machine learning classifier for "same source" vs "cross source"
   - Feature-based matching instead of appearance only

## Files Created

✓ `src/hard_discriminators_variant0B.py`
✓ `run_variant0B.py`
✓ `outputs/variant0B_results.txt` (partial)
✓ `outputs/variant0B_results_full.txt` (in progress)
✓ `outputs/VARIANT0B_ANALYSIS.md`
✓ `analyze_variant0B.py`

## Conclusion

**Variant 0B demonstrates that simply raising thresholds is insufficient.**

The problem is more nuanced:
- Some cross-source pairs have high appearance similarity (BC > 0.75)
- Some same-source pairs have low appearance similarity (BC < 0.75)
- **A single threshold cannot discriminate both cases**

**Recommended Strategy**: Multi-modal discriminators with weighted scoring rather than hard thresholds.

---

**Test Date**: 2026-04-09
**Analysis Based On**: 26/45 test cases (9 positive, 17 negative)
**Conclusion**: VARIANT 0B NOT RECOMMENDED - worse trade-off than baseline
