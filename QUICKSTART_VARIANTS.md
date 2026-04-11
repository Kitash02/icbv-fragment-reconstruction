# Variant Manager - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Basic Usage (Python API)

```python
from variant_manager import apply_variant, restore_baseline

# Apply the best variant
apply_variant("Variant 0 Iter 2 (85.1%) ⭐ BEST")

# Run your pipeline here
# ... your code ...

# Restore baseline when done
restore_baseline()
```

### 2. Command Line Usage

```bash
# List all available variants
python src/variant_manager.py

# Run pipeline with specific variant
python examples/run_with_variant.py \
    --input data/sample \
    --output outputs/results \
    --variant "Variant 0 Iter 2 (85.1%) ⭐ BEST"
```

### 3. Get Variant Information

```python
from variant_manager import get_available_variants, get_variant_description

# See all variants
variants = get_available_variants()
print(variants)

# Get detailed info
desc = get_variant_description("Variant 0 Iter 2 (85.1%) ⭐ BEST")
print(desc)
```

## 📊 Which Variant Should I Use?

| Use Case | Recommended Variant | Why |
|----------|---------------------|-----|
| **Production** | Variant 0 Iter 2 ⭐ | Best overall accuracy (85.1%) |
| **Research** | Variant 1 | Research-backed ensemble weights |
| **Minimize False Positives** | Variant 5 | Strong negative discrimination |
| **Homogeneous Textures** | Variant 8 | Fixes Gabor BC=1.0 issue |
| **Maximum Accuracy** | Variant 9 | Full research stack (92%+ target) |
| **Testing/Baseline** | Baseline | Reference implementation |

## 🎯 Quick Examples

### Example 1: Compare Two Variants

```python
from variant_manager import apply_variant, restore_baseline

variants_to_test = [
    "Baseline (77.8%)",
    "Variant 0 Iter 2 (85.1%) ⭐ BEST"
]

results = {}
for variant in variants_to_test:
    apply_variant(variant)

    # Run your pipeline
    result = run_pipeline(input_dir="data/sample")
    results[variant] = result

    restore_baseline()

# Compare results
print(results)
```

### Example 2: List and Select Interactively

```python
from variant_manager import get_available_variants, apply_variant

# Show menu
variants = get_available_variants()
print("Available variants:")
for i, v in enumerate(variants):
    print(f"{i}. {v}")

# User selects
choice = int(input("Select variant (0-5): "))
selected = variants[choice]

# Apply
apply_variant(selected)
print(f"Applied: {selected}")
```

### Example 3: GUI Integration Snippet

```python
import tkinter as tk
from tkinter import ttk, messagebox
from variant_manager import apply_variant
from variant_quick_reference import get_variant_names

class VariantPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # Dropdown
        ttk.Label(self, text="Algorithm Variant:").pack()
        self.variant_var = tk.StringVar()
        combo = ttk.Combobox(
            self,
            textvariable=self.variant_var,
            values=get_variant_names(),
            state='readonly'
        )
        combo.current(1)  # Default to best variant
        combo.pack()

        # Apply button
        ttk.Button(self, text="Apply", command=self.apply).pack()

    def apply(self):
        variant = self.variant_var.get()
        try:
            apply_variant(variant)
            messagebox.showinfo("Success", f"Applied: {variant}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
```

## 🔍 Variant Details at a Glance

### Variant 0 Iter 2 (⭐ BEST)
- **Accuracy:** 77.8% positive / 91.7% negative / 85.1% overall
- **Strategy:** Tightened thresholds (0.74/0.69)
- **Best for:** Production - excellent at rejecting false matches

### Variant 1
- **Accuracy:** 77.8% positive / 77.8% negative / 77.8% overall
- **Strategy:** Weighted ensemble (Color 0.35, Raw 0.25, Texture 0.20, Morph 0.15, Gabor 0.05)
- **Best for:** Research experiments with learned weights

### Variant 5
- **Accuracy:** 66.7% positive / 77.8% negative / 72.6% overall
- **Strategy:** Aggressive color^8 penalty (vs color^4)
- **Best for:** When false positives absolutely must be minimized

### Variant 8 (🧪 Experimental)
- **Expected:** 75-80% positive / 85-90% negative
- **Strategy:** Adaptive Gabor weighting (fixes BC=1.0 issue)
- **Best for:** Datasets with homogeneous textures (papyrus, smooth pottery)

### Variant 9 (🧪 Experimental)
- **Target:** 92%+ positive / 92%+ negative
- **Strategy:** 4-layer defense (hard disc + weighted + gating + thresholds)
- **Best for:** Maximum accuracy after validation

## 📁 File Locations

- **Core Module:** `src/variant_manager.py`
- **Quick Reference:** `src/variant_quick_reference.py`
- **Examples:** `examples/variant_selection_example.py`, `examples/run_with_variant.py`
- **Documentation:** `docs/VARIANT_MANAGER_GUIDE.md`
- **Architecture:** `README_VARIANT_SYSTEM.md`

## 🐛 Common Issues

### Issue: "Unknown variant"
**Solution:** Check spelling or list available variants:
```python
from variant_manager import get_available_variants
print(get_available_variants())
```

### Issue: "No module named 'variant_module'"
**Solution:** Make sure you're in the project root:
```bash
cd /path/to/icbv-fragment-reconstruction
python src/variant_manager.py
```

### Issue: Changes not taking effect
**Solution:** Import base modules before applying variant:
```python
import compatibility  # Import first
apply_variant("Variant 5 (66.7%)")  # Then apply
```

## 📚 Next Steps

1. **Read Full Documentation:** `docs/VARIANT_MANAGER_GUIDE.md`
2. **Explore Architecture:** `README_VARIANT_SYSTEM.md`
3. **Run Examples:** Try `examples/run_with_variant.py`
4. **Test Variants:** Compare performance on your data
5. **Integrate with GUI:** Use `variant_quick_reference.py` helpers

## 💡 Pro Tips

1. **Always restore baseline** after experiments to avoid confusion
2. **Use Variant 0 Iter 2** for production - it's tested and proven
3. **Test Variants 8 and 9** on your data - they're ready but not yet validated
4. **Check logs** for detailed patching information
5. **Use get_variant_description()** to remind yourself what each variant does

## 🎓 Learning Path

1. **Start:** Run `python src/variant_manager.py` to see all variants
2. **Practice:** Try `examples/variant_selection_example.py --list-variants`
3. **Experiment:** Run `examples/run_with_variant.py` with different variants
4. **Compare:** Test multiple variants on your dataset
5. **Integrate:** Add variant selection to your workflow/GUI

## ✅ Quick Checklist

- [ ] I can list all variants: `get_available_variants()`
- [ ] I can apply a variant: `apply_variant("Variant 0 Iter 2 (85.1%) ⭐ BEST")`
- [ ] I can restore baseline: `restore_baseline()`
- [ ] I can run the pipeline with a variant using `examples/run_with_variant.py`
- [ ] I understand which variant to use for my use case
- [ ] I've read the full documentation in `docs/VARIANT_MANAGER_GUIDE.md`

## 🚀 Ready to Go!

You now have everything you need to use the variant management system. Pick a variant, apply it, and run your pipeline. Happy reconstructing! 🏺

---

**For detailed information, see:**
- Full Guide: `docs/VARIANT_MANAGER_GUIDE.md`
- Architecture: `README_VARIANT_SYSTEM.md`
- Implementation Summary: `VARIANT_IMPLEMENTATION_SUMMARY.md`
