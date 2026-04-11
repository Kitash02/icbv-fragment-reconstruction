# Variant Manager - Usage Guide

## Overview

The Variant Manager provides a centralized system for managing and applying different algorithm variants to the archaeological fragment reconstruction pipeline. It enables dynamic switching between baseline and experimental configurations through selective monkey-patching of core modules.

## Available Variants

### 1. Baseline (77.8%)
**Status:** Reference implementation
**Accuracy:** 77.8% positive / 77.8% negative / 77.8% overall

Original algorithm with curvature cross-correlation, Fourier descriptors, and appearance penalties.

**Use case:** Baseline for comparison

---

### 2. Variant 0 Iter 2 (85.1%) ⭐ BEST
**Status:** Tested and validated
**Accuracy:** 77.8% positive / 91.7% negative / 85.1% overall

Tightened hard discriminator thresholds (color 0.74, texture 0.69).

**Key Features:**
- Evolutionary optimization: +2.8% color threshold, +3.0% texture threshold
- Excellent at rejecting false matches
- Maintains positive accuracy while improving negative accuracy

**Parameters:**
- `color_threshold`: 0.74 (was 0.72)
- `texture_threshold`: 0.69 (was 0.67)
- `edge_density_max_diff`: 0.15
- `entropy_max_diff`: 0.50

**Use case:** Best overall performance for production use

---

### 3. Variant 1 (77.8%)
**Status:** Tested
**Accuracy:** 77.8% positive / 77.8% negative / 77.8% overall

Weighted ensemble post-processing with learned weights.

**Key Features:**
- Research-backed weight distribution (arXiv:2510.17145 - 97.49%)
- Replaces five-way voting with weighted ensemble
- Weights: Color(0.35), Raw(0.25), Texture(0.20), Morph(0.15), Gabor(0.05)

**Use case:** Research experiments with ensemble weighting

---

### 4. Variant 5 (66.7%)
**Status:** Tested
**Accuracy:** 66.7% positive / 77.8% negative / 72.6% overall

Aggressive color^6 penalty for better cross-source discrimination.

**Key Features:**
- POWER_COLOR = 8.0 (vs 4.0 baseline)
- Strong negative discrimination
- Trade-off: -11.1% positive accuracy for maintained negative accuracy

**Use case:** When false positives must be minimized at any cost

---

### 5. Variant 8 (Ready)
**Status:** Ready for testing
**Accuracy:** Expected 75-80% positive / 85-90% negative

Adaptive Gabor weighting - fixes BC=1.0 uninformative issue.

**Key Features:**
- Detects homogeneous textures (low spectral diversity)
- Adaptively reduces Gabor weight when uninformative
- Normal mode: color^4 × texture^2 × gabor^2 × haralick^2
- Adaptive mode: color^5 × texture^3 × gabor^0.5 × haralick^3

**Expected Impact:**
- Eliminates 4-5 of 7 false positives from brown artifact BC=1.0 issue
- Minimal impact on positive accuracy

**Use case:** Datasets with homogeneous textures (papyrus, smooth pottery)

---

### 6. Variant 9 (Ready)
**Status:** Ready for testing
**Accuracy:** Target 92%+ positive / 92%+ negative (stretch: 95%+)

Full research-optimized stack combining best techniques.

**Key Features:**
- Multi-layer defense system
  - Layer 1: Hard discriminator pre-filter (fast rejection)
  - Layer 2: Weighted ensemble voting (discrimination)
  - Layer 3: Ensemble gating (prevent bad upgrades)
  - Layer 4: Stricter thresholds (final classification)
- Combines techniques from Variant 0D (89%/86%) with research ensemble

**Use case:** Maximum accuracy - production deployment after validation

---

## Usage

### Python API

```python
from variant_manager import (
    apply_variant,
    restore_baseline,
    get_available_variants,
    get_variant_description
)

# List all available variants
variants = get_available_variants()
print(variants)
# Output: ['Baseline (77.8%)', 'Variant 0 Iter 2 (85.1%) ⭐ BEST', ...]

# Get detailed description
desc = get_variant_description("Variant 0 Iter 2 (85.1%) ⭐ BEST")
print(desc)

# Apply a variant
apply_variant("Variant 0 Iter 2 (85.1%) ⭐ BEST")

# Run your reconstruction pipeline here
# ...

# Restore baseline when done
restore_baseline()
```

### Integration with main.py

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from variant_manager import apply_variant, restore_baseline

# Apply variant before running pipeline
apply_variant("Variant 0 Iter 2 (85.1%) ⭐ BEST")

# Run main pipeline
from main import main
main()

# Restore baseline after
restore_baseline()
```

### Command Line Example

```bash
# List all variants
python examples/variant_selection_example.py --list-variants

# Show detailed description
python examples/variant_selection_example.py --describe "Variant 0 Iter 2 (85.1%) ⭐ BEST"

# Apply a variant and run pipeline
python examples/variant_selection_example.py --variant "Variant 0 Iter 2 (85.1%) ⭐ BEST"
python src/main.py --input data/sample --output outputs/results
```

### GUI Integration (Future)

The variant manager is designed to integrate with GUI components:

```python
# In gui_components.py or similar

import tkinter as tk
from tkinter import ttk
from variant_manager import get_available_variants, apply_variant

class VariantSelectionPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # Dropdown for variant selection
        self.variant_var = tk.StringVar()
        variants = get_available_variants()

        ttk.Label(self, text="Algorithm Variant:").pack()
        self.variant_combo = ttk.Combobox(
            self,
            textvariable=self.variant_var,
            values=variants,
            state='readonly'
        )
        self.variant_combo.current(0)  # Default to baseline
        self.variant_combo.pack()

        # Apply button
        ttk.Button(
            self,
            text="Apply Variant",
            command=self.apply_selected_variant
        ).pack()

    def apply_selected_variant(self):
        variant_name = self.variant_var.get()
        apply_variant(variant_name)
        messagebox.showinfo("Success", f"Applied: {variant_name}")
```

## Implementation Details

### Monkey-Patching Strategy

The variant manager uses selective monkey-patching to modify only the necessary functions:

1. **Store originals:** Before patching, original functions are stored in `_original_functions` dict
2. **Import variant module:** Dynamically import the variant's implementation module
3. **Replace functions:** Patch the target module's functions with variant implementations
4. **Restoration:** `restore_baseline()` restores all original functions

### Patched Modules by Variant

| Variant | Patched Modules |
|---------|----------------|
| Baseline | None |
| Variant 0 Iter 2 | `hard_discriminators` |
| Variant 1 | `ensemble_postprocess` |
| Variant 5 | `compatibility`, `hard_discriminators` |
| Variant 8 | `compatibility` |
| Variant 9 | `ensemble_postprocess` |

### Error Handling

```python
from variant_manager import apply_variant

try:
    apply_variant("Variant 0 Iter 2 (85.1%) ⭐ BEST")
except ValueError as e:
    print(f"Invalid variant name: {e}")
except ImportError as e:
    print(f"Variant module not found: {e}")
except Exception as e:
    print(f"Failed to apply variant: {e}")
```

## Performance Comparison

| Variant | Positive | Negative | Overall | Best For |
|---------|----------|----------|---------|----------|
| Baseline | 77.8% | 77.8% | 77.8% | Reference |
| Variant 0 Iter 2 ⭐ | 77.8% | 91.7% | **85.1%** | Production |
| Variant 1 | 77.8% | 77.8% | 77.8% | Research |
| Variant 5 | 66.7% | 77.8% | 72.6% | Minimize FP |
| Variant 8 | 75-80% (est) | 85-90% (est) | 85-88% (est) | Homogeneous textures |
| Variant 9 | 92%+ (target) | 92%+ (target) | 92%+ (target) | Maximum accuracy |

## Troubleshooting

### Issue: ImportError when applying variant

**Cause:** Variant module not found in Python path

**Solution:**
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
```

### Issue: Functions not being patched

**Cause:** Module not yet imported when patching attempted

**Solution:** Import the base module before applying variant:
```python
import compatibility  # Import base module first
apply_variant("Variant 5 (66.7%)")
```

### Issue: Variant effects persist after restore_baseline()

**Cause:** Module caching in Python

**Solution:** Restart Python interpreter or use importlib.reload():
```python
import importlib
import compatibility

restore_baseline()
importlib.reload(compatibility)
```

## Future Extensions

### Adding New Variants

1. Create variant implementation module (e.g., `src/compatibility_variant10.py`)
2. Add variant configuration to `VARIANT_CONFIG` in `variant_manager.py`
3. Create `apply_variant_10()` function
4. Add to `VARIANT_APPLIERS` dispatcher dictionary

Example:
```python
def apply_variant_10():
    """Apply Variant 10: Description here."""
    logger.info("Applying Variant 10")

    variant_module = importlib.import_module('compatibility_variant10')
    import compatibility

    if 'compatibility' not in _original_functions:
        _original_functions['compatibility'] = {
            'build_compatibility_matrix': compatibility.build_compatibility_matrix
        }

    compatibility.build_compatibility_matrix = variant_module.build_compatibility_matrix
    logger.info("✓ Successfully patched compatibility module")

VARIANT_APPLIERS["Variant 10 (Description)"] = apply_variant_10
```

## References

- **arXiv:2309.13512:** 99.3% ensemble accuracy methodology
- **arXiv:2510.17145:** 97.49% weighted ensemble technique
- **arXiv:2511.12976:** MCAQ-YOLO morphological discriminators
- **Lecture 71 (ICBV):** Object recognition and appearance-based matching
- **Lecture 72 (ICBV):** 2D shape analysis and chain codes
- **Lecture 53 (ICBV):** Relaxation labeling and constraint propagation

## Support

For questions or issues:
1. Check this documentation
2. Review variant module source code
3. Check logs for detailed error messages
4. Consult experiment report documentation
