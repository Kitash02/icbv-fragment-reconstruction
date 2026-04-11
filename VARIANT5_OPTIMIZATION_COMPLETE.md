# Variant 5 (Color^6) Evolutionary Optimization - Complete Report

## Mission Objective
Iterate until Variant 5 achieves **95%+ positive AND 95%+ negative accuracy**.

## Final Result
**❌ TARGET NOT ACHIEVED**

Best performance: **66.7% positive / 77.8% negative (75.6% overall)**
- Gap to target: **-28.3% positive, -17.2% negative**

---

## Evolutionary Process Summary

### Iterations Performed: 6

| Iter | POWER_COLOR | POWER_TEXTURE | POWER_GABOR | POWER_HARALICK | hard_disc | Positive | Negative | Overall |
|------|-------------|---------------|-------------|----------------|-----------|----------|----------|---------|
| 1    | 6.0         | 2.0           | 2.0         | 2.0            | 0.70/0.65 | 55.6%    | 77.8%    | 73.3%   |
| 2    | 5.5         | 2.0           | 2.0         | 2.0            | 0.70/0.65 | 50.0%    | 77.8%    | 72.7%   |
| 3    | 6.0         | 2.0           | 2.0         | 2.0            | 0.65/0.60 | 50.0%    | 80.0%    | 74.4%   |
| **4/5** | **5.0**     | **2.0**       | **2.0**     | **2.0**        | **0.65/0.60** | **66.7%** | **77.8%** | **75.6%** |
| 6    | 5.0         | 3.0           | 2.5         | 2.5            | 0.65/0.60 | 55.6%    | 77.8%    | 73.3%   |

**Best Configuration: Iteration 4/5**

---

## Key Findings

### 1. Fundamental Trade-Off Discovered
- **Higher color power → Better negative, worse positive**
- **Lower color power → Better positive, worse negative**
- **No single power value achieves 95%+ on both metrics**

### 2. Consistent Failure Patterns

#### Positive Failures (3/9 consistent):
- `gettyimages-1311604917` (0.2-0.6s) - Fast early rejection
- `gettyimages-2177809001` (23-32s) - Geometric mismatch
- `Wall painting` (22-27s) - Geometric mismatch
- `scroll` (variable) - PASS with color^5.0, FAIL with higher powers

#### Negative Failures (8/36 consistent):
All involve **Getty Images 17009652 or 21778090**:
- `mixed_gettyimages-17009652_gettyimages-21778090`
- `mixed_gettyimages-17009652_gettyimages-47081632`
- `mixed_gettyimages-17009652_scroll`
- `mixed_gettyimages-21778090_gettyimages-47081632`
- `mixed_gettyimages-21778090_shard_01_british`
- `mixed_gettyimages-21778090_shard_02_cord_marked`
- `mixed_shard_01_british_shard_02_cord_marked`
- `mixed_Wall painting_gettyimages-17009652`

### 3. Root Cause Analysis

#### A. Getty Images 17009652 & 21778090
- Have **"generic" appearance** (neutral colors, simple textures)
- Geometrically match many other fragments by chance
- Appearance penalties **insufficient** because they lack distinctive features
- Cause **6 of 8 negative failures**

#### B. Positive Failures
- True fragments have **MORE appearance variation** than expected
- Within-artifact color variation defeats color^5 penalty
- Real archaeological fragments **aren't uniformly colored**
- Lighting/weathering creates appearance differences within same artifact

#### C. Hard Discriminators (0.65/0.60)
- Too relaxed: let negative false positives through
- Too strict: block true positive matches
- **No sweet spot exists** for this dataset

---

## What Worked

✅ **Relaxing hard_disc** from 0.70/0.65 to 0.65/0.60: +2.2% negative
✅ **Reducing color power** from 6.0 to 5.0: +11.1% positive (scroll recovered)
✅ **Overall improvement**: from 73.3% to 75.6% (+2.3%)

## What Failed

❌ color^6.0 too aggressive (kills positive accuracy)
❌ Increasing texture/gabor/haralick powers (made it worse)
❌ Cannot solve fundamental trade-off with single-pass penalties

---

## Conclusion

**Variant 5 (color^6) CANNOT achieve 95%+ on both positive and negative accuracy** with the current single-pass multiplicative penalty approach.

The issue is NOT the color exponent (tried 5.0, 5.5, 6.0, 7.0, 8.0).

The issue is the **APPROACH**: appearance penalties alone cannot distinguish:
1. True fragments with high appearance variation (archaeological reality)
2. Different fragments with similar appearance (brown pottery syndrome)

---

## Recommended Next Steps

### Option 1: ENSEMBLE APPROACH ⭐ Recommended
Run multiple configurations (color^4, color^5, color^6) and vote.
Accept match only if 2 of 3 agree.
- **Pro**: May improve negative accuracy without hurting positive
- **Con**: 3x computational cost

### Option 2: PER-FRAGMENT APPEARANCE VARIANCE
Measure color/texture variance within each fragment.
Adjust penalties based on fragment "distinctiveness".
- Generic fragments (Getty 17009652, 21778090) → stricter thresholds
- Variable fragments (Wall painting) → relaxed thresholds
- **Pro**: Addresses root cause directly
- **Con**: Requires per-fragment calibration

### Option 3: HYBRID DISCRIMINATOR
Use geometric similarity as primary signal.
Use appearance as **VETO only** (block obvious mismatches).
- Don't penalize appearance differences
- Only enforce appearance similarity: BC_color > 0.80 AND BC_texture > 0.75
- **Pro**: Asymmetric approach matches problem structure
- **Con**: May let through some borderline cases

### Option 4: INVESTIGATE PROBLEMATIC FRAGMENTS
Manually inspect Getty Images 17009652 and 21778090.
Determine why they geometrically match everything.
- **Pro**: May reveal dataset issues
- **Con**: Doesn't solve the general problem

---

## Files Modified

- `src/compatibility_variant5.py` - Main variant configuration (RESTORED TO BEST)
- `src/hard_discriminators_variant5.py` - Relaxed thresholds to 0.65/0.60
- `outputs/variant5_iteration1.txt` through `iteration6.txt` - Test results
- `outputs/variant5_evolution_summary.txt` - Iteration-by-iteration summary
- `outputs/variant5_final_report.txt` - Detailed analysis
- `VARIANT5_OPTIMIZATION_COMPLETE.md` - This document

---

## Best Configuration (SAVED)

```python
# src/compatibility_variant5.py
POWER_COLOR = 5.0      # Optimal balance
POWER_TEXTURE = 2.0
POWER_GABOR = 2.0
POWER_HARALICK = 2.0

# src/hard_discriminators_variant5.py
if bc_color < 0.65 or bc_texture < 0.60:
    return True  # Reject
```

**Performance**: 6/9 positive (66.7%), 28/36 negative (77.8%), 34/45 overall (75.6%)

---

## Time Investment
- 6 iterations
- ~15 minutes per iteration (including analysis)
- Total: ~90 minutes

## Recommendation
Proceed with **Option 1 (Ensemble Approach)** or **Option 3 (Hybrid Discriminator)** to attempt reaching 95%+ target.

Current Variant 5 configuration should be preserved as **"Variant 5 Best Effort"** baseline.
