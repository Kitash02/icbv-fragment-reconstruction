# GUI Sample Data Loading - Troubleshooting Guide

## Issue: "GUI can't find samples"

### Root Cause
The GUI uses Python's `__file__` variable to determine the project root, but this can fail if:
1. The GUI is launched from the wrong directory
2. Python is using compiled .pyc files
3. The working directory is not the project root

### Solution 1: Use the Launcher Script (RECOMMENDED)

```bash
cd C:\Users\I763940\icbv-fragment-reconstruction
python launch_gui.py
```

The launcher script:
- ✓ Automatically sets the correct working directory
- ✓ Verifies all required directories exist
- ✓ Checks for sample data before launching
- ✓ Provides clear error messages if something is wrong

### Solution 2: Always Launch from Project Root

```bash
# CORRECT - Launch from project root
cd C:\Users\I763940\icbv-fragment-reconstruction
python src/gui_main.py

# WRONG - Don't launch from src directory
cd C:\Users\I763940\icbv-fragment-reconstruction\src
python gui_main.py  # This will fail!
```

### Solution 3: Test Before Launching GUI

Run the test script to verify everything is set up correctly:

```bash
cd C:\Users\I763940\icbv-fragment-reconstruction
python test_sample_loading.py
```

This will check:
- ✓ Current working directory
- ✓ Required directories (src, data, outputs)
- ✓ Sample data directory existence
- ✓ Image files in sample directory
- ✓ GUI component imports

## How the Path Resolution Works

The GUI uses **4 fallback methods** to find the sample data:

### Method 1: Relative to __file__
```python
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sample_dir = os.path.join(project_root, "data", "sample")
```

### Method 2: From current working directory
```python
sample_dir = os.path.abspath(os.path.join(os.getcwd(), "data", "sample"))
```

### Method 3: Direct relative path
```python
sample_dir = os.path.abspath("data/sample")
```

### Method 4: One level up
```python
sample_dir = os.path.abspath("../data/sample")
```

If **all 4 methods fail**, the GUI shows a detailed error message with:
- All paths that were tried
- Current working directory
- Script directory
- Instructions to fix the issue

## Verify Sample Data Exists

Run this command to check:

```bash
ls -la C:/Users/I763940/icbv-fragment-reconstruction/data/sample/
```

You should see:
```
fragment_01.png  (17,115 bytes)
fragment_02.png  (11,461 bytes)
fragment_03.png   (9,906 bytes)
fragment_04.png   (9,158 bytes)
fragment_05.png   (7,866 bytes)
```

## Browse Option Not Finding data/ Folder

### Issue
When clicking "Browse Folder..." the dialog doesn't show the data/ directory.

### Root Cause
Same as above - the browse dialog's `initialdir` parameter uses the same path resolution logic.

### Solution
1. **Use launcher script** (sets working directory correctly)
2. **Or manually navigate** in the dialog:
   - The dialog opens
   - Navigate up to project root if needed
   - Open `data/` folder
   - Select `sample/` or `examples/` folder

## Quick Diagnostic Commands

### Check Current Directory
```bash
python -c "import os; print(os.getcwd())"
```
Should output: `C:\Users\I763940\icbv-fragment-reconstruction`

### Check Sample Directory Exists
```bash
python -c "import os; print(os.path.exists('data/sample'))"
```
Should output: `True`

### List Sample Files
```bash
python -c "import os; print(os.listdir('data/sample'))"
```
Should output: `['create_fragments.py', 'fragment_01.png', 'fragment_02.png', ...]`

### Test Path Resolution
```bash
python -c "
import os
sample = os.path.abspath('data/sample')
print(f'Sample dir: {sample}')
print(f'Exists: {os.path.exists(sample)}')
print(f'Files: {len([f for f in os.listdir(sample) if f.endswith(\".png\")])} PNG files')
"
```

## Error Messages Explained

### "Sample Data Not Found"
**Cause**: GUI tried all 4 path resolution methods and none found the data/sample directory.

**Fix**:
1. Verify you're in the project root: `cd C:\Users\I763940\icbv-fragment-reconstruction`
2. Use the launcher: `python launch_gui.py`
3. Or run test script first: `python test_sample_loading.py`

### "No Images Found"
**Cause**: The data/sample directory exists but contains no image files.

**Fix**:
1. Check directory contents: `ls data/sample/`
2. Verify PNG files exist
3. Re-run setup if needed: `python setup_examples.py`

### "Failed to load fragments"
**Cause**: Exception occurred while reading image files (permissions, corruption, etc.).

**Fix**:
1. Check file permissions: `ls -la data/sample/`
2. Try opening images manually to verify they're not corrupted
3. Check error message for specific file that failed

## Best Practices

### ✅ DO:
- Always launch from project root
- Use the launcher script for convenience
- Run test_sample_loading.py before reporting issues
- Check working directory if something fails

### ❌ DON'T:
- Launch from src/ directory
- Move or rename the data/ folder
- Run from arbitrary directories

## Quick Fix Checklist

If the GUI can't find samples:

1. [ ] Close the GUI
2. [ ] Open terminal/command prompt
3. [ ] Navigate to project root: `cd C:\Users\I763940\icbv-fragment-reconstruction`
4. [ ] Verify location: `dir` (should see src/, data/, outputs/)
5. [ ] Run test: `python test_sample_loading.py`
6. [ ] If test passes, use launcher: `python launch_gui.py`
7. [ ] In GUI, click "Load Sample Data" button
8. [ ] Verify 5 fragments load with thumbnails

## Still Not Working?

If you've followed all the steps and it still doesn't work:

1. Run the diagnostic script:
   ```bash
   python test_sample_loading.py > diagnosis.txt 2>&1
   ```

2. Check the output in `diagnosis.txt`

3. Look for the specific error message

4. The error message will show:
   - All paths that were tried
   - Which path should have worked
   - What your current working directory is
   - Exactly what command to run to fix it

## Summary

**The key to fixing "can't find samples" is simple:**

```bash
# Navigate to project root
cd C:\Users\I763940\icbv-fragment-reconstruction

# Use the launcher script
python launch_gui.py

# OR launch directly (if in project root)
python src/gui_main.py
```

**The GUI will always work if launched from the project root directory.**
