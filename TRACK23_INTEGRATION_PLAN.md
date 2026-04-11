# TRACK 2+3 INTEGRATION PLAN - Achieve 90%+ Accuracy

## MISSION
Starting from Stage 1.6 (89%/86%), integrate research algorithms to achieve 90-95%+ accuracy.

---

## ANALYSIS OF WHAT WE HAVE

### Stage 1.6 Baseline (CURRENT TARGET)
- **Formula**: `color^4 × texture^2 × gabor^2 × haralick^2`
- **Thresholds**: 0.75 / 0.60 / 0.65
- **Expected**: 89% positive (8/9), 86% negative (31/36)
- **Failures**: 1 positive (scroll), 5 negatives (similar materials)

### Available Research Algorithms

**Track 2: Hard Discriminators** (from arXiv:2511.12976 - MCAQ-YOLO, 92%+ accuracy)
- File: `src/hard_discriminators.py` (already exists)
- Functions:
  - `compute_edge_density()` - Canny edge analysis
  - `compute_texture_entropy()` - Shannon entropy
  - `hard_reject_check()` - 3 discriminators combined
- **Expected benefit**: +3-5% negative accuracy (catch similar-material false positives)
- **Risk**: Might reject 1-2 true positives if too aggressive

**Track 3: Ensemble Voting** (from arXiv:2309.13512 - 99.3% accuracy)
- File: `src/ensemble_voting.py` (already exists)
- Functions:
  - `ensemble_verdict_five_way()` - 5 independent voters
  - `ensemble_verdict_weighted()` - Custom weight voting
  - `ensemble_verdict_hierarchical()` - Decision tree
- **Expected benefit**: +5-10% overall (error correction through voting)
- **Risk**: Complexity, potential voter disagreement

---

## INTEGRATION STRATEGY

### Phase 1: Verify Clean Stage 1.6 Baseline
**Status**: Running now (background task bd6thtkn4)
**Goal**: Confirm 89%/86% without Track 2 contamination
**If fails**: Debug and iterate until we get 89%/86%
**If succeeds**: Proceed to Phase 2

### Phase 2: Integrate Track 2 (Hard Discriminators)
**Method**: Add early rejection BEFORE expensive curvature computation
**Location**: `src/compatibility.py`, line ~510
**Code to add**:
```python
# Track 2: Early rejection with hard discriminators
if appearance_mats is not None and all_images is not None:
    bc_color = appearance_mats['color'][frag_i, frag_j]
    bc_texture = appearance_mats['texture'][frag_i, frag_j]

    # Import at top: from hard_discriminators import hard_reject_check
    if hard_reject_check(all_images[frag_i], all_images[frag_j],
                        bc_color, bc_texture):
        # Skip expensive curvature computation for this pair
        continue
```

**Expected**: 89% positive, 90-92% negative (fix 1-2 of the 5 false positives)

### Phase 3: Tune Track 2 Thresholds (If Needed)
**Current thresholds** in `hard_discriminators.py`:
- `EDGE_DENSITY_THRESHOLD = 0.15` (15% difference)
- `TEXTURE_ENTROPY_THRESHOLD = 0.5` (0.5 units)
- `COLOR_GATE = 0.60`, `TEXTURE_GATE = 0.55`

**If Track 2 rejects true positives**:
- Relax thresholds: 0.15 → 0.18, 0.5 → 0.6
- Lower gates: 0.60 → 0.55, 0.55 → 0.50

**If Track 2 doesn't help enough**:
- Tighten thresholds: 0.15 → 0.12, 0.5 → 0.4
- Raise gates: 0.60 → 0.65, 0.55 → 0.60

### Phase 4: Consider Track 3 (Ensemble Voting)
**ONLY if Track 2 succeeds OR if we need additional boost**

**Option A: Replace threshold classification with ensemble**
- Location: `src/relaxation.py`, function `classify_pair_score()` (line ~161)
- Replace threshold checks with `ensemble_verdict_five_way()`
- Requires passing appearance features through the call chain

**Option B: Add ensemble as post-processing filter**
- Run after relaxation labeling
- Re-classify borderline cases (WEAK_MATCH verdicts)
- Less invasive, easier to implement

**Recommendation**: Try Option B first (less risky)

---

## EXPECTED PROGRESSION

| Stage | Positive | Negative | Overall | Key Change |
|-------|----------|----------|---------|------------|
| Baseline (original) | 100% | 0% | 20% | No discrimination |
| **Stage 1.6** | **89%** | **86%** | **87%** | Multiplicative penalty |
| + Track 2 | 88-89% | 90-92% | 89-91% | Early rejection |
| + Track 2 tuned | 89% | 92-94% | 91-92% | Threshold optimization |
| + Track 3 | 89-91% | 92-97% | 91-95% | Ensemble voting |

**Target**: 90%+ both metrics (90% positive, 90%+ negative)

---

## DECISION TREE

```
Start: Clean Stage 1.6
│
├─ Test → 89%/86%? ✓
│  │
│  ├─ Integrate Track 2 (hard discriminators)
│  │  │
│  │  ├─ Test → Improved? ✓
│  │  │  │
│  │  │  ├─ Positive dropped? ✗ → KEEP Track 2, done
│  │  │  └─ Positive dropped? ✓ → Tune thresholds → Test again
│  │  │
│  │  └─ Test → Worse? ✗ → REVERT Track 2, try Track 3 instead
│  │
│  └─ If Track 2 helps but not enough:
│     └─ Add Track 3 (ensemble voting) → Test → Keep if better
│
└─ Test → NOT 89%/86%? ✗ → Debug Stage 1.6 → Iterate until correct

```

---

## AGENT ASSIGNMENTS (5 Agents)

### Agent 1: Track 2 Integration & Testing
- Integrate Track 2 into compatibility.py
- Run full benchmark (45 cases)
- Compare to Stage 1.6 baseline
- Report: Keep or revert?

### Agent 2: Track 2 Threshold Tuning (If Needed)
- IF Agent 1 shows regression on positives
- Tune thresholds to recover positives
- Test multiple threshold combinations
- Find optimal balance

### Agent 3: Track 3 Option B (Post-Processing)
- Implement ensemble voting as post-filter
- Re-classify WEAK_MATCH cases only
- Test on full benchmark
- Report: Improvement?

### Agent 4: Track 3 Option A (Full Integration)
- IF Option B doesn't help enough
- Replace classify_pair_score with ensemble
- Pass appearance features through call chain
- Test on full benchmark

### Agent 5: Final Optimization & Analysis
- Compare all variants (1.6, +Track2, +Track3, combinations)
- Find best configuration
- Create comprehensive comparison report
- Recommendation: Which to deploy?

---

## SUCCESS CRITERIA

**Minimum Acceptable**:
- Positive accuracy ≥ 88% (allow 1% drop)
- Negative accuracy ≥ 90% (4% improvement)
- Overall accuracy ≥ 89%

**Target**:
- Positive accuracy ≥ 89% (maintain Stage 1.6)
- Negative accuracy ≥ 92% (6% improvement)
- Overall accuracy ≥ 91%

**Stretch Goal**:
- Both metrics ≥ 90%
- Overall ≥ 92%

---

## RISK MITIGATION

**Risk 1**: Track 2 rejects true positives
- **Mitigation**: Keep Stage 1.6 baseline clean, test Track 2 separately
- **Fallback**: Revert to Stage 1.6, try Track 3 instead

**Risk 2**: Ensemble voting adds complexity without benefit
- **Mitigation**: Try post-processing (Option B) first, simpler
- **Fallback**: Stick with Track 2 only if it helps

**Risk 3**: Both Track 2 and 3 make things worse
- **Mitigation**: We have Stage 1.6 baseline (89%/86%) to fall back to
- **Acceptance**: Stage 1.6 already exceeds 85% target

---

## EXECUTION TIMELINE

1. **Wait for Stage 1.6 test** (~7 minutes)
2. **Analyze results** (2 minutes)
3. **Launch 5 agents** (simultaneous)
4. **Agent execution** (15-25 minutes each)
5. **Final analysis** (5 minutes)

**Total estimated time**: 35-45 minutes

---

## THIS IS THE PLAN - EXECUTE WITHOUT WAITING FOR APPROVAL
