# Automated Testing Framework for Fragment Reconstruction

## Overview

Comprehensive automated testing and validation system for fragment reconstruction improvements. Validates EVERY phase autonomously with zero human intervention.

## Quick Start

```bash
# 1. Run smoke tests
python scripts/continuous_validator.py

# 2. Establish baseline
python scripts/test_phase_validation.py --phase baseline

# 3. Implement Phase 1A, then validate
python scripts/test_phase_validation.py --phase 1a

# 4. Generate visualizations
python scripts/visualize_improvement.py
```

See [`QUICK_START.md`](QUICK_START.md) for detailed walkthrough.

## Scripts

### Core Testing Scripts

1. **`test_phase_validation.py`** (300+ lines)
   - Automated test runner for each phase
   - Runs benchmark, extracts metrics, compares to baseline
   - Returns PASS/FAIL + detailed diagnostics
   ```bash
   python scripts/test_phase_validation.py --phase 1a
   python scripts/test_phase_validation.py --all
   ```

2. **`validate_metrics.py`** (200+ lines)
   - Reads test outputs and computes metrics
   - Generates comparison tables (baseline vs current)
   - Flags regressions automatically
   ```bash
   python scripts/validate_metrics.py --compare baseline phase_1a
   python scripts/validate_metrics.py --all
   ```

3. **`analyze_failure.py`** (400+ lines)
   - Automatic failure analysis
   - Identifies which pairs flipped
   - Suggests fixes with code snippets
   ```bash
   python scripts/analyze_failure.py --compare baseline phase_1a
   python scripts/analyze_failure.py --deep-dive --case "case_name"
   ```

4. **`rollback_phase.py`** (150+ lines)
   - Automated rollback of specific phase
   - Restores previous state from backup
   - Re-runs tests to confirm rollback
   ```bash
   python scripts/rollback_phase.py --phase 1a
   python scripts/rollback_phase.py --to-baseline
   ```

5. **`continuous_validator.py`** (200+ lines)
   - Quick smoke tests (< 10 seconds)
   - Validates: imports, functions, file structure
   - Fast feedback during development
   ```bash
   python scripts/continuous_validator.py
   ```

6. **`visualize_improvement.py`** (250+ lines)
   - Auto-generates comparison plots
   - Improvement trajectory, confusion matrices, performance
   - High-quality PNG output
   ```bash
   python scripts/visualize_improvement.py
   python scripts/visualize_improvement.py --phase 1b
   ```

7. **`parameter_sweep.py`** (300+ lines)
   - Automated parameter optimization
   - Sweeps: exponential power, histogram bins, LBP params
   - Finds optimal configuration automatically
   ```bash
   python scripts/parameter_sweep.py --phase 1b
   python scripts/parameter_sweep.py --phase 2a --quick
   ```

## Documentation

- **[`QUICK_START.md`](QUICK_START.md)** - 5-minute walkthrough
- **[`TESTING_FRAMEWORK.md`](TESTING_FRAMEWORK.md)** - Comprehensive guide
- **[`FAILURE_DIAGNOSIS_GUIDE.md`](FAILURE_DIAGNOSIS_GUIDE.md)** - Troubleshooting

## Output Structure

```
outputs/testing/
├── baseline_metrics.json           # Baseline performance
├── metrics_1a.json                 # Phase metrics
├── metrics_1b.json
├── metrics_2a.json
├── metrics_2b.json
├── metrics_tracking.csv            # Time series of all metrics
├── report_*.md                     # Detailed reports per phase
├── failure_analysis_*.json         # Failure diagnostics
├── plots/                          # Visualizations
│   ├── improvement_trajectory.png
│   ├── confusion_evolution.png
│   ├── performance_metrics.png
│   └── f1_comparison.png
└── parameter_sweeps/               # Parameter optimization results
    └── sweep_*.json
```

## Phase Definitions

| Phase | Description | Expected Neg Acc | Time Increase |
|-------|-------------|------------------|---------------|
| Baseline | BGR color space | 0% | - |
| 1A | Lab color space | 15-25% | ≤20% |
| 1B | Exponential penalty | 25-40% | ≤20% |
| 2A | LBP texture | 40-60% | ≤30% |
| 2B | Fractal dimension | 55-75% | ≤40% |

## Metrics Tracked

- **Accuracy**: Positive, Negative, Balanced
- **Classification**: Precision, Recall, F1, Specificity
- **Performance**: Total time, Time per fragment
- **Confusion Matrix**: TP, FP, TN, FN

## Automated Features

### Validation
- ✓ Runs benchmark automatically
- ✓ Extracts all metrics
- ✓ Compares to baseline
- ✓ Returns PASS/FAIL
- ✓ Generates detailed reports

### Diagnosis
- ✓ Identifies failure modes
- ✓ Analyzes which cases changed
- ✓ Suggests specific fixes
- ✓ Provides code snippets
- ✓ Recommends parameter sweeps

### Optimization
- ✓ Sweeps parameter space
- ✓ Tests each configuration
- ✓ Finds optimal values
- ✓ Reports results with recommendations

### Visualization
- ✓ Improvement trajectory
- ✓ Confusion matrix evolution
- ✓ Performance metrics
- ✓ F1 score comparison

### Safety
- ✓ Creates backups before changes
- ✓ Safe rollback mechanism
- ✓ Dry-run mode available
- ✓ Verifies rollback success

## Workflows

### Development Workflow
```bash
# 1. Quick validation
python scripts/continuous_validator.py

# 2. If pass, full validation
python scripts/test_phase_validation.py --phase 1a
```

### Troubleshooting Workflow
```bash
# 1. Analyze failure
python scripts/analyze_failure.py --compare baseline phase_1a

# 2. Tune parameters if needed
python scripts/parameter_sweep.py --phase 1a

# 3. Rollback if catastrophic
python scripts/rollback_phase.py --phase 1a
```

### Complete Validation Workflow
```bash
# Run all phases in sequence
python scripts/test_phase_validation.py --all

# Generate visualizations
python scripts/visualize_improvement.py
```

## Failure Modes

The framework automatically detects and diagnoses:

1. **Positive Accuracy Drop** → Tune penalty strength
2. **No Negative Improvement** → Add features or increase bins
3. **Time Explosion** → Optimize computation
4. **High False Positives** → Raise threshold
5. **High False Negatives** → Lower threshold

See [`FAILURE_DIAGNOSIS_GUIDE.md`](FAILURE_DIAGNOSIS_GUIDE.md) for details.

## Requirements

All scripts use standard Python libraries:
- `opencv-python` - Image processing
- `numpy` - Numerical operations
- `matplotlib` - Plotting (for visualization only)

Already included in project `requirements.txt`.

## Integration

### CI/CD Integration

```yaml
# .github/workflows/test.yml
- name: Run smoke tests
  run: python scripts/continuous_validator.py

- name: Validate phase
  run: python scripts/test_phase_validation.py --phase 1a
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit
python scripts/continuous_validator.py || exit 1
```

## Performance

- **Smoke tests**: <10 seconds
- **Phase validation**: ~2 minutes
- **Parameter sweep**: 5-15 minutes
- **Visualization**: <30 seconds

## Summary

Complete automated testing infrastructure:
- **7 comprehensive scripts** (1,800+ lines total)
- **3 detailed documentation files**
- **Full metrics tracking** with CSV
- **Visual progress monitoring**
- **Automatic failure diagnosis**
- **Parameter optimization**
- **Safe rollback capability**
- **< 10 second smoke tests**
- **Autonomous operation**

**Ready for production use. No manual intervention required.**

---

*Last updated: 2026-04-08*
