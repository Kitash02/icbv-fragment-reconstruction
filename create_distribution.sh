#!/bin/bash
# Package creation script for Fragment Reconstruction v2.0
# This script creates the final distribution ZIP file

set -e

echo "============================================"
echo "Fragment Reconstruction v2.0"
echo "Distribution Package Creator"
echo "============================================"
echo ""

# Configuration
DIST_DIR="dist/FragmentReconstruction"
OUTPUT_NAME="FragmentReconstruction_v2.0_Windows_x64.zip"
PROJECT_ROOT="/c/Users/I763940/icbv-fragment-reconstruction"

cd "$PROJECT_ROOT"

# Verify dist directory exists
if [ ! -d "$DIST_DIR" ]; then
    echo "ERROR: Distribution directory not found: $DIST_DIR"
    echo "Please run build_exe.sh first to create the EXE package"
    exit 1
fi

# Verify EXE exists
if [ ! -f "$DIST_DIR/FragmentReconstruction.exe" ]; then
    echo "ERROR: FragmentReconstruction.exe not found in $DIST_DIR"
    echo "Please run build_exe.sh first to create the EXE package"
    exit 1
fi

echo "Found distribution directory: $DIST_DIR"
echo "Found executable: FragmentReconstruction.exe"
echo ""

# Create README_INSTALL.txt for the distribution
echo "Creating README_INSTALL.txt..."
cat > "$DIST_DIR/README_INSTALL.txt" << 'EOF'
Fragment Reconstruction v2.0 - Windows
======================================

INSTALLATION:
1. Extract this ZIP file to any folder on your computer
2. Open the FragmentReconstruction folder
3. Double-click FragmentReconstruction.exe to launch

GETTING STARTED:
- Sample data is included - click "Load Sample Data" in the GUI
- See QUICK_START_GUI.md (in _internal folder) for detailed instructions
- See README.md (in _internal folder) for full documentation

SYSTEM REQUIREMENTS:
- Windows 10 or Windows 11 (64-bit)
- 4GB RAM minimum (8GB recommended for large datasets)
- 500MB free disk space
- Display resolution: 1280x720 or higher

NO PYTHON INSTALLATION REQUIRED
All dependencies are bundled in this package.

RUNNING THE APPLICATION:
Simply double-click FragmentReconstruction.exe

If Windows Defender shows a warning:
1. Click "More info"
2. Click "Run anyway"
   (This is normal for unsigned applications)

FEATURES:
- Load fragment images (PNG, JPG)
- Automatic fragment reconstruction
- Visual results display
- Configurable parameters
- Built-in sample data

DOCUMENTATION:
- README.md - Full project documentation
- QUICK_START_GUI.md - Quick start guide
- config/README.md - Configuration guide

SUPPORT:
For issues or questions, please refer to the documentation
or contact the development team.

VERSION: 2.0
BUILD DATE: 2026-04-11
PLATFORM: Windows x64
EOF

echo "Created README_INSTALL.txt"
echo ""

# Check if zip command is available
if ! command -v zip &> /dev/null; then
    echo "ERROR: 'zip' command not found"
    echo "Please install zip utility or create ZIP manually"
    echo ""
    echo "Manual creation on Windows:"
    echo "1. Right-click the FragmentReconstruction folder"
    echo "2. Select 'Send to' -> 'Compressed (zipped) folder'"
    echo "3. Rename to: $OUTPUT_NAME"
    exit 1
fi

# Create the ZIP file
echo "Creating distribution ZIP file..."
echo "This may take a minute..."
cd dist

# Remove old ZIP if exists
if [ -f "$OUTPUT_NAME" ]; then
    echo "Removing old ZIP file..."
    rm -f "$OUTPUT_NAME"
fi

# Create new ZIP
zip -r -q "$OUTPUT_NAME" FragmentReconstruction/

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "Package created successfully!"
    echo "============================================"
    echo ""

    # Get file size
    FILESIZE=$(ls -lh "$OUTPUT_NAME" | awk '{print $5}')

    echo "Distribution package: dist/$OUTPUT_NAME"
    echo "Package size: $FILESIZE"
    echo ""

    echo "Contents:"
    echo "  - FragmentReconstruction.exe (main application)"
    echo "  - Sample data (5 fragment images)"
    echo "  - Configuration files (4 presets)"
    echo "  - Documentation (README.md, QUICK_START_GUI.md)"
    echo "  - README_INSTALL.txt (installation instructions)"
    echo ""

    echo "DISTRIBUTION READY ✓"
    echo ""
    echo "Next steps:"
    echo "1. Test the package on a clean Windows machine (recommended)"
    echo "2. Share the ZIP file with end users"
    echo "3. Users simply extract and run FragmentReconstruction.exe"
    echo ""
else
    echo ""
    echo "============================================"
    echo "Package creation failed!"
    echo "============================================"
    echo ""
    echo "Please check the error messages above"
    echo "You may need to create the ZIP manually"
    exit 1
fi
