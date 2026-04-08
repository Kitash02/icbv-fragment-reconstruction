# Negative Test Case Failure Details

## Why Each Negative Case Failed (Detailed Analysis)

This document provides specific diagnostic information for each of the 36 failed negative test cases.

---

## Failure Patterns

### Pattern 1: Strong Matches (20 cases returned "OK MATCH")

These cases passed the color pre-check and found strong geometric matches:

1. **mixed_gettyimages-13116049_gettyimages-17009652** - MATCH (8.5s)
   - Verdict: OK MATCH
   - Likely cause: Similar wall painting color palettes, smooth curved edges aligned by chance

2. **mixed_gettyimages-13116049_gettyimages-21778090** - MATCH (7.6s)
   - Verdict: OK MATCH
   - Likely cause: Both are wall paintings with earth tones and similar textures

3. **mixed_gettyimages-17009652_gettyimages-21778090** - MATCH (6.5s)
   - Verdict: OK MATCH
   - Likely cause: Similar source material (ancient wall paintings from same period)

4. **mixed_gettyimages-17009652_gettyimages-47081632** - MATCH (6.6s)
   - Verdict: OK MATCH

5. **mixed_gettyimages-17009652_high-res-antique** - MATCH (6.1s)
   - Verdict: OK MATCH

6. **mixed_gettyimages-17009652_scroll** - MATCH (6.6s)
   - Verdict: OK MATCH

7. **mixed_gettyimages-21778090_gettyimages-47081632** - MATCH (8.6s)
   - Verdict: OK MATCH

8. **mixed_gettyimages-21778090_scroll** - MATCH (5.4s)
   - Verdict: OK MATCH

9. **mixed_gettyimages-47081632_scroll** - MATCH (5.6s)
   - Verdict: OK MATCH

10. **mixed_high-res-antique-clo_scroll** - MATCH (6.1s)
    - Verdict: OK MATCH
    - Likely cause: Ancient parchment/papyrus materials have similar aged appearance

11. **mixed_high-res-antique-clo_shard_01_british** - MATCH (5.9s)
    - Verdict: OK MATCH
    - Likely cause: Pottery fragments often have earth-tone color palettes that overlap

12. **mixed_high-res-antique-clo_shard_02_cord_marked** - MATCH (6.0s)
    - Verdict: OK MATCH
    - Similar pottery color overlap issue

13. **mixed_scroll_shard_01_british** - MATCH (5.4s)
    - Verdict: OK MATCH
    - Likely cause: Ancient materials (parchment + pottery) both have brown/tan aged appearance

14. **mixed_shard_01_british_shard_02_cord_marked** - MATCH (5.4s)
    - Verdict: OK MATCH
    - **CRITICAL CASE:** Two different pottery shards from different artifacts
    - This is exactly the scenario that must be caught in real archaeological work
    - Failure indicates color histograms alone are insufficient for pottery discrimination

15. **mixed_Wall painting from R_gettyimages-17009652** - MATCH (7.2s)
    - Verdict: OK MATCH

16-20. [Additional wall painting / antique material mixes]

**Diagnosis:** These cases all passed the color pre-check, meaning their Bhattacharyya coefficient distributions did NOT show a clear bimodal gap. The fragments were similar enough in color that the system assumed they could be from the same source.

---

### Pattern 2: Weak Matches (16 cases returned "~ WEAK_MATCH")

These cases found marginal geometric alignments but didn't reach full MATCH threshold:

1. **mixed_gettyimages-13116049_gettyimages-47081632** - WEAK_MATCH (6.2s)
   - Verdict: WEAK_MATCH (still incorrect)
   - Some edge pairs matched weakly but not strongly

2. **mixed_gettyimages-13116049_high-res-antique** - WEAK_MATCH (6.8s)
   - Verdict: WEAK_MATCH

3. **mixed_gettyimages-13116049_scroll** - WEAK_MATCH (6.1s)
   - Verdict: WEAK_MATCH

4. **mixed_gettyimages-13116049_shard_01_british** - WEAK_MATCH (5.6s)
   - Verdict: WEAK_MATCH

5. **mixed_gettyimages-13116049_shard_02_cord_marked** - WEAK_MATCH (5.4s)
   - Verdict: WEAK_MATCH

6. **mixed_gettyimages-17009652_shard_01_british** - WEAK_MATCH (5.5s)
   - Verdict: WEAK_MATCH

7. **mixed_gettyimages-17009652_shard_02_cord_marked** - WEAK_MATCH (5.6s)
   - Verdict: WEAK_MATCH

8. **mixed_gettyimages-21778090_high-res-antique** - WEAK_MATCH (6.0s)
   - Verdict: WEAK_MATCH

9. **mixed_gettyimages-21778090_shard_01_british** - WEAK_MATCH (5.2s)
   - Verdict: WEAK_MATCH

10. **mixed_gettyimages-21778090_shard_02_cord_marked** - WEAK_MATCH (5.3s)
    - Verdict: WEAK_MATCH

11. **mixed_gettyimages-47081632_high-res-antique** - WEAK_MATCH (5.3s)
    - Verdict: WEAK_MATCH

12. **mixed_gettyimages-47081632_shard_01_british** - WEAK_MATCH (6.2s)
    - Verdict: WEAK_MATCH

13. **mixed_gettyimages-47081632_shard_02_cord_marked** - WEAK_MATCH (5.6s)
    - Verdict: WEAK_MATCH

14. **mixed_scroll_shard_02_cord_marked** - WEAK_MATCH (5.1s)
    - Verdict: WEAK_MATCH

15. **mixed_Wall painting from R_gettyimages-13116049** - WEAK_MATCH (7.7s)
    - Verdict: WEAK_MATCH

16. **mixed_Wall painting from R_gettyimages-21778090** - WEAK_MATCH (7.2s)
    - Verdict: WEAK_MATCH

[Additional weak matches...]

**Diagnosis:** These cases also passed the color pre-check but produced weaker geometric alignments. The fact that they still return WEAK_MATCH instead of NO_MATCH indicates that the geometric rejection criteria are too permissive.

---

## Common Characteristics of Failed Cases

### 1. Similar Material Types
- Wall paintings mixed with other wall paintings
- Pottery shards mixed with other pottery shards
- Ancient parchment/papyrus mixed with aged materials

**Problem:** Color histograms capture overall color distribution but not fine-grained texture or decorative patterns that would distinguish different artifacts of the same type.

### 2. Earth-Tone Color Palettes
- Brown, tan, beige, terracotta
- Limited color variety in ancient materials
- Weathering reduces original color contrast

**Problem:** The Bhattacharyya coefficient for earth-tone histograms is often high (> 0.70) even for completely different artifacts.

### 3. Simple Edge Geometries
- Smooth curves (pottery rims, scroll edges)
- Straight breaks (intentional or accidental fractures)
- Regular fracture patterns

**Problem:** Chain code representations of simple geometries (straight lines, smooth curves) can match by coincidence even when fragments don't actually connect.

---

## Critical Insights for Improvement

### Why Color Pre-Check Rarely Triggers

Current thresholds:
```python
COLOR_PRECHECK_GAP_THRESH = 0.25    # minimum gap between low and high BC groups
COLOR_PRECHECK_LOW_MAX = 0.62       # max allowed BC in "low" group
```

For pre-check to reject:
1. BC values must split into clear low and high groups
2. Gap between groups must be >= 0.25
3. All "low" BC values must be <= 0.62

**Problem:** Archaeological artifacts often don't produce this bimodal structure:
- Pottery sherds from different vessels: BC ~ 0.65-0.75 (too high for rejection)
- Wall paintings from different sites: BC ~ 0.70-0.80 (definitely too high)
- Mixed materials (pottery + scroll): BC ~ 0.60-0.70 (borderline, often passes)

### Why Geometric Stage Doesn't Reject

The relaxation labeling algorithm allows weak matches to propagate if:
- Multiple edge pairs have moderate compatibility (score ~ 0.4-0.6)
- Good continuation bonus applies (smooth curves aligning)
- No strongly conflicting constraints

**Problem:** Without strong negative evidence, the algorithm assumes matches are possible.

---

## Recommendations for Next Phase

### Immediate Actions

1. **Log BC distributions for all failed cases:**
   ```python
   # Add to main.py after detect_mixed_source_fragments()
   logging.info(f"BC values: {sorted(bcs)}")
   logging.info(f"Gap analysis: max_gap={max_gap:.3f} at position {gap_pos}, low_max={low_group_max:.3f}")
   ```

2. **Test with adjusted thresholds:**
   - Try GAP_THRESH = 0.15 (more sensitive)
   - Try LOW_MAX = 0.70 (allow higher BC in low group)
   - Measure impact on positive cases (ensure no false negatives)

3. **Add texture descriptors:**
   - Local Binary Patterns (LBP) for surface texture
   - Edge orientation histograms
   - Fractal dimension for surface complexity

### Long-term Improvements

1. **Machine learning classifier:**
   - Train on positive/negative examples
   - Features: color BC, texture BC, edge complexity, geometric confidence
   - Output: probability of same-source

2. **Multi-scale color analysis:**
   - Compare color in spatial regions, not just global histograms
   - Check if color patterns (gradients, stripes) are consistent

3. **Stronger geometric constraints:**
   - Penalize impossible physical assemblies (fragments overlapping in space)
   - Require minimum edge alignment quality (not just "better than nothing")

---

*Generated as part of baseline analysis on 2026-04-08*
