# Real Fragment Test Harness

Comprehensive testing tool for evaluating the archaeological fragment reconstruction pipeline on real-world images.

## Purpose

This script tests the complete pipeline on validated real archaeological fragment images and compares performance against benchmark (synthetic) data. It helps identify:

- Which preprocessing steps work on real images
- Where the pipeline fails and why
- How well geometric matching generalizes from synthetic to real data
- The impact of real-world challenges (lighting, damage, irregular edges)

---

## Features

### 1. Preprocessing Validation
- Tests each real fragment through the preprocessing pipeline
- Logs success/failure for contour extraction
- Reports preprocessing success rate
- Identifies problematic images

### 2. Test Pair Generation
**Positive Cases** (same source):
- Takes 2-3 fragments from the SAME source artifact
- Tests if the system correctly matches them
- Measures true positive rate

**Negative Cases** (different sources):
- Takes 2 fragments from DIFFERENT source artifacts
- Tests if the system correctly rejects them
- Measures false positive rate

### 3. Full Pipeline Execution
- Runs complete reconstruction pipeline on each test pair
- Extracts chain codes and compatibility scores
- Runs relaxation labeling
- Computes match verdicts (MATCH/WEAK_MATCH/NO_MATCH)

### 4. Comprehensive Reporting
**JSON Report** (`real_fragment_test_report.json`):
- Machine-readable test results
- Per-fragment preprocessing outcomes
- Per-pair match results with confidence scores
- Summary statistics

**Markdown Report** (`real_fragment_test_report.md`):
- Human-readable executive summary
- Detailed failure analysis
- Benchmark comparison tables
- Insights and recommendations

**Visualizations**:
- `preprocessing_comparison.png` — Success rates (real vs benchmark)
- `accuracy_comparison.png` — Matching accuracy (positive/negative/overall)
- `confidence_distribution.png` — Score distributions by case type
- `color_vs_geometric.png` — Scatter plot of appearance vs shape similarity

---

## Usage

### Basic Usage
```bash
python scripts/test_real_fragments.py
```

Uses default paths:
- Input: `data/raw/real_fragments_validated/`
- Output: `outputs/real_fragment_analysis/`

### With Custom Paths
```bash
python scripts/test_real_fragments.py \
  --input data/raw/real_fragments_validated \
  --output outputs/real_fragment_analysis
```

### Compare Against Benchmark
```bash
python scripts/test_real_fragments.py \
  --benchmark-dir data/examples \
  --compare-benchmark
```

Loads expected benchmark performance and generates comparison plots.

### Verbose Mode
```bash
python scripts/test_real_fragments.py --verbose
```

Enables debug-level logging for detailed diagnostics.

---

## Expected Directory Structure

### Option 1: Organized by Source
```
data/raw/real_fragments_validated/
├── british_museum/
│   ├── shard_01.jpg
│   ├── shard_02.jpg
│   └── shard_03.jpg
├── wikimedia/
│   ├── pottery_frag_a.jpg
│   └── pottery_frag_b.jpg
└── metropolitan_museum/
    ├── fragment_01.png
    └── fragment_02.png
```

**Behavior**: Creates positive pairs within each source directory, negative pairs across directories.

### Option 2: Flat Structure
```
data/raw/real_fragments_validated/
├── frag_01.jpg
├── frag_02.jpg
├── frag_03.jpg
└── frag_04.jpg
```

**Behavior**: Treats all fragments as from "unknown_source". Creates positive pairs from adjacent fragments. Cannot create negative pairs.

### Recommendation
Use **Option 1** (organized by source) for meaningful positive/negative case testing.

---

## Output Files

After running, the output directory contains:

```
outputs/real_fragment_analysis/
├── real_fragment_test_report.json          # Machine-readable results
├── real_fragment_test_report.md            # Human-readable report
├── preprocessing_comparison.png            # Success rate chart
├── accuracy_comparison.png                 # Accuracy metrics chart
├── confidence_distribution.png             # Score histograms
├── color_vs_geometric.png                  # 2D scatter plot
└── test_real_fragments_YYYYMMDD_HHMMSS.log # Detailed log file
```

---

## Interpreting Results

### Preprocessing Success Rate
- **Target**: ≥ 80% on real fragments
- **Benchmark**: 100% (synthetic fragments have perfect backgrounds)

**Low success rate indicates**:
- Poor image quality (lighting, resolution)
- Complex backgrounds not properly removed
- Fragments too small or damaged

**Solutions**:
- Improve image capture conditions
- Adjust preprocessing parameters (Canny thresholds, morphological operations)
- Manual background removal for problematic images

### Positive Accuracy (Same Source Matching)
- **Target**: ≥ 70% on real fragments
- **Benchmark**: 100% (synthetic fragments have perfect edges)

**Low positive accuracy (false negatives) indicates**:
- Real fragment edges too damaged/eroded for geometric matching
- Preprocessing losing critical edge details
- Matching thresholds too strict

**Solutions**:
- Relax `MATCH_SCORE_THRESHOLD` (currently 0.55)
- Improve preprocessing to preserve edge details
- Consider using color/texture features to complement geometry

### Negative Accuracy (Different Source Rejection)
- **Target**: ≥ 70% on real fragments
- **Benchmark**: 100% (synthetic fragments from different sources are visually distinct)

**Low negative accuracy (false positives) indicates**:
- Fragments from different sources have similar geometric patterns by chance
- Color-based filtering not discriminative enough
- Matching thresholds too permissive

**Solutions**:
- Tighten `MATCH_SCORE_THRESHOLD`
- Improve color histogram comparison
- Add additional appearance features (texture, material properties)

### Confidence Scores

**Positive pairs** (same source):
- Should cluster above `MATCH_SCORE_THRESHOLD` (0.55)
- Average: 0.60 – 0.80 for good matches

**Negative pairs** (different sources):
- Should cluster below `WEAK_MATCH_SCORE_THRESHOLD` (0.35)
- Average: 0.10 – 0.30 for clear rejections

**Overlapping distributions** indicate:
- Ambiguous cases where geometric and appearance signals conflict
- Need for threshold tuning or feature improvements

---

## Example Output (Console)

```
======================================================================
Real Fragment Test Harness
======================================================================
Input directory: data/raw/real_fragments_validated
Output directory: outputs/real_fragment_analysis
Found 3 fragments in source 'british_museum'
Found 2 fragments in source 'wikimedia'
Total fragments to test: 5 from 2 sources
======================================================================
Phase 1: Testing Preprocessing Pipeline
======================================================================
✓ shard_01 — 324 contour points, 512x512 px, 45.2 ms
✓ shard_02 — 298 contour points, 480x500 px, 42.1 ms
✗ shard_03 — preprocessing failed: No contours found after binarization and cleanup. (38.5 ms)
✓ pottery_frag_a — 412 contour points, 600x600 px, 51.3 ms
✓ pottery_frag_b — 389 contour points, 580x590 px, 48.7 ms
======================================================================
Phase 2: Creating Test Pairs
======================================================================
Created 2 positive pairs (same source) and 2 negative pairs (different sources)
======================================================================
Phase 3: Testing Fragment Pairs
======================================================================
Testing 2 positive pairs (same source)...
✓ shard_01 ↔ shard_02 [SAME] — verdict=MATCH, confidence=0.627, color_BC=0.851, 1823 ms
Testing 2 negative pairs (different sources)...
✓ shard_01 ↔ pottery_frag_a [DIFF] — verdict=NO_MATCH, confidence=0.215, color_BC=0.423, 1645 ms
✓ shard_02 ↔ pottery_frag_b [DIFF] — verdict=NO_MATCH, confidence=0.198, color_BC=0.387, 1672 ms
======================================================================
REAL FRAGMENT TEST SUMMARY
======================================================================
Preprocessing Success Rate: 80.0%
Positive Accuracy:          100.0%
Negative Accuracy:          100.0%
Overall Accuracy:           100.0%
======================================================================

Full report: outputs/real_fragment_analysis/real_fragment_test_report.md
Visualizations: outputs/real_fragment_analysis/
```

---

## Troubleshooting

### "No fragments found in ..."
**Cause**: Empty input directory or wrong path.

**Solution**: Check that `data/raw/real_fragments_validated/` exists and contains images. Use `--input` to specify correct path.

### "Preprocessing failed: No contours found..."
**Cause**: Fragment not cleanly separated from background, or image too low quality.

**Solution**:
- Check image manually: Is fragment visible? Is background uniform?
- Try adjusting image (crop, brightness, contrast) before testing
- Use `--verbose` to see detailed preprocessing diagnostics

### "No positive pairs created"
**Cause**: Each source directory has only 1 fragment.

**Solution**: Add more fragments to each source, or manually specify which fragments are from the same source by organizing them into subdirectories.

### All pairs reported as NO_MATCH
**Cause**: Real fragments too damaged, or thresholds too strict.

**Solution**:
- Check confidence scores in report — are positive pairs close to threshold?
- Consider relaxing `MATCH_SCORE_THRESHOLD` in `src/relaxation.py`
- Inspect visualizations: is there clear separation between positive and negative distributions?

---

## Integration with Benchmark Testing

To compare real fragment performance against synthetic benchmarks:

1. **Run benchmark tests first**:
   ```bash
   python run_test.py --test-all
   ```

2. **Run real fragment tests with comparison**:
   ```bash
   python scripts/test_real_fragments.py --compare-benchmark
   ```

3. **Check comparison tables** in the markdown report:
   - Preprocessing success rate difference
   - Matching accuracy difference
   - Confidence score distributions

**Expected differences**:
- Real fragments: 70-90% success rates (due to real-world challenges)
- Benchmark: 95-100% success rates (clean synthetic data)

Large gaps (>30%) indicate areas for improvement in preprocessing robustness.

---

## Extending the Test Harness

### Adding Custom Metrics

Edit `compute_summary_statistics()` to add new metrics:

```python
# Example: Track average execution time
summary.avg_execution_time_ms = np.mean([r.execution_time_ms for r in pair_results])
```

### Custom Visualizations

Add new plots in `generate_visualizations()`:

```python
# Example: Execution time histogram
fig, ax = plt.subplots(1, 1, figsize=(10, 6))
times = [r.execution_time_ms for r in summary.pair_results]
ax.hist(times, bins=20, color='#3498db', edgecolor='black')
ax.set_xlabel('Execution Time (ms)')
ax.set_ylabel('Frequency')
ax.set_title('Pipeline Execution Time Distribution')
plt.savefig(os.path.join(output_dir, 'execution_time.png'), dpi=150)
```

### Additional Test Cases

Modify `create_test_pairs()` to generate custom pair combinations:

```python
# Example: Test all fragments against all others (exhaustive)
for i, frag_i in enumerate(all_fragments):
    for j, frag_j in enumerate(all_fragments):
        if i < j:
            pairs.append((frag_i, frag_j, source_i, source_j))
```

---

## Dependencies

- Python 3.7+
- opencv-python
- numpy
- matplotlib
- scipy (optional, for advanced statistics)

Install with:
```bash
pip install opencv-python numpy matplotlib scipy
```

---

## Related Scripts

- `generate_benchmark_data.py` — Creates synthetic fragment datasets
- `analyze_benchmark_results.py` — Analyzes benchmark test logs
- `profile_performance.py` — Measures pipeline execution performance
- `download_real_fragments.py` — Downloads real fragment images

---

## Contact & Support

For questions or issues:
1. Check the markdown report's "Insights and Recommendations" section
2. Enable `--verbose` mode for detailed diagnostics
3. Inspect log files in the output directory
4. Review preprocessing failures in the JSON report

---

**Last Updated**: 2026-04-08
