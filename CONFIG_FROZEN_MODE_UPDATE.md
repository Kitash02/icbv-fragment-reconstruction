# Config.py Frozen Mode Compatibility Update

**Date:** 2026-04-11
**Project:** ICBV Fragment Reconstruction
**Task:** Update src/config.py to use path_resolver for frozen mode compatibility

---

## Summary

Modified `src/src/config.py` to use the `path_resolver` module instead of `__file__` relative paths. This change ensures the configuration system works correctly in both development and frozen (PyInstaller executable) modes.

## Changes Made

### File: `C:\Users\I763940\icbv-fragment-reconstruction\src\src\config.py`

#### 1. Added path_resolver import (lines 32-41)

**Before:**
```python
import os
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List
```

**After:**
```python
import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List

# Add parent directory to path to import path_resolver
sys.path.insert(0, str(Path(__file__).parent.parent))
from path_resolver import get_config_file
```

#### 2. Updated DEFAULT_CONFIG_PATH (line 111)

**Before:**
```python
    # Default config path relative to this file
    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'default_config.yaml'
```

**After:**
```python
    # Default config path using path_resolver for frozen mode compatibility
    DEFAULT_CONFIG_PATH = get_config_file('default_config.yaml')
```

## Why This Change?

### Problem with `__file__` relative paths:
- In development mode: `__file__` points to the actual source file location
- In frozen mode (PyInstaller): `__file__` may not work as expected
- PyInstaller extracts files to a temporary directory (`sys._MEIPASS`)
- Relative paths from `__file__` can break when bundled

### Solution with path_resolver:
- `get_config_file()` automatically handles both modes
- In dev mode: returns `<project_root>/config/<filename>`
- In frozen mode: returns `<sys._MEIPASS>/config/<filename>`
- Consistent API regardless of execution context

## Testing

### Test 1: Simple config load test
```bash
cd "C:\Users\I763940\icbv-fragment-reconstruction"
python -c "import sys; sys.path.insert(0, 'src/src'); from config import Config; c = Config(); print('Config loads OK')"
```

**Result:** ✓ PASSED
```
Config loads OK
Config path: C:\Users\I763940\icbv-fragment-reconstruction\config\default_config.yaml
Config file exists: True
```

### Test 2: Comprehensive compatibility test
```bash
cd "C:\Users\I763940\icbv-fragment-reconstruction"
python test_config_frozen_compatibility.py
```

**Result:** ✓ ALL TESTS PASSED

Test coverage:
- [OK] path_resolver import
- [OK] get_config_file function
- [OK] config module import
- [OK] Config.DEFAULT_CONFIG_PATH
- [OK] Config instantiation
- [OK] Config section access (preprocessing, chain_code, shape_descriptors, compatibility, relaxation, hard_discriminators)
- [OK] Path resolver integration

### Test 3: Parameter access verification
```bash
python -c "import sys; sys.path.insert(0, 'src/src'); from config import Config; c = Config(); print('Sample parameter: gaussian_sigma =', c.preprocessing.gaussian_sigma)"
```

**Result:** ✓ PASSED
```
Config loaded successfully
Sample parameter: gaussian_sigma = 1.5
```

## Verification

### Path Resolution Verification
```bash
python -c "import sys; sys.path.insert(0, 'src'); from path_resolver import print_diagnostics; print_diagnostics()"
```

**Output:**
```
Execution Mode: DEVELOPMENT (Python)
Bundle Root: C:\Users\I763940\icbv-fragment-reconstruction
Config Dir: C:\Users\I763940\icbv-fragment-reconstruction\config
Config Dir Exists: True
```

### Other Files Checked

Verified that other files already use path_resolver correctly:
- `src/src/gui_components.py` - ✓ Already using path_resolver
- `src/path_resolver.py` - ✓ Core path resolution module (no changes needed)

## Files Modified

1. **`src/src/config.py`** - Updated to use path_resolver
2. **`test_config_frozen_compatibility.py`** - Created comprehensive test script

## Files Verified (No Changes Needed)

1. **`src/src/gui_components.py`** - Already using path_resolver
2. **`src/path_resolver.py`** - Core module (reference implementation)

## Development Mode Compatibility

✓ All existing functionality preserved
✓ Config loads correctly in development mode
✓ All config sections accessible
✓ YAML file validation works
✓ Parameter access works (dot notation and dictionary)

## Next Steps for Frozen Mode Testing

1. Build EXE with PyInstaller:
   ```bash
   bash build_exe.sh
   ```

2. Test the executable to verify:
   - Config file loads from bundled resources
   - path_resolver correctly resolves to sys._MEIPASS
   - All config sections accessible in frozen mode
   - No FileNotFoundError exceptions

3. Verify the frozen executable can:
   - Load default_config.yaml from bundle
   - Access all configuration parameters
   - Run reconstruction pipeline successfully

## Conclusion

The config.py module has been successfully updated to use path_resolver for frozen mode compatibility. All tests pass in development mode, and the changes maintain backward compatibility with existing code. The system is now ready for PyInstaller bundling and frozen executable testing.

---

**Status:** ✓ COMPLETE
**Development Mode Tests:** ✓ ALL PASSED
**Ready for EXE Build:** ✓ YES
