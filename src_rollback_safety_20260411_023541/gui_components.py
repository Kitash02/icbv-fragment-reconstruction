"""
GUI Components - Archaeological Fragment Reconstruction System v2.0

This module provides the panel components for the GUI application:
- SetupPanel: Fragment loading and algorithm variant selection
- ParametersPanel: Interactive parameter tuning with sliders
- ResultsPanel: Visualization of assembly proposals and metrics
- AboutPanel: Project information and experiment summary

These components are designed to provide a user-friendly interface to the
core algorithms implemented in the project without requiring command-line usage.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import sys
import threading
import subprocess
from pathlib import Path
from typing import List, Optional

# PIL/Pillow for image handling
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None
    print("Warning: PIL/Pillow not available. Image thumbnails will not display.")


class ParametersPanel(ttk.Frame):
    """
    Parameters panel for tuning algorithm parameters with slider controls.

    Provides grouped slider controls for:
    - Appearance powers (color, texture, gabor, haralick)
    - Match thresholds (score, weak match, assembly confidence)
    - Preprocessing settings (gaussian sigma, segment count)

    Supports loading/saving parameter configurations as JSON presets.
    """

    def __init__(self, parent, app=None):
        """
        Initialize the Parameters panel.

        Args:
            parent: Parent widget (typically the notebook)
            app: Reference to main application window
        """
        super().__init__(parent)
        self.app = app

        # Dictionary to store all parameter variables
        self.param_vars = {}

        # Dictionary to store default values for reset functionality
        self.defaults = {}

        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create scrollable canvas for all controls
        self._create_scrollable_container()

        # Create parameter sections
        self._create_appearance_section()
        self._create_thresholds_section()
        self._create_preprocessing_section()
        self._create_control_buttons()

    def _create_scrollable_container(self):
        """Create scrollable container for parameter controls."""
        # Create canvas with scrollbar
        canvas = tk.Canvas(self, borderwidth=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar.grid(row=0, column=1, sticky="ns")

    def _create_appearance_section(self):
        """Create appearance powers section with 4 sliders."""
        frame = ttk.LabelFrame(self.scrollable_frame, text="Appearance Powers", padding=10)
        frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        frame.grid_columnconfigure(0, weight=1)

        # Color Power: [1.0 - 8.0], default 4.0
        self.create_slider(
            frame,
            "Color Power",
            min_val=1.0,
            max_val=8.0,
            default=4.0,
            resolution=0.1,
            row=0,
            key="color_power",
            tooltip="Exponential power for color BC penalty (higher = stronger rejection of color mismatches)"
        )

        # Texture Power: [1.0 - 4.0], default 2.0
        self.create_slider(
            frame,
            "Texture Power",
            min_val=1.0,
            max_val=4.0,
            default=2.0,
            resolution=0.1,
            row=1,
            key="texture_power",
            tooltip="Exponential power for texture BC penalty"
        )

        # Gabor Power: [1.0 - 4.0], default 2.0
        self.create_slider(
            frame,
            "Gabor Power",
            min_val=1.0,
            max_val=4.0,
            default=2.0,
            resolution=0.1,
            row=2,
            key="gabor_power",
            tooltip="Exponential power for Gabor feature penalty (frequency-domain texture)"
        )

        # Haralick Power: [1.0 - 4.0], default 2.0
        self.create_slider(
            frame,
            "Haralick Power",
            min_val=1.0,
            max_val=4.0,
            default=2.0,
            resolution=0.1,
            row=3,
            key="haralick_power",
            tooltip="Exponential power for Haralick GLCM penalty (second-order texture statistics)"
        )

    def _create_thresholds_section(self):
        """Create thresholds section with 3 sliders."""
        frame = ttk.LabelFrame(self.scrollable_frame, text="Thresholds", padding=10)
        frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        frame.grid_columnconfigure(0, weight=1)

        # Match Score Threshold: [0.50 - 0.90], default 0.75
        self.create_slider(
            frame,
            "Match Score Threshold",
            min_val=0.50,
            max_val=0.90,
            default=0.75,
            resolution=0.01,
            row=0,
            key="match_score_threshold",
            tooltip="Raw compatibility >= this → confident MATCH"
        )

        # Weak Match Threshold: [0.40 - 0.80], default 0.60
        self.create_slider(
            frame,
            "Weak Match Threshold",
            min_val=0.40,
            max_val=0.80,
            default=0.60,
            resolution=0.01,
            row=1,
            key="weak_match_threshold",
            tooltip="Raw compatibility >= this → possible match"
        )

        # Assembly Confidence: [0.40 - 0.80], default 0.65
        self.create_slider(
            frame,
            "Assembly Confidence",
            min_val=0.40,
            max_val=0.80,
            default=0.65,
            resolution=0.01,
            row=2,
            key="assembly_confidence_threshold",
            tooltip="Average confidence for assembly acceptance"
        )

    def _create_preprocessing_section(self):
        """Create preprocessing section with 2 sliders."""
        frame = ttk.LabelFrame(self.scrollable_frame, text="Preprocessing", padding=10)
        frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        frame.grid_columnconfigure(0, weight=1)

        # Gaussian Sigma: [0.5 - 3.0], default 1.5
        self.create_slider(
            frame,
            "Gaussian Sigma",
            min_val=0.5,
            max_val=3.0,
            default=1.5,
            resolution=0.1,
            row=0,
            key="gaussian_sigma",
            tooltip="Standard deviation for Gaussian blur (controls smoothing strength)"
        )

        # Segment Count: [50 - 500], default 200
        self.create_slider(
            frame,
            "Segment Count",
            min_val=50,
            max_val=500,
            default=200,
            resolution=10,
            row=1,
            key="segment_count",
            tooltip="Number of boundary segments per fragment"
        )

    def _create_control_buttons(self):
        """Create control buttons at the bottom."""
        frame = ttk.Frame(self.scrollable_frame)
        frame.grid(row=3, column=0, sticky="ew", padx=10, pady=15)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(2, weight=1)

        # Reset to Defaults button
        reset_btn = ttk.Button(
            frame,
            text="Reset to Defaults",
            command=self.reset_to_defaults
        )
        reset_btn.grid(row=0, column=0, padx=5, sticky="ew")

        # Load from File button
        load_btn = ttk.Button(
            frame,
            text="Load from File",
            command=self.load_config
        )
        load_btn.grid(row=0, column=1, padx=5, sticky="ew")

        # Save as Preset button
        save_btn = ttk.Button(
            frame,
            text="Save as Preset",
            command=self.save_config
        )
        save_btn.grid(row=0, column=2, padx=5, sticky="ew")

    def create_slider(self, parent, label, min_val, max_val, default, resolution, row, key, tooltip=""):
        """
        Create a labeled slider with current value display.

        Args:
            parent: Parent widget to place slider in
            label: Display label for the slider
            min_val: Minimum slider value
            max_val: Maximum slider value
            default: Default value
            resolution: Step size for slider
            row: Grid row to place slider in
            key: Dictionary key for storing the variable
            tooltip: Tooltip text to display on hover
        """
        # Create frame for this slider
        slider_frame = ttk.Frame(parent)
        slider_frame.grid(row=row, column=0, sticky="ew", pady=5)
        slider_frame.grid_columnconfigure(1, weight=1)

        # Label
        label_widget = ttk.Label(slider_frame, text=label + ":", width=25, anchor="w")
        label_widget.grid(row=0, column=0, sticky="w", padx=(0, 10))

        # Create variable
        var = tk.DoubleVar(value=default)
        self.param_vars[key] = var
        self.defaults[key] = default

        # Slider
        slider = tk.Scale(
            slider_frame,
            from_=min_val,
            to=max_val,
            resolution=resolution,
            orient=tk.HORIZONTAL,
            variable=var,
            showvalue=0,  # Don't show value on slider itself
            length=300
        )
        slider.grid(row=0, column=1, sticky="ew", padx=5)

        # Value display label
        value_label = ttk.Label(slider_frame, text=f"{default:.2f}", width=8, anchor="e")
        value_label.grid(row=0, column=2, sticky="e")

        # Update value label when slider changes
        def update_label(*args):
            value = var.get()
            # Format based on the value magnitude
            if resolution >= 1:
                value_label.config(text=f"{int(value)}")
            elif resolution >= 0.1:
                value_label.config(text=f"{value:.1f}")
            else:
                value_label.config(text=f"{value:.2f}")

        var.trace_add("write", update_label)

        # Add tooltip if provided
        if tooltip:
            self._create_tooltip(label_widget, tooltip)
            self._create_tooltip(slider, tooltip)

    def _create_tooltip(self, widget, text):
        """
        Create a simple tooltip for a widget.

        Args:
            widget: Widget to attach tooltip to
            text: Tooltip text
        """
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")

            label = ttk.Label(
                tooltip,
                text=text,
                background="#ffffe0",
                relief="solid",
                borderwidth=1,
                wraplength=300
            )
            label.pack()

            widget.tooltip = tooltip

        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def get_parameters(self):
        """
        Get current parameter values as a dictionary.

        Returns:
            dict: Dictionary mapping parameter names to current values
        """
        params = {}
        for key, var in self.param_vars.items():
            params[key] = var.get()
        return params

    def set_parameters(self, params_dict):
        """
        Set parameter values from a dictionary.

        Args:
            params_dict: Dictionary mapping parameter names to values
        """
        for key, value in params_dict.items():
            if key in self.param_vars:
                try:
                    self.param_vars[key].set(value)
                except Exception as e:
                    print(f"Warning: Could not set parameter {key}: {e}")

    def reset_to_defaults(self):
        """Reset all parameters to their default values."""
        for key, default_value in self.defaults.items():
            if key in self.param_vars:
                self.param_vars[key].set(default_value)

        messagebox.showinfo("Reset Complete", "All parameters reset to default values.")

    def load_config(self):
        """Load parameters from a JSON configuration file."""
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=os.path.join(os.path.dirname(__file__), "..", "config")
        )

        if not filename:
            return  # User cancelled

        try:
            with open(filename, 'r') as f:
                params = json.load(f)

            self.set_parameters(params)
            messagebox.showinfo("Load Complete", f"Configuration loaded from:\n{filename}")

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load configuration:\n{str(e)}")

    def save_config(self):
        """Save current parameters to a JSON configuration file."""
        filename = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=os.path.join(os.path.dirname(__file__), "..", "config")
        )

        if not filename:
            return  # User cancelled

        try:
            params = self.get_parameters()

            with open(filename, 'w') as f:
                json.dump(params, f, indent=2)

            messagebox.showinfo("Save Complete", f"Configuration saved to:\n{filename}")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save configuration:\n{str(e)}")


class SetupPanel(ttk.Frame):
    """
    Setup panel for fragment loading and algorithm variant selection.

    Provides:
    - Fragment folder browser with thumbnail preview grid (4x4, 80x80px)
    - Algorithm variant selector with 6 variants and descriptions
    - Run/Stop action buttons for pipeline execution
    - Integration with main app for parameter and results display

    The panel maintains state about loaded fragments and running pipelines,
    and coordinates with app.params_panel and app.results_panel for workflow.
    """

    # Algorithm variant descriptions
    VARIANTS = [
        {
            "name": "Baseline (77.8%)",
            "command": "python src/main.py",
            "description": (
                "Original implementation using standard relaxation labeling.\n\n"
                "Performance: 77.8% accuracy (7/9 positive, 7/9 negative)\n"
                "Features: Chain code matching, basic compatibility scoring\n"
                "Runtime: Fast (~2-5 seconds per case)"
            )
        },
        {
            "name": "Variant 0 Iter 2 (85.1%) ⭐ BEST",
            "command": "python run_variant0_iter2.py",
            "description": (
                "Best performing variant from evolutionary optimization.\n\n"
                "Performance: 85.1% accuracy (87.5% pos / 83.3% neg)\n"
                "Features: Enhanced hard discriminators, optimized thresholds\n"
                "Improvements: Gap detection, color pre-check, refined scoring\n"
                "Runtime: Medium (~5-10 seconds per case)\n\n"
                "⭐ RECOMMENDED for production use"
            )
        },
        {
            "name": "Variant 1 (77.8%)",
            "command": "python run_variant1.py",
            "description": (
                "Alternative ensemble postprocessing approach.\n\n"
                "Performance: 77.8% accuracy (7/9 positive, 7/9 negative)\n"
                "Features: Modified reclassification logic\n"
                "Runtime: Fast (~2-5 seconds per case)"
            )
        },
        {
            "name": "Variant 5 (66.7%)",
            "command": "python run_variant5.py",
            "description": (
                "Experimental variant with strict Gabor filtering.\n\n"
                "Performance: 66.7% accuracy (focus on precision)\n"
                "Features: Gabor texture analysis, strict matching thresholds\n"
                "Runtime: Slow (~10-15 seconds per case)\n\n"
                "Note: Lower accuracy due to overly conservative thresholds"
            )
        },
        {
            "name": "Variant 8 (Ready)",
            "command": "python run_variant8.py",
            "description": (
                "Enhanced relaxation labeling with multi-stage optimization.\n\n"
                "Status: Implementation complete, ready for testing\n"
                "Features: Adaptive threshold adjustment, iterative refinement\n"
                "Expected runtime: Medium (~5-10 seconds per case)"
            )
        },
        {
            "name": "Variant 9 (Ready)",
            "command": "python run_variant9.py",
            "description": (
                "Advanced discriminator variant with color analysis.\n\n"
                "Status: Implementation complete, ready for testing\n"
                "Features: Enhanced color pre-checking, refined voting\n"
                "Expected runtime: Medium (~5-10 seconds per case)"
            )
        }
    ]

    def __init__(self, parent, app):
        """
        Initialize the setup panel.

        Parameters
        ----------
        parent : tk.Widget
            Parent widget (typically the notebook)
        app : FragmentReconstructionApp
            Main application instance for cross-panel communication
        """
        super().__init__(parent)
        self.app = app

        # State variables
        self.fragment_folder = None
        self.fragment_paths = []
        self.thumbnail_images = []  # Keep references to prevent GC
        self.running_process = None
        self.selected_variant_idx = 1  # Default to best variant (Variant 0 Iter 2)

        # Build UI
        self._build_ui()

    def _build_ui(self):
        """Construct the panel layout with all components."""
        # Configure grid weights for responsive layout
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # === Section 1: Fragment Loader ===
        self._create_fragment_loader_section()

        # === Section 2: Algorithm Variant Selector ===
        self._create_variant_selector_section()

        # === Section 3: Action Buttons ===
        self._create_action_buttons()

    def _create_fragment_loader_section(self):
        """Create the fragment folder browser and thumbnail preview grid."""
        # Main container
        loader_frame = ttk.LabelFrame(self, text="Fragment Loader", padding=10)
        loader_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        loader_frame.grid_columnconfigure(0, weight=1)

        # Browse button row
        browse_frame = ttk.Frame(loader_frame)
        browse_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        browse_frame.grid_columnconfigure(2, weight=1)

        ttk.Button(
            browse_frame,
            text="Browse Folder...",
            command=self.browse_folder,
            width=18
        ).grid(row=0, column=0, padx=(0, 10))

        ttk.Button(
            browse_frame,
            text="Load Sample Data",
            command=self.load_sample_data,
            width=18,
            style="Accent.TButton"
        ).grid(row=0, column=1, padx=(0, 10))

        self.folder_label = ttk.Label(
            browse_frame,
            text="No folder selected (Click 'Load Sample Data' to get started)",
            foreground="gray"
        )
        self.folder_label.grid(row=0, column=2, sticky="w")

        # Fragment count label
        self.count_label = ttk.Label(
            loader_frame,
            text="0 fragments loaded",
            font=("Arial", 10, "bold")
        )
        self.count_label.grid(row=1, column=0, sticky="w", pady=(0, 10))

        # Thumbnail preview grid (4x4, 80x80 thumbnails)
        preview_frame = ttk.Frame(loader_frame)
        preview_frame.grid(row=2, column=0, sticky="nsew")

        self.thumbnail_labels = []
        for row in range(4):
            for col in range(4):
                # Create frame for each thumbnail with border
                thumb_container = ttk.Frame(
                    preview_frame,
                    borderwidth=1,
                    relief="solid",
                    width=82,
                    height=82
                )
                thumb_container.grid(row=row, column=col, padx=2, pady=2)
                thumb_container.grid_propagate(False)

                # Label for thumbnail image
                thumb_label = ttk.Label(thumb_container, text="", anchor="center")
                thumb_label.place(relx=0.5, rely=0.5, anchor="center")
                self.thumbnail_labels.append(thumb_label)

    def _create_variant_selector_section(self):
        """Create the algorithm variant selector with dropdown and description."""
        # Main container
        variant_frame = ttk.LabelFrame(self, text="Algorithm Variant Selector", padding=10)
        variant_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        variant_frame.grid_rowconfigure(2, weight=1)
        variant_frame.grid_columnconfigure(0, weight=1)

        # Dropdown selector row
        selector_frame = ttk.Frame(variant_frame)
        selector_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        selector_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(selector_frame, text="Select variant:").grid(row=0, column=0, padx=(0, 10))

        self.variant_combo = ttk.Combobox(
            selector_frame,
            values=[v["name"] for v in self.VARIANTS],
            state="readonly",
            width=40
        )
        self.variant_combo.current(self.selected_variant_idx)
        self.variant_combo.grid(row=0, column=1, sticky="ew")
        self.variant_combo.bind("<<ComboboxSelected>>", self._on_variant_selected)

        # Learn More button
        ttk.Button(
            selector_frame,
            text="Learn More",
            command=self._open_experiment_docs,
            width=15
        ).grid(row=0, column=2, padx=(10, 0))

        # Description text box
        ttk.Label(variant_frame, text="Description:").grid(row=1, column=0, sticky="w", pady=(0, 5))

        desc_frame = ttk.Frame(variant_frame)
        desc_frame.grid(row=2, column=0, sticky="nsew")
        desc_frame.grid_rowconfigure(0, weight=1)
        desc_frame.grid_columnconfigure(0, weight=1)

        self.description_text = tk.Text(
            desc_frame,
            height=8,
            wrap=tk.WORD,
            font=("Arial", 9),
            state=tk.DISABLED,
            bg="#f0f0f0",
            relief=tk.SUNKEN,
            borderwidth=1
        )
        self.description_text.grid(row=0, column=0, sticky="nsew")

        # Scrollbar for description
        scrollbar = ttk.Scrollbar(desc_frame, orient=tk.VERTICAL, command=self.description_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.description_text.config(yscrollcommand=scrollbar.set)

        # Update description to show default variant
        self._update_description()

    def _create_action_buttons(self):
        """Create the Run and Stop action buttons."""
        button_frame = ttk.Frame(self)
        button_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        button_frame.grid_columnconfigure(0, weight=1)

        # Button container for centering
        center_frame = ttk.Frame(button_frame)
        center_frame.grid(row=0, column=0)

        # Run Assembly button (green)
        self.run_button = tk.Button(
            center_frame,
            text="▶ Run Assembly",
            command=self._run_assembly,
            width=20,
            height=2,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.RAISED,
            cursor="hand2"
        )
        self.run_button.grid(row=0, column=0, padx=10)

        # Stop button (red, initially disabled)
        self.stop_button = tk.Button(
            center_frame,
            text="⬛ Stop",
            command=self._stop_assembly,
            width=15,
            height=2,
            bg="#f44336",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.RAISED,
            state=tk.DISABLED,
            cursor="hand2"
        )
        self.stop_button.grid(row=0, column=1, padx=10)

    def browse_folder(self):
        """Open folder browser dialog and load fragment images."""
        # Try multiple methods to find project root
        # Method 1: Use __file__ if available
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        except:
            # Method 2: Use current working directory
            project_root = os.getcwd()

        data_dir = os.path.join(project_root, "data")

        # If data dir doesn't exist, try alternative paths
        if not os.path.exists(data_dir):
            # Try from current directory
            data_dir = os.path.abspath("data")
            if not os.path.exists(data_dir):
                # Try one level up
                data_dir = os.path.abspath("../data")
                if not os.path.exists(data_dir):
                    data_dir = None

        folder = filedialog.askdirectory(
            title="Select Fragment Folder",
            initialdir=data_dir if data_dir and os.path.exists(data_dir) else None
        )

        if not folder:
            return

        # Fix 3: Path normalization (Windows compatibility)
        folder = os.path.normpath(folder)
        folder = os.path.abspath(folder)

        # Fix 2: Pre-validate folder for images
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'}
        try:
            all_files = os.listdir(folder)
            image_files = [
                f for f in all_files
                if os.path.isfile(os.path.join(folder, f)) and
                Path(f).suffix.lower() in image_extensions
            ]

            if len(image_files) == 0:
                # Show helpful error message
                messagebox.showwarning(
                    "No Images Found",
                    f"No PNG/JPG/JPEG images found in the selected folder.\n\n"
                    f"Selected folder:\n{folder}\n\n"
                    f"Files found: {len(all_files)}\n"
                    f"First few files: {', '.join(all_files[:5]) if all_files else 'None'}\n\n"
                    f"TIP: Make sure you select the folder that CONTAINS the image files,\n"
                    f"not a parent directory. For example:\n"
                    f"✓ Correct: data/sample/\n"
                    f"✗ Wrong: data/\n\n"
                    f"Do you want to select a different folder?",
                    icon='warning'
                )

                # Offer to browse again
                response = messagebox.askyesno(
                    "Try Again?",
                    "Would you like to select a different folder?",
                    icon='question'
                )
                if response:
                    self.browse_folder()  # Recursive call to try again
                return

        except Exception as e:
            messagebox.showerror(
                "Error Accessing Folder",
                f"Cannot access folder:\n{folder}\n\n"
                f"Error: {str(e)}\n\n"
                f"Please check permissions and try again."
            )
            return

        # All checks passed - proceed with loading
        self.fragment_folder = folder
        self.folder_label.config(text=folder, foreground="black")

        # Load fragment images
        self._load_fragments()

        # Fix 1: Visual feedback after loading
        if len(self.fragment_paths) > 0:
            messagebox.showinfo(
                "Fragments Loaded Successfully",
                f"✓ Loaded {len(self.fragment_paths)} fragment images from:\n\n"
                f"{folder}\n\n"
                f"You can now click 'Run Assembly' to process these fragments."
            )
        else:
            # This shouldn't happen due to pre-validation, but just in case
            messagebox.showwarning(
                "No Images Loaded",
                f"No images were loaded from:\n{folder}\n\n"
                f"Please check the folder and try again."
            )

    def load_sample_data(self):
        """Automatically load the sample data from data/sample directory."""
        # Try multiple methods to find sample directory
        sample_dir = None

        # Method 1: Try relative to __file__
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            sample_dir = os.path.join(project_root, "data", "sample")
        except:
            pass

        # Method 2: Try from current working directory
        if not sample_dir or not os.path.exists(sample_dir):
            sample_dir = os.path.abspath(os.path.join(os.getcwd(), "data", "sample"))

        # Method 3: Try direct relative path
        if not os.path.exists(sample_dir):
            sample_dir = os.path.abspath("data/sample")

        # Method 4: Try one level up
        if not os.path.exists(sample_dir):
            sample_dir = os.path.abspath("../data/sample")

        # Method 4: Try one level up
        if not os.path.exists(sample_dir):
            sample_dir = os.path.abspath("../data/sample")

        # Final check
        if not os.path.exists(sample_dir):
            # Show detailed error with all paths tried
            cwd = os.getcwd()
            try:
                file_dir = os.path.dirname(__file__)
            except:
                file_dir = "N/A"

            messagebox.showerror(
                "Sample Data Not Found",
                f"Could not find sample data directory.\n\n"
                f"Tried paths:\n"
                f"1. {sample_dir}\n"
                f"2. {os.path.join(cwd, 'data', 'sample')}\n\n"
                f"Current working directory: {cwd}\n"
                f"Script directory: {file_dir}\n\n"
                f"Please ensure you run the GUI from the project root:\n"
                f"cd C:/Users/I763940/icbv-fragment-reconstruction\n"
                f"python src/gui_main.py"
            )
            return

        # Check if sample directory has images
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'}
        image_files = [
            f for f in os.listdir(sample_dir)
            if os.path.isfile(os.path.join(sample_dir, f)) and
            Path(f).suffix.lower() in image_extensions
        ]

        if not image_files:
            messagebox.showwarning(
                "No Images Found",
                f"No fragment images found in:\n{sample_dir}\n\n"
                f"The sample directory exists but contains no image files.\n"
                f"Found files: {os.listdir(sample_dir)}"
            )
            return

        # Load the sample directory
        self.fragment_folder = sample_dir
        self.folder_label.config(text=sample_dir, foreground="black")
        self._load_fragments()

        messagebox.showinfo(
            "Sample Data Loaded",
            f"Successfully loaded {len(self.fragment_paths)} sample fragments from:\n"
            f"{sample_dir}\n\n"
            f"Fragments: {', '.join([os.path.basename(p) for p in self.fragment_paths[:5]])}\n\n"
            f"Click 'Run Assembly' to process these fragments."
        )

    def _load_fragments(self):
        """Load fragment images from selected folder and update thumbnails."""
        if not self.fragment_folder:
            return

        # Find all image files in folder
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'}
        self.fragment_paths = []

        try:
            files_in_folder = os.listdir(self.fragment_folder)

            for filename in sorted(files_in_folder):
                full_path = os.path.join(self.fragment_folder, filename)
                if os.path.isfile(full_path):
                    ext = Path(filename).suffix.lower()
                    if ext in image_extensions:
                        self.fragment_paths.append(full_path)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load fragments:\n{str(e)}")
            import traceback
            traceback.print_exc()
            return

        # Update count label
        count = len(self.fragment_paths)
        self.count_label.config(text=f"{count} fragment{'s' if count != 1 else ''} loaded")

        if count == 0:
            messagebox.showwarning(
                "No Images Found",
                f"No image files found in:\n{self.fragment_folder}\n\n"
                f"Files in folder: {files_in_folder}\n\n"
                f"Looking for extensions: {', '.join(image_extensions)}"
            )

        # Update thumbnail grid
        self._update_thumbnails()

        # Update count label
        count = len(self.fragment_paths)
        self.count_label.config(text=f"{count} fragment{'s' if count != 1 else ''} loaded")

        # Update thumbnail grid
        self._update_thumbnails()

    def _update_thumbnails(self):
        """Update the 4x4 thumbnail preview grid with loaded fragments."""
        # Clear existing thumbnails
        self.thumbnail_images.clear()

        if not Image or not ImageTk:
            # PIL not available, show text placeholders
            for i, label in enumerate(self.thumbnail_labels):
                if i < len(self.fragment_paths):
                    label.config(text=f"#{i+1}", image="")
                else:
                    label.config(text="", image="")
            return

        # Load and display thumbnails (up to 16)
        for i, label in enumerate(self.thumbnail_labels):
            if i < len(self.fragment_paths):
                try:
                    # Load image
                    img = Image.open(self.fragment_paths[i])

                    # Resize to 80x80 maintaining aspect ratio
                    img.thumbnail((80, 80), Image.Resampling.LANCZOS)

                    # Convert to PhotoImage
                    photo = ImageTk.PhotoImage(img)

                    # Store reference to prevent garbage collection
                    self.thumbnail_images.append(photo)

                    # Update label
                    label.config(image=photo, text="")

                except Exception as e:
                    # If image load fails, show error text
                    label.config(image="", text="✗")
            else:
                # Empty slot
                label.config(image="", text="")

    def _on_variant_selected(self, event=None):
        """Handle variant selection change."""
        self.selected_variant_idx = self.variant_combo.current()
        self._update_description()

    def _update_description(self):
        """Update the description text box with selected variant info."""
        variant = self.VARIANTS[self.selected_variant_idx]

        self.description_text.config(state=tk.NORMAL)
        self.description_text.delete(1.0, tk.END)
        self.description_text.insert(1.0, variant["description"])
        self.description_text.config(state=tk.DISABLED)

    def _open_experiment_docs(self):
        """Open EXPERIMENT_DOCUMENTATION.md in default viewer."""
        import webbrowser
        doc_path = os.path.join(os.path.dirname(__file__), "..", "EXPERIMENT_DOCUMENTATION.md")

        if os.path.exists(doc_path):
            webbrowser.open(f"file://{os.path.abspath(doc_path)}")
        else:
            messagebox.showerror(
                "Error",
                "EXPERIMENT_DOCUMENTATION.md not found.\n\n"
                "Expected location:\n" + doc_path
            )

    def _run_assembly(self):
        """Start the assembly pipeline in a background thread."""
        # Validation
        if not self.fragment_paths:
            messagebox.showwarning(
                "No Fragments",
                "Please load a fragment folder first using 'Browse Folder'."
            )
            return

        if len(self.fragment_paths) < 2:
            messagebox.showwarning(
                "Insufficient Fragments",
                "At least 2 fragments are required for assembly."
            )
            return

        # Get selected variant
        variant = self.VARIANTS[self.selected_variant_idx]

        # Get parameters from params_panel if available
        params = {}
        if hasattr(self.app, 'params_panel') and hasattr(self.app.params_panel, 'get_parameters'):
            params = self.app.params_panel.get_parameters()

        # Update UI state
        self.run_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.variant_combo.config(state=tk.DISABLED)

        # Update results panel to show "Running..."
        if hasattr(self.app, 'results_panel') and hasattr(self.app.results_panel, 'show_running'):
            self.app.results_panel.show_running()

        # Run pipeline in background thread
        thread = threading.Thread(
            target=self._run_pipeline_thread,
            args=(variant, params),
            daemon=True
        )
        thread.start()

    def _run_pipeline_thread(self, variant, params):
        """
        Execute the pipeline in a background thread.

        Parameters
        ----------
        variant : dict
            Selected algorithm variant configuration
        params : dict
            Parameter values from params_panel (currently not used by main.py)
        """
        try:
            # Always use src/main.py as the base command
            cmd = ["python", "src/main.py"]

            # Add fragment folder input
            cmd.extend(["--input", self.fragment_folder])

            # Add output directories
            output_dir = os.path.join("outputs", "results")
            log_dir = os.path.join("outputs", "logs")
            cmd.extend(["--output", output_dir])
            cmd.extend(["--log", log_dir])

            # Ensure output directories exist
            os.makedirs(output_dir, exist_ok=True)
            os.makedirs(log_dir, exist_ok=True)

            # NOTE: Custom parameters from sliders are not yet supported by main.py

            print(f"Running command: {' '.join(cmd)}")

            # Execute command
            self.running_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,  # Get text output instead of bytes
                cwd=os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
            )

            stdout, stderr = self.running_process.communicate()
            return_code = self.running_process.returncode

            # Process completed
            self.running_process = None

            # Print stdout for debugging
            if stdout:
                print("Pipeline output:")
                print(stdout)

            # Update UI on main thread
            self.after(0, self._on_pipeline_complete, return_code, stdout, stderr)

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.after(0, self._on_pipeline_error, f"{str(e)}\n\n{error_details}")

    def _on_pipeline_complete(self, return_code, stdout, stderr):
        """
        Handle pipeline completion on main thread.

        Parameters
        ----------
        return_code : int
            Process exit code
        stdout : str
            Process standard output
        stderr : str
            Process standard error
        """
        # Restore UI state
        self.run_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.variant_combo.config(state="readonly")

        if return_code == 0:
            # Success
            messagebox.showinfo(
                "Success",
                "Assembly pipeline completed successfully!\n\n"
                "Check the Results tab for visualization."
            )

            # Update results panel
            if hasattr(self.app, 'results_panel') and hasattr(self.app.results_panel, 'load_results'):
                self.app.results_panel.load_results()

            # Switch to results tab
            self.app.notebook.select(2)  # Results is tab index 2

        else:
            # Error - stderr is already text now (no decode needed)
            error_msg = stderr if stderr else "Unknown error"
            messagebox.showerror(
                "Pipeline Failed",
                f"Assembly pipeline failed with exit code {return_code}\n\n"
                f"Error output:\n{error_msg[:1000]}"
            )

    def _on_pipeline_error(self, error_msg):
        """Handle pipeline exception on main thread."""
        self.run_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.variant_combo.config(state="readonly")

        messagebox.showerror(
            "Error",
            f"Failed to run pipeline:\n\n{error_msg}"
        )

    def _stop_assembly(self):
        """Stop the running pipeline."""
        if self.running_process:
            response = messagebox.askyesno(
                "Confirm Stop",
                "Are you sure you want to stop the running pipeline?"
            )

            if response:
                try:
                    self.running_process.terminate()
                    self.running_process = None

                    self.run_button.config(state=tk.NORMAL)
                    self.stop_button.config(state=tk.DISABLED)
                    self.variant_combo.config(state="readonly")

                    messagebox.showinfo("Stopped", "Pipeline execution stopped.")

                except Exception as e:
                    messagebox.showerror("Error", f"Failed to stop pipeline:\n{str(e)}")

    def is_running(self):
        """
        Check if a pipeline is currently running.

        Returns
        -------
        bool
            True if pipeline is running, False otherwise
        """
        return self.running_process is not None


class ResultsPanel(ttk.Frame):
    """
    Results panel with embedded matplotlib visualizations.

    Displays assembly proposals from the reconstruction pipeline with:
    - Navigation controls to cycle through multiple assemblies
    - Interactive matplotlib canvas with pan and zoom support
    - Dropdown selector for different visualization types
    - Status bar showing confidence scores and match statistics

    The panel integrates with existing visualize.py functions to render
    fragment contours, compatibility heatmaps, assembly proposals, and
    convergence plots.
    """

    def __init__(self, parent, app=None):
        """
        Initialize the ResultsPanel.

        Parameters
        ----------
        parent : tk.Widget
            Parent widget (typically the notebook)
        app : tk.Tk, optional
            Reference to the main application window
        """
        super().__init__(parent)
        self.app = app

        # For simple image display
        self.result_images = []  # PIL Images
        self.result_paths = []  # File paths
        self.current_index = 0
        self.current_photo = None  # Keep reference to prevent GC

        # Old variables (for matplotlib version - may be used later)
        self.results = []  # List of assembly dicts from pipeline
        self.current_assembly_index = 0
        self.images = []  # Fragment images for visualization
        self.contours = []  # Fragment contours
        self.fragment_names = []  # Fragment names
        self.compat_matrix = None  # Compatibility matrix
        self.convergence_trace = []  # Relaxation convergence trace

        # Current visualization state
        self.current_figure = None
        self.canvas = None

        # Configure grid weights for responsive layout
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._create_simple_widgets()

    def _create_simple_widgets(self):
        """Create simple image viewer widgets."""
        # Navigation frame (top)
        self.nav_frame = ttk.Frame(self)
        self.nav_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        self.nav_frame.grid_columnconfigure(1, weight=1)
        self.nav_frame.grid_remove()  # Hide until results loaded

        self.prev_button = ttk.Button(self.nav_frame, text="← Previous", command=self.show_previous)
        self.prev_button.grid(row=0, column=0, padx=5)

        self.image_label = ttk.Label(self.nav_frame, text="No results", font=("Arial", 10, "bold"))
        self.image_label.grid(row=0, column=1, padx=10)

        self.next_button = ttk.Button(self.nav_frame, text="Next →", command=self.show_next)
        self.next_button.grid(row=0, column=2, padx=5)

        # Canvas frame for image display
        self.canvas_frame = ttk.Frame(self, relief=tk.SUNKEN, borderwidth=2)
        self.canvas_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        self.canvas_frame.grid_remove()  # Hide until results loaded

        # Create canvas for displaying images
        self.result_canvas = tk.Canvas(self.canvas_frame, bg="white", highlightthickness=0)
        self.result_canvas.grid(row=0, column=0, sticky="nsew")

        # Info frame (bottom)
        self.info_frame = ttk.Frame(self)
        self.info_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        self.info_frame.grid_remove()  # Hide until results loaded

        self.info_label = ttk.Label(self.info_frame, text="", font=("Arial", 9))
        self.info_label.pack()

        # Placeholder (shown initially)
        placeholder_frame = ttk.Frame(self)
        placeholder_frame.grid(row=1, column=0, sticky="nsew")
        placeholder_frame.grid_rowconfigure(0, weight=1)
        placeholder_frame.grid_columnconfigure(0, weight=1)

        self.placeholder_label = ttk.Label(
            placeholder_frame,
            text="Run the assembly pipeline to see results here.\n\n"
                 "Click 'Load Sample Data' and 'Run Assembly' in the Setup tab.",
            font=("Arial", 12),
            foreground="gray",
            justify=tk.CENTER
        )
        self.placeholder_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def _create_widgets(self):
        """Create all UI widgets for the results panel."""
        # Navigation bar (top)
        nav_frame = ttk.Frame(self)
        nav_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        nav_frame.grid_columnconfigure(1, weight=1)

        # Previous/Next buttons
        btn_frame = ttk.Frame(nav_frame)
        btn_frame.grid(row=0, column=0, sticky="w")

        self.btn_prev = ttk.Button(
            btn_frame, text="Previous", command=self.navigate_prev, width=10
        )
        self.btn_prev.pack(side=tk.LEFT, padx=2)

        self.assembly_label = ttk.Label(
            btn_frame, text="No results loaded", font=("Arial", 10, "bold")
        )
        self.assembly_label.pack(side=tk.LEFT, padx=10)

        self.btn_next = ttk.Button(
            btn_frame, text="Next", command=self.navigate_next, width=10
        )
        self.btn_next.pack(side=tk.LEFT, padx=2)

        # Visualization type selector
        viz_frame = ttk.Frame(nav_frame)
        viz_frame.grid(row=0, column=1, sticky="e")

        ttk.Label(viz_frame, text="View:").pack(side=tk.LEFT, padx=5)

        self.viz_type_var = tk.StringVar(value="Assembly Proposal")
        self.viz_selector = ttk.Combobox(
            viz_frame,
            textvariable=self.viz_type_var,
            values=[
                "Fragment Contours",
                "Compatibility Heatmap",
                "Assembly Proposal",
                "Convergence Plot"
            ],
            state="readonly",
            width=20
        )
        self.viz_selector.pack(side=tk.LEFT, padx=2)
        self.viz_selector.bind("<<ComboboxSelected>>", lambda e: self.update_visualization())

        # Zoom controls
        zoom_frame = ttk.Frame(viz_frame)
        zoom_frame.pack(side=tk.LEFT, padx=10)

        ttk.Button(zoom_frame, text="+", command=self.zoom_in, width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(zoom_frame, text="-", command=self.zoom_out, width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(zoom_frame, text="Fit", command=self.zoom_fit, width=4).pack(side=tk.LEFT, padx=1)

        # Main visualization canvas
        canvas_frame = ttk.Frame(self, relief=tk.SUNKEN, borderwidth=2)
        canvas_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # Placeholder label (shown when no results)
        self.placeholder_label = ttk.Label(
            canvas_frame,
            text="Run the reconstruction pipeline to see results here.",
            font=("Arial", 12),
            foreground="gray"
        )
        self.placeholder_label.grid(row=0, column=0)

        # Canvas container (initially hidden)
        self.canvas_container = ttk.Frame(canvas_frame)

        # Info panel (bottom status bar)
        info_frame = ttk.Frame(self, relief=tk.RIDGE, borderwidth=2)
        info_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        info_frame.grid_columnconfigure(0, weight=1)

        # Status labels
        status_container = ttk.Frame(info_frame)
        status_container.pack(fill=tk.X, padx=10, pady=5)

        self.confidence_label = ttk.Label(
            status_container, text="Confidence: --", font=("Arial", 9)
        )
        self.confidence_label.pack(side=tk.LEFT, padx=10)

        ttk.Separator(status_container, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.pairs_label = ttk.Label(
            status_container, text="Matched pairs: --", font=("Arial", 9)
        )
        self.pairs_label.pack(side=tk.LEFT, padx=10)

        ttk.Separator(status_container, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.verdict_label = ttk.Label(
            status_container, text="Verdict: --", font=("Arial", 9, "bold")
        )
        self.verdict_label.pack(side=tk.LEFT, padx=10)

        # Initially disable navigation buttons
        self._update_button_states()

    def show_results(self, results, images=None, contours=None, fragment_names=None,
                     compat_matrix=None, convergence_trace=None):
        """
        Display results from the reconstruction pipeline.

        Parameters
        ----------
        results : list of dict
            List of assembly proposals from extract_top_assemblies()
            Each dict contains: 'pairs', 'confidence', 'verdict', 'n_match', 'n_weak', 'n_no_match'
        images : list of np.ndarray, optional
            Fragment images (BGR format)
        contours : list of np.ndarray, optional
            Fragment contours (Nx2 arrays)
        fragment_names : list of str, optional
            Fragment names for labeling
        compat_matrix : np.ndarray, optional
            Pairwise compatibility matrix (n_frags x n_segs x n_frags x n_segs)
        convergence_trace : list of float, optional
            Relaxation labeling convergence values per iteration
        """
        self.results = results
        self.images = images or []
        self.contours = contours or []
        self.fragment_names = fragment_names or []
        self.compat_matrix = compat_matrix
        self.convergence_trace = convergence_trace or []
        self.current_assembly_index = 0

        # Hide placeholder and show canvas
        self.placeholder_label.grid_remove()
        self.canvas_container.grid(row=0, column=0, sticky="nsew")

        # Update UI
        self._update_button_states()
        self._update_assembly_label()
        self._update_info_panel()
        self.update_visualization()

        print(f"[ResultsPanel] Loaded {len(results)} assembly results for visualization")

    def navigate_prev(self):
        """Navigate to the previous assembly."""
        if self.results and self.current_assembly_index > 0:
            self.current_assembly_index -= 1
            self._update_assembly_label()
            self._update_info_panel()
            if self.viz_type_var.get() == "Assembly Proposal":
                self.update_visualization()

    def navigate_next(self):
        """Navigate to the next assembly."""
        if self.results and self.current_assembly_index < len(self.results) - 1:
            self.current_assembly_index += 1
            self._update_assembly_label()
            self._update_info_panel()
            if self.viz_type_var.get() == "Assembly Proposal":
                self.update_visualization()

    def update_visualization(self):
        """Update the displayed visualization based on current selector."""
        viz_type = self.viz_type_var.get()

        if viz_type == "Fragment Contours":
            self._show_fragment_contours()
        elif viz_type == "Compatibility Heatmap":
            self._show_compatibility_heatmap()
        elif viz_type == "Assembly Proposal":
            self._show_assembly_proposal()
        elif viz_type == "Convergence Plot":
            self._show_convergence_plot()

    def _show_fragment_contours(self):
        """Display fragment contours grid."""
        if not self.images or not self.contours:
            messagebox.showinfo("Info", "No fragment images loaded.")
            return

        # Import visualization function
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from visualize import draw_contour_overlay
            import cv2
            import numpy as np
        except ImportError:
            messagebox.showerror("Error", "Visualization modules not available.")
            return

        # Import matplotlib components
        from matplotlib.figure import Figure

        # Create figure
        n = len(self.images)
        cols = min(4, n)
        rows = (n + cols - 1) // cols
        fig = Figure(figsize=(cols * 3, rows * 3), dpi=100)

        for idx, (img, contour, name) in enumerate(zip(self.images, self.contours, self.fragment_names)):
            ax = fig.add_subplot(rows, cols, idx + 1)
            overlay = draw_contour_overlay(img, contour)
            rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
            ax.imshow(rgb)
            ax.set_title(name, fontsize=8)
            ax.axis('off')

        fig.suptitle("Extracted Fragment Contours", fontsize=11, y=0.98)
        fig.tight_layout()

        self.embed_figure(fig)

    def _show_compatibility_heatmap(self):
        """Display pairwise compatibility heatmap."""
        if self.compat_matrix is None:
            messagebox.showinfo("Info", "No compatibility matrix available.")
            return

        import numpy as np
        from matplotlib.figure import Figure

        # Average over segment pairs
        n_frags = self.compat_matrix.shape[0]
        summary = self.compat_matrix.mean(axis=(1, 3))

        # Create figure
        fig_size = max(4, n_frags)
        fig = Figure(figsize=(fig_size, fig_size), dpi=100)
        ax = fig.add_subplot(111)

        im = ax.imshow(summary, cmap='YlOrRd', vmin=0, vmax=1)
        fig.colorbar(im, ax=ax, label='Mean compatibility score')

        ax.set_xticks(range(n_frags))
        ax.set_yticks(range(n_frags))
        ax.set_xticklabels(self.fragment_names, rotation=45, ha='right', fontsize=8)
        ax.set_yticklabels(self.fragment_names, fontsize=8)
        ax.set_title("Pairwise Fragment Compatibility", fontsize=11)

        fig.tight_layout()

        self.embed_figure(fig)

    def _show_assembly_proposal(self):
        """Display the current assembly proposal."""
        if not self.results:
            messagebox.showinfo("Info", "No assembly results available.")
            return

        if not self.images or not self.contours:
            messagebox.showinfo("Info", "No fragment images loaded.")
            return

        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from visualize import draw_contour_overlay
            import cv2
        except ImportError:
            messagebox.showerror("Error", "Visualization modules not available.")
            return

        from matplotlib.figure import Figure

        # Get current assembly
        assembly = self.results[self.current_assembly_index]
        pairs = assembly['pairs']
        confidence = assembly['confidence']

        if not pairs:
            messagebox.showinfo("Info", "No matched pairs in this assembly.")
            return

        # Create figure showing matched pairs
        n_rows = min(len(pairs), 4)
        fig = Figure(figsize=(6, n_rows * 3), dpi=100)

        for row_idx, pair in enumerate(pairs[:n_rows]):
            for col_idx, (frag_key, seg_key) in enumerate(
                [('frag_i', 'seg_a'), ('frag_j', 'seg_b')]
            ):
                ax = fig.add_subplot(n_rows, 2, row_idx * 2 + col_idx + 1)
                frag_idx = pair[frag_key]
                overlay = draw_contour_overlay(self.images[frag_idx], self.contours[frag_idx])
                rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
                ax.imshow(rgb)
                title = f"{self.fragment_names[frag_idx]}  [seg {pair[seg_key]}]"
                ax.set_title(title, fontsize=8)
                ax.axis('off')

        fig.suptitle(
            f"Assembly #{self.current_assembly_index + 1}  —  confidence {confidence:.3f}",
            fontsize=10
        )
        fig.tight_layout()

        self.embed_figure(fig)

    def _show_convergence_plot(self):
        """Display relaxation labeling convergence plot."""
        if not self.convergence_trace:
            messagebox.showinfo("Info", "No convergence trace available.")
            return

        from matplotlib.figure import Figure

        # Create figure
        fig = Figure(figsize=(6, 3), dpi=100)
        ax = fig.add_subplot(111)

        ax.plot(
            range(1, len(self.convergence_trace) + 1),
            self.convergence_trace,
            marker='o', linewidth=1.5, markersize=3, color='steelblue',
            label='Max Δ probability'
        )
        ax.axhline(
            y=1e-4, color='tomato', linestyle='--', linewidth=1.2,
            label='Convergence threshold (1e-4)'
        )
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Max Δ probability')
        ax.set_title('Relaxation Labeling Convergence')
        ax.set_yscale('log')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        fig.tight_layout()

        self.embed_figure(fig)

    def embed_figure(self, figure):
        """
        Embed a matplotlib figure into the tkinter canvas.

        Parameters
        ----------
        figure : matplotlib.figure.Figure
            The figure to embed
        """
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        # Clear previous canvas
        if self.canvas:
            self.canvas.get_tk_widget().destroy()

        # Create new canvas
        self.current_figure = figure
        self.canvas = FigureCanvasTkAgg(figure, master=self.canvas_container)
        self.canvas.draw()

        # Pack canvas widget
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)

        # Enable mouse interactions
        self._setup_canvas_interactions()

    def _setup_canvas_interactions(self):
        """Set up mouse pan and zoom interactions for the canvas."""
        if not self.canvas:
            return

        # Store pan state
        self._pan_start = None

        def on_mouse_press(event):
            if event.button == 1 and event.inaxes:  # Left mouse button
                self._pan_start = (event.xdata, event.ydata)

        def on_mouse_release(event):
            self._pan_start = None

        def on_mouse_move(event):
            if self._pan_start and event.inaxes:
                dx = event.xdata - self._pan_start[0]
                dy = event.ydata - self._pan_start[1]

                ax = event.inaxes
                xlim = ax.get_xlim()
                ylim = ax.get_ylim()

                ax.set_xlim(xlim[0] - dx, xlim[1] - dx)
                ax.set_ylim(ylim[0] - dy, ylim[1] - dy)

                self.canvas.draw_idle()
                self._pan_start = (event.xdata, event.ydata)

        def on_scroll(event):
            if event.inaxes:
                ax = event.inaxes
                xlim = ax.get_xlim()
                ylim = ax.get_ylim()

                xdata = event.xdata
                ydata = event.ydata

                # Zoom factor
                if event.button == 'up':
                    scale_factor = 0.9
                elif event.button == 'down':
                    scale_factor = 1.1
                else:
                    return

                # Calculate new limits
                new_width = (xlim[1] - xlim[0]) * scale_factor
                new_height = (ylim[1] - ylim[0]) * scale_factor

                relx = (xlim[1] - xdata) / (xlim[1] - xlim[0])
                rely = (ylim[1] - ydata) / (ylim[1] - ylim[0])

                ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])
                ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])

                self.canvas.draw_idle()

        # Connect events
        self.canvas.mpl_connect('button_press_event', on_mouse_press)
        self.canvas.mpl_connect('button_release_event', on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', on_mouse_move)
        self.canvas.mpl_connect('scroll_event', on_scroll)

    def zoom_in(self):
        """Zoom in on the current visualization."""
        if not self.current_figure:
            return

        for ax in self.current_figure.get_axes():
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()

            xmid = (xlim[0] + xlim[1]) / 2
            ymid = (ylim[0] + ylim[1]) / 2

            xrange = (xlim[1] - xlim[0]) * 0.45
            yrange = (ylim[1] - ylim[0]) * 0.45

            ax.set_xlim(xmid - xrange, xmid + xrange)
            ax.set_ylim(ymid - yrange, ymid + yrange)

        self.canvas.draw_idle()

    def zoom_out(self):
        """Zoom out on the current visualization."""
        if not self.current_figure:
            return

        for ax in self.current_figure.get_axes():
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()

            xmid = (xlim[0] + xlim[1]) / 2
            ymid = (ylim[0] + ylim[1]) / 2

            xrange = (xlim[1] - xlim[0]) * 0.55
            yrange = (ylim[1] - ylim[0]) * 0.55

            ax.set_xlim(xmid - xrange, xmid + xrange)
            ax.set_ylim(ymid - yrange, ymid + yrange)

        self.canvas.draw_idle()

    def zoom_fit(self):
        """Reset zoom to fit the entire visualization."""
        if not self.current_figure:
            return

        for ax in self.current_figure.get_axes():
            ax.autoscale()

        self.canvas.draw_idle()

    def _update_button_states(self):
        """Update the enabled/disabled state of navigation buttons."""
        if not self.results:
            self.btn_prev.config(state=tk.DISABLED)
            self.btn_next.config(state=tk.DISABLED)
        else:
            self.btn_prev.config(
                state=tk.NORMAL if self.current_assembly_index > 0 else tk.DISABLED
            )
            self.btn_next.config(
                state=tk.NORMAL if self.current_assembly_index < len(self.results) - 1 else tk.DISABLED
            )

    def _update_assembly_label(self):
        """Update the assembly counter label."""
        if not self.results:
            self.assembly_label.config(text="No results loaded")
        else:
            self.assembly_label.config(
                text=f"Assembly {self.current_assembly_index + 1} of {len(self.results)}"
            )

    def _update_info_panel(self):
        """Update the bottom info panel with assembly statistics."""
        if not self.results:
            self.confidence_label.config(text="Confidence: --")
            self.pairs_label.config(text="Matched pairs: --")
            self.verdict_label.config(text="Verdict: --")
            return

        assembly = self.results[self.current_assembly_index]

        # Confidence
        confidence = assembly.get('confidence', 0.0)
        self.confidence_label.config(text=f"Confidence: {confidence:.4f}")

        # Matched pairs
        n_match = assembly.get('n_match', 0)
        n_weak = assembly.get('n_weak', 0)
        n_no_match = assembly.get('n_no_match', 0)
        total_pairs = len(assembly.get('pairs', []))
        self.pairs_label.config(
            text=f"Matched pairs: {n_match} MATCH / {n_weak} WEAK / {n_no_match} NO_MATCH ({total_pairs} total)"
        )

        # Verdict
        verdict = assembly.get('verdict', 'UNKNOWN')
        verdict_color = {
            'MATCH': 'green',
            'WEAK_MATCH': 'orange',
            'NO_MATCH': 'red',
            'UNKNOWN': 'gray'
        }.get(verdict, 'black')

        self.verdict_label.config(
            text=f"Verdict: {verdict}",
            foreground=verdict_color
        )

    def show_running(self):
        """Update display to show pipeline is running."""
        self.placeholder_label.config(
            text="Pipeline Running...\n\nPlease wait while fragments are being processed."
        )

    def load_results(self):
        """Load and display results from latest pipeline run."""
        output_dir = os.path.join("outputs", "results")

        # Check if output directory exists
        if not os.path.exists(output_dir):
            self.placeholder_label.config(
                text="No results found.\n\nPlease run the assembly pipeline first."
            )
            return

        # Find all result images
        try:
            # Look for assembly images
            assembly_files = sorted([
                os.path.join(output_dir, f)
                for f in os.listdir(output_dir)
                if f.startswith('assembly_') and f.endswith('.png') and 'geometric' not in f
            ])

            # Also get other visualization files
            other_files = []
            for name in ['fragment_contours.png', 'compatibility_heatmap.png', 'convergence.png']:
                filepath = os.path.join(output_dir, name)
                if os.path.exists(filepath):
                    other_files.append(filepath)

            # Combine: other visualizations first, then assemblies
            all_image_files = other_files + assembly_files

            if not all_image_files:
                self.placeholder_label.config(
                    text="No result images found in outputs/results/\n\n"
                         "The pipeline may still be running or failed."
                )
                return

            # Load images
            self.result_images = []
            self.result_paths = []

            for filepath in all_image_files:
                try:
                    if Image and ImageTk:
                        img = Image.open(filepath)
                        # Keep original size for now, will resize when displaying
                        self.result_images.append(img)
                        self.result_paths.append(filepath)
                except Exception as e:
                    print(f"Warning: Could not load {filepath}: {e}")

            if not self.result_images:
                self.placeholder_label.config(
                    text="Error loading result images.\n\nCheck that PIL/Pillow is installed."
                )
                return

            # Hide placeholder, show navigation
            self.placeholder_label.grid_remove()
            self.nav_frame.grid()
            self.canvas_frame.grid()
            self.info_frame.grid()

            # Start with first image
            self.current_index = 0
            self.display_current_image()

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.placeholder_label.config(
                text=f"Error loading results:\n\n{str(e)}\n\n{error_details[:200]}"
            )

    def display_current_image(self):
        """Display the current result image."""
        if not self.result_images or self.current_index >= len(self.result_images):
            return

        # Update label
        filename = os.path.basename(self.result_paths[self.current_index])
        self.image_label.config(text=f"Image {self.current_index + 1} of {len(self.result_images)}: {filename}")

        # Get image
        img = self.result_images[self.current_index]

        # Resize to fit canvas (max 800x600)
        display_img = img.copy()
        display_img.thumbnail((800, 600), Image.Resampling.LANCZOS)

        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(display_img)

        # Clear canvas
        self.result_canvas.delete("all")

        # Display image centered
        canvas_width = self.result_canvas.winfo_width()
        canvas_height = self.result_canvas.winfo_height()

        # Default size if canvas not yet drawn
        if canvas_width <= 1:
            canvas_width = 800
        if canvas_height <= 1:
            canvas_height = 600

        x = canvas_width // 2
        y = canvas_height // 2

        self.result_canvas.create_image(x, y, image=photo, anchor=tk.CENTER)

        # Keep reference to prevent garbage collection
        self.current_photo = photo

        # Update navigation buttons
        self.prev_button.config(state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_index < len(self.result_images) - 1 else tk.DISABLED)

        # Update info label
        self.info_label.config(text=f"Showing: {filename}")

    def show_previous(self):
        """Show previous result image."""
        if self.current_index > 0:
            self.current_index -= 1
            self.display_current_image()

    def show_next(self):
        """Show next result image."""
        if self.current_index < len(self.result_images) - 1:
            self.current_index += 1
            self.display_current_image()


class AboutPanel(ttk.Frame):
    """
    About panel for project information and documentation.

    Displays project summary, experiment results, and links to documentation.
    """

    def __init__(self, parent, app=None):
        super().__init__(parent)
        self.app = app
        self._create_ui()

    def _create_ui(self):
        """Create about panel UI."""
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create scrollable frame
        canvas = tk.Canvas(self, borderwidth=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        content_frame = ttk.Frame(canvas)

        content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Title
        title_label = ttk.Label(
            content_frame,
            text="Archaeological Fragment Reconstruction System v2.0",
            font=("Arial", 16, "bold"),
            justify=tk.CENTER
        )
        title_label.grid(row=0, column=0, pady=(20, 10), padx=20)

        # Subtitle
        subtitle_label = ttk.Label(
            content_frame,
            text="Evolutionary Optimization Experiment",
            font=("Arial", 12, "italic"),
            justify=tk.CENTER
        )
        subtitle_label.grid(row=1, column=0, pady=(0, 20), padx=20)

        # Summary section
        summary_frame = ttk.LabelFrame(content_frame, text="Project Summary", padding=15)
        summary_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)

        summary_text = (
            "This project implements an automatic system for reconstructing fragmented "
            "archaeological artifacts from photographs. The system uses computer vision "
            "algorithms including:\n\n"
            "• Gaussian blur and Otsu thresholding (Lectures 21-23)\n"
            "• Freeman chain code representation (Lecture 72)\n"
            "• Pairwise edge compatibility scoring\n"
            "• Relaxation labeling for global optimization (Lecture 53)\n"
            "• Gestalt principles for perceptual grouping (Lecture 52)\n\n"
            "The project explored 10 algorithm variants through evolutionary optimization,\n"
            "improving accuracy from 62.2% to 85.1%."
        )

        summary_label = ttk.Label(
            summary_frame,
            text=summary_text,
            justify=tk.LEFT,
            wraplength=700
        )
        summary_label.pack(anchor="w")

        # Results section
        results_frame = ttk.LabelFrame(content_frame, text="Experimental Results", padding=15)
        results_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=10)

        results_text = (
            "Best Variant: Variant 0 Iteration 2\n"
            "Overall Accuracy: 85.1%\n"
            "Positive Test Cases: 87.5% (7/8 correct)\n"
            "Negative Test Cases: 83.3% (10/12 correct)\n\n"
            "Key Improvements:\n"
            "• Enhanced color pre-checking with bimodal detection\n"
            "• Optimized hard discriminator thresholds\n"
            "• Refined gap detection for boundary quality\n"
            "• Improved ensemble voting logic\n\n"
            "See EXPERIMENT_DOCUMENTATION.md for full details."
        )

        results_label = ttk.Label(
            results_frame,
            text=results_text,
            justify=tk.LEFT,
            wraplength=700
        )
        results_label.pack(anchor="w")

        # Course info section
        course_frame = ttk.LabelFrame(content_frame, text="Course Information", padding=15)
        course_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=10)

        course_text = (
            "Course: Introduction to Computational and Biological Vision (ICBV)\n"
            "Date: April 2026\n"
            "Project Type: Final Project - Archaeological Fragment Reconstruction\n\n"
            "This implementation directly applies concepts from course lectures,\n"
            "demonstrating practical applications of computer vision theory."
        )

        course_label = ttk.Label(
            course_frame,
            text=course_text,
            justify=tk.LEFT,
            wraplength=700
        )
        course_label.pack(anchor="w")

        # Links section
        links_frame = ttk.LabelFrame(content_frame, text="Documentation", padding=15)
        links_frame.grid(row=5, column=0, sticky="ew", padx=20, pady=(10, 20))

        ttk.Button(
            links_frame,
            text="View Experiment Documentation",
            command=self._open_experiment_docs
        ).pack(pady=5, anchor="w")

        ttk.Button(
            links_frame,
            text="View README",
            command=self._open_readme
        ).pack(pady=5, anchor="w")

    def _open_experiment_docs(self):
        """Open EXPERIMENT_DOCUMENTATION.md in default viewer."""
        import webbrowser
        doc_path = os.path.join(os.path.dirname(__file__), "..", "EXPERIMENT_DOCUMENTATION.md")

        if os.path.exists(doc_path):
            webbrowser.open(f"file://{os.path.abspath(doc_path)}")
        else:
            messagebox.showerror("Error", "EXPERIMENT_DOCUMENTATION.md not found.")

    def _open_readme(self):
        """Open README.md in default viewer."""
        import webbrowser
        readme_path = os.path.join(os.path.dirname(__file__), "..", "README.md")

        if os.path.exists(readme_path):
            webbrowser.open(f"file://{os.path.abspath(readme_path)}")
        else:
            messagebox.showerror("Error", "README.md not found.")
