# PyInstaller Build Instructions

## Files Created

1. **fragment_reconstruction.spec** - PyInstaller specification file
2. **build_exe.sh** - Automated build script

## Quick Build

```bash
# Option 1: Use the automated script
./build_exe.sh

# Option 2: Manual build
pip install pyinstaller
pyinstaller fragment_reconstruction.spec
```

## What Gets Bundled

### Application Files
- Entry point: `launch_gui.py`
- All modules in `src/` directory (auto-discovered)

### Data Files
- `data/sample/` - Sample fragment images for testing
- `config/` - Configuration files
- `README.md` - Main documentation
- `QUICK_START_GUI.md` - GUI quick start guide

### Hidden Imports
The spec file includes all necessary hidden imports:
- **Tkinter**: Full GUI framework including ttk, filedialog, messagebox
- **Scientific**: NumPy, SciPy (ndimage, signal, spatial)
- **Image Processing**: OpenCV (cv2), PIL/Pillow
- **Plotting**: Matplotlib with TkAgg backend
- **Configuration**: YAML, JSON

### Excluded Modules
- Testing frameworks (pytest, unittest)
- Development tools

## Output

### Directory Structure
```
dist/
└── FragmentReconstruction/
    ├── FragmentReconstruction.exe  (Main executable)
    ├── data/
    │   └── sample/                 (Sample images)
    ├── config/                     (Configuration files)
    ├── README.md                   (Documentation)
    ├── QUICK_START_GUI.md          (Quick start)
    └── [DLLs and dependencies]     (Auto-bundled libraries)
```

## Configuration Details

### Build Mode
- **Type**: One-directory distribution
- **Console**: Disabled (windowed mode)
- **Compression**: UPX enabled
- **Architecture**: Native (auto-detected)

### Benefits of One-Dir Mode
- Faster startup time
- Easier to debug
- Better performance
- Simpler dependency management

## Running the EXE

```bash
cd dist/FragmentReconstruction
./FragmentReconstruction.exe
```

## Distribution

To distribute the application:
1. Zip the entire `dist/FragmentReconstruction` folder
2. Users extract and run `FragmentReconstruction.exe`
3. No Python installation required on target machine

## Troubleshooting

### Missing Module Errors
If you encounter missing module errors, add them to `hiddenimports` in the spec file.

### Data Files Not Found
Verify the paths in the `datas` list match your directory structure.

### Large File Size
The bundled application includes:
- Python interpreter
- All libraries (NumPy, OpenCV, Matplotlib, etc.)
- Typical size: 200-400 MB

This is normal for scientific Python applications.

## Build Requirements

- Python 3.7+
- PyInstaller 5.0+
- All project dependencies installed
- Windows OS (for Windows executable)

## Clean Build

```bash
# Remove all build artifacts
rm -rf build dist
pyinstaller fragment_reconstruction.spec
```
