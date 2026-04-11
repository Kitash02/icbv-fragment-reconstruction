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

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Change to project root directory
os.chdir(script_dir)

print("=" * 70)
print(" Archaeological Fragment Reconstruction System v2.0")
print("=" * 70)
print(f"\nProject directory: {script_dir}")
print(f"Current directory: {os.getcwd()}")

# Verify we have the required directories
required_dirs = ['src', 'data', 'outputs']
missing = [d for d in required_dirs if not os.path.exists(d)]

if missing:
    print(f"\nERROR: Missing required directories: {', '.join(missing)}")
    print(f"Please ensure you are running from the project root directory.")
    sys.exit(1)

# Check if sample data exists
sample_dir = os.path.join(script_dir, 'data', 'sample')
if os.path.exists(sample_dir):
    image_files = [f for f in os.listdir(sample_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
    if image_files:
        print(f"Sample data: {len(image_files)} fragments found in data/sample/")
    else:
        print(f"Warning: No images found in data/sample/")
else:
    print(f"Warning: data/sample/ directory not found")

print("\nLaunching GUI...")
print("=" * 70)
print()

# Add src to Python path
sys.path.insert(0, os.path.join(script_dir, 'src'))

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
