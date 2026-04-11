# Benchmark Results Analysis Script

## Overview

`analyze_benchmark_results.py` is a standalone, non-invasive analysis tool for evaluating the performance of the archaeological fragment reconstruction pipeline. It parses benchmark metadata and test run logs to generate comprehensive visualizations and statistics about pipeline performance, failure modes, and matching characteristics.

## Features

### Data Parsing
- **Benchmark Metadata**: Parses JSON metadata from `data/benchmark/*/metadata.json` or `data/examples/*/*_meta.json`
- **Test Run Logs**: Parses log files from `outputs/logs/run_*.log`
- **Automatic Detection**: Identifies positive (same-image) and negative (mixed-image) test cases

### Extracted Metrics
- Match verdict (MATCH, WEAK_MATCH, NO_MATCH)
- Confidence scores
- Execution time (total and per-stage breakdown)
- Color similarity metrics (Bhattacharyya coefficient)
- Fragment counts and characteristics
- Convergence traces from relaxation labeling

### Failure Pattern Analysis
- Identifies which negative cases pass/fail
- Analyzes color similarity distribution for failed cases
- Identifies common characteristics of false positives/negatives
- Correlates surface damage with prediction accuracy

### Visualizations

Generated plots (saved to `outputs/analysis/`):

1. **confusion_matrix.png**: Confusion matrix showing TP, TN, FP, FN counts
2. **confidence_distributions.png**: Histograms of confidence scores for positive vs. negative cases
3. **runtime_breakdown.png**: Pie chart and stacked bar chart showing time spent in each pipeline stage
4. **color_similarity_heatmap.png**: Heatmap of color similarity metrics across test cases
5. **convergence_analysis.png**: Relaxation labeling convergence traces (correct vs. incorrect predictions)
6. **failure_characteristics.png**: Analysis of failure patterns (color metrics, fragment counts, damage correlation)

### Summary Statistics

Console output includes:
- Dataset overview (total/positive/negative cases)
- Confusion matrix (TP, TN, FP, FN)
- Performance metrics (accuracy, precision, recall, F1 score)
- Mean confidence scores by category
- Runtime performance
- Detailed failure case listings

### Output Files

- **analysis_report.json**: JSON file containing all summary statistics
- **6 PNG plots**: Visualizations as described above

## Usage

### Basic Usage

```bash
python scripts/analyze_benchmark_results.py
```

Uses default directories:
- Benchmark: `data/examples`
- Logs: `outputs/test_logs`
- Output: `outputs/analysis`

### Custom Directories

```bash
python scripts/analyze_benchmark_results.py \
  --benchmark-dir data/benchmark \
  --log-dir outputs/logs \
  --output-dir outputs/analysis
```

### Alternative Argument Names

For compatibility with existing workflows:

```bash
python scripts/analyze_benchmark_results.py \
  --examples data/examples \
  --logs outputs/test_logs
```

### Skip Plotting (Statistics Only)

```bash
python scripts/analyze_benchmark_results.py --no-plots
```

Generates console summary and JSON report without creating plots.

### Verbose Mode

```bash
python scripts/analyze_benchmark_results.py --verbose
```

Enables debug-level logging (includes matplotlib debug output).

## Dependencies

### Required
- **matplotlib**: For generating plots
- **numpy**: For numerical computations

### Optional
- **seaborn**: For prettier plots (automatically used if available)

Install dependencies:
```bash
pip install matplotlib numpy seaborn
```

## Integration with Pipeline

### After Running Tests

1. Generate benchmark data:
   ```bash
   python generate_benchmark_data.py --output data/examples/positive/my_test
   ```

2. Run tests:
   ```bash
   python run_test.py
   ```

3. Analyze results:
   ```bash
   python scripts/analyze_benchmark_results.py
   ```

### Interpreting Results

#### High Accuracy (>90%)
Pipeline correctly distinguishes same-image from mixed-image fragments.

#### High False Positive Rate
Pipeline incorrectly matches fragments from different images. Check:
- Color similarity threshold (may need tuning)
- Fragment edge characteristics
- Whether fragments have similar textures

#### High False Negative Rate
Pipeline fails to match fragments from the same image. Check:
- Surface damage levels
- Fragment sizes (too small?)
- Rotation normalization effectiveness

#### Color Similarity Analysis
- **High BC for FP**: Fragments from different images have similar colors (challenging case)
- **Low BC for FN**: Fragments from same image have varied colors (lighting/degradation)

#### Convergence Analysis
- **Fast convergence**: Clear geometric compatibility
- **Slow convergence**: Ambiguous cases requiring more iterations
- **Different patterns for correct/incorrect**: May indicate potential for early stopping

## Data Structures

### BenchmarkCase
Represents complete metadata for a benchmark test case:
- case_name, case_type
- source_image, source_size
- fragment counts and characteristics
- displacement parameters

### TestResult
Results from a single test run:
- verdicts (expected vs. actual)
- confidence scores
- timing breakdown
- color similarity metrics
- convergence trace

### AnalysisReport
Aggregated analysis results:
- confusion matrix
- performance metrics
- mean confidences by category
- failure patterns

## Example Output

```
================================================================================
                    BENCHMARK ANALYSIS SUMMARY
================================================================================

Dataset Overview:
  Total test cases: 20
  Positive cases (same-image): 12
  Negative cases (mixed-image): 8

Confusion Matrix:
  True Positives (TP):   11  (correct matches)
  True Negatives (TN):    7  (correct rejections)
  False Positives (FP):   1  (incorrect matches)
  False Negatives (FN):   1  (missed matches)

Performance Metrics:
  Accuracy:  0.900  (90.0%)
  Precision: 0.917  (of predicted matches, how many are correct)
  Recall:    0.917  (of actual matches, how many are found)
  F1 Score:  0.917  (harmonic mean of precision and recall)

Confidence Score Analysis:
  Mean confidence (TP): 0.856
  Mean confidence (TN): 0.124
  Mean confidence (FP): 0.523
  Mean confidence (FN): 0.089

Runtime Performance:
  Mean execution time: 4.23 seconds per case
```

## Design Philosophy

### Non-Invasive
- Does not modify any source code or test data
- Reads existing logs and metadata only
- Can be run repeatedly without side effects

### Standalone
- Single self-contained Python file
- Minimal dependencies
- Works with existing directory structure

### Comprehensive
- Covers all major evaluation metrics
- Multiple visualization types
- Detailed failure analysis

### Production-Ready
- Type hints throughout
- Comprehensive docstrings
- Error handling
- Windows console compatibility (no Unicode issues)

## Troubleshooting

### No test results found
**Solution**: Run `run_test.py` first to generate test logs.

### No metadata found
**Solution**: Ensure benchmark metadata JSON files exist in the specified directory.

### Import errors
**Solution**: Install required dependencies:
```bash
pip install matplotlib numpy
```

### Empty plots
**Issue**: Not enough test cases for meaningful visualization.
**Solution**: Run more test cases or check that logs are being parsed correctly.

## Future Enhancements

Potential improvements:
- ROC curve and AUC analysis
- Per-fragment difficulty analysis
- Jaggedness vs. accuracy correlation
- Cross-validation fold analysis
- HTML report generation
- Interactive plots with Plotly

## Author

Created as part of the ICBV archaeological fragment reconstruction project.

## License

Same as parent project.
