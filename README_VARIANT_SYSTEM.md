# Variant Selection and Monkey-Patching Infrastructure

## Overview

This implementation provides a complete variant management system for the archaeological fragment reconstruction pipeline. It enables dynamic algorithm switching through selective monkey-patching, allowing researchers and users to experiment with different optimization strategies without modifying the core codebase.

## Components

### 1. Core Module: `src/variant_manager.py`

The central variant management system that handles:
- Variant configuration database (6 variants)
- Monkey-patching logic for dynamic module replacement
- Original function storage for restoration
- Error handling and validation

**Key Functions:**
- `apply_variant(variant_name)` - Apply a specific variant
- `restore_baseline()` - Restore original implementations
- `get_available_variants()` - List all variant names
- `get_variant_description(variant_name)` - Get detailed description
- `get_variant_config(variant_name)` - Get configuration dictionary

### 2. Quick Reference: `src/variant_quick_reference.py`

Lightweight module for GUI integration with:
- Simplified variant information
- Display helpers
- Color schemes
- GUI integration examples

**Key Functions:**
- `get_variant_names()` - Get names for dropdowns
- `get_variant_display_info(variant_name)` - Get display info
- `format_variant_tooltip(variant_name)` - Format tooltips

### 3. Examples

#### `examples/variant_selection_example.py`
Basic variant selection and description viewer.

```bash
# List variants
python examples/variant_selection_example.py --list-variants

# Describe a variant
python examples/variant_selection_example.py --describe "Variant 0 Iter 2 (85.1%) ⭐ BEST"

# Apply a variant
python examples/variant_selection_example.py --variant "Variant 0 Iter 2 (85.1%) ⭐ BEST"
```

#### `examples/run_with_variant.py`
Complete pipeline integration with variant selection.

```bash
# Run pipeline with specific variant
python examples/run_with_variant.py --input data/sample --variant "Variant 0 Iter 2 (85.1%) ⭐ BEST"

# List available variants
python examples/run_with_variant.py --list-variants

# Keep variant active after run
python examples/run_with_variant.py --input data/sample --variant "Variant 1 (77.8%)" --no-restore
```

### 4. Documentation: `docs/VARIANT_MANAGER_GUIDE.md`

Comprehensive guide covering:
- All 6 variants with detailed descriptions
- Usage examples and integration patterns
- Performance comparison tables
- Troubleshooting guide
- Future extension instructions

## Supported Variants

| Variant | Accuracy | Status | Best For |
|---------|----------|--------|----------|
| **Baseline** | 77.8% / 77.8% | Reference | Testing, comparison |
| **Variant 0 Iter 2** ⭐ | 77.8% / 91.7% | **BEST** | **Production use** |
| **Variant 1** | 77.8% / 77.8% | Tested | Research experiments |
| **Variant 5** | 66.7% / 77.8% | Tested | Minimize false positives |
| **Variant 8** | 85-88% (est) | Ready | Homogeneous textures |
| **Variant 9** | 92%+ (target) | Ready | Maximum accuracy |

## Quick Start

### Python API

```python
from variant_manager import apply_variant, restore_baseline

# Apply best variant
apply_variant("Variant 0 Iter 2 (85.1%) ⭐ BEST")

# Run your pipeline
# ...

# Restore baseline
restore_baseline()
```

### Command Line

```bash
# List all variants
python src/variant_manager.py

# Run with specific variant
python examples/run_with_variant.py \
    --input data/sample \
    --output outputs/results \
    --variant "Variant 0 Iter 2 (85.1%) ⭐ BEST"
```

## Architecture

### Monkey-Patching Strategy

```
┌─────────────────────────────────────────────────────────┐
│ Variant Manager                                         │
├─────────────────────────────────────────────────────────┤
│ 1. Store Original Functions                            │
│    _original_functions['module_name']['func_name']     │
│                                                         │
│ 2. Import Variant Module                               │
│    variant_module = import('module_variant_X')         │
│                                                         │
│ 3. Replace Functions                                   │
│    base_module.func_name = variant_module.func_name    │
│                                                         │
│ 4. Restoration Available                               │
│    restore_baseline() → restore all originals          │
└─────────────────────────────────────────────────────────┘
```

### Module Mapping

```
Variant 0 Iter 2:
  hard_discriminators → hard_discriminators_variant0_iter2

Variant 1:
  ensemble_postprocess → ensemble_postprocess_variant1

Variant 5:
  compatibility → compatibility_variant5
  hard_discriminators → hard_discriminators_variant5

Variant 8:
  compatibility → compatibility_variant8

Variant 9:
  ensemble_postprocess → ensemble_postprocess_variant9_FINAL
```

## Integration Points

### 1. Main Pipeline Integration

```python
# In main.py or wrapper script
from variant_manager import apply_variant

# Apply variant before imports
apply_variant("Variant 0 Iter 2 (85.1%) ⭐ BEST")

# Import pipeline modules (patches are active)
from compatibility import build_compatibility_matrix
from ensemble_postprocess import reclassify_borderline_cases

# Run pipeline...
```

### 2. GUI Integration

```python
# In gui_components.py
import tkinter as tk
from tkinter import ttk
from variant_quick_reference import get_variant_names, VARIANT_COLORS
from variant_manager import apply_variant

class SetupPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # Variant selector
        ttk.Label(self, text="Algorithm Variant:").pack()

        self.variant_var = tk.StringVar()
        self.variant_combo = ttk.Combobox(
            self,
            textvariable=self.variant_var,
            values=get_variant_names(),
            state='readonly'
        )
        self.variant_combo.current(1)  # Default to best variant
        self.variant_combo.pack()

        # Apply button
        ttk.Button(
            self,
            text="Apply Variant",
            command=self._apply_variant
        ).pack()

    def _apply_variant(self):
        variant = self.variant_var.get()
        apply_variant(variant)
        messagebox.showinfo("Success", f"Applied: {variant}")
```

### 3. Testing Integration

```python
# In test suite
from variant_manager import apply_variant, restore_baseline
import pytest

@pytest.fixture
def variant_baseline():
    """Ensure baseline is active for test."""
    restore_baseline()
    yield
    restore_baseline()

@pytest.mark.parametrize("variant", [
    "Baseline (77.8%)",
    "Variant 0 Iter 2 (85.1%) ⭐ BEST",
    "Variant 1 (77.8%)"
])
def test_variant_accuracy(variant):
    apply_variant(variant)
    # Run tests...
    restore_baseline()
```

## Performance Characteristics

### Variant 0 Iter 2 (⭐ BEST)
- **Positive Accuracy:** 77.8% (maintained)
- **Negative Accuracy:** 91.7% (+13.9% vs baseline)
- **Overall Accuracy:** 85.1% (+7.3% vs baseline)
- **Strategy:** Tightened hard discriminator thresholds
- **Overhead:** None (pre-filter optimization)

### Variant 1 (Weighted Ensemble)
- **Positive Accuracy:** 77.8%
- **Negative Accuracy:** 77.8%
- **Overall Accuracy:** 77.8%
- **Strategy:** Learned ensemble weights
- **Overhead:** Minimal (weight multiplication)

### Variant 5 (Aggressive Penalty)
- **Positive Accuracy:** 66.7% (-11.1% vs baseline)
- **Negative Accuracy:** 77.8% (maintained)
- **Overall Accuracy:** 72.6% (-5.2% vs baseline)
- **Strategy:** color^8 penalty vs color^4
- **Overhead:** None (same computation, different exponent)

### Variant 8 (Adaptive Gabor)
- **Expected Positive:** 75-80%
- **Expected Negative:** 85-90%
- **Expected Overall:** 85-88%
- **Strategy:** Adaptive feature weighting
- **Overhead:** Spectral diversity computation

### Variant 9 (Full Stack)
- **Target Positive:** 92%+
- **Target Negative:** 92%+
- **Target Overall:** 92%+
- **Strategy:** 4-layer defense system
- **Overhead:** Pre-filter + gating checks

## Testing

### Unit Tests

```bash
# Test variant manager
python -m pytest tests/test_variant_manager.py

# Test variant application
python -m pytest tests/test_variant_integration.py

# Test all variants on sample data
python -m pytest tests/test_variant_accuracy.py
```

### Manual Testing

```bash
# Test standalone
python src/variant_manager.py

# Test quick reference
python src/variant_quick_reference.py

# Test example scripts
python examples/variant_selection_example.py --list-variants
python examples/run_with_variant.py --input data/sample --variant Baseline
```

## Error Handling

### Common Issues and Solutions

**Issue:** `ValueError: Unknown variant`
```python
# Solution: Check variant name spelling
from variant_manager import get_available_variants
print(get_available_variants())
```

**Issue:** `ImportError: No module named 'variant_module'`
```python
# Solution: Ensure variant module exists
import os
variant_path = 'src/hard_discriminators_variant0_iter2.py'
assert os.path.exists(variant_path)
```

**Issue:** Functions not being patched
```python
# Solution: Import base module before applying variant
import compatibility  # Import first
apply_variant("Variant 5 (66.7%)")  # Then apply
```

## Future Enhancements

### 1. Variant Persistence
Save/load variant configuration from JSON:
```python
def save_variant_config(variant_name, filepath):
    config = get_variant_config(variant_name)
    with open(filepath, 'w') as f:
        json.dump(config, f)
```

### 2. Variant Comparison
Run multiple variants in parallel:
```python
def compare_variants(input_dir, variants):
    results = {}
    for variant in variants:
        apply_variant(variant)
        results[variant] = run_pipeline(input_dir)
        restore_baseline()
    return results
```

### 3. Dynamic Parameter Tuning
Allow runtime parameter adjustment:
```python
def apply_variant_with_params(variant_name, **params):
    apply_variant(variant_name)
    # Override specific parameters
    import hard_discriminators
    hard_discriminators.COLOR_THRESHOLD = params.get('color_threshold', 0.74)
```

## References

- Variant implementations: `src/*_variant*.py`
- Documentation: `docs/VARIANT_MANAGER_GUIDE.md`
- Examples: `examples/variant_*.py`, `examples/run_with_variant.py`

## License

Part of the ICBV Fragment Reconstruction System.

## Contributing

To add a new variant:
1. Create variant implementation module
2. Add configuration to `VARIANT_CONFIG`
3. Create `apply_variant_X()` function
4. Add to `VARIANT_APPLIERS` dispatcher
5. Update documentation and tests

See `docs/VARIANT_MANAGER_GUIDE.md` for detailed instructions.
