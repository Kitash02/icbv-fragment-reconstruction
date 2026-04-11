# Variant 0 Evolutionary Optimization - Progress Report

## Mission
Iterate until Variant 0 achieves 95%+ positive AND 95%+ negative accuracy through systematic threshold optimization.

## Starting Configuration (Baseline - Iteration 0)
- **hard_disc_color**: 0.70
- **hard_disc_texture**: 0.65
- **color_precheck_gap**: 0.15
- **color_precheck_low_max**: 0.75

### Baseline Results (Partial - 8/9 positive, 18/36 negative completed)
- **Positive Accuracy**: 75.0% (6/8 PASS)
- **Negative Accuracy**: 83.3% (15/18 PASS)
- **False Positives**: 3 cross-source matches
  - mixed_gettyimages-13116049_gettyimages-17009652
  - mixed_gettyimages-17009652_shard_02_cord_marked
  - mixed_gettyimages-47081632_shard_01_british
- **False Negatives**: 2 same-source failures
  - scroll
  - Wall painting

**Analysis**: Baseline is far from 95% target. Need significant tightening to reduce false positives while maintaining true match detection.

## Optimization Strategy

### Iteration Sequence
Progressive threshold tightening in small increments to find optimal balance:

| Iteration | hard_disc_color | hard_disc_texture | Delta from Baseline | Strategy |
|-----------|----------------|-------------------|---------------------|----------|
| 0 (Baseline) | 0.70 | 0.65 | - | Starting point |
| 1 | 0.72 | 0.67 | +2.8%, +3.1% | Incremental tightening |
| 2 | 0.74 | 0.69 | +5.7%, +6.2% | Moderate tightening |
| 3 | 0.76 | 0.71 | +8.6%, +9.2% | Aggressive tightening |
| 4 | 0.78 | 0.73 | +11.4%, +12.3% | Maximum strictness |
| 5 | 0.80 | 0.75 | +14.3%, +15.4% | Ultra-strict (test limits) |

### Expected Evolution Pattern

1. **Iterations 0-1**: Establish baseline, minor improvements
2. **Iterations 2-3**: Negative accuracy should push toward 90%+
3. **Iterations 3-4**: Target zone for 95%+ negative, monitor positive trade-off
4. **Iteration 5**: Upper bound test - likely too strict, positive accuracy may drop below 70%

### Convergence Criteria

**SUCCESS**: Any iteration achieves:
- Positive accuracy ≥ 95% AND
- Negative accuracy ≥ 95%

**CEILING**: If no improvement >2% in 3 consecutive iterations, declare best achievable configuration.

**TRADE-OFF ANALYSIS**: If negative reaches 95%+ but positive drops below 70%, explore alternative approaches:
- Ensemble gating (upgrade filtering)
- Asymmetric thresholds (different for positive/negative cases)
- Hybrid approaches (combine multiple discriminators)

## Current Status

### Completed
- [x] Iteration 0 (Baseline): 75.0% pos, 83.3% neg (partial)
- [x] Iteration 1: 75.0% pos, 83.3% neg (partial, only 6 negative tests)

### Running
- [ ] Iteration 2: In progress
- [ ] Iteration 3: In progress
- [ ] Iteration 4: Queued

### Next Steps
1. Wait for iterations 2-4 to complete
2. Analyze full results and identify best configuration
3. If target not reached, run iterations 5-6
4. Generate final report with optimal configuration

## Key Insights

From baseline analysis:
- **False Positive Pattern**: Getty images cross-matching suggests BC scores in 0.70-0.78 range
- **False Negative Pattern**: "scroll" and "Wall painting" failing suggests edge cases with lower BC scores
- **Optimization Challenge**: Need to thread needle between rejecting cross-source (high BC) and accepting same-source (potentially lower BC)

## Files Generated

### Hard Discriminator Modules
- `src/hard_discriminators_variant0_iter1.py` through `iter6.py`

### Test Runners
- `run_variant0_iter1.py` through `iter5.py`

### Results
- `outputs/evolution/variant0_iter0_full.txt`
- `outputs/evolution/variant0_iter1_full.txt`
- `outputs/evolution/variant0_iter2.txt` (in progress)
- `outputs/evolution/variant0_iter3.txt` (in progress)

### Analysis Tools
- `parse_results.py` - Extract metrics from test outputs
- `run_evolution.py` - Master orchestrator for sequential execution
- `monitor_progress.py` - Real-time progress monitoring
- `outputs/evolution/variant0_progress.json` - Structured progress tracking

## Timeline
- Started: 2026-04-09
- Baseline completed: Partial results available
- Expected completion: All iterations within 60-90 minutes
