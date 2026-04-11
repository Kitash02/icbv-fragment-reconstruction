# Variant Test Runners Created

All variant test runners and supporting modules have been created successfully.

## Files Created

### Variant 2: Hierarchical Ensemble
- `run_variant2.py` - Test runner script
- `src/ensemble_postprocess_variant2.py` - Hierarchical ensemble module

**Configuration:**
- Formula: Baseline (color^4 × texture^2 × gabor^2 × haralick^2)
- Thresholds: 0.75 / 0.60 / 0.65 (baseline)
- Ensemble: Hierarchical decision tree (fast path optimization)

### Variant 3: Tuned Weighted Ensemble
- `run_variant3.py` - Test runner script
- `src/ensemble_postprocess_variant3.py` - Tuned weighted ensemble module

**Configuration:**
- Formula: Baseline (color^4 × texture^2 × gabor^2 × haralick^2)
- Thresholds: 0.75 / 0.60 / 0.65 (baseline)
- Ensemble: Weighted with custom weights (color=0.40, raw=0.25, texture=0.15, morph=0.15, gabor=0.05)

### Variant 4: Relaxed Thresholds
- `run_variant4.py` - Test runner script
- `src/relaxation_variant4.py` - Relaxed threshold module

**Configuration:**
- Formula: Baseline (color^4 × texture^2 × gabor^2 × haralick^2)
- Thresholds: 0.70 / 0.55 / 0.60 (relaxed)
- Ensemble: Baseline (five-way voting)

### Variant 5: Color-Dominant Formula
- `run_variant5.py` - Test runner script
- `src/compatibility_variant5.py` - Color-dominant formula module

**Configuration:**
- Formula: color^6 × texture^2 × gabor^2 × haralick^2 (POWER_COLOR=6.0)
- Thresholds: 0.75 / 0.60 / 0.65 (baseline)
- Ensemble: Baseline (five-way voting)

### Variant 6: Balanced Powers
- `run_variant6.py` - Test runner script
- `src/compatibility_variant6.py` - Balanced powers module

**Configuration:**
- Formula: color^2 × texture^2 × gabor^2 × haralick^2 (all powers=2.0)
- Thresholds: 0.75 / 0.60 / 0.65 (baseline)
- Ensemble: Baseline (five-way voting)

### Variant 7: Optimized Powers + Tuned Thresholds
- `run_variant7.py` - Test runner script
- `src/compatibility_variant7.py` - Optimized powers module
- `src/relaxation_variant7.py` - Tuned thresholds module

**Configuration:**
- Formula: color^5 × texture^2.5 × gabor^2 × haralick^2
- Thresholds: 0.72 / 0.58 / 0.62 (tuned)
- Ensemble: Baseline (five-way voting)

### Variant 8: Adaptive Thresholds
- `run_variant8.py` - Test runner script
- `src/relaxation_variant8.py` - Adaptive thresholds module

**Configuration:**
- Formula: Baseline (color^4 × texture^2 × gabor^2 × haralick^2)
- Thresholds: Adaptive based on artifact type
  - Pottery: 0.78 / 0.63 / 0.68 (stricter)
  - Sculpture: 0.70 / 0.55 / 0.60 (relaxed)
  - Default: 0.75 / 0.60 / 0.65 (baseline)
- Ensemble: Baseline (five-way voting)

### Variant 9: Full Research Stack
- `run_variant9.py` - Test runner script
- `src/ensemble_postprocess_variant9.py` - Full stack ensemble module

**Configuration:**
- Formula: color^5 × texture^2.5 × gabor^2 × haralick^2 (from Variant 7)
- Thresholds: Adaptive (from Variant 8)
- Ensemble: Weighted with tuned weights (from Variant 3)

## How to Run

Each variant can be run independently:

```bash
# Run a specific variant
python run_variant2.py
python run_variant3.py
python run_variant4.py
python run_variant5.py
python run_variant6.py
python run_variant7.py
python run_variant8.py
python run_variant9.py
```

Or run all variants in sequence:

```bash
for i in {2..9}; do
    echo "Running Variant $i..."
    python run_variant${i}.py
done
```

## Implementation Details

### Monkey-Patching Strategy
Each `run_variant{N}.py` file uses Python's module system to replace baseline modules:

1. Adds `src/` to Python path
2. Imports variant-specific modules
3. Replaces baseline modules in `sys.modules`
4. Runs `run_test.main()`

This approach ensures:
- No modifications to existing files
- Clean separation of variants
- Easy comparison between variants
- All variants use the same test harness

### Module Replacement Patterns

**Ensemble changes only:**
- Import `ensemble_postprocess_variant{N}`
- Replace `sys.modules['ensemble_postprocess']`

**Threshold changes only:**
- Import `relaxation_variant{N}`
- Replace `sys.modules['relaxation']`

**Formula changes only:**
- Import `compatibility_variant{N}`
- Replace `sys.modules['compatibility']`

**Multiple changes:**
- Import multiple variant modules
- Replace multiple entries in `sys.modules`

## Variant Characteristics

| Variant | Formula | Thresholds | Ensemble | Purpose |
|---------|---------|------------|----------|---------|
| 2 | Baseline | Baseline | Hierarchical | Speed optimization |
| 3 | Baseline | Baseline | Weighted (tuned) | Better discrimination |
| 4 | Baseline | Relaxed | Baseline | Higher recall |
| 5 | Color^6 | Baseline | Baseline | Max color emphasis |
| 6 | Balanced | Baseline | Baseline | Equal weighting |
| 7 | Optimized | Tuned | Baseline | Balanced optimization |
| 8 | Baseline | Adaptive | Baseline | Context-aware |
| 9 | Optimized | Adaptive | Weighted | Full stack |

## Expected Outcomes

Based on the configuration design:

- **Variant 2**: Should be fastest (hierarchical fast-path)
- **Variant 3**: Should improve on color-based discrimination
- **Variant 4**: Should detect more matches (higher recall)
- **Variant 5**: Should maximize color discrimination (may over-penalize)
- **Variant 6**: Should balance all features equally
- **Variant 7**: Should be well-balanced overall
- **Variant 8**: Should adapt to artifact characteristics
- **Variant 9**: Should achieve highest overall accuracy

## Notes

All variant files follow the same structure and conventions as the existing Variant 1.
No existing files were modified during this process.
