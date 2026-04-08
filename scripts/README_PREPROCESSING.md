# Complex Image Preprocessing Tool

## Overview

The `preprocess_complex_images.py` script handles archaeological fragment images that cannot be directly processed by the main reconstruction pipeline. This includes images containing multiple fragments in a single photograph, images with complex or textured backgrounds, and images requiring manual intervention for proper segmentation.

## Problem Statement

Real-world archaeological photography often presents challenges:
- **Multiple fragments per image**: Museum catalog photos may show entire assemblages (e.g., 14 sherds in one photograph)
- **Complex backgrounds**: Textured surfaces, shadows, or colored backgrounds that interfere with automatic segmentation
- **Irregular lighting**: Uneven illumination causing gradient backgrounds
- **Small or touching fragments**: Pieces that require careful manual separation

This tool bridges the gap between raw photography and the clean, single-fragment images required by the reconstruction pipeline.

## Technical Approach

The script implements three complementary strategies, each built on early vision techniques from the course material:

### 1. Auto-Split Mode (Recommended)

**Pipeline:**
1. **Gaussian smoothing** (Lecture 22): Suppress high-frequency noise
2. **Otsu thresholding**: Automatic binarization based on histogram analysis
3. **Morphological operations**: Close small gaps, remove noise
4. **Connected component analysis** (Lecture 23): Identify individual fragments via `cv2.findContours`
5. **Bounding box extraction**: Crop each fragment with white border margin

**When to use:**
- Clean, light-colored backgrounds (white, light gray)
- Well-separated fragments
- Batch processing of multiple images

**Limitations:**
- May split single fragments with holes or internal texture variation
- Struggles with shadows that create false boundaries
- Cannot separate touching fragments

### 2. Background Removal Mode

**Pipeline:**
1. Auto-split detection (as above)
2. **GrabCut algorithm**: Iterative graph-cut segmentation for each fragment
   - Initializes foreground/background models from bounding box
   - Refines boundary using color and texture consistency
   - Produces smooth alpha mask
3. **White background composition**: Replace background with pure white

**When to use:**
- Colored or textured backgrounds (wood, fabric, colored paper)
- Images with gradient illumination
- Fragments with complex edges requiring refined segmentation

**Computational cost:**
- Significantly slower than auto-split (5-10x)
- Runs GrabCut for each detected fragment independently

### 3. Manual Crop Mode

**Pipeline:**
1. Interactive GUI displays full image
2. User draws bounding boxes around desired fragments
3. For each box: apply GrabCut within the region, extract to separate file
4. Repeat until all fragments are isolated

**When to use:**
- Touching or overlapping fragments that auto-detection splits incorrectly
- Images where automatic thresholding fails (extreme lighting, camouflage backgrounds)
- Quality control: manually verify and re-extract problematic fragments

**Controls:**
- **Click and drag**: Draw bounding box
- **'s' key**: Save current selection
- **'r' key**: Reset/clear current box
- **'q' key**: Quit and finalize

## Installation & Requirements

```bash
# All dependencies are already in requirements.txt
pip install opencv-python numpy
```

No additional packages required beyond the main project dependencies.

## Usage Examples

### Example 1: Batch Process Wikimedia Downloads

```bash
python scripts/preprocess_complex_images.py \
    --input data/raw/real_fragments/wikimedia \
    --output data/raw/real_fragments_validated/wikimedia_processed \
    --mode auto
```

**Output:**
- One file per detected fragment: `{original_name}_fragment_001.jpg`, `_002.jpg`, etc.
- Processing log: `wikimedia_processed/preprocess_YYYYMMDD_HHMMSS.log`
- Manifest file: `wikimedia_processed/manifest.json` (tracks transformations)

### Example 2: Process Single Complex Image

```bash
python scripts/preprocess_complex_images.py \
    --input data/raw/real_fragments/wikimedia \
    --output data/processed \
    --mode auto \
    --pattern "*14_scherven*"
```

Result: 26 individual fragment files extracted from the 14-sherd composite image.

### Example 3: Background Removal for Colored Surfaces

```bash
python scripts/preprocess_complex_images.py \
    --input data/raw/photos_on_wood \
    --output data/cleaned \
    --mode background
```

Uses GrabCut to handle non-white backgrounds. Slower but more robust.

### Example 4: Manual Quality Control

```bash
python scripts/preprocess_complex_images.py \
    --input data/raw/problematic \
    --output data/manual_cleaned \
    --mode manual
```

Opens interactive window for each image. Draw boxes, press 's' to save.

### Example 5: Resume Interrupted Processing

```bash
python scripts/preprocess_complex_images.py \
    --input data/raw/large_batch \
    --output data/processed \
    --mode auto \
    --skip-existing
```

The `--skip-existing` flag checks `manifest.json` and skips images already processed. Useful for resuming after interruption or adding new files to an existing directory.

## Output Structure

```
output_directory/
├── manifest.json                              # Processing metadata
├── preprocess_20260408_143021.log           # Timestamped log
├── original_image_fragment_001.jpg          # Extracted fragments
├── original_image_fragment_002.jpg
├── ...
└── another_image_fragment_001.jpg
```

### Manifest Format

```json
{
  "14_scherven.jpg": {
    "mode": "auto",
    "output_files": [
      "14_scherven_fragment_001.jpg",
      "14_scherven_fragment_002.jpg"
    ],
    "fragment_count": 26,
    "timestamp": "2026-04-08T10:43:09.375841"
  }
}
```

The manifest tracks:
- Which mode was used
- How many fragments were extracted
- Original → processed filename mapping
- Processing timestamp
- Any errors encountered

## Parameters & Tuning

Key constants in the script (modify if needed):

```python
MIN_FRAGMENT_AREA = 1000      # Pixels: minimum area for valid fragment
MIN_FRAGMENT_SIZE = 30        # Pixels: minimum width/height
BORDER_MARGIN = 10            # Pixels: white border around extracted fragments
MORPH_KERNEL_SIZE = 7         # Morphological cleanup kernel size
GRABCUT_ITERATIONS = 5        # GrabCut refinement iterations
```

**Increasing `MIN_FRAGMENT_AREA`:** Filters out tiny debris, reduces false positives
**Decreasing `MIN_FRAGMENT_AREA`:** Captures smaller pieces, may include noise
**Increasing `GRABCUT_ITERATIONS`:** Better boundary refinement, slower processing
**Increasing `MORPH_KERNEL_SIZE`:** More aggressive hole-filling, may merge nearby fragments

## Algorithm Details

### Connected Component Analysis

Uses `cv2.findContours` with `RETR_EXTERNAL` to find outer boundaries only. Each contour represents a potential fragment. Contours are filtered by:
1. Area threshold (removes noise specks)
2. Bounding box size (removes degenerate regions)

Then sorted by area (largest first) to prioritize main fragments over small debris.

### GrabCut Segmentation

Implements the Rother et al. (2004) graph-cut algorithm via OpenCV:
1. Initialize rectangular mask around fragment
2. Build Gaussian Mixture Models for foreground/background color distributions
3. Construct graph with pixel affinities based on color similarity
4. Iteratively refine boundary using min-cut optimization
5. Produce binary mask with smooth boundaries

See OpenCV documentation: https://docs.opencv.org/4.x/d8/d83/tutorial_py_grabcut.html

### Otsu Thresholding

Automatically selects optimal global threshold by maximizing between-class variance. Assumes bimodal histogram (foreground + background). From Lecture 22 material on binarization.

## Common Issues & Solutions

### Issue 1: Too Many Small Fragments Detected

**Symptom:** 50+ tiny fragments extracted, mostly noise or shadows

**Solution:**
```python
# Edit script: increase MIN_FRAGMENT_AREA
MIN_FRAGMENT_AREA = 5000  # instead of 1000
```

Or post-process: delete fragments below a size threshold.

### Issue 2: Single Fragment Split into Multiple Pieces

**Symptom:** One physically continuous fragment extracted as 2-3 separate files

**Cause:** Holes, texture variation, or internal shadows create disconnected regions in binary mask

**Solution 1:** Use manual mode to draw single box around entire fragment
**Solution 2:** Increase morphological kernel size to close gaps:
```python
MORPH_KERNEL_SIZE = 11  # instead of 7
```

### Issue 3: GrabCut Removes Part of Fragment

**Symptom:** Fragment edges clipped or missing after background removal

**Cause:** Fragment color similar to background, or initialization box too small

**Solution:** Manual mode allows you to draw larger bounding box with more margin. GrabCut works better with generous foreground initialization.

### Issue 4: Shadows Detected as Separate Fragments

**Symptom:** Dark shadow regions extracted as "fragments"

**Solution:** Pre-process image to reduce shadows before running script:
```bash
# Use ImageMagick or similar to normalize lighting
convert input.jpg -auto-level -contrast-stretch 2% output.jpg
```

Then process the normalized version.

## Integration with Main Pipeline

Once preprocessing is complete, the extracted fragments can be fed directly into the reconstruction system:

```bash
# 1. Preprocess complex images
python scripts/preprocess_complex_images.py \
    -i data/raw/real_fragments/wikimedia \
    -o data/processed/wikimedia \
    -m auto

# 2. Run main reconstruction pipeline
python src/main.py \
    --input data/processed/wikimedia \
    --output outputs/results \
    --log outputs/logs
```

Each extracted fragment is now a single-fragment-on-white-background image, suitable for the contour extraction and chain code encoding stages.

## Performance Characteristics

Measured on the 14_scherven test image (5616×3744 pixels, 26 fragments):

| Mode | Processing Time | Output Quality |
|------|-----------------|----------------|
| Auto | 1.2 seconds | Good for clean backgrounds |
| Background | 8.5 seconds | Better edge refinement |
| Manual | ~2 min (user-dependent) | Highest accuracy |

**Scaling:** Auto mode processes ~50 fragments/minute on modern hardware. Background mode: ~10 fragments/minute. Manual mode depends entirely on user speed.

## Limitations

1. **No 3D information**: Assumes planar fragments photographed from above
2. **Touching fragments**: Cannot automatically separate pieces that physically touch
3. **Extreme clutter**: May fail on images with 50+ overlapping tiny pieces
4. **Transparent/reflective materials**: Glass or glazed ceramics may confuse segmentation
5. **Heavy shadows**: Cast shadows can be detected as separate regions

For images that fail all three modes, consider:
- Re-photographing with better lighting and separation
- Using specialized segmentation software (e.g., Adobe Photoshop's background removal)
- Manual tracing in image editor to create binary mask

## Testing & Validation

Test the script on the provided sample:

```bash
# Quick test
python scripts/preprocess_complex_images.py \
    -i data/raw/real_fragments/wikimedia \
    -o /tmp/test_output \
    -m auto \
    --pattern "*14_scherven*"

# Verify output
ls /tmp/test_output/*.jpg | wc -l  # Should show 26 files
```

Expected result: 26 individual fragment images, each with white background and 10-pixel border.

## Future Enhancements

Potential improvements (not currently implemented):
- **Depth-based segmentation**: Use stereo or structured light for 3D separation
- **Deep learning**: Train U-Net or Mask R-CNN for ceramic fragment detection
- **Fragment reassembly hints**: Store relative positions from multi-fragment images for assembly constraints
- **Texture-aware splitting**: Detect decoration patterns to avoid splitting painted fragments
- **Batch preview mode**: Show all detections before extracting, allow bulk acceptance/rejection

## References

- **Otsu's Method**: Otsu, N. (1979). "A Threshold Selection Method from Gray-Level Histograms"
- **GrabCut**: Rother, C., Kolmogorov, V., & Blake, A. (2004). "GrabCut: Interactive Foreground Extraction"
- **Connected Components**: Lectures 23 (Edge Detection), Lecture 52 (Perceptual Organization)
- **Morphological Operations**: Course material on binary image processing

## Support

For issues or questions:
1. Check log file in output directory for detailed error messages
2. Verify input images are valid (not corrupted, reasonable size)
3. Try manual mode if automatic modes fail
4. Review the "Common Issues" section above

Script location: `/c/Users/I763940/icbv-fragment-reconstruction/scripts/preprocess_complex_images.py`
