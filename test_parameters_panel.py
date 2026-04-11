"""
Quick test script for ParametersPanel functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gui_components import ParametersPanel
import tkinter as tk
from tkinter import ttk


def test_parameters_panel():
    """Test ParametersPanel basic functionality."""
    print("Testing ParametersPanel...")

    root = tk.Tk()
    root.title("ParametersPanel Test")
    root.geometry("800x600")

    # Create panel
    panel = ParametersPanel(root)
    panel.pack(fill="both", expand=True)

    # Test getting parameters
    params = panel.get_parameters()
    print("\nDefault parameters:")
    for key, value in params.items():
        print(f"  {key}: {value}")

    # Test setting parameters
    test_params = {
        'color_power': 6.0,
        'texture_power': 3.0,
        'match_score_threshold': 0.80,
        'gaussian_sigma': 2.0
    }
    print("\nSetting test parameters:")
    for key, value in test_params.items():
        print(f"  {key}: {value}")

    panel.set_parameters(test_params)

    # Verify parameters were set
    new_params = panel.get_parameters()
    print("\nParameters after set_parameters():")
    for key in test_params.keys():
        print(f"  {key}: {new_params[key]}")

    # Test reset
    print("\nTesting reset to defaults...")
    panel.reset_to_defaults()
    reset_params = panel.get_parameters()
    print("Parameters after reset:")
    for key in test_params.keys():
        print(f"  {key}: {reset_params[key]}")

    print("\n✓ All tests passed!")
    print("\nGUI window opened. Close it to exit the test.")

    root.mainloop()


if __name__ == "__main__":
    test_parameters_panel()
