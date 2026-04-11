# Test Real Fragments - Usage Examples

## Quick Start

### 1. Basic Test (Default Paths)
```bash
python scripts/test_real_fragments.py
```

This will:
- Look for real fragments in `data/raw/real_fragments_validated/`
- Test preprocessing on all found fragments
- Create positive and negative test pairs
- Generate reports in `outputs/real_fragment_analysis/`

**Expected output**:
```
======================================================================
Real Fragment Test Harness
======================================================================
Found 3 fragments in source 'british_museum'
Found 2 fragments in source 'wikimedia'
Total fragments to test: 5 from 2 sources
...
======================================================================
REAL FRAGMENT TEST SUMMARY
======================================================================
Preprocessing Success Rate: 80.0%
Positive Accuracy:          100.0%
Negative Accuracy:          100.0%
Overall Accuracy:           100.0%
======================================================================
```

---

## 2. Custom Input Directory
```bash
python scripts/test_real_fragments.py \
  --input /path/to/my/real/fragments \
  --output outputs/my_test_results
```

Useful when testing different fragment collections.

---

## 3. Compare Against Benchmark
```bash
python scripts/test_real_fragments.py \
  --benchmark-dir data/examples \
  --compare-benchmark
```

This loads expected benchmark performance and generates comparison visualizations:
- Side-by-side accuracy charts
- Performance difference tables
- Gap analysis in the markdown report

**Sample output**:
```
### Comparison with Benchmark

| Metric | Real Fragments | Benchmark | Difference |
|--------|----------------|-----------|------------|
| Preprocessing Success | 85.0% | 100.0% | -15.0% |
| Positive Accuracy | 75.0% | 100.0% | -25.0% |
| Negative Accuracy | 90.0% | 100.0% | -10.0% |
| Overall Accuracy | 82.5% | 100.0% | -17.5% |
```

---

## 4. Verbose Debug Mode
```bash
python scripts/test_real_fragments.py --verbose
```

Enables detailed diagnostic logging:
- Preprocessing step-by-step execution
- Chain code extraction details
- Compatibility matrix computation
- Relaxation labeling iterations

Useful for debugging preprocessing failures.

---

## Directory Structure Examples

### Example 1: Multiple Sources (Recommended)
```
data/raw/real_fragments_validated/
├── british_museum/
│   ├── pottery_shard_01.jpg    # From British Museum collection
│   ├── pottery_shard_02.jpg    # Same artifact as 01
│   └── pottery_shard_03.jpg    # Same artifact as 01 and 02
├── wikimedia/
│   ├── fresco_fragment_a.jpg   # Roman fresco from Wikimedia
│   └── fresco_fragment_b.jpg   # Same fresco as a
└── metropolitan/
    ├── tablet_piece_1.png      # Clay tablet from Met Museum
    └── tablet_piece_2.png      # Same tablet as piece_1
```

**Test pairs created**:
- **Positive pairs** (same source, should match):
  - british_museum: pottery_shard_01 ↔ pottery_shard_02
  - british_museum: pottery_shard_02 ↔ pottery_shard_03
  - wikimedia: fresco_fragment_a ↔ fresco_fragment_b
  - metropolitan: tablet_piece_1 ↔ tablet_piece_2

- **Negative pairs** (different sources, should NOT match):
  - pottery_shard_01 ↔ fresco_fragment_a
  - pottery_shard_01 ↔ tablet_piece_1
  - fresco_fragment_a ↔ tablet_piece_1

### Example 2: Flat Structure (Limited Testing)
```
data/raw/real_fragments_validated/
├── fragment_01.jpg
├── fragment_02.jpg
├── fragment_03.jpg
└── fragment_04.jpg
```

**Test pairs created**:
- **Positive pairs** (assumes adjacent = same source):
  - fragment_01 ↔ fragment_02
  - fragment_02 ↔ fragment_03
  - fragment_03 ↔ fragment_04

- **Negative pairs**: None (cannot determine different sources)

**Limitation**: Cannot test false positive rate without source organization.

---

## Sample Workflow

### Step 1: Download Real Fragments
```bash
python scripts/download_real_fragments.py
```

Downloads curated real fragment images to `data/raw/real_fragments/`.

### Step 2: Organize by Source
Manually organize downloaded fragments:
```bash
mkdir -p data/raw/real_fragments_validated/british_museum
mkdir -p data/raw/real_fragments_validated/wikimedia

mv data/raw/real_fragments/shard_01_british.jpg data/raw/real_fragments_validated/british_museum/
mv data/raw/real_fragments/shard_02_cord_marked.jpg data/raw/real_fragments_validated/wikimedia/
```

### Step 3: Run Tests
```bash
python scripts/test_real_fragments.py --compare-benchmark
```

### Step 4: Review Results
```bash
# Open markdown report
open outputs/real_fragment_analysis/real_fragment_test_report.md

# Or on Windows
start outputs/real_fragment_analysis/real_fragment_test_report.md

# View visualizations
open outputs/real_fragment_analysis/preprocessing_comparison.png
open outputs/real_fragment_analysis/accuracy_comparison.png
open outputs/real_fragment_analysis/confidence_distribution.png
open outputs/real_fragment_analysis/color_vs_geometric.png
```

---

## Interpreting Output Files

### 1. `real_fragment_test_report.md`
Human-readable report with:
- Executive summary (success rates, accuracy)
- Preprocessing failure details
- Detailed pair-by-pair results table
- Benchmark comparison (if enabled)
- Insights and recommendations

**Look for**:
- "Preprocessing Failures" section — which images failed and why
- "Detailed Pair Results" table — which pairs were correctly/incorrectly matched
- "Insights and Recommendations" — actionable next steps

### 2. `real_fragment_test_report.json`
Machine-readable results for automated analysis:
```json
{
  "timestamp": "2026-04-08T10:30:15.123456",
  "summary": {
    "n_fragments_tested": 5,
    "preprocessing_success_rate": 0.8,
    "positive_accuracy": 0.75,
    "negative_accuracy": 0.9,
    "overall_accuracy": 0.825
  },
  "preprocessing_results": [...],
  "pair_results": [...]
}
```

**Use for**:
- Automated testing pipelines
- Long-term performance tracking
- Batch analysis across multiple test runs

### 3. Visualizations

#### `preprocessing_comparison.png`
Bar chart comparing preprocessing success rates:
- Real Fragments: 85.0%
- Benchmark: 100.0%

**Interpretation**: A 15% gap is acceptable for real-world images. Gaps >30% indicate serious preprocessing issues.

#### `accuracy_comparison.png`
Grouped bar chart showing:
- Positive case accuracy (true positive rate)
- Negative case accuracy (true negative rate)
- Overall accuracy

**Interpretation**: Real fragments should achieve ≥70% on both positive and negative cases.

#### `confidence_distribution.png`
Histogram overlay showing:
- Green bars: Positive pairs (should cluster high)
- Red bars: Negative pairs (should cluster low)
- Green dashed line: MATCH threshold (0.55)
- Orange dashed line: WEAK_MATCH threshold (0.35)

**Interpretation**: Clear separation = good discriminative power. Overlapping distributions = ambiguous cases.

#### `color_vs_geometric.png`
Scatter plot with:
- X-axis: Color similarity (Bhattacharyya coefficient)
- Y-axis: Geometric confidence score
- Green dots: Positive pairs (same source)
- Red dots: Negative pairs (different sources)
- Circles: Match found
- X marks: No match

**Interpretation**: Positive pairs should cluster in top-right (high color + geometric similarity). Negative pairs should scatter in bottom-left.

---

## Common Issues and Solutions

### Issue 1: No fragments found
```
[ERROR] No fragments found in data/raw/real_fragments_validated
```

**Solution**: Check that directory exists and contains images:
```bash
ls data/raw/real_fragments_validated/
# Should show image files or subdirectories
```

### Issue 2: All preprocessing failures
```
Preprocessing Success Rate: 0.0%
```

**Possible causes**:
- Images have complex backgrounds (not removed)
- Images are too low resolution (<300x300 px)
- Fragment is too small relative to image size

**Solution**:
```bash
# Check a sample image
python -c "import cv2; print(cv2.imread('data/raw/real_fragments_validated/british_museum/shard_01.jpg').shape)"

# Try preprocessing manually to see error
python -c "
import sys; sys.path.insert(0, 'src')
from preprocessing import preprocess_fragment
img, contour = preprocess_fragment('data/raw/real_fragments_validated/british_museum/shard_01.jpg')
print(f'Success: {len(contour)} contour points')
"
```

### Issue 3: All pairs fail to match (0% positive accuracy)
```
Positive Accuracy: 0.0%
```

**Possible causes**:
- Real fragments too damaged for geometric matching
- Matching thresholds too strict
- Preprocessing losing edge details

**Solution**:
1. Check confidence scores in report — are positive pairs close to threshold?
2. Try relaxing threshold temporarily to see if it helps:
   ```python
   # In src/relaxation.py, temporarily change:
   MATCH_SCORE_THRESHOLD = 0.45  # was 0.55
   ```
3. Inspect preprocessing output:
   ```bash
   python scripts/test_real_fragments.py --verbose
   # Check log for "Extracted contour with N boundary points"
   # Should be >200 points for good edge detail
   ```

### Issue 4: High false positive rate (negative accuracy low)
```
Negative Accuracy: 30.0%
```

**Possible causes**:
- Fragments from different sources have similar geometric patterns
- Color-based filtering not working
- Thresholds too permissive

**Solution**:
1. Check color_vs_geometric.png — are false positives high on both axes?
2. If geometric similarity is accidental, tighten threshold:
   ```python
   # In src/relaxation.py:
   MATCH_SCORE_THRESHOLD = 0.65  # was 0.55
   ```
3. If color filtering failed, check color BC values in JSON report:
   ```bash
   grep -A 5 '"is_positive_case": false' outputs/real_fragment_analysis/real_fragment_test_report.json
   # Look for high "color_bc" values (>0.6) in false positives
   ```

---

## Advanced Usage

### Test Specific Fragment Pairs
Modify the script to test only specific pairs:

```python
# Add after line 625 in test_real_fragments.py
# Manual pair list
manual_pairs = [
    ('british_museum/shard_01.jpg', 'british_museum/shard_02.jpg', True),  # positive
    ('british_museum/shard_01.jpg', 'wikimedia/fresco_a.jpg', False),     # negative
]

for frag_a_name, frag_b_name, is_positive in manual_pairs:
    frag_a = Path(args.input) / frag_a_name
    frag_b = Path(args.input) / frag_b_name
    result = test_fragment_pair(frag_a, frag_b, 'source_a', 'source_b', logger)
    # ... rest of pair testing
```

### Export Results to CSV
```python
# Add after line 780 (after JSON export)
import csv

csv_path = os.path.join(args.output, 'pair_results.csv')
with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Fragment A', 'Fragment B', 'Type', 'Verdict', 'Confidence', 'Color BC', 'Correct'])
    for r in summary.pair_results:
        writer.writerow([
            r.frag_a, r.frag_b,
            'SAME' if r.is_positive_case else 'DIFF',
            r.verdict, r.confidence, r.color_bc,
            '✓' if (r.match_found == r.is_positive_case) else '✗'
        ])
```

### Batch Testing Multiple Collections
```bash
#!/bin/bash
# test_all_collections.sh

for collection in british_museum wikimedia metropolitan louvre
do
    echo "Testing $collection..."
    python scripts/test_real_fragments.py \
        --input data/raw/real_fragments_validated/$collection \
        --output outputs/real_fragment_analysis/$collection \
        --compare-benchmark
done

# Aggregate results
python -c "
import json
from pathlib import Path

collections = ['british_museum', 'wikimedia', 'metropolitan', 'louvre']
for coll in collections:
    path = Path(f'outputs/real_fragment_analysis/{coll}/real_fragment_test_report.json')
    if path.exists():
        data = json.loads(path.read_text())
        print(f'{coll}: {data[\"summary\"][\"overall_accuracy\"]*100:.1f}% accuracy')
"
```

---

## Next Steps

After running tests:

1. **If preprocessing success < 80%**:
   - Review failed images in the markdown report
   - Improve image quality or adjust preprocessing parameters
   - Consider manual background removal for problematic cases

2. **If positive accuracy < 70%**:
   - Relax matching thresholds
   - Investigate if preprocessing is losing edge details
   - Consider adding texture/appearance features to complement geometry

3. **If negative accuracy < 70%**:
   - Tighten matching thresholds
   - Improve color-based filtering
   - Add more discriminative features

4. **If overall performance is good (>80%)**:
   - Document successful parameters
   - Use as baseline for future improvements
   - Test on larger real fragment collections

---

**Last Updated**: 2026-04-08
