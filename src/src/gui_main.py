"""
GUI Main Application - Archaeological Fragment Reconstruction System v2.0

This module provides a tkinter-based desktop interface for the fragment
reconstruction pipeline. It wraps the existing CLI implementation (src/main.py)
with a user-friendly graphical interface allowing interactive parameter tuning,
algorithm variant selection, and real-time progress monitoring.

Course mapping: This GUI component does not correspond to a specific lecture
but provides accessibility to the core algorithms implemented in the project.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from path_resolver import get_resource_path, get_docs_file

try:
    from gui_components import SetupPanel, ParametersPanel, ResultsPanel, AboutPanel
except ImportError:
    # Components not yet created - show placeholder
    SetupPanel = ParametersPanel = ResultsPanel = AboutPanel = None


class FragmentReconstructionApp(tk.Tk):
    """
    Main application window for archaeological fragment reconstruction.

    Provides tabbed interface with:
    - Setup: Fragment loading and algorithm variant selection
    - Parameters: Interactive threshold and appearance power tuning
    - Results: Visualization of assembly proposals and metrics
    - About: Project information and experiment summary
    """

    def __init__(self):
        super().__init__()

        self.title("Archaeological Fragment Reconstruction v2.0")
        self.geometry("1200x800")

        # Configure window icon (if available)
        try:
            icon_path = get_resource_path("assets/icon.png")
            if icon_path.exists():
                icon = tk.PhotoImage(file=str(icon_path))
                self.iconphoto(True, icon)
        except Exception:
            pass  # Icon not critical

        # Configure grid weight for responsive layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create menu bar
        self._create_menu_bar()

        # Create main notebook (tabbed interface)
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Create tabs
        self._create_tabs()

        # Center window on screen
        self._center_window()

        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_menu_bar(self):
        """Create menu bar with File and Help menus."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Fragment Folder...", command=self._load_fragments)
        file_menu.add_separator()
        file_menu.add_command(label="Load Configuration...", command=self._load_config)
        file_menu.add_command(label="Save Configuration...", command=self._save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="View Documentation", command=self._open_docs)
        help_menu.add_command(label="View Experiment Report", command=self._open_experiment_docs)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about)

    def _create_tabs(self):
        """Create all tab panels."""

        # Check if components are available
        if SetupPanel is None:
            # Placeholder tabs while components are being developed
            self._create_placeholder_tabs()
            return

        # Setup Tab
        try:
            self.setup_panel = SetupPanel(self.notebook, app=self)
            self.notebook.add(self.setup_panel, text="Setup")
        except Exception as e:
            print(f"Warning: Could not create Setup panel: {e}")
            self.setup_panel = self._create_placeholder("Setup panel coming soon...")
            self.notebook.add(self.setup_panel, text="Setup")

        # Parameters Tab
        try:
            self.params_panel = ParametersPanel(self.notebook, app=self)
            self.notebook.add(self.params_panel, text="Parameters")
        except Exception as e:
            print(f"Warning: Could not create Parameters panel: {e}")
            self.params_panel = self._create_placeholder("Parameters panel coming soon...")
            self.notebook.add(self.params_panel, text="Parameters")

        # Results Tab
        try:
            self.results_panel = ResultsPanel(self.notebook, app=self)
            self.notebook.add(self.results_panel, text="Results")
        except Exception as e:
            print(f"Warning: Could not create Results panel: {e}")
            self.results_panel = self._create_placeholder("Results panel coming soon...")
            self.notebook.add(self.results_panel, text="Results")

        # About Tab
        try:
            self.about_panel = AboutPanel(self.notebook, app=self)
            self.notebook.add(self.about_panel, text="About")
        except Exception as e:
            print(f"Warning: Could not create About panel: {e}")
            self.about_panel = self._create_placeholder("About panel coming soon...")
            self.notebook.add(self.about_panel, text="About")

    def _create_placeholder_tabs(self):
        """Create placeholder tabs during development."""
        tab_names = ["Setup", "Parameters", "Results", "About"]
        for name in tab_names:
            frame = self._create_placeholder(f"{name} panel will be implemented soon...")
            self.notebook.add(frame, text=name)

    def _create_placeholder(self, message):
        """Create a placeholder frame with centered message."""
        frame = ttk.Frame(self.notebook)
        label = ttk.Label(frame, text=message, font=("Arial", 14))
        label.place(relx=0.5, rely=0.5, anchor="center")
        return frame

    def _center_window(self):
        """Center window on screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def _load_fragments(self):
        """Menu callback to load fragment folder."""
        if hasattr(self, 'setup_panel') and hasattr(self.setup_panel, 'browse_folder'):
            self.setup_panel.browse_folder()
        else:
            messagebox.showinfo("Info", "Please use the Setup tab to load fragments.")

    def _load_config(self):
        """Menu callback to load configuration from file."""
        if hasattr(self, 'params_panel') and hasattr(self.params_panel, 'load_config'):
            self.params_panel.load_config()
        else:
            messagebox.showinfo("Info", "Configuration loading not yet implemented.")

    def _save_config(self):
        """Menu callback to save configuration to file."""
        if hasattr(self, 'params_panel') and hasattr(self.params_panel, 'save_config'):
            self.params_panel.save_config()
        else:
            messagebox.showinfo("Info", "Configuration saving not yet implemented.")

    def _open_docs(self):
        """Open README.md in default viewer."""
        import webbrowser
        readme_path = get_docs_file("README.md")
        if readme_path:
            webbrowser.open(f"file://{readme_path}")
        else:
            messagebox.showerror("Error", "README.md not found")

    def _open_experiment_docs(self):
        """Open EXPERIMENT_DOCUMENTATION.md in default viewer."""
        import webbrowser
        doc_path = get_docs_file("EXPERIMENT_DOCUMENTATION.md")
        if doc_path:
            webbrowser.open(f"file://{doc_path}")
        else:
            messagebox.showerror("Error", "EXPERIMENT_DOCUMENTATION.md not found")

    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            "Archaeological Fragment Reconstruction System v2.0\n\n"
            "Evolutionary optimization experiment:\n"
            "• Tested 10 algorithm variants\n"
            "• Improved accuracy from 62.2% → 85.1%\n"
            "• Best: Variant 0 Iteration 2 (87.5% pos / 83.3% neg)\n\n"
            "Course: Introduction to Computational and Biological Vision\n"
            "Date: April 2026\n\n"
            "View full documentation via Help → View Experiment Report"
        )

    def _on_close(self):
        """Handle window close event."""
        # Check if pipeline is running
        if hasattr(self, 'setup_panel') and hasattr(self.setup_panel, 'is_running'):
            if self.setup_panel.is_running():
                response = messagebox.askyesno(
                    "Confirm Exit",
                    "Pipeline is currently running. Are you sure you want to exit?"
                )
                if not response:
                    return

        self.quit()
        self.destroy()


def main():
    """
    Launch the GUI application.

    Creates and starts the tkinter main event loop for the fragment
    reconstruction system GUI.
    """
    app = FragmentReconstructionApp()
    app.mainloop()


if __name__ == "__main__":
    main()
