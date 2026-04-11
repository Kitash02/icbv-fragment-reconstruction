"""
Variant Quick Reference - For GUI Integration

This module provides simple data structures and helper functions for
GUI components that need to display variant information without
importing the full variant_manager module.
"""

# Quick reference data for GUI dropdowns and displays
VARIANT_QUICK_REFERENCE = [
    {
        "name": "Baseline (77.8%)",
        "short_desc": "Original algorithm",
        "accuracy": "77.8% / 77.8%",
        "badge": "",
        "recommended_for": "Testing and comparison"
    },
    {
        "name": "Variant 0 Iter 2 (85.1%) ⭐ BEST",
        "short_desc": "Tightened thresholds",
        "accuracy": "77.8% / 91.7%",
        "badge": "⭐ BEST",
        "recommended_for": "Production use - best overall accuracy"
    },
    {
        "name": "Variant 1 (77.8%)",
        "short_desc": "Weighted ensemble",
        "accuracy": "77.8% / 77.8%",
        "badge": "",
        "recommended_for": "Research experiments"
    },
    {
        "name": "Variant 5 (66.7%)",
        "short_desc": "Aggressive color penalty",
        "accuracy": "66.7% / 77.8%",
        "badge": "",
        "recommended_for": "Minimize false positives"
    },
    {
        "name": "Variant 8 (Ready)",
        "short_desc": "Adaptive Gabor weighting",
        "accuracy": "Expected: 85-88%",
        "badge": "🧪 EXPERIMENTAL",
        "recommended_for": "Homogeneous textures"
    },
    {
        "name": "Variant 9 (Ready)",
        "short_desc": "Full research stack",
        "accuracy": "Target: 92%+",
        "badge": "🧪 EXPERIMENTAL",
        "recommended_for": "Maximum accuracy (after testing)"
    }
]


def get_variant_names():
    """Get list of variant names for dropdown menus."""
    return [v["name"] for v in VARIANT_QUICK_REFERENCE]


def get_variant_display_info(variant_name):
    """Get display information for a variant."""
    for variant in VARIANT_QUICK_REFERENCE:
        if variant["name"] == variant_name:
            return variant
    return None


def format_variant_tooltip(variant_name):
    """Format a tooltip string for a variant."""
    info = get_variant_display_info(variant_name)
    if not info:
        return ""

    return (
        f"{info['short_desc']}\n"
        f"Accuracy: {info['accuracy']}\n"
        f"Best for: {info['recommended_for']}"
    )


# Color scheme for GUI display
VARIANT_COLORS = {
    "Baseline (77.8%)": "#808080",  # Gray
    "Variant 0 Iter 2 (85.1%) ⭐ BEST": "#00AA00",  # Green (best)
    "Variant 1 (77.8%)": "#0088FF",  # Blue (research)
    "Variant 5 (66.7%)": "#FF8800",  # Orange (trade-off)
    "Variant 8 (Ready)": "#AA00AA",  # Purple (experimental)
    "Variant 9 (Ready)": "#AA00AA"   # Purple (experimental)
}


# Example GUI integration code (for reference)
GUI_INTEGRATION_EXAMPLE = """
# Example: Integrating with tkinter GUI

import tkinter as tk
from tkinter import ttk
from variant_quick_reference import (
    get_variant_names,
    format_variant_tooltip,
    VARIANT_COLORS
)
from variant_manager import apply_variant

class VariantSelector(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # Label
        ttk.Label(self, text="Algorithm Variant:").pack(pady=5)

        # Dropdown
        self.variant_var = tk.StringVar()
        self.combo = ttk.Combobox(
            self,
            textvariable=self.variant_var,
            values=get_variant_names(),
            state='readonly',
            width=40
        )
        self.combo.current(0)  # Default to Baseline
        self.combo.pack(pady=5)

        # Bind tooltip
        self.combo.bind('<Motion>', self._show_tooltip)

        # Apply button
        self.apply_btn = ttk.Button(
            self,
            text="Apply Variant",
            command=self._apply_variant
        )
        self.apply_btn.pack(pady=5)

        # Status label
        self.status_label = ttk.Label(self, text="Current: Baseline")
        self.status_label.pack(pady=5)

    def _show_tooltip(self, event):
        variant = self.variant_var.get()
        tooltip_text = format_variant_tooltip(variant)
        # Show tooltip (implementation depends on tooltip library)
        # self.tooltip.show(tooltip_text)

    def _apply_variant(self):
        variant = self.variant_var.get()
        try:
            apply_variant(variant)
            self.status_label.config(
                text=f"Current: {variant}",
                foreground=VARIANT_COLORS.get(variant, "black")
            )
            messagebox.showinfo("Success", f"Applied variant: {variant}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply variant: {e}")
"""


if __name__ == "__main__":
    # Configure UTF-8 encoding for Windows console
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    # Display quick reference
    print("Variant Quick Reference")
    print("=" * 70)

    for variant in VARIANT_QUICK_REFERENCE:
        print(f"\n{variant['name']} {variant['badge']}")
        print(f"  Description: {variant['short_desc']}")
        print(f"  Accuracy: {variant['accuracy']}")
        print(f"  Recommended for: {variant['recommended_for']}")

    print("\n" + "=" * 70)
    print("\nFor detailed information, use:")
    print("  from variant_manager import get_variant_description")
    print("  print(get_variant_description('Variant 0 Iter 2 (85.1%) ⭐ BEST'))")
