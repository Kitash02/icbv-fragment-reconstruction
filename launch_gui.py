#!/usr/bin/env python
"""
Launcher script for Archaeological Fragment Reconstruction GUI.

This script ensures the GUI is launched from the correct directory
and that all paths are properly resolved.

Usage:
    python launch_gui.py
"""

import os
import sys
from pathlib import Path

# Detect frozen mode
if getattr(sys, 'frozen', False):
    script_dir = Path(sys._MEIPASS)
    sys.path.insert(0, str(script_dir / 'src'))
else:
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    sys.path.insert(0, str(script_dir / 'src'))

# After adding src to path, import path_resolver
from path_resolver import get_sample_data_dir, is_frozen

print("=" * 70)
print(" Archaeological Fragment Reconstruction System v2.0")
print("=" * 70)
print(f"\nProject directory: {script_dir}")
print(f"Current directory: {os.getcwd()}")
print(f"Frozen mode: {is_frozen()}")

# Simplified directory checks for frozen mode
if not (script_dir / 'src').exists():
    print("ERROR: src directory missing")
    sys.exit(1)

# Check if sample data exists
sample_dir = get_sample_data_dir()
if sample_dir.exists():
    image_files = [f for f in sample_dir.iterdir() if f.suffix.lower() in ('.png', '.jpg', '.jpeg')]
    if image_files:
        print(f"Sample data: {len(image_files)} fragments found in data/sample/")
    else:
        print(f"Warning: No images found in data/sample/")
else:
    print(f"Warning: data/sample/ directory not found")

print("\nLaunching GUI...")
print("=" * 70)
print()

# Import and run GUI
try:
    from src.gui_main import main
    main()
except ImportError as e:
    print(f"ERROR: Failed to import GUI: {e}")
    print(f"\nPlease ensure all dependencies are installed:")
    print(f"  pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
