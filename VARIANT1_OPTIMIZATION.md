# Variant 1 Weight Optimization Guide

## Overview

Variant 1 uses **Weighted Ensemble Voting** from arXiv:2510.17145, which achieved 97.49% accuracy on general object classification. We optimize these weights specifically for pottery fragment reconstruction.

## Current Implementation

**File**: `src/ensemble_voting.py` → `ensemble_verdict_weighted()`

**Current Weights** (from paper, trained on general objects):
- Color: 0.35
- Raw Compatibility: 0.25
- Texture: 0.20
- Morphology: 0.15
- Gabor: 0.05

## Hypothesis: Pottery-Specific Optimization

For pottery fragments, **color is MORE discriminative** than for general objects because:

1. **Pigment chemistry is artifact-specific**: Different pottery types use different clay and firing techniques
2. **Manufacturing consistency**: Fragments from the same vessel share identical pigment composition
3. **Weathering patterns**: Fragments from the same vessel have correlated weathering/patina

Therefore, we hypothesize that **increasing the color weight** will improve pottery-specific accuracy.

## Optimization Strategy

### Evolutionary Approach

Test progressively higher color weights while reducing less discriminative features:

| Iteration | Color | Raw | Texture | Morph | Gabor | Rationale |
|-----------|-------|-----|---------|-------|-------|-----------|
| Baseline  | 0.35  | 0.25| 0.20    | 0.15  | 0.05  | Paper defaults (general objects) |
| Iter 1    | 0.40  | 0.25| 0.20    | 0.15  | 0.00  | Remove Gabor (least useful for pottery) |
| Iter 2    | 0.45  | 0.25| 0.15    | 0.15  | 0.00  | Increase color, reduce texture |
| Iter 3    | 0.50  | 0.25| 0.10    | 0.15  | 0.00  | Color at 0.50 (dominant feature) |
| Iter 4    | 0.50  | 0.25| 0.15    | 0.10  | 0.00  | Alternative: balance texture/morph |
| Iter 5    | 0.55  | 0.20| 0.15    | 0.10  | 0.00  | Maximum color emphasis |

### Target Metrics

**Success criteria**: ≥95% positive accuracy AND ≥95% negative accuracy

**Why 95%?**
- Paper claims 97.49% on general objects
- With pottery-specific optimization, 95%+ should be achievable
- Lower than 95% suggests weights are not optimal for pottery

## How to Run Optimization

### Option 1: Automated Evolution (Full Test - 2-3 hours)

```bash
python evolve_variant1_weights.py
```

This runs all 6 configurations on the full 45-case test suite (9 positive + 36 negative).
Each test takes ~10-20 minutes. Total time: 2-3 hours.

**Output**: `evolution_results_variant1.txt` with complete results table.

### Option 2: Quick Test (3 Key Configurations - 30 minutes)

```bash
python evolve_variant1_quick.py
```

Tests 3 key configurations:
1. Baseline (current weights)
2. Color-optimized (0.50 color weight)
3. Balanced (0.45 color + 0.30 geometry)

**Output**: `evolution_quick_results.txt`

### Option 3: Manual Testing (Recommended for Development)

**Step 1**: Update weights for a specific configuration:

```bash
# Test baseline
python test_weights_manual.py --preset baseline

# Test color-optimized
python test_weights_manual.py --preset color-opt

# Test balanced
python test_weights_manual.py --preset balanced

# Custom weights
python test_weights_manual.py --color 0.50 --raw 0.25 --texture 0.15 --morph 0.10 --gabor 0.00
```

**Step 2**: Run the test:

```bash
python test_variant1_quick.py
```

**Step 3**: Record results and repeat for next configuration.

**Step 4**: Restore original weights when done:

```bash
python test_weights_manual.py --restore
```

## Expected Results

Based on the paper and pottery-specific characteristics:

| Configuration | Expected Pos% | Expected Neg% | Expected Overall% |
|---------------|---------------|---------------|-------------------|
| Baseline      | 85-90%        | 85-90%        | 85-90%            |
| Color-opt     | 90-95%        | 90-95%        | 90-95%            |
| Balanced      | 88-93%        | 88-93%        | 88-93%            |

**Best case**: One configuration achieves ≥95% on both metrics (target reached!)

**Good case**: Multiple configurations achieve 90-95% (significant improvement over baseline)

**Worst case**: All configurations perform similarly (~85-90% → weights not the bottleneck)

## Interpreting Results

### If Color-Optimized Wins

**Conclusion**: Pigment chemistry is indeed the dominant discriminator for pottery.

**Action**: Update `ensemble_voting.py` default weights to color-optimized configuration.

**Impact**: Paper claims 97.49% with learned weights. If we achieve 90-95% with color optimization, we've successfully adapted the technique to pottery-specific domain.

### If Baseline Wins

**Conclusion**: Paper's general-purpose weights are already optimal for pottery.

**Action**: No changes needed. The current 85-90% performance is limited by other factors (geometric matching, thresholds, etc.), not ensemble weights.

**Next steps**: Focus optimization on other variants (Variant 2-9).

### If Balanced Wins

**Conclusion**: Both color AND geometry are important; neither should dominate.

**Action**: Use balanced weights (0.45 color + 0.30 geometry).

**Insight**: Pottery matching requires both appearance (color) and geometric (curvature) features in balance.

## Implementation Details

### How Weight Modification Works

The scripts temporarily modify `src/ensemble_voting.py`:

```python
# Original (in ensemble_verdict_weighted)
if weights is None:
    weights = {
        'color': 0.35,
        'raw_compat': 0.25,
        'texture': 0.20,
        'morphological': 0.15,
        'gabor': 0.05
    }
```

The script replaces this block with the test configuration, runs the test, then restores the original.

**Backup**: Original file is saved as `ensemble_voting.py.backup` before any modification.

### Scoring Formula

The weighted score is computed as:

```python
weighted_score = (
    weights['color'] * bc_color +                    # Bhattacharyya color histogram
    weights['raw_compat'] * raw_compat_norm +        # Geometric compatibility (curvature)
    weights['texture'] * bc_texture +                # LBP texture histogram
    weights['gabor'] * bc_gabor +                    # Gabor frequency features
    weights['morphological'] * morph_score           # Edge density + entropy
)
```

Then classify:
- **MATCH** if weighted_score ≥ 0.75
- **WEAK_MATCH** if weighted_score ≥ 0.60
- **NO_MATCH** otherwise

## Files Created

1. **`evolve_variant1_weights.py`**: Full automated evolution (all 6 configs, 2-3 hours)
2. **`evolve_variant1_quick.py`**: Quick test (3 configs, 30 minutes)
3. **`test_weights_manual.py`**: Manual weight updater (for iterative testing)
4. **`VARIANT1_OPTIMIZATION.md`**: This guide

## Recommended Workflow

For **development/debugging**:
1. Use manual testing (`test_weights_manual.py` + `test_variant1_quick.py`)
2. Test baseline first to establish reference performance
3. Test color-optimized to see if pottery-specific optimization helps
4. Test balanced to see if multi-feature approach works

For **final validation**:
1. Run full evolution (`evolve_variant1_weights.py`) once you've narrowed down to 2-3 promising configs
2. Let it run overnight or during a long break (2-3 hours)
3. Analyze results table to determine best configuration

## Paper Reference

**arXiv:2510.17145**: "Late Fusion with Learned Weights for Object Classification"

Key findings:
- Weighted ensemble outperformed equal voting (97.49% vs 95.32%)
- Weights learned via grid search on validation set
- Color features had highest weight (0.35) for general objects
- Domain-specific weight tuning improved accuracy by 2-5%

**Our adaptation**: Apply same weighted ensemble technique but optimize weights specifically for pottery fragments (where color should be more discriminative than for general objects).

## Success Metrics

**Minimum acceptable**: 85% positive + 85% negative (current baseline)

**Good**: 90% positive + 90% negative (10% improvement)

**Target**: 95% positive + 95% negative (paper's claimed performance)

**Stretch**: 97%+ (match paper's best results)

## Next Steps After Optimization

1. **Apply best weights**: Update `ensemble_voting.py` default weights
2. **Document results**: Add performance table to project README
3. **Compare to other variants**: Is Variant 1 the best approach, or are Variants 2-9 better?
4. **Iterate**: If 95% not reached, try:
   - Different weight combinations (grid search)
   - Adjust thresholds (0.75/0.60 → try 0.70/0.55 or 0.80/0.65)
   - Combine with other improvements (better curvature matching, etc.)
