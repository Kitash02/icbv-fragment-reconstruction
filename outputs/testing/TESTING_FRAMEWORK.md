# Testing Framework Documentation

## Overview

This automated testing and validation system provides comprehensive infrastructure for validating fragment reconstruction improvements across all phases. The framework is designed for autonomous execution with no human intervention required.

## Architecture

The testing framework consists of 7 main components:

### 1. Phase Validation (`test_phase_validation.py`)
- **Purpose**: Automated test runner for each improvement phase
- **Features**:
  - Runs benchmark tests automatically
  - Extracts and compares metrics
  - Returns PASS/FAIL with detailed diagnostics
  - Tracks metrics across phases
  - Generates comprehensive reports

### 2. Metrics Validation (`validate_metrics.py`)
- **Purpose**: Computes and validates detailed metrics
- **Features**:
  - Calculates: accuracy, precision, recall, F1, specificity
  - Generates comparison tables
  - Flags regressions automatically
  - Analyzes case-by-case changes
  - Tracks confusion matrix evolution

### 3. Failure Analysis (`analyze_failure.py`)
- **Purpose**: Diagnoses why phases fail
- **Features**:
  - Identifies which test cases flipped
  - Analyzes failure patterns
  - Suggests specific fixes with code snippets
  - Generates parameter sweep scripts
  - Deep-dive analysis for specific cases

### 4. Phase Rollback (`rollback_phase.py`)
- **Purpose**: Safely rollback phase changes
- **Features**:
  - Creates backups before rollback
  - Restores previous phase state
  - Verifies rollback success with tests
  - Lists available backups
  - Supports dry-run mode

### 5. Continuous Validation (`continuous_validator.py`)
- **Purpose**: Fast smoke tests for rapid development
- **Features**:
  - Validates imports
  - Checks function signatures
  - Tests basic functionality
  - Verifies file structure
  - Runs in < 10 seconds

### 6. Visualization (`visualize_improvement.py`)
- **Purpose**: Generates comparison plots
- **Features**:
  - Improvement trajectory graphs
  - Confusion matrix evolution
  - Performance metrics charts
  - F1 score comparisons
  - High-quality PNG output

### 7. Parameter Sweep (`parameter_sweep.py`)
- **Purpose**: Automated parameter optimization
- **Features**:
  - Sweeps exponential power values
  - Tests histogram bin configurations
  - Optimizes LBP parameters
  - Finds optimal configurations automatically
  - Saves results for analysis

## Phase Definitions

### Baseline
- **Description**: Current implementation (BGR color space)
- **Expected**: 100% positive accuracy, 0% negative accuracy
- **Files**: `src/compatibility.py`, `src/main.py`

### Phase 1A: Lab Color Space
- **Description**: Replace BGR with Lab color space
- **Expected Improvements**:
  - Negative accuracy: 15-25%
  - Positive accuracy: ≥95%
- **Acceptable Regressions**:
  - Positive accuracy drop: ≤2%
  - Time increase: ≤20%

### Phase 1B: Exponential Color Penalty
- **Description**: Apply exponential penalty (power=2.5)
- **Expected Improvements**:
  - Negative accuracy: 25-40%
  - Positive accuracy: ≥95%
- **Acceptable Regressions**:
  - Positive accuracy drop: ≤3%
  - Time increase: ≤20%

### Phase 2A: LBP Texture Signatures
- **Description**: Add Local Binary Pattern texture descriptors
- **Expected Improvements**:
  - Negative accuracy: 40-60%
  - Positive accuracy: ≥95%
- **Acceptable Regressions**:
  - Positive accuracy drop: ≤3%
  - Time increase: ≤30%

### Phase 2B: Fractal Dimension
- **Description**: Add box-counting fractal dimension
- **Expected Improvements**:
  - Negative accuracy: 55-75%
  - Positive accuracy: ≥95%
- **Acceptable Regressions**:
  - Positive accuracy drop: ≤3%
  - Time increase: ≤40%

## Usage Guide

### Basic Workflow

#### 1. Establish Baseline
```bash
python scripts/test_phase_validation.py --phase baseline
```

This creates `outputs/testing/baseline_metrics.json` which serves as the comparison point for all phases.

#### 2. Validate Each Phase
```bash
# After implementing Phase 1A
python scripts/test_phase_validation.py --phase 1a

# After implementing Phase 1B
python scripts/test_phase_validation.py --phase 1b

# Continue for all phases
```

#### 3. Run All Phases Sequentially
```bash
python scripts/test_phase_validation.py --all
```

This runs all phases in order and stops if any phase fails.

### Continuous Development Workflow

During development, use the continuous validator for fast feedback:

```bash
# Quick smoke tests (< 10 seconds)
python scripts/continuous_validator.py

# After smoke tests pass, run full validation
python scripts/test_phase_validation.py --phase 1a
```

### Analyzing Failures

If a phase fails:

```bash
# Analyze what went wrong
python scripts/analyze_failure.py --compare baseline phase_1a

# Deep-dive into specific test case
python scripts/analyze_failure.py --deep-dive --case "mixed_gettyimages-13116049_gettyimages-17009652"

# Generate parameter sweep script
python scripts/analyze_failure.py --phase 1b --generate-sweep
```

### Parameter Optimization

If a phase needs tuning:

```bash
# Automatic parameter sweep
python scripts/parameter_sweep.py --phase 1b

# Quick sweep (fewer configurations)
python scripts/parameter_sweep.py --phase 1b --quick

# Specific parameter
python scripts/parameter_sweep.py --phase 2a --param lbp_params
```

### Rollback

If a phase fails catastrophically:

```bash
# Dry-run to see what would happen
python scripts/rollback_phase.py --phase 1a --dry-run

# Actual rollback
python scripts/rollback_phase.py --phase 1a --verify

# Rollback to baseline
python scripts/rollback_phase.py --to-baseline
```

### Visualization

Generate plots after running tests:

```bash
# Generate all plots
python scripts/visualize_improvement.py

# Plots up to specific phase
python scripts/visualize_improvement.py --phase 1b

# Custom output directory
python scripts/visualize_improvement.py --output outputs/my_plots
```

## Output Structure

```
outputs/testing/
├── baseline_metrics.json           # Baseline performance
├── metrics_1a.json                 # Phase 1A metrics
├── metrics_1b.json                 # Phase 1B metrics
├── metrics_2a.json                 # Phase 2A metrics
├── metrics_2b.json                 # Phase 2B metrics
├── metrics_tracking.csv            # All metrics over time
├── report_baseline_*.md            # Detailed reports
├── report_1a_*.md
├── test_results_*.txt              # Raw test outputs
├── failure_analysis_*.json         # Failure analysis results
├── plots/                          # Visualization plots
│   ├── improvement_trajectory.png
│   ├── confusion_evolution.png
│   ├── performance_metrics.png
│   └── f1_comparison.png
└── parameter_sweeps/               # Parameter sweep results
    └── sweep_1b_exponential_power_*.json
```

## Metrics Computed

### Accuracy Metrics
- **Positive Accuracy**: TP / (TP + FN)
- **Negative Accuracy**: TN / (TN + FP)
- **Balanced Accuracy**: (Positive + Negative) / 2

### Classification Metrics
- **Precision**: TP / (TP + FP)
- **Recall**: TP / (TP + FN)
- **F1 Score**: 2 * (Precision * Recall) / (Precision + Recall)
- **Specificity**: TN / (TN + FP)

### Performance Metrics
- **Total Time**: Sum of all test case execution times
- **Time per Fragment**: Total time / number of test cases

## Regression Detection

The framework automatically detects:

1. **Critical Regressions** (fail immediately):
   - Positive accuracy < 93%
   - Positive accuracy drop > 5%

2. **Warnings** (review required):
   - Positive accuracy drop > 2%
   - Time increase > 50%
   - No improvement in negative accuracy

## Automated Reporting

After each phase validation, the system generates:

### Test Report (`report_<phase>_*.md`)
- Phase information and description
- Metrics comparison table
- List of issues found
- Recommendation to proceed or fix
- Detailed diagnostics

### Metrics Tracking (`metrics_tracking.csv`)
- Chronological record of all test runs
- Enables trend analysis
- Tracks degradation over time

### Visual Reports (`plots/*.png`)
- Improvement trajectory
- Confusion matrix evolution
- Performance metrics
- F1 score comparison

## Failure Diagnosis Guide

### Failure Mode 1: Positive Accuracy Dropped

**Symptoms**:
- Baseline: 100%
- Current: <98%

**Diagnostic Steps**:
1. Identify which positive pairs now fail
2. Check their color BC, texture BC, geometric scores
3. Analyze if penalty became too strong

**Common Causes**:
- Exponential power too high
- Color penalty weight too high
- Threshold too strict

**Suggested Fixes**:
- Reduce exponential power (2.5 → 2.0)
- Reduce color penalty weight (0.80 → 0.70)
- Lower matching threshold

### Failure Mode 2: No Improvement in Negative Accuracy

**Symptoms**:
- Baseline: 0%
- Current: <10% (expected: 15-20% for Phase 1A)

**Diagnostic Steps**:
1. Check color BC distribution for negative pairs
2. If BC > 0.90 for most pairs → color too similar
3. If BC < 0.80 for most pairs → penalty wrong

**Common Causes**:
- Color alone insufficient (need texture)
- Histogram bins too coarse
- Exponential penalty not working

**Suggested Fixes**:
- Skip to texture phase (2A)
- Increase histogram bins (16→32)
- Tune exponential power with sweep

### Failure Mode 3: Processing Time Exploded

**Symptoms**:
- Baseline: 5s per fragment
- Current: >7.5s per fragment (>50% increase)

**Diagnostic Steps**:
1. Profile each component
2. Identify bottleneck (color, texture, fractal)
3. Check for inefficient loops

**Common Causes**:
- Too many histogram bins
- LBP parameters too fine
- Redundant computations

**Suggested Fixes**:
- Reduce histogram bins
- Reduce LBP points/radius
- Add caching/memoization
- Vectorize with NumPy

## Best Practices

### 1. Always Backup Before Changes
```bash
# Create backup of current state
cp src/compatibility.py outputs/implementation/backup_compatibility_$(date +%Y%m%d_%H%M%S).py
```

### 2. Run Smoke Tests Before Full Tests
```bash
python scripts/continuous_validator.py && python scripts/test_phase_validation.py --phase 1a
```

### 3. Use Dry-Run for Risky Operations
```bash
python scripts/rollback_phase.py --phase 1a --dry-run
```

### 4. Track All Changes
The framework automatically tracks all metrics in `metrics_tracking.csv`. Review this regularly.

### 5. Generate Plots After Each Phase
```bash
python scripts/visualize_improvement.py --phase 1a
```

Visualizations make it easier to spot trends and regressions.

## Troubleshooting

### Tests Take Too Long
- Use `--no-rotate` flag in run_test.py
- Use `--quick` flag in parameter_sweep.py
- Run continuous_validator.py instead of full tests

### Cannot Find Baseline Metrics
```bash
# Regenerate baseline
python scripts/test_phase_validation.py --phase baseline
```

### Rollback Not Working
- Check if backup exists: `python scripts/rollback_phase.py --list`
- Create manual backup first
- Use `--dry-run` to preview changes

### Plots Not Generating
- Check if matplotlib installed: `pip install matplotlib`
- Check if metrics files exist in `outputs/testing/`
- Run with error output: `python scripts/visualize_improvement.py 2>&1 | tee plot_errors.txt`

## Integration with CI/CD

The testing framework can be integrated into continuous integration:

```yaml
# Example .github/workflows/test.yml
name: Phase Validation

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run smoke tests
        run: python scripts/continuous_validator.py
      - name: Run phase validation
        run: python scripts/test_phase_validation.py --all
```

## Advanced Usage

### Custom Metrics
To add custom metrics, modify `validate_metrics.py`:

```python
# Add new metric calculation
custom_metric = compute_custom_metric(current, baseline)

comparison["deltas"]["custom_metric"] = {
    "current": custom_metric,
    "baseline": baseline_custom,
    "delta": custom_metric - baseline_custom,
}
```

### Custom Parameter Sweeps
To sweep custom parameters, modify `parameter_sweep.py`:

```python
def sweep_custom_param(self) -> List[Dict]:
    param_values = [1.0, 2.0, 3.0, 4.0, 5.0]

    for value in param_values:
        self.modify_code("custom_param", value)
        metrics = self.run_test()
        # Record results
```

### Custom Visualizations
To add custom plots, modify `visualize_improvement.py`:

```python
def plot_custom_metric(self, metrics: Dict[str, Dict]) -> Path:
    # Create custom visualization
    fig, ax = plt.subplots()
    # ... plot code ...
    plt.savefig(output_file)
    return output_file
```

## Support

For issues or questions:
1. Check this documentation
2. Review failure analysis output
3. Check `outputs/testing/` for detailed logs
4. Run with verbose output: `python -u script.py`

## Summary

This testing framework provides:
- ✓ Automated validation of all phases
- ✓ Comprehensive metrics tracking
- ✓ Automatic failure diagnosis
- ✓ Parameter optimization
- ✓ Safe rollback capabilities
- ✓ Visual progress tracking
- ✓ Fast smoke tests for development

All designed for autonomous execution with clear PASS/FAIL results and actionable recommendations.
