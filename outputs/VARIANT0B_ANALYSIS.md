# VARIANT 0B TEST RESULTS - STRICTER HARD DISCRIMINATORS

## Configuration Changes

**File Created**: `src/hard_discriminators_variant0B.py`

**Changes from Baseline** (line 124):
- **bc_color threshold**: 0.70 → 0.75 (increased by 0.05)
- **bc_texture threshold**: 0.65 → 0.70 (increased by 0.05)

**Rationale**:
The stricter thresholds aim to eliminate the remaining 9 false positives observed in baseline testing, particularly problematic matches like:
- getty-17009652 ↔ getty-21778090
- getty-17009652 ↔ scroll/pottery
- Cross-source matches with BC scores in the 0.70-0.75 range

## Test Execution

**Runner Script**: `run_variant0B.py`
- Monkey-patches `src.hard_discriminators` with variant0B implementation
- Runs full 45-test suite (9 positive, 36 negative)

## Partial Results (Test In Progress)

### Observed from Partial Output:

**Positive Tests** (9/9 observed):
- ✓ gettyimages-1311604917: PASS (+ MATCH 52.4s)
- ✓ gettyimages-170096524: PASS (+ MATCH 39.0s)
- ✓ gettyimages-2177809001: PASS (+ MATCH 41.8s)
- ✓ gettyimages-470816328: PASS (+ MATCH 47.0s)
- ✓ high-res-antique: PASS (+ MATCH 40.2s)
- ✗ scroll: FAIL (- NO_MATCH 38.2s) **FALSE NEGATIVE**
- ✓ shard_01_british: PASS (+ MATCH 40.0s)
- ✓ shard_02_cord_marked: PASS (+ MATCH 43.4s)
- ✗ Wall painting: FAIL (- NO_MATCH 57.9s) **FALSE NEGATIVE**

**Negative Tests** (4/36 observed):
- ✗ mixed_getty-13116049_getty-17009652: FAIL (+ MATCH 68.9s) **FALSE POSITIVE**
- ✓ mixed_getty-13116049_getty-21778090: PASS (- NO_MATCH 0.5s)
- ✓ mixed_getty-13116049_getty-47081632: PASS (- NO_MATCH 0.8s)
- ? mixed_getty-13116049_high-res-antique: (incomplete at time of writing)
- ...remaining 32 tests not yet complete

## Preliminary Analysis

### Impact on Positive Tests (7/9 = 77.8%):
- **2 False Negatives** (scroll, Wall painting)
- These likely have BC scores just below the new stricter thresholds
- **CONCERN**: Increased thresholds may be TOO STRICT, blocking legitimate matches

### Impact on Negative Tests (3/4 = 75% observed):
- **1 False Positive** (getty-13116049 ↔ getty-17009652)
- **2 Correct Rejections** (fast, 0.5-0.8s indicates early rejection)
- **POSITIVE**: Early rejections suggest discriminators are working

### Performance Observations:
- Positive tests: ~40-50s (slower due to full processing)
- Negative PASS: ~0.5-0.8s (very fast, early rejection working)
- Negative FAIL: ~69s (full processing when discriminators don't catch)

## Key Target Status (Partial):

### Target False Positives to Eliminate:
1. ✓ getty-13116049 ↔ getty-21778090: **CORRECTLY REJECTED** (0.5s)
2. ✓ getty-13116049 ↔ getty-47081632: **CORRECTLY REJECTED** (0.8s)
3. ✗ getty-13116049 ↔ getty-17009652: **STILL FALSE POSITIVE** (68.9s)
4. ? getty-17009652 ↔ getty-21778090: NOT YET OBSERVED
5. ? getty-17009652 ↔ scroll: NOT YET OBSERVED
6. ? other cross-source pairs: NOT YET OBSERVED

## Preliminary Conclusions

### Positive Impact:
1. **Fast rejections working**: Cross-source pairs being rejected in <1s
2. **Some targets eliminated**: 2 of 3 observed getty-13116049 matches correctly rejected
3. **Discriminators active**: Early rejection is functioning as designed

### Negative Impact:
1. **False negatives introduced**: 2/9 positive tests failing (22% failure rate)
2. **Thresholds may be too strict**: Blocking legitimate same-source matches (scroll, Wall painting)
3. **Trade-off not optimal**: Gaining negative accuracy at cost of positive accuracy

## Expected Final Results (Projected)

Based on partial observations:

**Positive Accuracy**: 7/9 = 77.8% (DOWN from baseline 88.9%)
- 2 false negatives is concerning for a reconstruction system

**Negative Accuracy**: If 3/4 pattern holds across 36 tests:
- Projected: ~75-80% (UP from baseline 55.6% or current 75%)

**Overall Accuracy**: ~78% (vs baseline 64.4%)

## Recommendations

### If Test Completes with Projected Results:

**VARIANT 0B = TOO STRICT**

**Issue**: Threshold of 0.75/0.70 blocks legitimate matches

**Recommendation**:
1. **Try VARIANT 0B_MODERATE**: Use thresholds of 0.72/0.68 (middle ground)
2. **Alternative**: Use 0.73/0.67 as compromise
3. **Or**: Keep current baseline (0.70/0.65) but strengthen other discriminators

### Alternative Approach:

Instead of raising thresholds uniformly, consider:
1. **Differential thresholds** for known problematic pairs
2. **Edge density threshold** adjustment (currently at 0.15)
3. **Texture entropy threshold** tuning (currently at 0.5)
4. **Combined discriminator** scoring instead of OR logic

## Files Created

1. ✓ `src/hard_discriminators_variant0B.py` - Stricter threshold implementation
2. ✓ `run_variant0B.py` - Test runner with monkey-patching
3. ✓ `outputs/variant0B_results.txt` - Initial partial results
4. ⏳ `outputs/variant0B_results_full.txt` - Full test output (in progress)
5. ✓ `analyze_variant0B.py` - Results analysis script

## Next Steps

1. **Wait for test completion** to get full 45-case results
2. **Run analysis script**: `python analyze_variant0B.py`
3. **Compare with baseline**: Measure exact accuracy trade-offs
4. **If negative accuracy < 85%**: Try intermediate threshold values
5. **If positive accuracy < 85%**: Thresholds are too strict, need to back off
6. **Consider**: Investigating why scroll and Wall painting have low BC scores

## Status

⏳ **TEST IN PROGRESS** - Waiting for completion of full 45-test suite

**Estimated Completion**: ~10-15 minutes (based on ~40-50s per test × 45 tests)
**Test Started**: ~09:15
**Last Observation**: 9/9 positive, 4/36 negative tests completed

---

**Created**: 2026-04-09
**Analysis Based On**: Partial results from first 13 test cases
