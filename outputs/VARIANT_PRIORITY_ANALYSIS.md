# VARIANT PRIORITY ANALYSIS - RETEST WITH FIXED BASELINE

**Analysis Date:** 2026-04-09
**Baseline Performance:** Variant 0 FIXED achieved 75.6% overall (34/45 pass)
**Improvement:** +13.4% over original baseline (62.2% → 75.6%)

---

## PRIORITY RANKING FOR RETEST

### 🔥 TIER 1: HIGHEST POTENTIAL (Expected 75-82% accuracy)

#### 1. Variant 9: Full Research Stack
**Configuration:**
- Formula: Baseline (color^4 × texture^2 × gabor^2 × haralick^2)
- Ensemble: Weighted (color=0.40, raw=0.25, texture=0.15, morph=0.15, gabor=0.05)
- Thresholds: Adaptive (per artifact type)

**Why High Priority:**
- Combines TWO optimizations: weighted ensemble + adaptive thresholds
- Original target: 99.3% (arXiv:2309.13512)
- Fixed baseline improves negative discrimination by 19.4% → adaptive thresholds should compound this
- Weighted ensemble in V1 failed (57.8%), but adaptive thresholds may fix the issues

**Expected Results:**
- Overall: 77-82%
- Positive: 70-75% (adaptive thresholds should help)
- Negative: 75-85% (weighted + adaptive combination)
- **Prediction: BEST CANDIDATE for 80%+ accuracy**

**Risk:** Medium (two complex components may have interaction issues)

---

#### 2. Variant 8: Adaptive Thresholds Per Artifact Type
**Configuration:**
- Formula: Baseline (color^4 × texture^2 × gabor^2 × haralick^2)
- Thresholds: Adaptive based on appearance variance
  - High variance (scrolls, wall paintings): 0.70 / 0.55
  - Low variance (pottery sherds): 0.75 / 0.60

**Why High Priority:**
- Directly addresses the problem cases:
  - Wall painting (false negative) → relaxed thresholds should help
  - Getty images (false positives) → may benefit from adaptive handling
- Fixed baseline already shows 75% negative accuracy → adaptive should push to 80%+
- Simpler than V9 (single optimization)

**Expected Results:**
- Overall: 75-80%
- Positive: 70-80% (relaxed thresholds for difficult cases)
- Negative: 75-80% (maintains current performance)
- **Prediction: Most stable improvement over fixed baseline**

**Risk:** Low (single, well-defined optimization)

---

#### 3. Variant 5: Color-Dominant (color^6)
**Configuration:**
- Formula: color^6 × texture^2 × gabor^2 × haralick^2
- Thresholds: 0.75 / 0.60 / 0.65 (same as baseline)

**Why High Priority:**
- Directly targets false positives with more aggressive color penalty
- Fixed baseline has 9 false positives (mostly Getty images with similar colors)
- Color^6 vs baseline color^4 = 56% increase in color penalty
- Expected to reduce false positives from 9 to 4-6 cases

**Expected Results:**
- Overall: 73-78%
- Positive: 60-70% (may lose some true positives due to strict penalty)
- Negative: 80-85% (excellent false positive rejection)
- **Prediction: Best negative discrimination (80%+ negative accuracy)**

**Risk:** Medium (may be too aggressive, losing positive recall)

---

#### 4. Variant 7: Optimized Powers + Tuned Thresholds
**Configuration:**
- Formula: color^5 × texture^2.5 × gabor^2 × haralick^2
- Thresholds: 0.72 / 0.58 / 0.62 (slightly relaxed from 0.75 / 0.60 / 0.65)

**Why High Priority:**
- Balanced approach: increases color penalty (4→5) but also texture weight (2→2.5)
- Relaxed thresholds may recover false negatives (wall painting case)
- Texture^2.5 may help with pottery shard discrimination (British vs Cord-marked)
- Two optimizations work in complementary directions

**Expected Results:**
- Overall: 75-80%
- Positive: 70-80% (relaxed thresholds help)
- Negative: 72-77% (color^5 helps discrimination)
- **Prediction: Best balanced performance (positive and negative both good)**

**Risk:** Low (well-tuned, tested approach)

---

### ⚠️ TIER 2: MEDIUM POTENTIAL (Expected 68-75% accuracy)

#### 5. Variant 4: Relaxed Thresholds
**Configuration:**
- Formula: Baseline (color^4 × texture^2 × gabor^2 × haralick^2)
- Thresholds: 0.70 / 0.55 / 0.60 (vs baseline 0.75 / 0.60 / 0.65)

**Why Medium Priority:**
- Targets false negatives (fixed baseline has 3)
- May recover wall painting case and Getty 1311604917
- Risk: relaxed thresholds may increase false positives (9 → 12-15)

**Expected Results:**
- Overall: 70-75%
- Positive: 75-85% (better recall)
- Negative: 65-70% (worse discrimination)
- **Trade-off: +3 true positives, -2 to -5 true negatives**

**Risk:** Medium (may undo the negative accuracy gains from fix)

---

#### 6. Variant 3: Tuned Weighted Ensemble
**Configuration:**
- Formula: Baseline (color^4 × texture^2 × gabor^2 × haralick^2)
- Ensemble: Weighted (color=0.40, raw=0.25, texture=0.15, morph=0.15, gabor=0.05)
- Thresholds: 0.75 / 0.60 / 0.65

**Why Medium Priority:**
- Variant 1 (weighted, different weights) FAILED (57.8%)
- But V3 has higher color weight (0.40 vs 0.35) which may help with fixed baseline
- Fixed baseline's improved negative discrimination may make weighted voting more effective
- Simpler than V9 (no adaptive thresholds)

**Expected Results:**
- Overall: 68-73%
- Positive: 65-70%
- Negative: 68-75%
- **Uncertain: May fail like V1, or may benefit from higher color weight**

**Risk:** High (V1 already failed with similar approach)

---

### 💡 TIER 3: LOWER POTENTIAL (Expected 65-75% accuracy)

#### 7. Variant 6: Balanced Powers (all^2)
**Configuration:**
- Formula: color^2 × texture^2 × gabor^2 × haralick^2 (equal weighting)
- Thresholds: 0.75 / 0.60 / 0.65

**Why Lower Priority:**
- Reduces color dominance (color^4 → color^2)
- Fixed baseline BENEFITS from color^4 (good negative discrimination)
- Equal weighting may lose discriminative power
- Expected to increase false positives significantly

**Expected Results:**
- Overall: 65-72%
- Positive: 75-85% (better recall)
- Negative: 60-70% (worse discrimination)
- **High variance: Could be anywhere from 60-75%**

**Risk:** High (goes against what made the fix successful)

---

#### 8. Variant 2: Hierarchical Ensemble (Fast Routing)
**Configuration:**
- Formula: Baseline (color^4 × texture^2 × gabor^2 × haralick^2)
- Ensemble: Hierarchical (fast reject → fast match → 5-way fallback)
- Thresholds: 0.75 / 0.60 / 0.65

**Why Lower Priority:**
- Primarily a SPEED optimization, not accuracy
- Expected to match fixed baseline (75.6%) but run 2-3x faster
- No accuracy improvement expected
- Useful for production, but not for research

**Expected Results:**
- Overall: 74-76% (same as baseline)
- Positive: 65-70% (same as baseline)
- Negative: 74-76% (same as baseline)
- **Speed: 2-3x faster than baseline**

**Risk:** Low (should just match baseline performance)

---

## RECOMMENDED TESTING ORDER

### Phase 1: High-Value Variants (Run First)
1. **Variant 8** (Adaptive Thresholds) - Most likely to work
2. **Variant 9** (Full Research Stack) - Highest upside
3. **Variant 5** (Color^6) - Best for false positive reduction
4. **Variant 7** (Optimized Powers) - Best balanced approach

**Expected Outcome:** At least 1-2 variants achieve 78-82% accuracy

### Phase 2: Medium-Value Variants (Run If Phase 1 Successful)
5. **Variant 4** (Relaxed Thresholds) - Good for positive recall
6. **Variant 3** (Tuned Weighted) - Uncertain but worth trying

**Expected Outcome:** Learn about threshold trade-offs

### Phase 3: Lower-Value Variants (Run For Completeness)
7. **Variant 6** (Balanced Powers) - Research interest only
8. **Variant 2** (Hierarchical) - For production optimization

**Expected Outcome:** Complete the analysis, but no major accuracy gains

---

## ENSEMBLE STRATEGY

Once all variants complete, build meta-classifier:

### Ensemble Option 1: Voting
- Combine predictions from top 3-5 variants
- Use majority voting (at least 3/5 agree)
- Expected: 78-83% overall accuracy

### Ensemble Option 2: Weighted Voting
- Weight each variant by its negative accuracy
- Prioritize variants with low false positive rates
- Expected: 80-85% overall accuracy

### Ensemble Option 3: Stacked Classifier
- Train second-level classifier on variant predictions
- Use logistic regression or random forest
- Expected: 82-87% overall accuracy (requires training data)

---

## RISK MITIGATION

### Execution Plan
1. Run variants **SEQUENTIALLY** (not parallel)
2. Add timeout (10 minutes per variant)
3. Log all errors with full stack traces
4. Save intermediate results every 5 test cases
5. Validate output files before proceeding to next variant

### Expected Issues
- **Module conflicts:** Fixed by sequential execution
- **File I/O errors:** Fixed by separate output directories per variant
- **Memory leaks:** Fixed by restarting Python process between variants
- **Timeout issues:** Fixed by 10-minute limit + progress logging

---

## SUCCESS CRITERIA

### Minimum Success (Viable)
- At least 2 variants complete with 75%+ accuracy
- At least 1 variant achieves 78%+ accuracy
- Zero execution errors or crashes

### Target Success (Good)
- All 8 variants complete successfully
- At least 1 variant achieves 80%+ accuracy
- Ensemble achieves 82%+ accuracy

### Stretch Success (Excellent)
- At least 2 variants achieve 80%+ accuracy
- Ensemble achieves 85%+ accuracy
- Identify optimal configuration for production use

---

## TIMELINE ESTIMATE

Assuming 45 test cases × ~10 seconds per case × 10 variants:
- Sequential execution: ~75 minutes (1.25 hours)
- With setup/teardown: ~90 minutes (1.5 hours)
- Total project time: 2 hours (including analysis)

**Recommendation:** Run overnight or during low-activity period.

---

## FINAL RECOMMENDATION

**Start with Variants 8, 9, 5, 7 in that order.**

These four variants have the highest probability of achieving 78-82% accuracy with the fixed baseline. If time permits, complete the remaining variants for full analysis.

**Target:** Find at least ONE variant that achieves 80%+ overall accuracy.

**Stretch Goal:** Build ensemble classifier achieving 85%+ overall accuracy.

---

**Analysis Date:** 2026-04-09
**Based On:** Variant 0 FIXED results (75.6% accuracy, 75% negative accuracy)
**Next Action:** Run sequential testing with proper error handling
