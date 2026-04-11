#!/bin/bash
# Build script for Fragment Reconstruction GUI executable
# This script automates the process of building a standalone Windows executable

set -e  # Exit on any error

echo "============================================"
echo "Fragment Reconstruction EXE Build Script"
echo "============================================"
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

echo "Python version:"
python --version
echo ""

# Install PyInstaller if not already installed
echo "Installing PyInstaller..."
pip install pyinstaller
echo ""

# Clean previous builds
echo "Cleaning previous builds..."
if [ -d "build" ]; then
    rm -rf build
    echo "  - Removed build/"
fi
if [ -d "dist" ]; then
    rm -rf dist
    echo "  - Removed dist/"
fi
echo ""

# Verify spec file exists
if [ ! -f "fragment_reconstruction.spec" ]; then
    echo "Error: fragment_reconstruction.spec not found"
    exit 1
fi

# Build the executable
echo "Building EXE with PyInstaller..."
echo "This may take several minutes..."
echo ""
pyinstaller fragment_reconstruction.spec

# Check if build was successful
if [ -d "dist/FragmentReconstruction" ]; then
    echo ""
    echo "============================================"
    echo "Build completed successfully!"
    echo "============================================"
    echo ""
    echo "Executable location: dist/FragmentReconstruction/FragmentReconstruction.exe"
    echo ""
    echo "To run the application:"
    echo "  cd dist/FragmentReconstruction"
    echo "  ./FragmentReconstruction.exe"
    echo ""
    echo "To distribute: zip the entire 'dist/FragmentReconstruction' folder"
else
    echo ""
    echo "============================================"
    echo "Build failed!"
    echo "============================================"
    echo "Please check the error messages above"
    exit 1
fi
