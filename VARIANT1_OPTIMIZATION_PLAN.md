# Variant 1 Evolutionary Optimization Strategy
## Current Status (Iteration 0 - Baseline)

### Configuration
- **Ensemble Type**: Weighted voting
- **Weights**:
  - color: 0.35 (35%)
  - raw_compat: 0.25 (25%)
  - texture: 0.20 (20%)
  - morphological: 0.15 (15%)
  - gabor: 0.05 (5%)
- **Thresholds**:
  - MATCH threshold: 0.75
  - WEAK_MATCH threshold: 0.60

### Baseline Test Results
From partial run (3 cases):
- Test case 1: FAIL (False Negative - expected MATCH, got NO_MATCH)
- Test case 2: PASS (59.3s processing time)
- Test case 3: Timed out (>30s)

**Initial Assessment**:
- At least 1 FN in first 3 positive cases = 33%+ FN rate on small sample
- Processing time is high (59s per case)
- Need to reduce FN rate significantly

## Optimization Plan

### Phase 1: Reduce False Negatives (Iterations 1-3)
**Problem**: Current weights too discriminative, missing true matches

**Strategy**: Decrease color weight, increase texture/gabor
- Color is TOO dominant at 0.35, causing FN
- Need more permissive ensemble

**Iteration 1**: Balanced weights
```python
weights = {
    'color': 0.30,          # Decrease from 0.35
    'raw_compat': 0.28,     # Increase from 0.25
    'texture': 0.23,        # Increase from 0.20
    'morphological': 0.14,  # Slight decrease
    'gabor': 0.05           # Keep same
}
```

**Iteration 2**: More permissive (if FN still high)
```python
weights = {
    'color': 0.28,
    'raw_compat': 0.28,
    'texture': 0.25,
    'morphological': 0.14,
    'gabor': 0.05
}
```

**Iteration 3**: Lower thresholds (if weights not enough)
```python
# Keep iteration 2 weights, but adjust thresholds:
match_thresh = 0.72      # From 0.75
weak_thresh = 0.57       # From 0.60
```

### Phase 2: Fine-tune for False Positives (Iterations 4-6)
**Only proceed if Phase 1 achieves Positive >= 95%**

Monitor negative accuracy:
- If Negative < 95%: Increase color weight slightly
- If Negative >= 95%: Done!

**Iteration 4**: Fine balance
```python
weights = {
    'color': 0.32,          # Slight increase from iter 2
    'raw_compat': 0.28,
    'texture': 0.23,
    'morphological': 0.13,
    'gabor': 0.04
}
```

### Phase 3: Micro-adjustments (Iterations 7-10)
**Target**: Both metrics >= 95%

Iteratively adjust by 0.01-0.02 increments based on which metric needs improvement.

## Implementation Steps

### Step 1: Update Weights
Edit `src/ensemble_voting.py`, line 172-178:

```python
if weights is None:
    weights = {
        'color': 0.30,          # ADJUSTED
        'raw_compat': 0.28,     # ADJUSTED
        'texture': 0.23,        # ADJUSTED
        'morphological': 0.14,  # ADJUSTED
        'gabor': 0.05
    }
```

### Step 2: (Optional) Adjust Thresholds
Edit `src/ensemble_voting.py`, line 205:

```python
return classify_by_threshold(weighted_score, match_thresh=0.72, weak_thresh=0.57)
```

### Step 3: Test
```bash
python run_variant1.py --no-rotate
```

### Step 4: Analyze Results
Look for:
- Positive accuracy (target >= 95%)
- Negative accuracy (target >= 95%)
- FP rate = 100 - negative_acc
- FN rate = 100 - positive_acc

### Step 5: Iterate
Based on results, go to next iteration in plan.

## Quick Reference: Adjustment Rules

### If FN rate > 10% (Positive < 90%)
- **Decrease color weight** by 0.03-0.05
- **Increase texture weight** by 0.02-0.03
- **Increase raw_compat weight** by 0.01-0.02

### If FP rate > 10% (Negative < 90%)
- **Increase color weight** by 0.03-0.05
- **Decrease gabor weight** by 0.01-0.02

### If both rates 5-10%
- **Lower both thresholds** by 0.02-0.03 (if FN dominant)
- **Raise both thresholds** by 0.02-0.03 (if FP dominant)

### If both rates < 5%
- **Micro-adjust weights** by 0.01
- **Fine-tune thresholds** by 0.01

## Expected Timeline
- Each iteration: ~5-10 minutes (45 test cases)
- Phase 1 (FN reduction): 3 iterations = 15-30 min
- Phase 2 (FP fine-tune): 2-3 iterations = 10-30 min
- Phase 3 (micro-adjust): 2-5 iterations = 10-50 min
- **Total estimated time**: 35-110 minutes

## Success Criteria
- Positive accuracy >= 95%
- Negative accuracy >= 95%
- Overall accuracy >= 95%
- **Target**: Both metrics at 95%+ simultaneously

## Current Action: Start Iteration 1
Implement the Iteration 1 weights (balanced approach) and run test.
