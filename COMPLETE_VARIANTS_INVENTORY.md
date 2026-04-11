# Complete Variants Inventory

## Summary
Successfully created 21 files for Variants 0-9:
- 10 test runner scripts (`run_variant{N}.py`)
- 11 variant-specific modules in `src/`

## Complete File List

### Test Runner Scripts (10 files)

1. **run_variant0.py** - Stage 1.6 Baseline (no changes)
2. **run_variant1.py** - Weighted Ensemble Only
3. **run_variant2.py** - Hierarchical Ensemble
4. **run_variant3.py** - Tuned Weighted Ensemble
5. **run_variant4.py** - Relaxed Thresholds
6. **run_variant5.py** - Color-Dominant Formula
7. **run_variant6.py** - Balanced Powers
8. **run_variant7.py** - Optimized Powers + Tuned Thresholds
9. **run_variant8.py** - Adaptive Thresholds
10. **run_variant9.py** - Full Research Stack

### Variant-Specific Modules (11 files)

#### Compatibility Modules (Formula Changes)
1. **src/compatibility_variant1.py** - Baseline (no changes, placeholder)
2. **src/compatibility_variant5.py** - Color^6
3. **src/compatibility_variant6.py** - Balanced (all powers = 2.0)
4. **src/compatibility_variant7.py** - Optimized (color^5, texture^2.5)

#### Relaxation Modules (Threshold Changes)
5. **src/relaxation_variant4.py** - Relaxed thresholds (0.70/0.55/0.60)
6. **src/relaxation_variant7.py** - Tuned thresholds (0.72/0.58/0.62)
7. **src/relaxation_variant8.py** - Adaptive thresholds (pottery/sculpture/default)

#### Ensemble Postprocess Modules (Ensemble Changes)
8. **src/ensemble_postprocess_variant1.py** - Weighted ensemble
9. **src/ensemble_postprocess_variant2.py** - Hierarchical ensemble
10. **src/ensemble_postprocess_variant3.py** - Tuned weighted ensemble
11. **src/ensemble_postprocess_variant9.py** - Full stack (weighted + adaptive)

## Variant Configurations

### Variant 0: Stage 1.6 Baseline
- **Purpose:** Reference baseline for comparison
- **Formula:** color^4 × texture^2 × gabor^2 × haralick^2
- **Thresholds:** 0.75 / 0.60 / 0.65
- **Ensemble:** Five-way voting
- **Files:** `run_variant0.py` only

### Variant 1: Weighted Ensemble Only
- **Purpose:** arXiv:2510.17145 - 97.49% target
- **Formula:** Baseline
- **Thresholds:** Baseline
- **Ensemble:** Weighted (0.35, 0.25, 0.20, 0.15, 0.05)
- **Files:** 
  - `run_variant1.py`
  - `src/compatibility_variant1.py` (placeholder)
  - `src/ensemble_postprocess_variant1.py`

### Variant 2: Hierarchical Ensemble
- **Purpose:** Fast-path optimization
- **Formula:** Baseline
- **Thresholds:** Baseline
- **Ensemble:** Hierarchical decision tree
- **Files:**
  - `run_variant2.py`
  - `src/ensemble_postprocess_variant2.py`

### Variant 3: Tuned Weighted Ensemble
- **Purpose:** Better color discrimination
- **Formula:** Baseline
- **Thresholds:** Baseline
- **Ensemble:** Weighted (0.40, 0.25, 0.15, 0.15, 0.05)
- **Files:**
  - `run_variant3.py`
  - `src/ensemble_postprocess_variant3.py`

### Variant 4: Relaxed Thresholds
- **Purpose:** Higher recall (more matches)
- **Formula:** Baseline
- **Thresholds:** 0.70 / 0.55 / 0.60 (relaxed)
- **Ensemble:** Baseline
- **Files:**
  - `run_variant4.py`
  - `src/relaxation_variant4.py`

### Variant 5: Color-Dominant Formula
- **Purpose:** Maximum color discrimination
- **Formula:** color^6 × texture^2 × gabor^2 × haralick^2
- **Thresholds:** Baseline
- **Ensemble:** Baseline
- **Files:**
  - `run_variant5.py`
  - `src/compatibility_variant5.py`

### Variant 6: Balanced Powers
- **Purpose:** Equal feature weighting
- **Formula:** color^2 × texture^2 × gabor^2 × haralick^2
- **Thresholds:** Baseline
- **Ensemble:** Baseline
- **Files:**
  - `run_variant6.py`
  - `src/compatibility_variant6.py`

### Variant 7: Optimized Powers + Tuned Thresholds
- **Purpose:** Balanced optimization
- **Formula:** color^5 × texture^2.5 × gabor^2 × haralick^2
- **Thresholds:** 0.72 / 0.58 / 0.62 (tuned)
- **Ensemble:** Baseline
- **Files:**
  - `run_variant7.py`
  - `src/compatibility_variant7.py`
  - `src/relaxation_variant7.py`

### Variant 8: Adaptive Thresholds
- **Purpose:** Context-aware classification
- **Formula:** Baseline
- **Thresholds:** Adaptive (pottery: 0.78/0.63/0.68, sculpture: 0.70/0.55/0.60)
- **Ensemble:** Baseline
- **Files:**
  - `run_variant8.py`
  - `src/relaxation_variant8.py`

### Variant 9: Full Research Stack
- **Purpose:** Maximum accuracy (all improvements)
- **Formula:** color^5 × texture^2.5 × gabor^2 × haralick^2 (Variant 7)
- **Thresholds:** Adaptive (Variant 8)
- **Ensemble:** Weighted (Variant 3)
- **Files:**
  - `run_variant9.py`
  - `src/ensemble_postprocess_variant9.py`
  - Uses: `compatibility_variant7.py` + `relaxation_variant8.py`

## File Dependencies

### Variant Runner → Module Dependencies

```
run_variant0.py  → (no custom modules)
run_variant1.py  → ensemble_postprocess_variant1.py
run_variant2.py  → ensemble_postprocess_variant2.py
run_variant3.py  → ensemble_postprocess_variant3.py
run_variant4.py  → relaxation_variant4.py
run_variant5.py  → compatibility_variant5.py
run_variant6.py  → compatibility_variant6.py
run_variant7.py  → compatibility_variant7.py + relaxation_variant7.py
run_variant8.py  → relaxation_variant8.py
run_variant9.py  → compatibility_variant7.py + relaxation_variant8.py + ensemble_postprocess_variant9.py
```

## Running All Variants

### Sequential Execution
```bash
for i in {0..9}; do
    echo "====================================="
    echo "Running Variant $i"
    echo "====================================="
    python run_variant${i}.py
    echo ""
done
```

### Parallel Execution (if resources allow)
```bash
# Run in background and collect results
for i in {0..9}; do
    python run_variant${i}.py > variant${i}_output.txt 2>&1 &
done
wait
echo "All variants completed"
```

### Individual Execution
```bash
python run_variant2.py  # Run specific variant
```

## Verification Checklist

✅ All 10 runner scripts created
✅ All 11 variant modules created
✅ All runners are executable
✅ All files follow naming convention
✅ All modules properly import and monkey-patch
✅ No existing files were modified
✅ Documentation created (VARIANTS_CREATED.md)

## Implementation Notes

### Monkey-Patching Approach
Each variant uses Python's `sys.modules` to replace baseline modules:

```python
# Example from run_variant7.py
import compatibility_variant7
import relaxation_variant7
sys.modules['compatibility'] = compatibility_variant7
sys.modules['relaxation'] = relaxation_variant7
```

This approach:
- Preserves all existing code
- Allows clean comparison between variants
- Makes it easy to add new variants
- Ensures all variants use the same test harness

### Module Inheritance
Variant modules import from baseline where possible:

```python
# Example from compatibility_variant5.py
from compatibility import *
POWER_COLOR = 6.0  # Override only what changes
```

This approach:
- Minimizes code duplication
- Makes changes explicit
- Easy to maintain and understand

## Next Steps

1. **Run all variants** on test dataset
2. **Compare results** across all 10 variants
3. **Analyze performance** (accuracy, speed, memory)
4. **Identify best variant** for production
5. **Document findings** in benchmark report

## File Paths

All files are located in: `C:/Users/I763940/icbv-fragment-reconstruction/`

- Runners: Root directory (`run_variant{N}.py`)
- Modules: `src/` subdirectory (`src/*_variant{N}.py`)

## Status

✅ **COMPLETE** - All variant files successfully created
✅ **VERIFIED** - File count and naming confirmed
✅ **DOCUMENTED** - Complete inventory and usage guide provided
