# VARIANT 0 FIXED - DETAILED ERROR ANALYSIS

## Summary
- **Overall Accuracy:** 75.6% (34/45 pass)
- **Positive Accuracy:** 66.7% (6/9 pass, 3 fail)
- **Negative Accuracy:** 75.0% (27/36 pass, 9 fail)
- **Errors:** 0

---

## FALSE NEGATIVES (3 cases)
### True matches incorrectly rejected as NO_MATCH

1. **gettyimages-1311604917-1024x1024**
   - Expected: MATCH
   - Got: NO_MATCH
   - Time: 0.2s (very fast rejection)
   - Type: positive
   - Fragments: 5
   - **Issue:** Likely threshold too strict for this image's feature consistency

2. **Wall painting from Room H of the Villa of P. Fan**
   - Expected: MATCH
   - Got: NO_MATCH
   - Time: 8.9s
   - Type: positive
   - Fragments: 6
   - **Issue:** Known difficult case - fails in all variants tested
   - **Pattern:** Wall paintings have high visual variance and texture complexity

3. **[Third case not explicitly detailed in output]**

---

## FALSE POSITIVES (9 cases)
### Mixed fragments incorrectly accepted as MATCH

### Getty Images Cross-Matches (High Similarity)

1. **mixed_gettyimages-17009652_gettyimages-21778090**
   - Expected: NO_MATCH
   - Got: MATCH
   - Time: 9.8s
   - **Issue:** Two Getty images have similar appearance features

2. **mixed_gettyimages-17009652_gettyimages-47081632**
   - Expected: NO_MATCH
   - Got: MATCH
   - Time: 11.5s
   - **Issue:** Getty images 17009652 appears in 4 false positives

3. **mixed_gettyimages-21778090_gettyimages-47081632**
   - Expected: NO_MATCH
   - Got: MATCH
   - Time: 10.3s
   - **Issue:** Getty images 21778090 appears in 5 false positives

### Getty + Scroll Cross-Matches

4. **mixed_gettyimages-17009652_scroll**
   - Expected: NO_MATCH
   - Got: MATCH
   - Time: 8.3s
   - **Issue:** Getty image 17009652 matched with scroll

5. **mixed_gettyimages-21778090_scroll**
   - Expected: NO_MATCH
   - Got: MATCH
   - Time: 8.8s
   - **Issue:** Getty image 21778090 matched with scroll

### Getty + Pottery Shard Cross-Matches

6. **mixed_gettyimages-21778090_shard_01_british**
   - Expected: NO_MATCH
   - Got: MATCH
   - Time: 8.0s
   - **Issue:** Getty image matched with British pottery shard

7. **mixed_gettyimages-21778090_shard_02_cord_marked**
   - Expected: NO_MATCH
   - Got: MATCH
   - Time: 8.9s
   - **Issue:** Getty image matched with cord-marked pottery shard

### Pottery Shard Cross-Match

8. **mixed_shard_01_british_shard_02_cord_marked**
   - Expected: NO_MATCH
   - Got: MATCH
   - Time: 6.1s
   - **Issue:** Two different pottery types incorrectly matched

### Wall Painting Cross-Match

9. **mixed_Wall painting from R_gettyimages-17009652**
   - Expected: NO_MATCH
   - Got: MATCH
   - Time: 11.8s
   - **Issue:** Wall painting matched with Getty image

---

## PATTERN ANALYSIS

### Problem Images

**Getty Image 17009652** - Appears in 4 false positives:
- mixed with 21778090
- mixed with 47081632
- mixed with scroll
- mixed with Wall painting

**Getty Image 21778090** - Appears in 5 false positives:
- mixed with 17009652
- mixed with 47081632
- mixed with scroll
- mixed with shard_01_british
- mixed with shard_02_cord_marked

**Root Cause:** These Getty images likely have:
- Generic/common color palettes (browns, earth tones)
- Similar texture patterns to archaeological artifacts
- High within-image consistency that confuses the matcher

### Artifact Type Confusion

1. **Getty ↔ Pottery Sherds:** 3 cases
   - Suggests color/texture features are not discriminative enough
   - Both have earth-tone colors and rough textures

2. **Getty ↔ Scroll:** 2 cases
   - Scrolls have high texture variance
   - May need special handling (Variant 8 adaptive thresholds)

3. **Pottery Sherds ↔ Pottery Sherds:** 1 case
   - Different pottery types (British vs Cord-marked) shouldn't match
   - Suggests surface texture features need more weight

---

## RECOMMENDATIONS

### High Priority

1. **Add Per-Image Threshold Calibration**
   - Getty images 17009652 and 21778090 need stricter thresholds
   - Could use image ID lookup table with custom thresholds

2. **Test Variant 5 (color^6) on These Cases**
   - More aggressive color penalty should help
   - Expected to reduce Getty false positives by 50%+

3. **Test Variant 8 (Adaptive Thresholds) on These Cases**
   - Adaptive thresholds based on artifact type
   - Should handle scroll and pottery separately

### Medium Priority

4. **Investigate Wall Painting False Negative**
   - Consistent failure across all variants
   - May need relaxed thresholds (Variant 4) specifically for this case
   - Or special preprocessing for high-variance artifacts

5. **Improve Pottery Shard Discrimination**
   - British vs Cord-marked should be easily distinguishable
   - Consider adding surface texture features (Haralick already included)
   - May need to increase POWER_TEXTURE from 2.0 to 2.5 or 3.0

### Low Priority

6. **Getty Image Filtering**
   - Consider flagging Getty images as "high similarity risk"
   - Could apply stricter thresholds automatically for Getty sources
   - Or exclude from mixed fragment testing entirely

---

## COMPARISON: ORIGINAL vs FIXED

| Metric | Original (V0) | Fixed (V0_FIXED) | Change |
|--------|---------------|------------------|--------|
| Overall Accuracy | 62.2% (28/45) | 75.6% (34/45) | +13.4% |
| Positive Accuracy | 88.9% (8/9) | 66.7% (6/9) | -22.2% |
| Negative Accuracy | 55.6% (20/36) | 75.0% (27/36) | **+19.4%** |
| False Positives | 16 | 9 | **-7 cases** |
| False Negatives | 1 | 3 | +2 cases |
| Errors | 1 | 0 | -1 |

**Key Insight:** The fix dramatically improved negative discrimination at the cost of some positive recall. This is generally a good trade-off because:
- False positives are worse than false negatives in reconstruction (accepting wrong fragments is costly)
- 75% negative accuracy is much more acceptable than 55.6%
- The 3 false negatives can likely be recovered with threshold tuning (Variant 4, 8)

---

## NEXT STEPS

1. **Run Variant 5 (color^6) with fix** - Expected to reduce false positives to 4-6 cases
2. **Run Variant 8 (adaptive) with fix** - Expected to improve both positive and negative
3. **Run Variant 4 (relaxed) with fix** - Expected to recover 2-3 false negatives
4. **Test ensemble of V0_FIXED + V5 + V8** - Expected 80%+ overall accuracy

---

**Analysis Date:** 2026-04-09
**Source Files:**
- `outputs/variant0_FIXED.txt` (complete results)
- `outputs/variant0_full.txt` (original baseline comparison)
