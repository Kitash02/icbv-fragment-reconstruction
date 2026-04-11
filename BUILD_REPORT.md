# PyInstaller Build Report
## Fragment Reconstruction Application

**Build Date:** April 11, 2026  
**PyInstaller Version:** 6.19.0  
**Python Version:** 3.11.9  
**Platform:** Windows-10-10.0.26200-SP0

---

## Build Status: SUCCESS

### Build Summary

The Windows executable has been successfully built using PyInstaller with the onedir distribution format.

### Output Location

```
C:\Users\I763940\icbv-fragment-reconstruction\dist\FragmentReconstruction\
```

### Key Files

**Executable:**
- `FragmentReconstruction.exe` (12 MB)

**Documentation:**
- `_internal/README.md` (17 KB)
- `_internal/QUICK_START_GUI.md` (2.1 KB)
- `_internal/config/README.md`

**Sample Data:**
- `_internal/data/sample/fragment_01.png` (17 KB)
- `_internal/data/sample/fragment_02.png` (12 KB)
- `_internal/data/sample/fragment_03.png` (9.7 KB)
- `_internal/data/sample/fragment_04.png` (9.0 KB)
- `_internal/data/sample/fragment_05.png` (7.7 KB)

**Configuration Files:**
- `_internal/config/default_config.yaml` (14 KB)
- `_internal/config/gui_default_preset.json`
- `_internal/config/gui_high_precision_preset.json`
- `_internal/config/gui_permissive_preset.json`

### Package Structure

```
FragmentReconstruction/
├── FragmentReconstruction.exe          # Main executable (12 MB)
└── _internal/                          # Dependencies and data
    ├── data/
    │   └── sample/                     # Sample fragment images
    ├── config/                         # Configuration files
    ├── README.md                       # Main documentation
    ├── QUICK_START_GUI.md              # Quick start guide
    ├── numpy/                          # NumPy library
    ├── scipy/                          # SciPy library
    ├── cv2/                            # OpenCV library
    ├── matplotlib/                     # Matplotlib library
    ├── PIL/                            # Pillow library
    ├── tcl8/                           # Tcl/Tk for GUI
    ├── python311.dll                   # Python runtime
    └── [other dependencies]
```

### Build Configuration

**Spec File:** `fragment_reconstruction.spec`

**Entry Point:** `launch_gui.py`

**Build Mode:** One Directory (onedir)
- Creates a folder with the EXE and all dependencies
- Easier to distribute and debug
- No extraction overhead at runtime

**Console Mode:** Disabled (windowed application)

**UPX Compression:** Enabled

### Dependencies Bundled

**Core Libraries:**
- Python 3.11.9 runtime
- tkinter (GUI framework)
- NumPy 2.2.6 (numerical computing)
- OpenCV (computer vision)
- Pillow/PIL (image processing)
- Matplotlib (visualization)
- SciPy (scientific computing)
- PyYAML (configuration)

**Hidden Imports Included:**
- tkinter.ttk
- tkinter.filedialog
- tkinter.messagebox
- tkinter.scrolledtext
- PIL._tkinter_finder
- matplotlib.backends.backend_tkagg
- scipy.ndimage
- scipy.signal
- scipy.spatial

### Build Warnings

Minor warnings about missing optional modules (expected):
- cupy.cuda (GPU acceleration - optional)
- numpy.random.RandomState (deprecated API)
- dask.typing (optional dependency)
- cupyx (optional GPU support)
- numpy_distutils (deprecated, optional)

These warnings are expected and do not affect the application functionality.

### Distribution Size

**Estimated Total Size:** ~200-300 MB (typical for scientific Python applications with NumPy, SciPy, OpenCV, and Matplotlib)

**EXE Size:** 12 MB  
**Dependencies:** ~200-300 MB in `_internal/` folder

### Verification Checklist

- [x] Build completed without errors
- [x] EXE file exists and is 12 MB
- [x] Sample data bundled in `_internal/data/sample/`
- [x] Configuration files bundled in `_internal/config/`
- [x] Documentation files included (README.md, QUICK_START_GUI.md)
- [x] All required Python libraries included
- [x] GUI libraries (Tkinter) properly bundled
- [x] Scientific libraries (NumPy, SciPy, OpenCV) included
- [x] No critical build errors

### Distribution Instructions

To distribute the application:

1. **Zip the entire folder:**
   ```bash
   cd dist
   zip -r FragmentReconstruction.zip FragmentReconstruction/
   ```

2. **Share with users:**
   - Users extract the ZIP file
   - Run `FragmentReconstruction.exe`
   - No Python installation required

3. **System Requirements:**
   - Windows 10/11 (64-bit)
   - ~300 MB disk space
   - No additional dependencies needed

### Testing Recommendations

Before distribution, test the executable:

1. Run the EXE on a clean Windows system (without Python installed)
2. Verify the GUI launches correctly
3. Test loading sample fragments
4. Test the reconstruction pipeline
5. Verify configuration presets work
6. Check that output files are created correctly

### Notes

- The application is built as a windowed application (console=False)
- All data files and configurations are bundled automatically
- The `_internal` folder must stay with the EXE file
- File size is appropriate for scientific Python applications with GUI

---

**Build Log:** `build.log` (in project root)  
**Warnings Log:** `build/fragment_reconstruction/warn-fragment_reconstruction.txt`

**Status:** Ready for distribution and testing
