# DECISION TREES FOR AUTONOMOUS TUNING

**Document Purpose:** Visual decision trees for autonomous parameter tuning and failure recovery

**Usage:** Implementation agent should follow these trees sequentially without human intervention

---

## MASTER DECISION FLOW

```
START: Current baseline (HSV color only)
│
├─> Phase 1A: Implement Lab Color
│   │
│   ├─> VALIDATION: Test Lab performance
│   │   │
│   │   ├─> SUCCESS (Neg Acc ≥ 15%)
│   │   │   └─> Proceed to Phase 1B
│   │   │
│   │   └─> FAILURE (Neg Acc < 15%)
│   │       └─> Fallback: Try Opponent Color
│   │           └─> Still fail? Try Normalized RGB
│   │               └─> Still fail? Keep HSV, proceed anyway
│   │
│   └─> Phase 1B: Add Exponential Penalty
│       │
│       ├─> VALIDATION: Test exponential impact
│       │   │
│       │   ├─> SUCCESS (Neg Acc ≥ 30%)
│       │   │   └─> Proceed to Phase 2A
│       │   │
│       │   ├─> PARTIAL (Neg Acc 20-30%)
│       │   │   └─> Tune power: try 3.0
│       │   │       └─> Proceed to Phase 2A
│       │   │
│       │   └─> FAILURE (Neg Acc < 20%)
│       │       └─> Decision Tree 1 (Exponential Power Tuning)
│       │           └─> If still fail: Proceed anyway to Phase 2A
│       │
│       └─> Phase 2A: Add LBP Texture
│           │
│           ├─> VALIDATION: Test texture discrimination
│           │   │
│           │   ├─> SUCCESS (Neg Acc ≥ 60%)
│           │   │   └─> Proceed to Phase 2B
│           │   │
│           │   ├─> PARTIAL (Neg Acc 45-60%)
│           │   │   └─> Decision Tree 2 (LBP Parameter Tuning)
│           │   │       └─> Proceed to Phase 2B
│           │   │
│           │   └─> FAILURE (Neg Acc < 45%)
│           │       └─> Decision Tree 3 (Texture Alternative)
│           │           └─> Try GLCM or Gabor
│           │               └─> Proceed to Phase 2B
│           │
│           └─> Phase 2B: Add Fractal Dimension
│               │
│               ├─> VALIDATION: Test complete system
│               │   │
│               │   ├─> SUCCESS (Bal Acc ≥ 85%)
│               │   │   └─> DONE! System complete
│               │   │
│               │   ├─> GOOD (Bal Acc 75-85%)
│               │   │   └─> Decision Tree 4 (Feature Weighting)
│               │   │       └─> Fine-tune and finalize
│               │   │
│               │   └─> INSUFFICIENT (Bal Acc < 75%)
│               │       └─> Decision Tree 5 (Architecture Change)
│               │           └─> Try two-stage or hybrid approach
│               │
│               └─> END: Report final performance
```

---

## DECISION TREE 1: EXPONENTIAL POWER TUNING

**Context:** Phase 1B shows insufficient negative accuracy
**Goal:** Find optimal exponential power for color penalty

```
START: Current power = 2.5, Neg Acc < 30%
│
├─> Analyze current distribution
│   │
│   ├─> Check: Positive Accuracy
│   │   │
│   │   ├─> Pos Acc < 90%? (Too many false negatives)
│   │   │   │
│   │   │   └─> DIAGNOSIS: Power too strong, suppressing true matches
│   │   │       │
│   │   │       ├─> ACTION 1: Reduce power to 2.0
│   │   │       │   └─> Re-test
│   │   │       │       ├─> Pos Acc ≥ 90% AND Neg Acc ≥ 25%?
│   │   │       │       │   └─> SUCCESS: Keep power = 2.0
│   │   │       │       │
│   │   │       │       └─> Pos Acc still < 90%?
│   │   │       │           └─> ACTION 2: Reduce power to 1.5
│   │   │       │               └─> Re-test
│   │   │       │                   ├─> Pos Acc ≥ 90%?
│   │   │       │                   │   └─> SUCCESS: Keep power = 1.5
│   │   │       │                   │
│   │   │       │                   └─> Still < 90%?
│   │   │       │                       └─> CRITICAL: Color feature broken
│   │   │       │                           └─> Jump to Decision Tree 3 (Try alternative color)
│   │   │
│   │   └─> Pos Acc ≥ 90%? (True matches preserved)
│   │       │
│   │       └─> Check: Negative Accuracy
│   │           │
│   │           ├─> Neg Acc < 20%? (Too many false positives)
│   │           │   │
│   │           │   └─> DIAGNOSIS: Power too weak, not rejecting enough
│   │           │       │
│   │           │       ├─> ACTION 1: Increase power to 3.0
│   │           │       │   └─> Re-test
│   │           │       │       ├─> Pos Acc ≥ 90% AND Neg Acc ≥ 25%?
│   │           │       │       │   └─> SUCCESS: Keep power = 3.0
│   │           │       │       │
│   │           │       │       └─> Neg Acc still < 25%?
│   │           │       │           └─> ACTION 2: Increase power to 3.5
│   │           │       │               └─> Re-test
│   │           │       │                   ├─> Neg Acc ≥ 25%?
│   │           │       │                   │   └─> SUCCESS: Keep power = 3.5
│   │           │       │                   │
│   │           │       │                   └─> Still < 25%?
│   │           │       │                       └─> CRITICAL: Color alone insufficient
│   │           │       │                           └─> ACCEPT and proceed to Phase 2A
│   │           │       │                               (Texture will help)
│   │           │
│   │           └─> Neg Acc 20-30%? (Marginal)
│   │               │
│   │               └─> DECISION: Accept and proceed to Phase 2A
│   │                   └─> Reason: Texture will boost to 60%+
│   │
│   └─> Compute separation metric (Cohen's d)
│       │
│       ├─> Cohen's d > 0.8?
│       │   └─> Excellent separation, proceed
│       │
│       ├─> Cohen's d = 0.5-0.8?
│       │   └─> Acceptable separation, proceed
│       │
│       └─> Cohen's d < 0.5?
│           └─> Poor separation, consider color alternative
│
└─> END: Power optimized or decision made to proceed
```

**Implementation Code:**

```python
def decision_tree_1_exponential_power(scores_same, scores_diff, current_power=2.5):
    """
    Autonomous exponential power tuning
    """
    powers_to_try = []

    # Compute current metrics
    pos_acc = (scores_same > MATCH_THRESHOLD).mean()
    neg_acc = (scores_diff <= MATCH_THRESHOLD).mean()
    cohens_d = compute_separation(scores_same, scores_diff)

    print(f"Current: power={current_power}, Pos={pos_acc:.2%}, Neg={neg_acc:.2%}, d={cohens_d:.3f}")

    # Decision logic
    if pos_acc < 0.90:
        # Too strong - reduce
        if current_power > 2.0:
            powers_to_try = [2.0, 1.5, 1.0]
        else:
            powers_to_try = [1.5, 1.0]
        print("DIAGNOSIS: Power too strong (false negatives)")

    elif neg_acc < 0.20:
        # Too weak - increase
        if current_power < 3.0:
            powers_to_try = [3.0, 3.5, 4.0]
        else:
            powers_to_try = [3.5, 4.0]
        print("DIAGNOSIS: Power too weak (false positives)")

    elif neg_acc < 0.30:
        # Marginal - try one increment
        powers_to_try = [current_power + 0.5]
        print("DIAGNOSIS: Marginal performance, try increasing")

    else:
        # Acceptable
        print("SUCCESS: Current power acceptable")
        return current_power, "success"

    # Try alternatives
    for power in powers_to_try:
        # This would be implemented by re-running Phase 1B with new power
        print(f"  → Would try power = {power}")

    # In practice, return first alternative to try
    if len(powers_to_try) > 0:
        return powers_to_try[0], "tuning"
    else:
        return current_power, "accept"
```

---

## DECISION TREE 2: LBP PARAMETER TUNING

**Context:** Phase 2A shows insufficient texture discrimination
**Goal:** Optimize LBP parameters or switch to alternative

```
START: LBP with P=24, R=3, Neg Acc < 60%
│
├─> Analyze texture BC distribution
│   │
│   ├─> Compute: mean BC for cross-source pairs
│   │   │
│   │   ├─> Mean BC > 0.85? (No discrimination)
│   │   │   │
│   │   │   └─> DIAGNOSIS: Texture too similar OR LBP not capturing differences
│   │   │       │
│   │   │       ├─> Check: BC variance
│   │   │       │   │
│   │   │       │   ├─> Variance > 0.20? (High noise)
│   │   │       │   │   │
│   │   │       │   │   └─> TRY 1: Change LBP method
│   │   │       │   │       ├─> Switch to 'ror' (more compact)
│   │   │       │   │       │   └─> Re-test
│   │   │       │   │       │       ├─> Improved?
│   │   │       │   │       │       │   └─> SUCCESS: Keep 'ror'
│   │   │       │   │       │       │
│   │   │       │   │       │       └─> No improvement?
│   │   │       │   │       │           └─> TRY 2: Reduce P to 16
│   │   │       │   │       │               └─> Re-test
│   │   │       │   │       │                   └─> Jump to Alternative decision
│   │   │       │   │
│   │   │       │   └─> Variance < 0.20? (Stable but no separation)
│   │   │       │       │
│   │   │       │       └─> TRY 1: Increase R to 4 (larger scale)
│   │   │       │           └─> Re-test
│   │   │       │               ├─> Mean BC < 0.80?
│   │   │       │               │   └─> SUCCESS: Keep R=4
│   │   │       │               │
│   │   │       │               └─> Still BC > 0.85?
│   │   │       │                   └─> TRY 2: Try R=2 (smaller scale)
│   │   │       │                       └─> Re-test
│   │   │       │                           └─> Still no improvement?
│   │   │       │                               └─> JUMP to Decision Tree 3 (Alternative)
│   │   │
│   │   ├─> Mean BC = 0.75-0.85? (Marginal separation)
│   │   │   │
│   │   │   └─> DIAGNOSIS: Some discrimination, but not enough
│   │   │       │
│   │   │       ├─> TRY 1: Increase exponential power to 2.5
│   │   │       │   └─> Re-test (amplify small differences)
│   │   │       │       ├─> Neg Acc ≥ 55%?
│   │   │       │       │   └─> SUCCESS: Keep power=2.5
│   │   │       │       │
│   │   │       │       └─> Still < 55%?
│   │   │       │           └─> TRY 2: Increase power to 3.0
│   │   │       │               └─> Re-test
│   │   │       │                   └─> Accept result, proceed
│   │   │
│   │   └─> Mean BC < 0.75? (Good separation)
│   │       │
│   │       └─> DIAGNOSIS: Feature working, but accuracy still low
│   │           │
│   │           └─> CHECK: Are same-source pairs also low BC?
│   │               │
│   │               ├─> YES (Mean same-source BC < 0.80)?
│   │               │   │
│   │               │   └─> PROBLEM: Texture not capturing similarity
│   │               │       └─> Try increasing R or P (finer detail)
│   │               │           └─> Or jump to alternative
│   │               │
│   │               └─> NO (Same-source BC ≥ 0.80)?
│   │                   │
│   │                   └─> DIAGNOSIS: Exponential power insufficient
│   │                       └─> Increase power to 2.5 or 3.0
│   │
│   └─> Decision: Keep current or switch to alternative?
│       │
│       ├─> If any improvement over baseline → KEEP and proceed
│       │
│       └─> If no improvement after 2-3 attempts → SWITCH to alternative
│           └─> JUMP to Decision Tree 3
│
└─> END: LBP optimized or decision to switch
```

**Implementation Code:**

```python
def decision_tree_2_lbp_tuning(bc_same, bc_diff, current_config):
    """
    Autonomous LBP parameter tuning
    """
    mean_same = np.mean(bc_same)
    mean_diff = np.mean(bc_diff)
    var_diff = np.var(bc_diff)

    print(f"Current LBP: P={current_config['P']}, R={current_config['R']}")
    print(f"  Same-source BC: {mean_same:.3f}")
    print(f"  Diff-source BC: {mean_diff:.3f}")
    print(f"  Variance: {var_diff:.3f}")

    # Decision logic
    if mean_diff > 0.85:
        if var_diff > 0.04:  # variance > 0.20² = 0.04
            print("DIAGNOSIS: High BC, high variance → try 'ror' method")
            return {'P': 24, 'R': 3, 'method': 'ror'}, "tune_method"
        else:
            print("DIAGNOSIS: High BC, low variance → try R=4")
            return {'P': 24, 'R': 4, 'method': 'uniform'}, "tune_radius"

    elif mean_diff > 0.75:
        print("DIAGNOSIS: Marginal BC → increase exponential power")
        return "increase_power_to_2.5", "tune_power"

    elif mean_diff < 0.75:
        if mean_same < 0.80:
            print("DIAGNOSIS: Good separation but same-source also low → increase detail")
            return {'P': 32, 'R': 3, 'method': 'uniform'}, "tune_detail"
        else:
            print("SUCCESS: Good separation, keep current")
            return current_config, "success"

    else:
        print("UNKNOWN: Try alternative texture method")
        return "switch_to_glcm", "alternative"
```

---

## DECISION TREE 3: TEXTURE ALTERNATIVE SELECTION

**Context:** LBP tuning failed to achieve acceptable performance
**Goal:** Select and test alternative texture method

```
START: LBP failed (BC > 0.85 or Neg Acc < 45% after tuning)
│
├─> Analyze pottery texture characteristics
│   │
│   ├─> CHECK 1: Directional patterns present?
│   │   │
│   │   ├─> YES (wheel marks, brush strokes visible)
│   │   │   │
│   │   │   └─> PRIMARY CHOICE: Gabor Filters
│   │   │       │
│   │   │       ├─> Implement Gabor with directional config
│   │   │       │   └─> 8 orientations, 3 frequencies
│   │   │       │
│   │   │       └─> Test Gabor
│   │   │           ├─> BC < 0.80?
│   │   │           │   └─> SUCCESS: Use Gabor
│   │   │           │
│   │   │           └─> BC still > 0.85?
│   │   │               └─> TRY 2: GLCM
│   │   │
│   │   └─> NO (isotropic texture)
│   │       │
│   │       └─> PRIMARY CHOICE: GLCM
│   │           │
│   │           ├─> Implement GLCM with standard config
│   │           │   └─> distances=[1,2,3], angles=[0,45,90,135]
│   │           │
│   │           └─> Test GLCM
│   │               ├─> Separation improved?
│   │               │   └─> SUCCESS: Use GLCM
│   │               │
│   │               └─> Still no improvement?
│   │                   └─> TRY 3: HOG
│   │
│   ├─> CHECK 2: After trying 2 alternatives, any improvement?
│   │   │
│   │   ├─> YES (BC improved by ≥ 0.05 or Neg Acc improved by ≥ 5%)
│   │   │   └─> ACCEPT: Use best alternative
│   │   │       └─> Proceed to Phase 2B
│   │   │
│   │   └─> NO (no significant improvement)
│   │       │
│   │       └─> DECISION: Texture discrimination inherently weak
│   │           │
│   │           ├─> OPTION A: Disable texture feature
│   │           │   └─> Rely on color + fractal only
│   │           │       └─> Proceed to Phase 2B
│   │           │
│   │           └─> OPTION B: Use texture with low weight
│   │               └─> Set texture weight = 0.10 (vs 0.25)
│   │                   └─> Proceed to Phase 2B
│   │
│   └─> TEST ALL ALTERNATIVES: Rapid validation
│       │
│       └─> For each alternative (GLCM, Gabor, HOG):
│           ├─> Compute features for 10 same-source pairs
│           ├─> Compute features for 10 diff-source pairs
│           ├─> Calculate Cohen's d
│           └─> Select alternative with highest Cohen's d
│               └─> If d > 0.5: USE IT
│               └─> If d < 0.5: DISABLE TEXTURE
│
└─> END: Alternative selected or texture disabled
```

**Implementation Code:**

```python
def decision_tree_3_texture_alternative(fragments, pairs_same, pairs_diff):
    """
    Autonomous texture alternative selection
    """
    print("DECISION TREE 3: Selecting texture alternative")

    alternatives = {
        'glcm': compute_glcm_features,
        'gabor': compute_gabor_features,
        'hog': compute_hog_features
    }

    results = {}

    # Test each alternative on subset
    for name, func in alternatives.items():
        print(f"  Testing {name}...")

        # Compute for subset (first 10 pairs)
        scores_same = []
        scores_diff = []

        for f1, f2 in pairs_same[:10]:
            feat1 = func(cv2.cvtColor(f1.image, cv2.COLOR_BGR2GRAY))
            feat2 = func(cv2.cvtColor(f2.image, cv2.COLOR_BGR2GRAY))
            sim = compute_feature_similarity(feat1, feat2)
            scores_same.append(sim)

        for f1, f2 in pairs_diff[:10]:
            feat1 = func(cv2.cvtColor(f1.image, cv2.COLOR_BGR2GRAY))
            feat2 = func(cv2.cvtColor(f2.image, cv2.COLOR_BGR2GRAY))
            sim = compute_feature_similarity(feat1, feat2)
            scores_diff.append(sim)

        # Compute separation
        cohens_d = compute_separation(scores_same, scores_diff)
        results[name] = cohens_d

        print(f"    Cohen's d = {cohens_d:.3f}")

    # Select best
    best_method = max(results, key=results.get)
    best_d = results[best_method]

    if best_d > 0.5:
        print(f"SELECTED: {best_method} (d={best_d:.3f})")
        return best_method, "use_alternative"
    else:
        print(f"DECISION: All alternatives weak (best d={best_d:.3f})")
        print("  → Disabling texture feature")
        return None, "disable_texture"
```

---

## DECISION TREE 4: FEATURE WEIGHTING OPTIMIZATION

**Context:** All features implemented, but balanced accuracy 75-85%
**Goal:** Optimize feature weights to reach ≥ 85% balanced accuracy

```
START: All features active, Bal Acc = 75-85%
│
├─> Analyze individual feature contributions
│   │
│   ├─> For each feature: compute correlation with final match decision
│   │   │
│   │   └─> Identify:
│   │       ├─> Strong features (high correlation)
│   │       ├─> Moderate features (medium correlation)
│   │       └─> Weak features (low correlation)
│   │
│   ├─> Rank features by separation (Cohen's d)
│   │   │
│   │   └─> Priority ranking:
│   │       1. Highest d → Most discriminative
│   │       2. Medium d → Moderate discriminative
│   │       3. Lowest d → Least discriminative
│   │
│   └─> Decision: Adjust exponential powers based on ranking
│       │
│       ├─> Strong feature (d > 0.8)
│       │   └─> Increase power to 2.5-3.0 (amplify advantage)
│       │
│       ├─> Moderate feature (d = 0.5-0.8)
│       │   └─> Keep power at 2.0 (standard)
│       │
│       └─> Weak feature (d < 0.5)
│           └─> Reduce power to 0.5-1.0 or disable
│
├─> Parameter sweep: Grid search on exponential powers
│   │
│   ├─> Define search space
│   │   │
│   │   └─> Power ranges:
│   │       ├─> Color: [1.5, 2.0, 2.5, 3.0, 3.5]
│   │       ├─> Texture: [1.0, 1.5, 2.0, 2.5, 3.0]
│   │       └─> Fractal: [0.0, 0.5, 1.0, 1.5]
│   │
│   ├─> Sampling strategy
│   │   │
│   │   ├─> OPTION A: Full grid (5×5×4 = 100 combinations)
│   │   │   └─> Time: ~10-30 minutes
│   │   │   └─> Use if: Computational budget allows
│   │   │
│   │   ├─> OPTION B: Random search (20 samples)
│   │   │   └─> Time: ~2-5 minutes
│   │   │   └─> Use if: Need fast optimization
│   │   │
│   │   └─> OPTION C: Bayesian optimization (10 iterations)
│   │       └─> Time: ~5-10 minutes
│   │       └─> Use if: Want smart sampling
│   │
│   └─> For each combination:
│       ├─> Recompute all compatibility scores
│       ├─> Compute balanced accuracy
│       └─> Track best configuration
│
├─> Analyze failure patterns
│   │
│   ├─> Which pairs still failing?
│   │   │
│   │   ├─> False Positives (same-source rejected)
│   │   │   │
│   │   │   └─> Analyze: Which feature(s) causing rejection?
│   │   │       ├─> Color low? → Reduce color power
│   │   │       ├─> Texture low? → Reduce texture power
│   │   │       └─> Multiple low? → Problem with fragment quality
│   │   │
│   │   └─> False Negatives (diff-source accepted)
│   │       │
│   │       └─> Analyze: Why not rejected?
│   │           ├─> All features too high? → Increase all powers
│   │           ├─> One feature masking others? → Use product fusion
│   │           └─> Threshold too low? → Increase MATCH_THRESHOLD
│   │
│   └─> Decision: Architecture change needed?
│       │
│       ├─> If false positives > false negatives
│       │   └─> Powers too strong → REDUCE
│       │
│       ├─> If false negatives > false positives
│       │   └─> Powers too weak → INCREASE
│       │
│       └─> If balanced but both high
│           └─> Threshold wrong → ADJUST MATCH_THRESHOLD
│
└─> END: Optimal weights found or architecture change needed
```

**Implementation Code:**

```python
def decision_tree_4_feature_weighting(fragments, pairs_same, pairs_diff,
                                      current_powers):
    """
    Autonomous feature weight optimization
    """
    print("DECISION TREE 4: Optimizing feature weights")

    # Analyze individual features
    features = ['color', 'texture', 'fractal']
    separations = {}

    for feat in features:
        # Compute feature values for all pairs
        values_same = compute_feature_values(pairs_same, feat)
        values_diff = compute_feature_values(pairs_diff, feat)

        # Compute Cohen's d
        d = compute_separation(values_same, values_diff)
        separations[feat] = d

        print(f"  {feat}: Cohen's d = {d:.3f}")

    # Rank features
    ranked = sorted(separations.items(), key=lambda x: x[1], reverse=True)

    print("\nFeature ranking (by discriminative power):")
    for i, (feat, d) in enumerate(ranked, 1):
        print(f"  {i}. {feat}: d={d:.3f}")

    # Recommend powers based on ranking
    recommended_powers = {}

    for feat, d in ranked:
        if d > 0.8:
            recommended_powers[feat] = 2.5  # Strong feature
            print(f"  → {feat}: STRONG, use power=2.5")
        elif d > 0.5:
            recommended_powers[feat] = 2.0  # Moderate
            print(f"  → {feat}: MODERATE, use power=2.0")
        else:
            recommended_powers[feat] = 0.5  # Weak
            print(f"  → {feat}: WEAK, use power=0.5 or disable")

    # Grid search (coarse)
    print("\nGrid search for optimal powers...")

    power_ranges = {
        'color': [1.5, 2.0, 2.5, 3.0],
        'texture': [1.0, 1.5, 2.0, 2.5],
        'fractal': [0.0, 0.5, 1.0]
    }

    best_acc = 0
    best_config = None

    for p_color in power_ranges['color']:
        for p_texture in power_ranges['texture']:
            for p_fractal in power_ranges['fractal']:
                # Test this configuration (simplified)
                acc = test_power_configuration(
                    pairs_same, pairs_diff,
                    p_color, p_texture, p_fractal
                )

                if acc > best_acc:
                    best_acc = acc
                    best_config = {
                        'color': p_color,
                        'texture': p_texture,
                        'fractal': p_fractal
                    }

    print(f"\nBest configuration: {best_config}")
    print(f"  Balanced accuracy: {best_acc:.1%}")

    return best_config, best_acc
```

---

## DECISION TREE 5: ARCHITECTURE CHANGE

**Context:** All tuning attempts unsuccessful, Bal Acc < 75%
**Goal:** Change overall architecture strategy

```
START: Bal Acc < 75% after all tuning
│
├─> Analyze fundamental problem
│   │
│   ├─> CHECK 1: Are features fundamentally weak?
│   │   │
│   │   ├─> All Cohen's d < 0.5?
│   │   │   │
│   │   │   └─> YES: Features not discriminative
│   │   │       │
│   │   │       └─> OPTION A: Disable weak features
│   │   │           ├─> Keep only strong features (d > 0.5)
│   │   │           └─> Re-test with reduced feature set
│   │   │
│   │   └─> NO: At least one feature with d > 0.5
│   │       │
│   │       └─> Proceed to CHECK 2
│   │
│   ├─> CHECK 2: Is fusion strategy appropriate?
│   │   │
│   │   ├─> Using multiplicative (product)?
│   │   │   │
│   │   │   ├─> Check: Many false positives?
│   │   │   │   └─> YES: Product too lenient
│   │   │   │       └─> TRY: Two-stage filtering
│   │   │   │           ├─> Stage 1: Appearance filter (color × texture)
│   │   │   │           └─> Stage 2: Geometry filter
│   │   │   │
│   │   │   └─> Check: Many false negatives?
│   │   │       └─> YES: Product too strict
│   │   │           └─> TRY: Weighted sum
│   │   │               └─> Reduce impact of weakest feature
│   │   │
│   │   └─> Using weighted sum?
│   │       │
│   │       └─> TRY: Switch to product (more conservative)
│   │
│   ├─> CHECK 3: Is threshold appropriate?
│   │   │
│   │   ├─> Current: MATCH_THRESHOLD = 0.50
│   │   │   │
│   │   │   ├─> Many false positives?
│   │   │   │   └─> INCREASE to 0.55 or 0.60
│   │   │   │
│   │   │   └─> Many false negatives?
│   │   │       └─> DECREASE to 0.45 or 0.40
│   │   │
│   │   └─> Optimal threshold search
│   │       │
│   │       └─> Test thresholds: [0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65]
│   │           └─> Find threshold maximizing balanced accuracy
│   │
│   └─> CHECK 4: Is data quality sufficient?
│       │
│       ├─> Review fragment images
│       │   │
│       │   ├─> Poor lighting?
│       │   ├─> Occlusions?
│       │   ├─> Extreme angles?
│       │   └─> Scale variations?
│       │
│       └─> If data quality issues:
│           └─> RECOMMENDATION: Image preprocessing needed
│               ├─> Illumination normalization
│               ├─> Scale standardization
│               └─> Quality filtering
│
├─> ARCHITECTURE OPTIONS
│   │
│   ├─> OPTION 1: Two-Stage Filtering
│   │   │
│   │   ├─> Stage 1 (Fast rejection):
│   │   │   └─> appearance = (color^2.5) × (texture^2.0)
│   │   │   └─> if appearance < 0.65: REJECT
│   │   │
│   │   └─> Stage 2 (Full scoring):
│   │       └─> score = geometric × appearance × (fractal^0.5)
│   │       └─> if score > 0.50: ACCEPT
│   │
│   ├─> OPTION 2: Weighted Sum Fusion
│   │   │
│   │   └─> score = 0.40×geom + 0.30×(color^2.5) + 0.20×(texture^2.0) + 0.10×fractal
│   │       └─> More robust to weak features
│   │
│   ├─> OPTION 3: Hybrid Approach
│   │   │
│   │   ├─> Use only features that work
│   │   │   └─> If color good, texture bad, fractal bad:
│   │   │       └─> score = geometric × (color^2.5)
│   │   │
│   │   └─> Adaptive: Enable features based on performance
│   │
│   └─> OPTION 4: Raise Threshold
│       │
│       └─> If Pos Acc high but Neg Acc low:
│           └─> MATCH_THRESHOLD = 0.60 or 0.65
│           └─> Accept lower Pos Acc for better Neg Acc
│
└─> END: Architecture change implemented
```

**Implementation Code:**

```python
def decision_tree_5_architecture_change(current_accuracy, feature_separations):
    """
    Autonomous architecture selection
    """
    print("DECISION TREE 5: Architecture change needed")
    print(f"  Current balanced accuracy: {current_accuracy:.1%}")

    # Check feature quality
    weak_features = [f for f, d in feature_separations.items() if d < 0.5]
    strong_features = [f for f, d in feature_separations.items() if d >= 0.5]

    print(f"  Strong features: {strong_features}")
    print(f"  Weak features: {weak_features}")

    # Decision logic
    if len(strong_features) == 0:
        print("\nDECISION: No strong features - fundamental problem")
        print("  → RECOMMENDATION: Revisit data quality and preprocessing")
        return "data_quality_issue"

    elif len(weak_features) >= 2:
        print("\nDECISION: Multiple weak features - simplify model")
        print("  → Use only strong features")
        return "disable_weak_features", strong_features

    else:
        print("\nDECISION: Features OK but fusion/threshold suboptimal")

        # Try architecture options
        options = [
            "two_stage_filtering",
            "weighted_sum_fusion",
            "threshold_optimization"
        ]

        print("  → Will try:")
        for opt in options:
            print(f"     - {opt}")

        return "try_architecture_options", options
```

---

## USAGE SUMMARY

### How Implementation Agent Should Use These Trees

1. **Sequential Execution**: Follow trees in order (1 → 2 → 3 → 4 → 5)

2. **Early Termination**: If success criteria met, stop (don't continue to next tree)

3. **Autonomous Decision**: No human input required - all decisions codified

4. **Logging**: Print decisions and rationale for transparency

5. **Failure Handling**: Every branch has a fallback - no dead ends

6. **Validation**: Test after each change, record metrics

### Integration Example

```python
def autonomous_implementation():
    """
    Master function orchestrating all decision trees
    """
    # Phase 1A: Lab Color
    implement_lab_color()
    validate_phase("1A")

    # Phase 1B: Exponential (with Decision Tree 1)
    implement_exponential_penalty()
    metrics = validate_phase("1B")

    if metrics['neg_acc'] < 0.30:
        # Trigger Decision Tree 1
        new_power = decision_tree_1_exponential_power(
            metrics['scores_same'],
            metrics['scores_diff'],
            current_power=2.5
        )
        re_implement_with_new_power(new_power)
        metrics = validate_phase("1B_tuned")

    # Phase 2A: LBP Texture (with Decision Trees 2 & 3)
    implement_lbp_texture()
    metrics = validate_phase("2A")

    if metrics['neg_acc'] < 0.60:
        # Trigger Decision Tree 2
        result = decision_tree_2_lbp_tuning(
            metrics['bc_same'],
            metrics['bc_diff'],
            current_config={'P': 24, 'R': 3, 'method': 'uniform'}
        )

        if result[1] == "alternative":
            # Trigger Decision Tree 3
            alternative = decision_tree_3_texture_alternative(
                fragments, pairs_same, pairs_diff
            )
            implement_texture_alternative(alternative)

    # Phase 2B: Fractal
    implement_fractal()
    metrics = validate_phase("2B")

    # Final optimization (with Decision Trees 4 & 5)
    if metrics['balanced_acc'] < 0.85:
        # Trigger Decision Tree 4
        optimal_config = decision_tree_4_feature_weighting(
            fragments, pairs_same, pairs_diff, current_powers
        )

        if metrics['balanced_acc'] < 0.75:
            # Trigger Decision Tree 5
            architecture = decision_tree_5_architecture_change(
                metrics['balanced_acc'], feature_separations
            )
            implement_architecture_change(architecture)

    # Done!
    return final_metrics
```

---

**Document Version:** 1.0
**Date:** 2026-04-08
**Status:** Ready for autonomous implementation
**Next Steps:** Create safety checks document (SAFETY_CHECKS.md)
