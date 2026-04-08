# Testing Framework Quick Start Guide

## 30-Second Start

```bash
# 1. Establish baseline
python scripts/test_phase_validation.py --phase baseline

# 2. Implement Phase 1A changes in src/compatibility.py

# 3. Validate Phase 1A
python scripts/test_phase_validation.py --phase 1a

# 4. Generate visualizations
python scripts/visualize_improvement.py
```

## 5-Minute Walkthrough

### Step 1: Verify Setup (10 seconds)

```bash
# Quick smoke test
python scripts/continuous_validator.py
```

Expected output:
```
✓ ALL SMOKE TESTS PASSED
  Code is ready for testing
```

### Step 2: Establish Baseline (2 minutes)

```bash
python scripts/test_phase_validation.py --phase baseline
```

This runs the full test suite and saves baseline metrics to `outputs/testing/baseline_metrics.json`.

Expected output:
```
✓ Phase baseline PASSED all checks

Positive Accuracy: 100.0%
Negative Accuracy: 0.0%
Balanced Accuracy: 50.0%
```

### Step 3: Implement Phase 1A (manual step)

Edit `src/compatibility.py` to use Lab color space:

```python
# Change color space conversion
lab = cv2.cvtColor(image, cv2.COLOR_BGR2Lab)  # Was BGR

# Update histogram bins
bins = (16, 8, 8)  # L, a, b channels
```

### Step 4: Validate Phase 1A (2 minutes)

```bash
python scripts/test_phase_validation.py --phase 1a
```

Expected output:
```
✓ Phase 1a PASSED

Positive Accuracy: 98.5% (drop: -1.5% ✓)
Negative Accuracy: 17.2% (improvement: +17.2% ✓✓✓)
Balanced Accuracy: 57.9% (improvement: +7.9% ✓)

✓ PROCEED to Phase 1B (Exponential Penalty)
```

### Step 5: Visualize Progress (30 seconds)

```bash
python scripts/visualize_improvement.py
```

Generates plots in `outputs/testing/plots/`:
- `improvement_trajectory.png`
- `confusion_evolution.png`
- `performance_metrics.png`
- `f1_comparison.png`

## Common Workflows

### Development Workflow

During active development:

```bash
# 1. Make code changes
vim src/compatibility.py

# 2. Quick validation (< 10 seconds)
python scripts/continuous_validator.py

# 3. Full validation if smoke tests pass
python scripts/test_phase_validation.py --phase 1a
```

### Troubleshooting Workflow

If tests fail:

```bash
# 1. Analyze failure
python scripts/analyze_failure.py --compare baseline phase_1a

# 2. Check specific case
python scripts/analyze_failure.py --deep-dive --case "case_name"

# 3. If needed, tune parameters
python scripts/parameter_sweep.py --phase 1a

# 4. If catastrophic, rollback
python scripts/rollback_phase.py --phase 1a
```

### Validation Workflow

Validate all phases at once:

```bash
# Run complete sequence
python scripts/test_phase_validation.py --all

# Stops at first failure
```

## File Locations

### Input
- Test data: `data/examples/positive/` and `data/examples/negative/`
- Source code: `src/compatibility.py`, `src/main.py`

### Output
- Metrics: `outputs/testing/metrics_*.json`
- Reports: `outputs/testing/report_*.md`
- Plots: `outputs/testing/plots/*.png`
- Logs: `outputs/test_logs/*.log`

## Key Scripts

### test_phase_validation.py
- **Purpose**: Main validation script
- **Run time**: ~2 minutes per phase
- **Usage**: `python scripts/test_phase_validation.py --phase 1a`

### continuous_validator.py
- **Purpose**: Fast smoke tests
- **Run time**: <10 seconds
- **Usage**: `python scripts/continuous_validator.py`

### analyze_failure.py
- **Purpose**: Diagnose failures
- **Run time**: <5 seconds
- **Usage**: `python scripts/analyze_failure.py --compare baseline phase_1a`

### parameter_sweep.py
- **Purpose**: Find optimal parameters
- **Run time**: 5-15 minutes
- **Usage**: `python scripts/parameter_sweep.py --phase 1b`

### visualize_improvement.py
- **Purpose**: Generate comparison plots
- **Run time**: <30 seconds
- **Usage**: `python scripts/visualize_improvement.py`

## Interpreting Results

### PASS Criteria

A phase passes if:
- Positive accuracy ≥ 95%
- Negative accuracy improved as expected
- Processing time increase < 50%
- No critical regressions

### FAIL Criteria

A phase fails if:
- Positive accuracy < 93% (critical)
- No improvement in negative accuracy
- Processing time > 150% of baseline
- Critical regressions detected

## Quick Fixes

### Positive Accuracy Dropped
```bash
# Tune exponential power
python scripts/parameter_sweep.py --phase 1b
```

### No Negative Improvement
```bash
# Increase histogram bins or add texture
python scripts/parameter_sweep.py --phase 1a --param lab_bins
```

### Tests Too Slow
```bash
# Use no-rotate mode
python run_test.py --no-rotate
```

## Phase Sequence

1. **Baseline**: Current implementation
2. **Phase 1A**: Lab color space (expect +15-20% neg acc)
3. **Phase 1B**: Exponential penalty (expect +10% neg acc)
4. **Phase 2A**: LBP texture (expect +15-20% neg acc)
5. **Phase 2B**: Fractal dimension (expect +10-15% neg acc)

## Expected Timeline

- Baseline: 2 minutes
- Phase 1A: 2 minutes test + 30 min implementation
- Phase 1B: 2 minutes test + 15 min implementation
- Phase 2A: 3 minutes test + 60 min implementation
- Phase 2B: 3 minutes test + 45 min implementation

Total: ~2.5 hours for full roadmap

## Troubleshooting

### "Baseline metrics not found"
```bash
python scripts/test_phase_validation.py --phase baseline
```

### "Tests taking too long"
```bash
# Use quick mode (no rotation)
python run_test.py --no-rotate
```

### "All tests fail"
```bash
# Run smoke tests first
python scripts/continuous_validator.py
```

### "Cannot rollback"
```bash
# List available backups
python scripts/rollback_phase.py --list

# Create manual backup
cp src/compatibility.py outputs/implementation/backup_$(date +%Y%m%d).py
```

## Next Steps

After mastering quick start:
1. Read `TESTING_FRAMEWORK.md` for comprehensive documentation
2. Read `FAILURE_DIAGNOSIS_GUIDE.md` for troubleshooting
3. Explore parameter sweeps for optimization
4. Integrate with CI/CD for automation

## Summary

The testing framework provides:
- **Fast feedback**: <10 second smoke tests
- **Comprehensive validation**: Full test suite in ~2 minutes
- **Automatic diagnosis**: Identifies issues and suggests fixes
- **Visual tracking**: Charts showing improvement trajectory
- **Safe rollback**: Undo changes if needed

Start with smoke tests, validate phases incrementally, visualize progress.
