# Quick Start: Variant 6 Evolutionary Optimization

## One-Command Evolution (Recommended)

```bash
cd /c/Users/I763940/icbv-fragment-reconstruction
python evolve_variant6_manual.py
```

This will:
1. Set POWER_COLOR to the next untested value
2. Run the full test suite
3. Record results automatically
4. Tell you to run it again for the next iteration

**Repeat 5 times** to test all power values: 2.0, 2.5, 3.0, 3.5, 4.0

---

## Step-by-Step Manual Approach

### Iteration 1: POWER_COLOR = 2.0

```bash
# 1. Setup
python update_variant6_power.py  # Sets power to 2.0

# 2. Test
python test_variant6_simple.py --no-rotate  # Takes 3-5 minutes

# 3. Record (example with hypothetical results)
python record_variant6_result.py 2.0 88.9 83.3
```

### Iteration 2: POWER_COLOR = 2.5

```bash
python update_variant6_power.py  # Sets power to 2.5
python test_variant6_simple.py --no-rotate
python record_variant6_result.py 2.5 88.9 91.7
```

### Iteration 3: POWER_COLOR = 3.0

```bash
python update_variant6_power.py  # Sets power to 3.0
python test_variant6_simple.py --no-rotate
python record_variant6_result.py 3.0 100.0 94.4
```

**STOP HERE IF 95%+ ON BOTH METRICS!**

### Iterations 4-5 (if needed)

Continue with 3.5 and 4.0 if target not yet achieved.

---

## Reading Results

### During Test

Look for lines like:
```
> [P] positive_case_name    + MATCH    45.2s  PASS
> [N] negative_case_name    - NO_MATCH 2.1s   PASS
```

Count the PASS/FAIL for each category.

### At End of Test

```
TOTAL  X/45 pass  Y fail  Z error
```

Calculate:
- Positive accuracy = (positive_pass / 9) × 100%
- Negative accuracy = (negative_pass / 36) × 100%

### Final Summary

After all iterations:
```bash
python update_variant6_power.py  # Shows final summary
```

---

## Expected Timeline

- **Each test**: 3-5 minutes
- **Total for 5 iterations**: 15-25 minutes
- **Early stop possible**: If 95%/95% achieved before iteration 5

---

## Target Metrics

**Success = BOTH of**:
- Positive accuracy ≥ 95% (≥8 out of 9 pass)
- Negative accuracy ≥ 95% (≥34 out of 36 pass)

**Predicted winner**: POWER_COLOR = 2.5 to 3.0

---

## Troubleshooting

### Test hangs or crashes
- Check `outputs/` folder for partial results
- Kill process: Ctrl+C
- Restart from current iteration

### Module not found errors
```bash
cd /c/Users/I763940/icbv-fragment-reconstruction
export PYTHONPATH=$PWD/src:$PYTHONPATH
```

### Wrong results
- Verify POWER_COLOR was actually updated:
  ```bash
  grep "^POWER_COLOR" src/compatibility_variant6.py
  ```

---

## Quick Commands Reference

```bash
# Set up evolution
python setup_variant6_evolution.py

# Run one iteration (auto)
python evolve_variant6_manual.py

# Manual control
python update_variant6_power.py        # Update power
python test_variant6_simple.py --no-rotate  # Test
python record_variant6_result.py 2.0 88.9 94.4  # Record

# Check current state
grep "^POWER_COLOR" src/compatibility_variant6.py
cat outputs/variant6_manual_progress.json

# View full analysis
cat VARIANT6_EVOLUTIONARY_OPTIMIZATION.md
```

---

**Ready to start?**

```bash
python evolve_variant6_manual.py
```
