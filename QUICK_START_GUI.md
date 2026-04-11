# Quick Start - GUI Application

## Easiest Way to Launch

```bash
cd C:\Users\I763940\icbv-fragment-reconstruction
python launch_gui.py
```

This launcher:
- ✅ Sets the correct working directory automatically
- ✅ Verifies all required directories exist
- ✅ Checks for sample data
- ✅ Launches the GUI with proper paths

## What You'll See

```
======================================================================
 Archaeological Fragment Reconstruction System v2.0
======================================================================

Project directory: C:\Users\I763940\icbv-fragment-reconstruction
Current directory: C:\Users\I763940\icbv-fragment-reconstruction
Sample data: 5 fragments found in data/sample/

Launching GUI...
======================================================================
```

Then the GUI window opens with 4 tabs: Setup, Parameters, Results, About.

## In the GUI

1. **Click "Load Sample Data"** button (Setup tab)
   - 5 sample fragments load automatically
   - Thumbnails appear in grid
   - Message confirms: "Successfully loaded 5 sample fragments"

2. **Select Algorithm Variant** (dropdown)
   - Default: "Variant 0 Iter 2 (85.1%) ⭐ BEST"
   - Or choose from 5 other variants

3. **Click "Run Assembly"** (green button)
   - Progress bar shows status
   - Takes 2-5 minutes
   - Results appear automatically

4. **View Results** (Results tab)
   - Navigate with Prev/Next buttons
   - Zoom with +/- buttons
   - Switch visualization types

## Troubleshooting

If anything doesn't work:

```bash
python test_sample_loading.py
```

This diagnostic script checks:
- ✅ Correct directory
- ✅ Sample data exists
- ✅ Image files found
- ✅ GUI can import

See `GUI_TROUBLESHOOTING.md` for detailed help.

## Alternative Launch Methods

### Method 1: Direct Launch
```bash
cd C:\Users\I763940\icbv-fragment-reconstruction
python src/gui_main.py
```

### Method 2: CLI (Original)
```bash
python src/main.py --input data/sample --output outputs/results --log outputs/logs
```

---

**That's it! The GUI is ready to use.** 🎉
