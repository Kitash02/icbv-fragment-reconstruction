"""
Quick test to verify sample data loading in GUI.
Run this from project root: python test_sample_loading.py
"""

import os
import sys

# Add src to path
sys.path.insert(0, 'src')

print("=" * 60)
print("TESTING SAMPLE DATA LOADING")
print("=" * 60)

# Check current directory
cwd = os.getcwd()
print(f"\n1. Current working directory: {cwd}")

# Check if we're in the right place
expected_dirs = ['src', 'data', 'outputs']
missing = [d for d in expected_dirs if not os.path.exists(d)]

if missing:
    print(f"\nERROR: Not in project root directory!")
    print(f"   Missing directories: {missing}")
    print(f"\n   Please run from project root:")
    print(f"   cd C:/Users/I763940/icbv-fragment-reconstruction")
    print(f"   python test_sample_loading.py")
    sys.exit(1)

print("[OK] In correct project directory")

# Check data/sample exists
sample_dir = os.path.join(cwd, 'data', 'sample')
print(f"\n2. Sample directory: {sample_dir}")
print(f"   Exists: {os.path.exists(sample_dir)}")

if not os.path.exists(sample_dir):
    print(f"ERROR: Sample directory not found!")
    sys.exit(1)

print("[OK] Sample directory found")

# Check for image files
image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'}
all_files = os.listdir(sample_dir)
image_files = [
    f for f in all_files
    if os.path.isfile(os.path.join(sample_dir, f)) and
    os.path.splitext(f)[1].lower() in image_extensions
]

print(f"\n3. Files in sample directory:")
print(f"   Total files: {len(all_files)}")
print(f"   Image files: {len(image_files)}")

if image_files:
    print(f"\n   Images found:")
    for img in image_files:
        full_path = os.path.join(sample_dir, img)
        size = os.path.getsize(full_path)
        print(f"      - {img} ({size:,} bytes)")
    print(f"\n[OK] Sample images ready to load!")
else:
    print(f"ERROR: No image files found in {sample_dir}")
    print(f"   Files present: {all_files}")
    sys.exit(1)

# Test GUI component import
print(f"\n4. Testing GUI component import...")
try:
    from gui_components import SetupPanel
    print("[OK] SetupPanel imported successfully")
except ImportError as e:
    print(f"ERROR importing SetupPanel: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("SUCCESS: All checks passed - Sample data is ready!")
print("=" * 60)
print("\nYou can now run the GUI:")
print("   python src/gui_main.py")
print("\nThen click 'Load Sample Data' button in the Setup tab.")
print("=" * 60)
