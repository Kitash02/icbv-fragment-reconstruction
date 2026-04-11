# Variant Testing System

## Overview

This testing infrastructure allows systematic evaluation of 10 algorithm variants to achieve research-level accuracy (95-100%) on the pottery fragment reconstruction benchmark.

**Current Baseline**: Stage 1.6 - 89% positive, 86% negative (87% overall)
**Target**: 95-100% both metrics

## Quick Start

### Run All Variants in Parallel (Recommended)
```bash
cd icbv-fragment-reconstruction
python parallel_variant_tester.py
```
This launches all 10 variants simultaneously. Results in ~15-30 minutes.

### Run Single Variant
```bash
python launch_variant.py 0    # Test baseline only
python launch_variant.py 5    # Test color^6 variant
python launch_variant.py 9    # Test full research stack
```

### Run All Variants Sequentially
```bash
python launch_variant.py all
```

### Check Variant Files
```bash
bash check_variants.sh
```

## Variant Descriptions

### Variant 0: Stage 1.6 Baseline (Control)
- **Formula**: color^4 × texture^2 × gabor^2 × haralick^2
- **Thresholds**: 0.75 / 0.60 / 0.65
- **Ensemble**: 5-way voting
- **Expected**: 89%/86%
- **Files**: `run_variant0.py`

### Variant 1: Weighted Ensemble Only
- **Paper**: arXiv:2510.17145 (97.49% claimed)
- **Change**: Replace 5-way with weighted ensemble voting
- **Weights**: Color(0.35), Raw(0.25), Texture(0.20), Morph(0.15), Gabor(0.05)
- **Files**: `run_variant1.py`, `src/ensemble_postprocess_variant1.py`

### Variant 2: Hierarchical Ensemble Only
- **Change**: Hierarchical routing for speed
- **Logic**: Fast rejection → Fast accept → Full ensemble for hard cases
- **Expected**: Same accuracy, faster runtime
- **Files**: `run_variant2.py`, `src/ensemble_postprocess_variant2.py`

### Variant 3: Tuned Weighted Ensemble
- **Change**: Optimized weights for pottery specifically
- **Weights**: Color(0.40↑), Raw(0.25), Texture(0.15↓), Morph(0.15), Gabor(0.05)
- **Rationale**: Color most discriminative for pottery
- **Expected**: 93-96%
- **Files**: `run_variant3.py`, `src/ensemble_postprocess_variant3.py`

### Variant 4: Relaxed Thresholds
- **Change**: Lower thresholds to recover false negatives
- **Thresholds**: 0.70 / 0.55 / 0.60 (was 0.75 / 0.60 / 0.65)
- **Expected**: 92-94% positive, 84-86% negative
- **Files**: `run_variant4.py`, `src/relaxation_variant4.py`

### Variant 5: Color-Dominant (color^6)
- **Change**: More aggressive color penalty
- **Formula**: color^6 × texture^2 × gabor^2 × haralick^2
- **Expected**: 78-85% positive (worse), 92-95% negative (better)
- **Files**: `run_variant5.py`, `src/compatibility_variant5.py`

### Variant 6: Balanced Powers (all ^2)
- **Change**: Equal feature weighting
- **Formula**: color^2 × texture^2 × gabor^2 × haralick^2
- **Expected**: 95-100% positive (more permissive), 75-82% negative (worse)
- **Files**: `run_variant6.py`, `src/compatibility_variant6.py`

### Variant 7: Optimized Powers
- **Change**: Intermediate power configuration
- **Formula**: color^5 × texture^2.5 × gabor^2 × haralick^2
- **Thresholds**: 0.72 / 0.58 / 0.62
- **Expected**: 90-93% positive, 89-92% negative
- **Files**: `run_variant7.py`, `src/compatibility_variant7.py`, `src/relaxation_variant7.py`

### Variant 8: Adaptive Thresholds
- **Change**: Different thresholds per artifact type
- **Logic**: High variance artifacts (scroll) → 0.70/0.55, Low variance (pottery) → 0.75/0.60
- **Expected**: 92-95% positive (recovers scroll), 86-89% negative
- **Files**: `run_variant8.py`, `src/relaxation_variant8.py`

### Variant 9: Full Research Stack
- **Paper**: arXiv:2309.13512 (99.3% claimed)
- **Changes**: ALL optimizations combined
  - Weighted ensemble (tuned weights)
  - Adaptive thresholds
  - Hierarchical routing
- **Expected**: 95-99%
- **Files**: `run_variant9.py`, `src/ensemble_postprocess_variant9.py`, `src/relaxation_variant9.py`

## Results Location

After running tests:
- **Individual results**: `outputs/variant_testing/variant_N/`
- **Comparison report**: `outputs/variant_testing/parallel_test_results.json`
- **Summary**: `VARIANT_TESTING_RESULTS.md` (auto-updated)

## File Structure

```
icbv-fragment-reconstruction/
├── run_variant0.py              # Baseline test runner
├── run_variant1.py              # Variant 1 test runner
├── ...
├── run_variant9.py              # Variant 9 test runner
├── parallel_variant_tester.py   # Master coordinator (parallel)
├── launch_variant.py            # Single variant launcher
├── check_variants.sh            # Verify all files ready
├── VARIANT_TESTING_RESULTS.md   # Results summary
└── src/
    ├── compatibility.py              # BASELINE (protected)
    ├── relaxation.py                 # BASELINE (protected)
    ├── ensemble_postprocess.py       # BASELINE (protected)
    ├── compatibility_variant5.py     # Variant 5 formula
    ├── compatibility_variant6.py     # Variant 6 formula
    ├── compatibility_variant7.py     # Variant 7 formula
    ├── relaxation_variant4.py        # Variant 4 thresholds
    ├── relaxation_variant7.py        # Variant 7 thresholds
    ├── relaxation_variant8.py        # Variant 8 adaptive
    ├── relaxation_variant9.py        # Variant 9 adaptive
    ├── ensemble_postprocess_variant1.py  # Variant 1 weighted
    ├── ensemble_postprocess_variant2.py  # Variant 2 hierarchical
    ├── ensemble_postprocess_variant3.py  # Variant 3 tuned
    └── ensemble_postprocess_variant9.py  # Variant 9 full stack
```

## Implementation Strategy

### Critical Constraint: NO BASELINE MODIFICATIONS
- **NEVER** modify `src/compatibility.py`
- **NEVER** modify `src/relaxation.py`
- **NEVER** modify `src/ensemble_postprocess.py`
- Stage 1.6 baseline must remain reproducible

### Variant Isolation
Each variant:
1. Creates NEW files (e.g., `compatibility_variant5.py`)
2. Uses monkey-patching in test runner: `sys.modules['compatibility'] = compatibility_variant5`
3. Runs standard `run_test.main()` with patched modules

### Why This Works
- Each variant test is independent
- Baseline always available for comparison
- No risk of cross-contamination
- Easy rollback if needed

## Success Criteria

**Primary Goal**: ≥95% both positive and negative accuracy
**Acceptable Goal**: ≥92% both metrics (5-6% improvement)
**Minimum Goal**: Identify why research claims (99.3%) don't match our results

## Tier Classification

- **Tier 1 (Excellent)**: 95%+ both metrics → Deploy immediately
- **Tier 2 (Good)**: 90%+ both metrics → Consider deployment
- **Tier 3 (Acceptable)**: 85%+ both metrics → Phase 4 refinement
- **Tier 4 (Baseline)**: <85% → Keep Stage 1.6

## Next Steps After Testing

1. **If Tier 1 achieved**: Deploy best variant, update baseline
2. **If Tier 2 achieved**: Evaluate trade-offs (accuracy vs complexity), possibly deploy
3. **If Tier 3 achieved**: Phase 4 - Create hybrid configurations from top 3 performers
4. **If all ≤87%**: Stage 1.6 is optimal; research algorithms don't apply to this dataset

## Troubleshooting

### Variant file missing
```bash
bash check_variants.sh  # Check which files are missing
# Wait for background agents to complete
```

### Import errors
Verify monkey-patching in `run_variantN.py`:
```python
import sys
sys.path.insert(0, "src")
import compatibility_variantN
sys.modules['compatibility'] = compatibility_variantN
```

### Baseline regression
Compare to Variant 0 (control). If Variant 0 ≠ 89%/86%, something changed the baseline.

## Development Notes

**Created**: 2026-04-09
**Purpose**: Systematic search for 95%+ accuracy configuration
**Approach**: Parallel testing of 10 isolated variants
**Timeline**: ~15-30 minutes for full parallel test suite
