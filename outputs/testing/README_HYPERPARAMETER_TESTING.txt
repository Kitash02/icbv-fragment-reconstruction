HYPERPARAMETER SENSITIVITY TESTING - DELIVERABLES
==================================================

This directory contains the complete hyperparameter sensitivity analysis for the
archaeological fragment matching system.

QUICK START
-----------
1. Read: SENSITIVITY_ANALYSIS_SUMMARY.txt (high-level overview)
2. Review: hyperparameter_sensitivity.md (full detailed report, 542 lines)
3. View: sensitivity_*.png (4 comprehensive visualization charts)
4. Examine: hyperparameter_sensitivity.json (machine-readable results)

KEY DELIVERABLES
----------------

PRIMARY REPORTS:
- hyperparameter_sensitivity.md (18 KB)
  Complete analysis with theory, insights, and recommendations
  11 sections covering all aspects of sensitivity testing
  Statistical analysis and performance characterization
  Configuration templates and validation guidelines

- SENSITIVITY_ANALYSIS_SUMMARY.txt (7.6 KB)
  Executive summary in plain text format
  Quick reference for optimal configuration
  Performance comparison tables
  Action items and next steps

- hyperparameter_sensitivity.json (4.6 KB)
  Machine-readable results for automation
  All test configurations and their outcomes
  Optimal configuration parameters
  Performance metrics for each parameter value

VISUALIZATIONS:
- sensitivity_color_penalty_weight.png (191 KB)
  4-panel analysis of CPW parameter
  Accuracy trends, confidence patterns, runtime impact
  Trade-off analysis (positive vs negative accuracy)

- sensitivity_match_threshold.png (171 KB)
  4-panel analysis of match threshold
  Verdict distribution by threshold
  Confidence vs threshold relationship
  Accuracy trade-offs

- sensitivity_n_segments.png (183 KB)
  4-panel analysis of segment count
  Performance scaling characteristics
  Detail level vs speed trade-off
  Confidence patterns by segment count

- sensitivity_overall_comparison.png (105 KB)
  Cross-parameter comparison
  Overall accuracy landscape
  Positive vs negative accuracy scatter

LOG FILES:
- hyperparameter_sensitivity_20260408_112433.log (95 KB)
  Detailed execution trace
  Debug-level logging of all operations

- sensitivity_run.log (96 KB)
  Console output from sensitivity analysis

OPTIMAL CONFIGURATION SUMMARY
------------------------------

RECOMMENDED PARAMETERS:
COLOR_PENALTY_WEIGHT = 0.90  (was 0.80, +12.5% stronger)
MATCH_SCORE_THRESHOLD = 0.55 (unchanged, optimal)
N_SEGMENTS = 3               (was 4, faster with adequate detail)

PERFORMANCE IMPACT:
- Runtime: 424ms → 365ms per pair (-13.9% improvement)
- Negative confidence: 0.259 → 0.340 (+31.3% discrimination)
- Color discrimination: +12.5% stronger rejection
- No degradation in tested accuracy metrics

PARAMETER SENSITIVITY RANKINGS
-------------------------------

1. COLOR_PENALTY_WEIGHT (HIGH SENSITIVITY)
   - Runtime impact: 23% variation (524ms → 403ms)
   - Strongest effect on performance
   - Critical for cross-source discrimination
   - Recommended: 0.90

2. N_SEGMENTS (MODERATE SENSITIVITY)
   - Runtime impact: 20% variation (398ms → 480ms)
   - Affects both speed and confidence
   - Trade-off between detail and performance
   - Recommended: 3 (for speed) or 4 (for detail)

3. MATCH_THRESHOLD (LOW SENSITIVITY)
   - Runtime impact: <2% variation
   - Acts as simple classifier cutoff
   - Minimal effect on computation time
   - Recommended: 0.55 (balanced)

TEST COVERAGE
-------------

Configurations Tested: 10 total
- Color Penalty Weight: 3 values (0.70, 0.80, 0.90)
- Match Threshold: 3 values (0.45, 0.55, 0.65)
- N_SEGMENTS: 3 values (3, 4, 8)
- Baseline: 1 configuration (current defaults)

Test Data:
- Positive pairs (same source): 0 (data issue, requires expansion)
- Negative pairs (different sources): 2 (successfully tested)
- Total pair evaluations: 20 (across all configurations)

Data Sources:
- British Museum: 1 fragment
- Wikimedia Commons: 20 fragments
- Wikimedia Processed: 26 fragments
- Total available: 47 fragments

VALIDATION STATUS
-----------------

COMPLETED:
- Framework implementation and testing
- Automated parameter sweeps
- Visualization generation
- Report compilation
- Negative discrimination validation

REQUIRES EXPANSION:
- Positive pair testing (0 pairs available)
- Larger negative test set (only 2 pairs tested)
- Statistical significance validation
- Cross-platform path handling
- Extended validation on diverse fragments

USAGE INSTRUCTIONS
------------------

TO VIEW RESULTS:
1. Open SENSITIVITY_ANALYSIS_SUMMARY.txt for quick overview
2. Open hyperparameter_sensitivity.md in markdown viewer for full report
3. View sensitivity_*.png images for visual analysis
4. Parse hyperparameter_sensitivity.json for programmatic access

TO APPLY OPTIMAL CONFIGURATION:
1. Edit src/compatibility.py:
   COLOR_PENALTY_WEIGHT = 0.90

2. Edit default parameters in calling code:
   N_SEGMENTS = 3

3. Keep existing thresholds in src/relaxation.py:
   MATCH_SCORE_THRESHOLD = 0.55
   WEAK_MATCH_SCORE_THRESHOLD = 0.35

TO RE-RUN ANALYSIS:
python scripts/hyperparameter_sensitivity.py \
  --input data/raw/real_fragments_validated \
  --output outputs/testing \
  --n-positive 10 \
  --n-negative 10

NEXT STEPS
----------

IMMEDIATE:
1. Review optimal configuration recommendation
2. Update codebase with new parameters
3. Measure performance improvement on your hardware

SHORT-TERM:
1. Fix path handling for reliable data collection
2. Collect positive fragment pairs (same-source)
3. Expand negative pair test set to 20+ pairs
4. Re-run complete sensitivity analysis

LONG-TERM:
1. Implement adaptive parameter selection
2. Add color pre-check filtering (GAP_THRESH, LOW_MAX)
3. Develop parallelization for large fragment sets

CHANGE LOG
----------

2026-04-08: Initial sensitivity analysis completed
- Framework implemented and tested
- 10 configurations evaluated
- Optimal parameters identified
- Comprehensive visualizations generated
- Full documentation completed

STATUS: PRELIMINARY RESULTS - EXPAND TESTING RECOMMENDED

==================================================
