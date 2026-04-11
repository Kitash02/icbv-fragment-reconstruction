# Path Resolver Module Documentation

**Module:** `src/path_resolver.py`
**Purpose:** Handle file paths correctly in both development and frozen (PyInstaller) modes
**Created:** 2026-04-11

---

## Overview

The `path_resolver` module provides a unified interface for resolving file paths in the ICBV Fragment Reconstruction application. It automatically detects whether the application is running as:

1. **Development mode** - Normal Python execution from source
2. **Frozen mode** - PyInstaller bundled executable (.exe)

This ensures that the application can correctly locate resources (configs, sample data) and create writable outputs (results, logs) in both environments.

---

## Core Concepts

### Bundle Root
The directory containing the application code and bundled resources.
- **Dev mode:** Project root directory (parent of `src/`)
- **Frozen mode:** PyInstaller's temporary extraction folder (`sys._MEIPASS`)

### User Base Directory
The directory for user-writable files.
- **Dev mode:** Same as bundle root (project directory)
- **Frozen mode:** `~/Documents/ICBV_FragmentReconstruction/`

### Resource Paths
Read-only files bundled with the application (configs, sample data, documentation).

### User Directories
Writable locations created automatically (output, logs, temp).

---

## API Reference

### Detection Functions

#### `is_frozen() -> bool`
Check if running as a PyInstaller frozen executable.

```python
if path_resolver.is_frozen():
    print("Running as .exe")
else:
    print("Running in development mode")
```

**Returns:** `True` if frozen, `False` otherwise

---

### Path Resolution Functions

#### `get_bundle_root() -> Path`
Get the root directory of the application bundle.

```python
root = path_resolver.get_bundle_root()
# Dev: C:\Users\...\icbv-fragment-reconstruction
# Frozen: C:\Users\...\AppData\Local\Temp\_MEI123456
```

**Returns:** Path object pointing to the bundle root

---

#### `get_resource_path(relative_path: str) -> Path`
Get absolute path to a bundled resource.

```python
config_dir = path_resolver.get_resource_path("config")
sample_img = path_resolver.get_resource_path("data/sample/fragment1.png")
```

**Parameters:**
- `relative_path` (str): Path relative to bundle root

**Returns:** Absolute Path object to the resource

**Use for:** Config files, sample data, templates, documentation

---

#### `get_user_base_dir() -> Path`
Get the base directory for user-writable files.

```python
base = path_resolver.get_user_base_dir()
# Dev: C:\Users\...\icbv-fragment-reconstruction
# Frozen: C:\Users\...\Documents\ICBV_FragmentReconstruction
```

**Returns:** Path to user base directory (created if needed)

---

### Writable Directory Functions

#### `get_output_dir() -> Path`
Get directory for output files (reconstructed images, results).

```python
output_dir = path_resolver.get_output_dir()
result_path = output_dir / f"reconstruction_{timestamp}.png"
```

**Returns:** Path to output directory (created if needed)

**Location:**
- Dev: `<project>/output/`
- Frozen: `~/Documents/ICBV_FragmentReconstruction/output/`

---

#### `get_log_dir() -> Path`
Get directory for log files.

```python
log_dir = path_resolver.get_log_dir()
log_file = log_dir / f"run_{timestamp}.log"
```

**Returns:** Path to logs directory (created if needed)

**Location:**
- Dev: `<project>/logs/`
- Frozen: `~/Documents/ICBV_FragmentReconstruction/logs/`

---

#### `get_temp_dir() -> Path`
Get directory for temporary/intermediate processing files.

```python
temp_dir = path_resolver.get_temp_dir()
temp_file = temp_dir / "processing_cache.pkl"
```

**Returns:** Path to temp directory (created if needed)

**Location:**
- Dev: `<project>/temp/`
- Frozen: `~/Documents/ICBV_FragmentReconstruction/temp/`

---

### Specific Resource Functions

#### `get_sample_data_dir() -> Path`
Get directory containing sample fragment images.

```python
sample_dir = path_resolver.get_sample_data_dir()
# Points to data/sample/
```

**Returns:** Path to sample data directory

---

#### `get_config_file(filename: str) -> Path`
Get path to a specific configuration file.

```python
settings = path_resolver.get_config_file("settings.json")
algorithms = path_resolver.get_config_file("algorithms.yaml")
```

**Parameters:**
- `filename` (str): Name of config file

**Returns:** Path to `config/{filename}`

---

#### `get_data_dir() -> Path`
Get the main data directory.

```python
data_dir = path_resolver.get_data_dir()
# Points to data/
```

**Returns:** Path to data directory

---

#### `get_executable_dir() -> Path`
Get directory containing the executable or main script.

```python
exe_dir = path_resolver.get_executable_dir()
# Frozen: Directory containing the .exe
# Dev: Project root
```

**Returns:** Path to executable directory

---

### Utility Functions

#### `ensure_user_directories() -> None`
Ensure all user-writable directories exist.

```python
# Call during application initialization
path_resolver.ensure_user_directories()
```

This creates:
- Output directory
- Log directory
- Temp directory

---

#### `get_path_diagnostics() -> dict`
Get diagnostic information about all resolved paths.

```python
diagnostics = path_resolver.get_path_diagnostics()
print(f"Is frozen: {diagnostics['is_frozen']}")
print(f"Bundle root: {diagnostics['bundle_root']}")
print(f"Output exists: {diagnostics['output_dir_exists']}")
```

**Returns:** Dictionary with keys:
- `is_frozen` (bool)
- `sys.executable` (str)
- `bundle_root` (str)
- `bundle_root_exists` (bool)
- `user_base_dir` (str)
- `user_base_dir_exists` (bool)
- `output_dir`, `log_dir`, `temp_dir` (str)
- `*_exists` for each directory (bool)
- `sample_data_dir`, `config_dir`, `data_dir`, `executable_dir`
- `sys._MEIPASS` (if frozen)

**Use for:** Debugging path issues, logging initialization state

---

#### `print_diagnostics() -> None`
Print formatted diagnostic information.

```python
path_resolver.print_diagnostics()
```

Outputs:
```
======================================================================
PATH RESOLVER DIAGNOSTICS
======================================================================
Execution Mode: DEVELOPMENT (Python)

System Information:
  sys.executable: C:\Users\...\python.exe
  ...

Bundle/Project Paths (Read-Only Resources):
  Bundle Root: C:\Users\...\icbv-fragment-reconstruction
  ...

User Paths (Writable Directories):
  Output Dir: C:\Users\...\icbv-fragment-reconstruction\output
  ...
```

**Use for:** Debugging, troubleshooting, initial setup verification

---

## Usage Examples

### Basic Usage

```python
import sys
sys.path.insert(0, 'src')
import path_resolver

# Initialize directories
path_resolver.ensure_user_directories()

# Get sample data
sample_dir = path_resolver.get_sample_data_dir()
for img_path in sample_dir.glob("*.png"):
    print(f"Found fragment: {img_path.name}")

# Save output
output_dir = path_resolver.get_output_dir()
result_path = output_dir / "reconstruction.png"
save_image(result_path)

# Create log file
log_dir = path_resolver.get_log_dir()
log_path = log_dir / f"run_{timestamp}.log"
setup_logging(log_path)
```

### Configuration Loading

```python
import json
import path_resolver

# Load configuration
config_path = path_resolver.get_config_file("settings.json")
if config_path.exists():
    with open(config_path) as f:
        config = json.load(f)
else:
    # Use defaults
    config = get_default_config()
```

### Frozen vs Development Handling

```python
import path_resolver

if path_resolver.is_frozen():
    # Running as .exe - use conservative settings
    max_fragments = 50
    enable_debug = False
else:
    # Development mode - enable extra features
    max_fragments = 100
    enable_debug = True
```

### Initialization in main.py

```python
def main():
    # Initialize path resolution
    path_resolver.ensure_user_directories()

    # Setup logging
    log_dir = path_resolver.get_log_dir()
    log_file = log_dir / f"run_{datetime.now():%Y%m%d_%H%M%S}.log"
    setup_logging(log_file)

    # Log diagnostic info
    logger.info("Application starting")
    diagnostics = path_resolver.get_path_diagnostics()
    logger.info(f"Execution mode: {'FROZEN' if diagnostics['is_frozen'] else 'DEV'}")
    logger.info(f"Bundle root: {diagnostics['bundle_root']}")

    # Continue with application logic...
```

---

## Testing

### Running Tests

```bash
# Run the test script
python test_path_resolver.py
```

### Test Coverage

The test script verifies:

1. **Frozen/dev detection** - Correctly identifies execution mode
2. **Bundle root resolution** - Points to correct directory
3. **Resource paths** - Resolves bundled resources correctly
4. **User directories** - Creates writable directories
5. **Specific functions** - All helper functions work
6. **Directory initialization** - `ensure_user_directories()` creates all folders
7. **Diagnostics** - Diagnostic functions return complete data
8. **Return types** - All functions return Path objects

### Expected Output

```
======================================================================
RUNNING PATH_RESOLVER TESTS
======================================================================

TEST 1: Basic Detection
[PASS] PASSED: Correctly detected development mode

TEST 2: Bundle Root
[PASS] PASSED: Bundle root correctly resolved

...

TEST SUMMARY
Total Tests: 8
Passed: 8
Failed: 0

[PASS] ALL TESTS PASSED
```

---

## PyInstaller Integration

### Spec File Configuration

When building with PyInstaller, ensure resources are bundled:

```python
# icbv_reconstruction.spec

a = Analysis(
    ['src/main.py'],
    ...
)

# Bundle data directories
a.datas += [
    ('config/*', 'config', 'DATA'),
    ('data/sample/*', 'data/sample', 'DATA'),
]

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    ...
)
```

### Frozen Mode Behavior

When the application runs as a frozen .exe:

1. PyInstaller extracts bundled resources to a temporary folder
2. `sys._MEIPASS` points to this temporary folder
3. `get_bundle_root()` returns `sys._MEIPASS`
4. Resources are read from the temporary folder
5. User data is written to `~/Documents/ICBV_FragmentReconstruction/`

This separation ensures:
- Bundled resources remain read-only and protected
- User outputs persist after application closes
- No write-permission issues in system directories
- Clean separation of application and user data

---

## Troubleshooting

### Issue: "File not found" in frozen mode

**Cause:** Resource not bundled in .exe

**Solution:** Add resource to spec file `datas` list:
```python
a.datas += [('path/to/resource', 'path/to/resource', 'DATA')]
```

### Issue: "Permission denied" writing output

**Cause:** Trying to write to bundle directory in frozen mode

**Solution:** Use `get_output_dir()` or `get_log_dir()` for writable paths:
```python
# Wrong - tries to write to temp extraction folder
path = path_resolver.get_bundle_root() / "output.png"

# Correct - writes to user directory
path = path_resolver.get_output_dir() / "output.png"
```

### Issue: Paths not working on Windows

**Cause:** Using string concatenation instead of Path operations

**Solution:** Use Path methods:
```python
# Wrong
path = str(root) + "/config/settings.json"

# Correct
path = root / "config" / "settings.json"
```

### Issue: Need to debug path issues

**Solution:** Run diagnostics:
```python
python -c "import sys; sys.path.insert(0, 'src'); import path_resolver; path_resolver.print_diagnostics()"
```

Or add to your code:
```python
import path_resolver
path_resolver.print_diagnostics()
```

---

## Best Practices

1. **Always use path_resolver for file paths** - Never hardcode paths
2. **Use Path objects** - Don't convert to strings unless necessary
3. **Initialize early** - Call `ensure_user_directories()` at startup
4. **Log diagnostics** - Include path info in log files for debugging
5. **Test both modes** - Test development mode and frozen .exe
6. **Document assumptions** - If code assumes a file exists, document it
7. **Handle missing files** - Check `.exists()` before reading
8. **Use appropriate functions** - Resources vs user directories

---

## Related Files

- **Module:** `C:\Users\I763940\icbv-fragment-reconstruction\src\path_resolver.py`
- **Tests:** `C:\Users\I763940\icbv-fragment-reconstruction\test_path_resolver.py`
- **Spec file:** `C:\Users\I763940\icbv-fragment-reconstruction\icbv_reconstruction.spec`

---

## Version History

- **2026-04-11:** Initial creation
  - Complete path resolution for dev/frozen modes
  - All core functions implemented
  - Comprehensive test coverage
  - Full documentation

---

## Support

For issues or questions about path resolution:

1. Run `python test_path_resolver.py` to verify basic functionality
2. Run diagnostics to check path configuration
3. Review this documentation for usage examples
4. Check PyInstaller spec file for bundled resources
