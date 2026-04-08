# Failure Diagnosis Guide

## Quick Reference

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| Positive accuracy < 95% | Penalty too strong | Reduce exponential power or color weight |
| Negative accuracy no improvement | Feature insufficient | Add texture or increase bins |
| Time increased > 50% | Inefficient computation | Reduce histogram bins or LBP parameters |
| All negative cases fail | Threshold too high | Lower MATCH threshold |
| All positive cases fail | Implementation error | Check code for bugs |

## Detailed Failure Modes

### Failure Mode 1: Positive Accuracy Dropped

#### Symptoms
- Baseline positive accuracy: 100%
- Current positive accuracy: <98%
- Some same-source fragments no longer match

#### Diagnostic Process

1. **Identify Failed Cases**
   ```bash
   python scripts/analyze_failure.py --compare baseline phase_1a
   ```

2. **Check Which Pairs Flipped**
   Look for output like:
   ```
   Cases that flipped from PASS to FAIL: 3
   [1] fragment_003 <-> fragment_007
   [2] fragment_012 <-> fragment_015
   ```

3. **Analyze Individual Cases**
   ```bash
   python scripts/analyze_failure.py --deep-dive --case "gettyimages-1311604917-1024x1024"
   ```

4. **Check Metrics for Failed Pairs**
   - Color BC: Should be high (>0.90) for same-source
   - Texture BC: Should be high if texture phase
   - Geometric score: Should indicate good alignment

#### Common Causes

**Cause 1A: Exponential Penalty Too Strong**
- Color BC was 0.85 (good but not perfect)
- Exponential penalty: (1 - 0.85)^2.5 = 0.15^2.5 ≈ 0.008
- Final score becomes too low

**Solution**:
```python
# In src/compatibility.py
# Reduce exponential power
penalty_factor = (1.0 - bc) ** 2.0  # Was 2.5
```

**Cause 1B: Color Weight Too High**
- Color penalty weight of 0.80 too aggressive
- Even small color differences cause rejection

**Solution**:
```python
# In src/compatibility.py
# Reduce color penalty weight
COLOR_PENALTY_WEIGHT = 0.70  # Was 0.80
```

**Cause 1C: Histogram Bins Too Fine**
- Very fine histogram bins (e.g., 64x32x32)
- Small variations in lighting cause mismatch

**Solution**:
```python
# In src/compatibility.py
# Reduce bin counts
bins_L, bins_a, bins_b = 16, 8, 8  # Was 64, 32, 32
```

#### Parameter Tuning

Run parameter sweep to find optimal values:

```bash
# For exponential power
python scripts/parameter_sweep.py --phase 1b

# For histogram bins
python scripts/parameter_sweep.py --phase 1a --param lab_bins
```

#### Expected Results After Fix

- Positive accuracy: ≥98%
- Negative accuracy: maintained or improved
- Balanced accuracy: improved overall

---

### Failure Mode 2: No Improvement in Negative Accuracy

#### Symptoms
- Baseline negative accuracy: 0%
- Expected improvement: 15-25% (Phase 1A), 25-40% (Phase 1B)
- Actual improvement: <10%
- Negative pairs still match when they shouldn't

#### Diagnostic Process

1. **Check Color BC Distribution**
   ```bash
   python scripts/analyze_failure.py --phase 1a
   ```

2. **Look for Patterns**
   ```
   Negative pair color BC distribution:
   - BC > 0.95: 20 pairs (56%)  ← Too similar!
   - BC 0.85-0.95: 10 pairs (28%)
   - BC < 0.85: 6 pairs (16%)
   ```

3. **Analyze Specific Cases**
   Pick pairs with high BC but different sources:
   ```bash
   python scripts/analyze_failure.py --deep-dive --case "mixed_gettyimages-13116049_gettyimages-17009652"
   ```

#### Common Causes

**Cause 2A: Color Alone Insufficient**
- Different-source fragments have similar colors
- Example: Two pottery fragments, both brown
- Color BC > 0.90, but they're from different pots

**Solution**: Skip to texture phase
```bash
# Implement Phase 2A immediately
# Color alone cannot separate these pairs
```

**Cause 2B: Histogram Bins Too Coarse**
- Bins: 8x4x4 (very coarse)
- Cannot distinguish subtle color differences

**Solution**:
```python
# In src/compatibility.py
# Increase bin resolution
bins_L, bins_a, bins_b = 32, 16, 16  # Was 8, 4, 4
```

**Cause 2C: Exponential Power Wrong**
- Power = 1.0: Too weak, no penalty
- Power = 4.0: Too strong, hurts positive cases
- Need sweet spot around 2.0-2.5

**Solution**: Run parameter sweep
```bash
python scripts/parameter_sweep.py --phase 1b
```

**Cause 2D: Color Space Issue**
- Lab color space not implemented correctly
- Still using BGR histograms

**Solution**: Verify implementation
```python
# Check in src/compatibility.py
# Should be:
lab = cv2.cvtColor(image, cv2.COLOR_BGR2Lab)
# NOT:
# bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
```

#### Investigation Steps

**Step 1: Profile Color BC Values**

Create simple script to check BC distribution:

```python
import json
metrics = json.load(open("outputs/testing/metrics_1a.json"))

# Extract BC values for failed negative cases
# (Requires augmenting metrics collection)
```

**Step 2: Visual Inspection**

Look at actual fragment images:

```bash
# Open fragments directory
cd data/examples/negative/mixed_gettyimages-13116049_gettyimages-17009652
ls *.png
```

Visually check:
- Are colors actually similar?
- Is texture similar?
- Would a human confuse them?

**Step 3: Manual BC Calculation**

```python
import cv2
import numpy as np
from src.compatibility import compute_color_signature

# Load two fragments
frag1 = cv2.imread("fragment1.png")
frag2 = cv2.imread("fragment2.png")

# Compute signatures
sig1 = compute_color_signature(frag1)
sig2 = compute_color_signature(frag2)

# Compute BC
bc = cv2.compareHist(sig1, sig2, cv2.HISTCMP_BHATTACHARYYA)
print(f"Color BC: {bc:.3f}")
```

#### Expected Results After Fix

- Negative accuracy: ≥15% (Phase 1A), ≥25% (Phase 1B)
- Positive accuracy: maintained ≥98%
- BC distribution: clear separation between positive/negative

---

### Failure Mode 3: Processing Time Exploded

#### Symptoms
- Baseline: 5.0s per fragment
- Current: >7.5s per fragment (>50% increase)
- Tests take too long to run

#### Diagnostic Process

1. **Profile Performance**
   ```bash
   python scripts/profile_performance.py
   ```

2. **Check Component Times**
   Look for bottleneck:
   ```
   Component timings:
   - Color histogram:    0.1s
   - Texture (LBP):      3.5s  ← Bottleneck!
   - Fractal:            0.2s
   - Geometric:          0.3s
   ```

3. **Analyze Configuration**
   - Histogram bins: How many?
   - LBP parameters: P=?, R=?
   - Fractal scales: How many?

#### Common Causes

**Cause 3A: Too Many Histogram Bins**
- Bins: 64x32x32 = 65,536 bins
- Most bins empty, but still computed

**Solution**:
```python
# In src/compatibility.py
# Reduce to reasonable resolution
bins_L, bins_a, bins_b = 16, 8, 8  # Was 64, 32, 32
```

**Cause 3B: LBP Parameters Too Fine**
- P=24, R=3 → Very detailed texture
- Computation time: O(P * width * height)

**Solution**:
```python
# In src/compatibility.py
# Reduce LBP detail
P, R = 8, 1  # Was 24, 3
# Or moderate:
P, R = 16, 2
```

**Cause 3C: Too Many Fractal Scales**
- Scales: range(4, 10) → 6 scales
- Each scale requires image resizing

**Solution**:
```python
# In src/compatibility.py
# Reduce fractal scales
scales = range(4, 7)  # Was range(4, 10)
```

**Cause 3D: Redundant Computations**
- Computing color histogram for each pair
- Should compute once per fragment

**Solution**: Add memoization
```python
# In src/compatibility.py
_color_signature_cache = {}

def compute_color_signature(image, cache_key=None):
    if cache_key and cache_key in _color_signature_cache:
        return _color_signature_cache[cache_key]

    # Compute signature
    signature = ...

    if cache_key:
        _color_signature_cache[cache_key] = signature

    return signature
```

#### Performance Optimization Checklist

- [ ] Histogram bins reasonable (16-32 for L, 8-16 for a/b)
- [ ] LBP parameters moderate (P≤16, R≤2)
- [ ] Fractal scales limited (≤5 scales)
- [ ] Memoization for repeated computations
- [ ] Vectorized operations (NumPy instead of loops)
- [ ] No redundant cv2.cvtColor calls

#### Expected Results After Fix

- Time per fragment: ≤120% of baseline (6.0s if baseline was 5.0s)
- No accuracy regression
- All tests complete in reasonable time (<10 minutes)

---

### Failure Mode 4: High False Positive Rate

#### Symptoms
- Negative accuracy very low (<10%)
- Most negative pairs match when they shouldn't
- False positives > True negatives

#### Diagnostic Process

1. **Check Confusion Matrix**
   ```bash
   python scripts/validate_metrics.py --compare baseline phase_1a
   ```

   Look for:
   ```
   False Positives: 30  ← Too many!
   True Negatives:  6
   ```

2. **Analyze Threshold**
   - What is current MATCH threshold?
   - Are scores clustering just above threshold?

3. **Check Penalty Effectiveness**
   - Is color penalty being applied?
   - Is penalty strong enough?

#### Common Causes

**Cause 4A: Threshold Too Low**
- MATCH threshold = 0.50
- Many negative pairs score 0.52-0.60

**Solution**:
```python
# In src/main.py or matching logic
# Raise threshold
MATCH_THRESHOLD = 0.60  # Was 0.50
```

**Cause 4B: Penalty Not Applied**
- Code bug: penalty calculated but not used
- Or penalty weight = 0

**Solution**: Verify code
```python
# Check in src/compatibility.py
final_score = base_score * (1.0 - COLOR_PENALTY_WEIGHT * penalty_factor)
# Make sure this line exists and penalty_factor is used
```

**Cause 4C: Penalty Too Weak**
- Exponential power = 1.0 (linear)
- Even BC=0.5 only gives 50% penalty

**Solution**:
```python
# Increase exponential power
penalty_factor = (1.0 - bc) ** 2.5  # Was 1.0
```

#### Expected Results After Fix

- False positive rate: <20% of negative cases
- Negative accuracy: ≥15% (Phase 1A)
- Balanced accuracy: improved

---

### Failure Mode 5: High False Negative Rate

#### Symptoms
- Positive accuracy low (<95%)
- Same-source fragments don't match
- False negatives > True positives

#### Diagnostic Process

1. **Check Confusion Matrix**
   ```
   True Positives:   5
   False Negatives:  4  ← Too many!
   ```

2. **Identify Failed Positive Cases**
   ```bash
   python scripts/analyze_failure.py --compare baseline phase_1a
   ```

3. **Check Individual Cases**
   - Do they visually match?
   - Are they actually from same source?
   - Could be test data issue

#### Common Causes

**Cause 5A: Threshold Too High**
- MATCH threshold = 0.70
- Positive pairs score 0.65-0.69

**Solution**:
```python
# Lower threshold
MATCH_THRESHOLD = 0.55  # Was 0.70
```

**Cause 5B: Penalty Too Strong**
(See Failure Mode 1)

**Cause 5C: Test Data Issue**
- Some "positive" pairs actually from different sources
- Check test data generation

**Solution**: Verify test data
```bash
cd data/examples/positive
# Check each directory - all fragments should be from same source
```

#### Expected Results After Fix

- Positive accuracy: ≥98%
- False negative rate: <5% of positive cases
- Recall: ≥0.95

---

## Diagnostic Flowchart

```
Test Failed?
│
├─ Positive Accuracy < 95%
│  │
│  ├─ Check penalty strength
│  ├─ Check threshold
│  └─ Run parameter sweep
│
├─ Negative Accuracy < Expected
│  │
│  ├─ Check BC distribution
│  ├─ Visual inspection of negative pairs
│  ├─ Consider adding texture
│  └─ Increase histogram bins
│
├─ Time > 150% of Baseline
│  │
│  ├─ Profile components
│  ├─ Reduce histogram bins
│  ├─ Reduce LBP parameters
│  └─ Add caching
│
└─ All Tests Fail
   │
   ├─ Check imports
   ├─ Check for code errors
   └─ Run continuous_validator.py
```

## Automated Diagnosis

The `analyze_failure.py` script automatically runs these diagnostic steps:

```bash
# Comprehensive analysis
python scripts/analyze_failure.py --compare baseline phase_1a

# Output includes:
# - Failure mode identification
# - Suggested fixes with code
# - Parameter sweep recommendations
# - Deep-dive instructions
```

## Manual Diagnosis Steps

If automated diagnosis is unclear:

### 1. Examine Raw Output
```bash
cat outputs/testing/test_results_*.txt
```

Look for patterns in which cases fail.

### 2. Check Code Changes
```bash
git diff src/compatibility.py
```

Verify implementation matches intended changes.

### 3. Test Individual Components
```python
# Test color signature in isolation
from src.compatibility import compute_color_signature
import cv2

img = cv2.imread("test_fragment.png")
sig = compute_color_signature(img)
print(f"Signature shape: {sig.shape}")
print(f"Signature range: [{sig.min():.3f}, {sig.max():.3f}]")
```

### 4. Compare BC Values
```python
# Compute BC for known similar/dissimilar pairs
sig1 = compute_color_signature(img1)
sig2 = compute_color_signature(img2)
bc = cv2.compareHist(sig1, sig2, cv2.HISTCMP_BHATTACHARYYA)
print(f"BC: {bc:.3f}")  # Should be <0.2 for similar, >0.5 for dissimilar
```

## Getting Help

1. Run automated diagnosis first
2. Check this guide for your failure mode
3. Review test logs in `outputs/testing/`
4. Examine code changes carefully
5. Use parameter sweeps to find optimal values

## Summary

Most failures fall into five modes:
1. Penalty too strong → tune parameters
2. Feature insufficient → add next phase
3. Performance issue → optimize computation
4. Too permissive → raise threshold
5. Too restrictive → lower threshold

Use the automated tools to diagnose quickly, then apply targeted fixes.
