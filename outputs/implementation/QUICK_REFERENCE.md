# QUICK REFERENCE CARD

**One-page summary of critical information for rapid lookup**

---

## EXACT PARAMETERS (Copy-Paste Ready)

```python
# PHASE 1A: Lab Color
LAB_CONFIG = {
    'L_bins': 16,
    'a_bins': 8,
    'b_bins': 8,
    'exponential_power': 1.0  # Baseline, change in Phase 1B
}

# PHASE 1B: Exponential Penalty
EXPONENTIAL_POWER_COLOR = 2.5  # Try [2.0, 2.5, 3.0] if needed

# PHASE 2A: LBP Texture
LBP_CONFIG = {
    'P': 24,
    'R': 3,
    'method': 'uniform',
    'exponential_power': 2.0
}

# PHASE 2B: Fractal Dimension
FRACTAL_CONFIG = {
    'scales': [2, 4, 8, 16, 32],
    'exponential_power': 0.5
}

# THRESHOLDS
MATCH_THRESHOLD = 0.50  # Keep existing
```

---

## SUCCESS CRITERIA (Check After Each Phase)

| Phase | Positive Acc | Negative Acc | Balanced Acc | Notes |
|-------|-------------|--------------|--------------|-------|
| 1A | ≥ 95% | ≥ 15% | - | Slight improvement over HSV |
| 1B | ≥ 90% | ≥ 30% | - | 2x negative accuracy |
| 2A | ≥ 90% | ≥ 60% | - | Major boost from texture |
| 2B | ≥ 90% | ≥ 75% | ≥ 85% | Final target |

---

## WHEN TO SWITCH TO ALTERNATIVES

| Feature | Trigger | Alternative 1 | Alternative 2 | Alternative 3 |
|---------|---------|--------------|--------------|--------------|
| **Lab Color** | BC > 0.85 diff-source | Opponent Color | Normalized RGB | Adaptive HSV |
| **LBP Texture** | BC > 0.85 diff-source | GLCM | Gabor | HOG |
| **Fractal** | Std > 0.15 | Complexity Ratio | Bending Energy | Disable |

---

## DECISION TREE QUICK LOOKUP

**Phase 1B failing?** → Decision Tree 1 (Exponential Power Tuning)
- Pos Acc < 90%? → Reduce power
- Neg Acc < 20%? → Increase power

**Phase 2A failing?** → Decision Tree 2 (LBP Parameter Tuning)
- BC > 0.85? → Try R=4 or switch to GLCM
- Variance > 0.20? → Try 'ror' method or reduce P

**Need texture alternative?** → Decision Tree 3 (Texture Alternative Selection)
- Directional patterns? → Gabor
- Isotropic texture? → GLCM

**Balanced Acc 75-85%?** → Decision Tree 4 (Feature Weighting)
- Rank features by Cohen's d
- Adjust exponential powers
- Grid search

**Balanced Acc < 75%?** → Decision Tree 5 (Architecture Change)
- Try two-stage filtering
- Try weighted sum fusion
- Disable weak features

---

## PRE-FLIGHT CHECKS (Run Before Each Phase)

```python
# Before Phase 1A
preflight_phase_1a()
# Check: Lab conversion, 3D histogram, BC computation

# Before Phase 1B
preflight_phase_1b()
# Check: Exponential formula, edge cases (BC=0, BC=1)

# Before Phase 2A
preflight_phase_2a()
# Check: scikit-image, LBP computation, histogram

# Before Phase 2B
preflight_phase_2b()
# Check: Box counting, linear regression, degenerate handling
```

---

## COMMON EDGE CASES

| Edge Case | Expected Behavior | Action if Fails |
|-----------|------------------|----------------|
| BC = 0 | 0^2.5 = 0 | Check for divide-by-zero |
| BC = 1 | 1^2.5 = 1 | Verify identical histograms |
| Empty histogram | BC = 0 | Add epsilon: hist + 1e-8 |
| Tiny contour | Skip fractal | Return None, use neutral score |
| Uniform image | Single LBP bin | Valid, histogram concentrated |

---

## FEATURE FUSION FORMULAS

**Primary (Multiplicative):**
```python
score = geometric × (color_BC^2.5) × (texture_BC^2.0) × (fractal_sim^0.5)
```

**Fallback 1 (Two-Stage):**
```python
appearance = (color_BC^2.5) × (texture_BC^2.0)
if appearance < 0.65: reject
else: score = geometric × appearance × (fractal_sim^0.5)
```

**Fallback 2 (Weighted Sum):**
```python
score = 0.35×geometric + 0.25×(color^2.5) + 0.25×(texture^2.0) + 0.15×fractal
```

---

## COHEN'S D INTERPRETATION

| Cohen's d | Effect Size | Interpretation | Action |
|-----------|------------|---------------|--------|
| > 0.8 | Large | Excellent discrimination | Keep feature |
| 0.5 - 0.8 | Medium | Acceptable discrimination | Keep feature |
| 0.2 - 0.5 | Small | Poor discrimination | Try alternative |
| < 0.2 | Negligible | No discrimination | Disable feature |

Formula:
```python
d = (mean_same - mean_diff) / sqrt((var_same + var_diff) / 2)
```

---

## CATASTROPHIC FAILURE RECOVERY

**If implementation breaks:**
1. Git rollback: `git checkout checkpoint_phase_X_timestamp`
2. Review SAFETY_CHECKS.md
3. Fix bug, re-run pre-flight
4. Retry implementation

**If data corruption suspected:**
1. Run `validate_no_data_corruption()`
2. Check fragment images still readable
3. Verify backup files exist
4. Restore from backup if needed

**If performance unacceptable after all attempts:**
1. Document what was tried
2. Report final configuration
3. Recommend data quality improvements or alternative approaches

---

## FILE LOCATIONS

```
outputs/implementation/
├── EXACT_PARAMETERS.md          # All parameter values
├── BACKUP_SOLUTIONS.md          # Alternative algorithms
├── DECISION_TREES.md            # Autonomous decision logic
├── SAFETY_CHECKS.md             # Pre-flight validation
├── IMPLEMENTATION_ROADMAP.md    # Master guide
├── QUICK_REFERENCE.md           # This file
├── phase_1a_validation.txt      # Generated during implementation
├── phase_1b_validation.txt      # Generated during implementation
├── phase_2a_validation.txt      # Generated during implementation
├── phase_2b_validation.txt      # Generated during implementation
├── final_validation.txt         # Generated at end
└── final_config.json            # Generated at end
```

---

## VALIDATION METRICS TO LOG

For each phase, record:
```python
metrics = {
    'phase': '1A',
    'positive_accuracy': 0.XXX,
    'negative_accuracy': 0.XXX,
    'balanced_accuracy': 0.XXX,
    'cohens_d': 0.XXX,
    'mean_same_source': 0.XXX,
    'mean_diff_source': 0.XXX,
    'std_same_source': 0.XXX,
    'std_diff_source': 0.XXX,
    'separation_gap': 0.XXX,
    'decision': 'success/tuning/alternative/failure',
    'reasoning': 'Why decision was made',
    'next_action': 'proceed/tune/switch/skip'
}
```

---

## IMPLEMENTATION CHECKLIST

- [ ] Master pre-flight check passed
- [ ] Git backup created
- [ ] Phase 1A: Lab color implemented
- [ ] Phase 1A: Validation passed (Neg Acc ≥ 15%)
- [ ] Phase 1B: Exponential penalty implemented
- [ ] Phase 1B: Validation passed (Neg Acc ≥ 30%)
- [ ] Phase 2A: LBP texture implemented
- [ ] Phase 2A: Validation passed (Neg Acc ≥ 60%)
- [ ] Phase 2B: Fractal dimension implemented
- [ ] Phase 2B: Validation passed (Bal Acc ≥ 85%)
- [ ] Final optimization (if needed)
- [ ] Final validation report generated
- [ ] Final configuration saved
- [ ] Git commit with detailed message

---

## CONTACT POINTS (When to Ask Human)

**PROCEED AUTONOMOUSLY if:**
- Decision tree provides guidance
- Backup solution available
- Performance acceptable (> 75%)

**ONLY ASK HUMAN if:**
- Catastrophic failure (data corruption)
- All alternatives exhausted AND Bal Acc < 75%
- Fundamental assumption violated

---

## ESTIMATED TIME

| Phase | Time | Notes |
|-------|------|-------|
| Pre-flight | 30 min | One-time setup |
| Phase 1A | 1-2 hours | Includes validation |
| Phase 1B | 0.5-1 hour | Simple change |
| Phase 2A | 1-2 hours | May need alternative |
| Phase 2B | 1-2 hours | Fractal computation |
| Final Opt | 0.5-2 hours | If needed |
| **TOTAL** | **4-8 hours** | End-to-end |

---

## KEY SCIENTIFIC REFERENCES

- **LBP:** Ojala et al. (2002) - Established P=8,16,24 and R=1,2,3
- **Lab Color:** Fairchild (2013) - JND thresholds, perceptual uniformity
- **Fractal:** Mandelbrot (1982) - Box counting, dimension interpretation
- **Feature Fusion:** Kittler et al. (1998) - Sum, product, voting rules

---

## QUICK IMPLEMENTATION SNIPPETS

**Lab Color Histogram:**
```python
lab = cv2.cvtColor(image, cv2.COLOR_BGR2Lab)
hist, _ = np.histogramdd(lab.reshape(-1, 3),
                         bins=[16, 8, 8],
                         range=[[0, 256], [0, 256], [0, 256]])
hist = hist.flatten() / (hist.sum() + 1e-8)
```

**LBP Histogram:**
```python
from skimage.feature import local_binary_pattern
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
lbp = local_binary_pattern(gray, P=24, R=3, method='uniform')
hist, _ = np.histogram(lbp, bins=26, range=(0, 26))
hist = hist / (hist.sum() + 1e-8)
```

**Bhattacharyya Coefficient:**
```python
bc = np.sum(np.sqrt(hist1 * hist2))
```

**Exponential Penalty:**
```python
penalty = bc ** power
```

**Cohen's d:**
```python
d = (mean1 - mean2) / np.sqrt((var1 + var2) / 2)
```

---

**Print this page for quick reference during implementation!**
