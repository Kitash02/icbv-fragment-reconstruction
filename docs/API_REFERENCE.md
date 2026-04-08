# API Reference
**Archaeological Fragment Reconstruction System**
**Version**: 1.0
**Last Updated**: 2026-04-08

---

## Table of Contents

1. [Overview](#overview)
2. [Main Pipeline](#main-pipeline)
3. [Preprocessing Module](#preprocessing-module)
4. [Chain Code Module](#chain-code-module)
5. [Compatibility Module](#compatibility-module)
6. [Relaxation Module](#relaxation-module)
7. [Shape Descriptors Module](#shape-descriptors-module)
8. [Visualization Module](#visualization-module)
9. [Assembly Renderer Module](#assembly-renderer-module)
10. [Hard Discriminators Module](#hard-discriminators-module)
11. [Ensemble Voting Module](#ensemble-voting-module)
12. [Type Definitions](#type-definitions)

---

## Overview

This API reference documents all public functions in the Archaeological Fragment Reconstruction System. The system is organized into 10 modules, each handling a specific stage of the reconstruction pipeline.

### Module Organization

```
src/
├── main.py                   # Pipeline orchestration
├── preprocessing.py          # Image loading and boundary extraction
├── chain_code.py            # Freeman chain code encoding
├── compatibility.py         # Pairwise edge scoring
├── relaxation.py            # Assembly optimization
├── shape_descriptors.py     # Fourier and PCA descriptors
├── visualize.py             # Result rendering
├── assembly_renderer.py     # Geometric assembly visualization
├── hard_discriminators.py   # Fast rejection criteria
└── ensemble_voting.py       # Multi-discriminator voting
```

### Import Examples

```python
# Import preprocessing
from preprocessing import preprocess_fragment

# Import chain code
from chain_code import encode_fragment, normalize_chain_code

# Import compatibility
from compatibility import build_compatibility_matrix

# Import relaxation
from relaxation import run_relaxation, extract_top_assemblies

# Import visualization
from visualize import render_fragment_grid, render_compatibility_heatmap
```

---

## Main Pipeline

**Module**: `src/main.py`

The main pipeline orchestrates the entire reconstruction process from image loading to result rendering.

### Functions

#### `run_pipeline(args: argparse.Namespace) -> None`

Execute the full reconstruction pipeline.

**Parameters**:
- `args` (`argparse.Namespace`): Command-line arguments containing:
  - `input` (str): Path to folder containing fragment images
  - `output` (str): Path to output folder for results
  - `log` (str): Path to folder for log files

**Returns**: None (writes results to disk)

**Side Effects**:
- Creates timestamped log file in `args.log`
- Writes rendered images to `args.output`
- Prints `[RESULT]` verdict to console

**Example**:
```python
import argparse
from main import run_pipeline

args = argparse.Namespace(
    input='data/sample',
    output='outputs/results',
    log='outputs/logs'
)
run_pipeline(args)
```

**Workflow**:
1. Load and preprocess fragment images
2. Extract chain codes and segment boundaries
3. Build compatibility matrix
4. Run relaxation labeling
5. Extract top assemblies
6. Render results

---

#### `detect_mixed_source_fragments(images: list) -> tuple`

Detect whether fragments come from multiple source images via color analysis.

**Parameters**:
- `images` (`list[np.ndarray]`): List of BGR fragment images

**Returns**: `tuple[bool, float, float]`
- `is_mixed` (bool): True if bimodal color distribution detected
- `min_bc` (float): Minimum pairwise Bhattacharyya coefficient
- `max_gap` (float): Largest gap in sorted BC values

**Algorithm**:
1. Compute pairwise Bhattacharyya coefficients for all image pairs
2. Sort coefficients and detect bimodal structure
3. Return True if gap > threshold and low group < threshold

**Example**:
```python
from main import detect_mixed_source_fragments
import cv2

images = [cv2.imread(f'fragment_{i}.png') for i in range(5)]
is_mixed, min_bc, gap = detect_mixed_source_fragments(images)

if is_mixed:
    print(f"Mixed sources detected: gap={gap:.3f}, min_BC={min_bc:.3f}")
```

---

#### `setup_logging(log_dir: str) -> logging.Logger`

Configure file and console logging with timestamped log file.

**Parameters**:
- `log_dir` (str): Directory for log files

**Returns**: `logging.Logger` - Configured logger instance

**Side Effects**:
- Creates `log_dir` if it doesn't exist
- Creates timestamped log file: `run_YYYYMMDD_HHMMSS.log`

**Example**:
```python
from main import setup_logging

logger = setup_logging('outputs/logs')
logger.info("Pipeline started")
```

---

#### `collect_fragment_paths(input_dir: str) -> list`

Collect all image file paths from input directory.

**Parameters**:
- `input_dir` (str): Directory containing fragment images

**Returns**: `list[Path]` - Sorted list of image file paths

**Raises**:
- `FileNotFoundError`: If no images found in directory

**Supported Formats**: `.png`, `.jpg`, `.jpeg`, `.bmp`

**Example**:
```python
from main import collect_fragment_paths

paths = collect_fragment_paths('data/sample')
print(f"Found {len(paths)} fragment images")
```

---

#### `build_arg_parser() -> argparse.ArgumentParser`

Build command-line argument parser for the main pipeline.

**Returns**: `argparse.ArgumentParser` - Configured parser

**Arguments**:
- `--input` (required): Input folder path
- `--output` (default: `outputs/results`): Output folder path
- `--log` (default: `outputs/logs`): Log folder path

**Example**:
```python
from main import build_arg_parser

parser = build_arg_parser()
args = parser.parse_args(['--input', 'data/sample'])
```

---

## Preprocessing Module

**Module**: `src/preprocessing.py`

Implements the early vision pipeline (Lectures 21-23): Gaussian smoothing, edge detection, thresholding, and contour extraction.

### Functions

#### `preprocess_fragment(path: str) -> tuple`

Full preprocessing pipeline for a single fragment image.

**Parameters**:
- `path` (str): Path to fragment image file

**Returns**: `tuple[np.ndarray, np.ndarray]`
- `image` (np.ndarray): Original BGR image
- `contour` (np.ndarray): Extracted boundary as (N, 2) array of (x, y) coordinates

**Algorithm**:
1. Load image (handles both RGBA and BGR)
2. If RGBA: use alpha channel as mask (exact for synthetic fragments)
3. Otherwise: Gaussian blur → Canny or Otsu threshold → morphological cleanup
4. Extract largest contour with `CHAIN_APPROX_NONE` (preserves all boundary pixels)

**Raises**:
- `FileNotFoundError`: If image file doesn't exist
- `ValueError`: If no contour found or contour too small

**Example**:
```python
from preprocessing import preprocess_fragment

image, contour = preprocess_fragment('fragment_01.png')
print(f"Contour: {len(contour)} points")
```

---

#### `load_image(path: str) -> np.ndarray`

Load fragment image from disk as BGR numpy array.

**Parameters**:
- `path` (str): Image file path

**Returns**: `np.ndarray` - BGR image (H, W, 3)

**Raises**:
- `FileNotFoundError`: If image cannot be loaded

---

#### `apply_gaussian_blur(image: np.ndarray) -> np.ndarray`

Convert to grayscale and apply Gaussian smoothing (Lecture 22).

**Parameters**:
- `image` (np.ndarray): BGR image

**Returns**: `np.ndarray` - Blurred grayscale image

**Algorithm**: Gaussian kernel (5×5), σ=1.5

---

#### `compute_sobel_magnitude(blurred: np.ndarray) -> np.ndarray`

Compute Sobel gradient magnitude map (Lecture 23).

**Parameters**:
- `blurred` (np.ndarray): Grayscale image

**Returns**: `np.ndarray` - Normalized gradient magnitude [0, 255]

**Algorithm**: M = sqrt(Gx² + Gy²), normalized to [0, 255]

---

#### `canny_silhouette(blurred: np.ndarray) -> np.ndarray`

Detect fragment boundary with Canny edge detector (Lecture 23).

**Parameters**:
- `blurred` (np.ndarray): Grayscale image

**Returns**: `np.ndarray` - Binary silhouette mask or None if failed

**Algorithm**:
1. Automatic threshold selection from median intensity
2. Low:high ratio = 1:3 (Lecture 23 recommendation)
3. Flood-fill from corners to create solid mask

---

#### `detect_background_brightness(image: np.ndarray) -> float`

Estimate background brightness by sampling image corners.

**Parameters**:
- `image` (np.ndarray): Grayscale image

**Returns**: `float` - Mean corner brightness [0, 255]

**Usage**: Determines whether to use THRESH_BINARY or THRESH_BINARY_INV

---

#### `otsu_threshold(blurred: np.ndarray, light_background: bool) -> np.ndarray`

Apply Otsu's global binarization.

**Parameters**:
- `blurred` (np.ndarray): Grayscale image
- `light_background` (bool): True if background is lighter than fragment

**Returns**: `np.ndarray` - Binary mask

---

#### `adaptive_threshold(blurred: np.ndarray, light_background: bool) -> np.ndarray`

Apply local adaptive binarization for uneven illumination.

**Parameters**:
- `blurred` (np.ndarray): Grayscale image
- `light_background` (bool): True if background is lighter than fragment

**Returns**: `np.ndarray` - Binary mask

**Algorithm**: Gaussian-weighted adaptive threshold, block size=25, C=6

---

#### `morphological_cleanup(binary_mask: np.ndarray) -> np.ndarray`

Apply closing then opening to clean binary mask.

**Parameters**:
- `binary_mask` (np.ndarray): Binary silhouette mask

**Returns**: `np.ndarray` - Cleaned binary mask

**Algorithm**:
- Closing (2 iterations): fills small holes
- Opening (1 iteration): removes noise spurs
- Kernel: 7×7 ellipse

---

#### `best_binary_mask(blurred: np.ndarray, light_background: bool) -> np.ndarray`

Choose binarization strategy that yields largest clean region.

**Parameters**:
- `blurred` (np.ndarray): Grayscale image
- `light_background` (bool): True if background is lighter

**Returns**: `np.ndarray` - Best binary mask (Otsu or adaptive)

---

#### `extract_largest_contour(binary_mask: np.ndarray) -> np.ndarray`

Extract outer boundary of largest connected region.

**Parameters**:
- `binary_mask` (np.ndarray): Binary silhouette mask

**Returns**: `np.ndarray` - Contour points as (N, 2) array

**Raises**:
- `ValueError`: If no contours found or largest too small

**Algorithm**: Uses `CHAIN_APPROX_NONE` to retain every boundary pixel

---

#### `alpha_channel_mask(image_bgra: np.ndarray) -> np.ndarray`

Extract binary silhouette from RGBA image's alpha channel.

**Parameters**:
- `image_bgra` (np.ndarray): RGBA image (H, W, 4)

**Returns**: `np.ndarray` - Binary mask (H, W)

**Usage**: Exact segmentation for synthetic benchmark fragments

---

## Chain Code Module

**Module**: `src/chain_code.py`

Implements Freeman 8-directional chain code encoding and normalization (Lecture 72).

### Functions

#### `encode_fragment(contour_points: np.ndarray, n_segments: int = 4) -> tuple`

Full chain code pipeline for a fragment contour.

**Parameters**:
- `contour_points` (np.ndarray): Boundary pixels as (N, 2) array
- `n_segments` (int): Number of boundary segments to create

**Returns**: `tuple[List[int], List[List[int]]]`
- `normalized_chain` (List[int]): Normalized full chain code
- `segments` (List[List[int]]): List of segment chain codes

**Algorithm**:
1. Convert pixels to Freeman chain code
2. Apply first-difference encoding (rotation invariant)
3. Apply cyclic-minimum normalization (starting-point invariant)
4. Split into n_segments equal-length segments
5. Encode each segment with local rotation normalization

**Example**:
```python
from chain_code import encode_fragment
import numpy as np

contour = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
chain, segments = encode_fragment(contour, n_segments=4)
print(f"Chain length: {len(chain)}, Segments: {len(segments)}")
```

---

#### `points_to_chain_code(contour_points: np.ndarray) -> List[int]`

Convert consecutive boundary pixels to Freeman 8-directional codes.

**Parameters**:
- `contour_points` (np.ndarray): Boundary pixels as (N, 2) array

**Returns**: `List[int]` - Freeman chain codes [0-7]

**Direction Encoding**:
```
  5   6   7
    ↖ ↑ ↗
  4 ← · → 0
    ↙ ↓ ↘
  3   2   1
```

---

#### `first_difference(chain: List[int]) -> List[int]`

Compute first-difference chain code for rotation invariance (Lecture 72).

**Parameters**:
- `chain` (List[int]): Raw Freeman chain code

**Returns**: `List[int]` - First-difference code

**Algorithm**: d[i] = (c[i] - c[i-1]) mod 8

**Property**: Invariant to rotation by multiples of 45°

---

#### `cyclic_minimum_rotation(sequence: List[int]) -> List[int]`

Return lexicographically smallest cyclic rotation (Lecture 72).

**Parameters**:
- `sequence` (List[int]): Input sequence

**Returns**: `List[int]` - Normalized sequence

**Property**: Removes dependency on arbitrary starting point

---

#### `normalize_chain_code(chain: List[int]) -> List[int]`

Produce fully normalized chain code descriptor (Lecture 72).

**Parameters**:
- `chain` (List[int]): Raw Freeman chain

**Returns**: `List[int]` - Normalized chain code

**Algorithm**: First-difference → Cyclic-minimum

---

#### `segment_chain_code(chain: List[int], n_segments: int) -> List[List[int]]`

Divide chain code into n_segments equal-length boundary segments.

**Parameters**:
- `chain` (List[int]): Chain code
- `n_segments` (int): Number of segments

**Returns**: `List[List[int]]` - List of segment chain codes

---

#### `contour_to_pixel_segments(contour_points: np.ndarray, n_segments: int) -> List[np.ndarray]`

Divide contour into n_segments equal-length pixel groups.

**Parameters**:
- `contour_points` (np.ndarray): Boundary pixels (N, 2)
- `n_segments` (int): Number of segments

**Returns**: `List[np.ndarray]` - List of pixel segments

**Note**: Division mirrors `segment_chain_code` so indices match

---

#### `rotate_segment_to_horizontal(pixel_segment: np.ndarray) -> np.ndarray`

Rotate pixel segment so its spine vector becomes horizontal.

**Parameters**:
- `pixel_segment` (np.ndarray): Segment pixels (K, 2)

**Returns**: `np.ndarray` - Rotated and quantized pixels

**Algorithm**:
1. Compute spine angle: θ = atan2(last - first)
2. Rotate by -θ to make spine horizontal
3. Re-quantize to integer grid

**Purpose**: Local orientation invariance for segment matching

---

#### `encode_segment_with_local_rotation(pixel_segment: np.ndarray) -> List[int]`

Encode boundary segment with local rotation normalization.

**Parameters**:
- `pixel_segment` (np.ndarray): Segment pixels (K, 2)

**Returns**: `List[int]` - Normalized chain code

**Algorithm**: Rotate-to-horizontal → Chain-code → First-diff → Cyclic-min

---

#### `compute_curvature_profile(pixel_segment: np.ndarray) -> np.ndarray`

Compute discrete curvature (turning-angle) profile (Lecture 72).

**Parameters**:
- `pixel_segment` (np.ndarray): Segment pixels (K, 2)

**Returns**: `np.ndarray` - Curvature profile (K-2,) in radians

**Algorithm**:
```
kappa[i] = atan2(v[i] × v[i-1], v[i] · v[i-1])
where v[i] = p[i+1] - p[i]
```

**Properties**:
- Translation invariant
- Rotation invariant
- No quantization (floating-point)

---

## Compatibility Module

**Module**: `src/compatibility.py`

Implements pairwise edge compatibility scoring (Lectures 23, 52, 71, 72).

### Primary Functions

#### `build_compatibility_matrix(all_segments, all_pixel_segments, all_images) -> np.ndarray`

Build full pairwise compatibility matrix over all fragment segments.

**Parameters**:
- `all_segments` (List[List[List[int]]]): Chain codes per fragment per segment
- `all_pixel_segments` (List[List[np.ndarray]]): Pixel coords per fragment per segment
- `all_images` (List[np.ndarray]): BGR images (for color/texture)

**Returns**: `np.ndarray` - 4D compatibility tensor (n_frags, n_segs, n_frags, n_segs)

**Algorithm**:
1. Compute curvature profiles for all segments
2. Build color similarity matrix (Bhattacharyya coefficients)
3. Build texture similarity matrix (LBP histograms)
4. Build Gabor similarity matrix (frequency-domain texture)
5. Build Haralick similarity matrix (GLCM features)
6. For each segment pair (i,a) → (j,b):
   - Compute curvature cross-correlation (PRIMARY)
   - Add Fourier descriptor score (global shape)
   - Add good-continuation bonus (smooth joins)
   - Multiply by appearance penalty (color⁴ × texture² × gabor² × haralick²)

**Example**:
```python
from compatibility import build_compatibility_matrix

# all_segments: list of list of chain codes
# all_pixel_segs: list of list of pixel arrays
# images: list of BGR images

compat = build_compatibility_matrix(all_segments, all_pixel_segs, images)
print(f"Compatibility matrix shape: {compat.shape}")
```

---

#### `profile_similarity(kappa_a: np.ndarray, kappa_b: np.ndarray) -> float`

Rotation-invariant segment similarity via curvature cross-correlation.

**Parameters**:
- `kappa_a` (np.ndarray): Curvature profile of segment A
- `kappa_b` (np.ndarray): Curvature profile of segment B

**Returns**: `float` - Similarity score [0, 1]

**Algorithm** (Lecture 72):
1. Resample both profiles to same length N
2. Zero-mean and unit-variance normalize
3. Compute circular cross-correlation via FFT: O(N log N)
4. Test 4 hypotheses: forward/reverse × original/negated
5. Return max peak / N mapped to [0, 1]

**Properties**:
- Fully rotation invariant (continuous angles)
- Anti-parallel aware (physically correct for joins)
- Fast: O(N log N) vs O(N²) edit distance

**Example**:
```python
from compatibility import profile_similarity
from chain_code import compute_curvature_profile

kappa_a = compute_curvature_profile(segment_a_pixels)
kappa_b = compute_curvature_profile(segment_b_pixels)
score = profile_similarity(kappa_a, kappa_b)
```

---

#### `good_continuation_bonus(chain_end: List[int], chain_start: List[int]) -> float`

Gestalt good-continuation bonus at proposed join point (Lecture 52).

**Parameters**:
- `chain_end` (List[int]): Final direction codes of first segment
- `chain_start` (List[int]): Initial direction codes of second segment

**Returns**: `float` - Bonus in [0, 1]

**Algorithm**:
```
direction_change = abs(chain_end[-1] - chain_start[0]) mod 8
normalized_change = direction_change / 4.0
bonus = exp(-normalized_change / σ)
```

**Interpretation**: Smooth joins (small direction change) receive high bonus

---

### Color and Texture Functions

#### `compute_color_signature(image_bgr: np.ndarray) -> np.ndarray`

Compact Lab color histogram for appearance matching (Lecture 71).

**Parameters**:
- `image_bgr` (np.ndarray): BGR image

**Returns**: `np.ndarray` - Normalized histogram (L+a+b bins)

**Algorithm**:
1. Convert BGR → Lab color space
2. Compute separate histograms: L* (16 bins), a* (8 bins), b* (8 bins)
3. Concatenate and normalize to sum=1

**Rationale**: Lab is perceptually uniform and excellent for earthen ceramics

---

#### `color_bhattacharyya(sig_a: np.ndarray, sig_b: np.ndarray) -> float`

Bhattacharyya coefficient between color signatures (Lecture 71).

**Parameters**:
- `sig_a` (np.ndarray): Color histogram A
- `sig_b` (np.ndarray): Color histogram B

**Returns**: `float` - BC in [0, 1]

**Formula**: BC = Σ sqrt(p_i × q_i)

**Interpretation**:
- BC = 1.0: identical color distributions
- BC ≈ 0.0: non-overlapping distributions

---

#### `compute_texture_signature(image_bgr: np.ndarray) -> np.ndarray`

Local Binary Pattern (LBP) texture descriptor.

**Parameters**:
- `image_bgr` (np.ndarray): BGR image

**Returns**: `np.ndarray` - LBP histogram (26 bins), normalized

**Algorithm**:
1. Convert to grayscale
2. Compute LBP with radius=3, 24 neighbors, uniform patterns
3. Histogram with 26 bins (24+2 for uniform patterns)

**Properties**:
- Rotation invariant
- Illumination robust
- Captures local surface micro-texture

---

#### `texture_bhattacharyya(sig_a: np.ndarray, sig_b: np.ndarray) -> float`

Bhattacharyya coefficient between LBP texture signatures.

**Parameters**:
- `sig_a`, `sig_b` (np.ndarray): LBP histograms

**Returns**: `float` - BC in [0, 1]

---

#### `extract_gabor_features(image_gray: np.ndarray) -> np.ndarray`

Gabor filter bank for multi-scale texture analysis.

**Parameters**:
- `image_gray` (np.ndarray): Grayscale image

**Returns**: `np.ndarray` - Feature vector (120 dimensions)

**Algorithm**:
- 5 scales × 8 orientations = 40 filters
- Each filter → 3 features (mean, std, energy)
- Total: 120 features, L2-normalized

---

#### `gabor_similarity(feat_a: np.ndarray, feat_b: np.ndarray) -> float`

Cosine similarity between Gabor feature vectors.

**Parameters**:
- `feat_a`, `feat_b` (np.ndarray): Gabor features

**Returns**: `float` - Similarity in [0, 1]

---

#### `extract_haralick_features(image_gray: np.ndarray) -> np.ndarray`

Haralick texture features from Gray-Level Co-occurrence Matrix.

**Parameters**:
- `image_gray` (np.ndarray): Grayscale image

**Returns**: `np.ndarray` - Feature vector (60 dimensions)

**Algorithm**:
- GLCM computed at 3 distances × 4 angles
- 5 properties: contrast, dissimilarity, homogeneity, energy, correlation
- Total: 60 features (5 × 12), L2-normalized

---

#### `haralick_similarity(feat_a: np.ndarray, feat_b: np.ndarray) -> float`

Cosine similarity between Haralick feature vectors.

**Parameters**:
- `feat_a`, `feat_b` (np.ndarray): Haralick features

**Returns**: `float` - Similarity in [0, 1]

---

### Utility Functions

#### `edit_distance(seq_a: List[int], seq_b: List[int]) -> int`

Levenshtein edit distance between integer sequences.

**Parameters**:
- `seq_a`, `seq_b` (List[int]): Integer sequences

**Returns**: `int` - Minimum edit distance

**Complexity**: O(m×n) time, O(n) space (single-row DP)

---

#### `segment_compatibility(seg_a: List[int], seg_b: List[int]) -> float`

Normalized compatibility score between chain code segments.

**Parameters**:
- `seg_a`, `seg_b` (List[int]): Chain code segments

**Returns**: `float` - Score in [0, 1]

**Algorithm**: 1.0 - (edit_distance / max_length)

**Note**: Superseded by `profile_similarity` in production

---

#### `segment_fourier_score(seg_pixels_a: np.ndarray, seg_pixels_b: np.ndarray) -> float`

Global shape similarity via Fourier descriptors (Lecture 72).

**Parameters**:
- `seg_pixels_a`, `seg_pixels_b` (np.ndarray): Pixel coordinates

**Returns**: `float` - Similarity in [0, 1]

**Algorithm**:
1. Treat pixels as complex signal: z = x + jy
2. Compute FFT magnitude spectrum
3. Normalize: Z[0]=0, Z[1]=1
4. Compare first K coefficients

---

## Relaxation Module

**Module**: `src/relaxation.py`

Implements relaxation labeling for global assembly optimization (Lecture 53).

### Functions

#### `run_relaxation(compat_matrix: np.ndarray) -> tuple`

Run full relaxation labeling loop until convergence.

**Parameters**:
- `compat_matrix` (np.ndarray): 4D compatibility tensor (n_frags, n_segs, n_frags, n_segs)

**Returns**: `tuple[np.ndarray, List[float]]`
- `probs` (np.ndarray): Final probability matrix (same shape as compat_matrix)
- `trace` (List[float]): Per-iteration max delta values

**Algorithm** (Lecture 53):
1. Initialize probabilities proportional to compatibility
2. Loop (max 50 iterations or until delta < 1e-4):
   - Compute contextual support Q(i, λ)
   - Update: P ← P × (1 + Q) / Σ[P × (1 + Q)]
   - Record max delta
3. Return converged probabilities and trace

**Example**:
```python
from relaxation import run_relaxation

probs, trace = run_relaxation(compat_matrix)
print(f"Converged in {len(trace)} iterations")
```

---

#### `extract_top_assemblies(probs, n_top=3, compat_matrix=None) -> List[dict]`

Extract top-n candidate assemblies from converged probabilities.

**Parameters**:
- `probs` (np.ndarray): Probability matrix from `run_relaxation`
- `n_top` (int): Number of assemblies to extract
- `compat_matrix` (np.ndarray): Optional raw compatibility for scoring

**Returns**: `List[dict]` - List of assembly dictionaries

**Assembly Dictionary Structure**:
```python
{
    'pairs': [                      # List of matched pairs
        {
            'frag_i': int,         # Fragment index
            'seg_a': int,          # Segment index
            'frag_j': int,         # Partner fragment index
            'seg_b': int,          # Partner segment index
            'score': float,        # Relaxation probability
            'raw_compat': float,   # Raw compatibility score
            'verdict': str,        # "MATCH" / "WEAK_MATCH" / "NO_MATCH"
        },
        ...
    ],
    'confidence': float,            # Mean probability over pairs
    'verdict': str,                 # Assembly-level verdict
    'n_match': int,                 # Number of MATCH pairs
    'n_weak': int,                  # Number of WEAK_MATCH pairs
    'n_no_match': int,              # Number of NO_MATCH pairs
}
```

**Extraction Algorithm**:
1. Greedy highest-probability assignment
2. Each unit matched to best available label
3. Small random perturbation for diversity
4. Repeat n_top times

---

#### `classify_pair_score(raw_compat: float) -> str`

Classify segment-pair compatibility score.

**Parameters**:
- `raw_compat` (float): Raw compatibility score

**Returns**: `str` - "MATCH", "WEAK_MATCH", or "NO_MATCH"

**Thresholds**:
- MATCH: raw_compat ≥ 0.75
- WEAK_MATCH: 0.60 ≤ raw_compat < 0.75
- NO_MATCH: raw_compat < 0.60

---

#### `classify_assembly(confidence: float, matched_pairs: List[dict]) -> str`

Return verdict for complete assembly proposal.

**Parameters**:
- `confidence` (float): Mean relaxation probability
- `matched_pairs` (List[dict]): List of pair dictionaries

**Returns**: `str` - "MATCH", "WEAK_MATCH", or "NO_MATCH"

**Criteria**:
- MATCH: ≥60% pairs are MATCH AND ≥40% valid
- WEAK_MATCH: ≥40% pairs are MATCH or WEAK_MATCH
- NO_MATCH: <40% valid pairs

---

#### `initialize_probabilities(compat_matrix: np.ndarray) -> np.ndarray`

Set initial label probabilities proportional to compatibility.

**Parameters**:
- `compat_matrix` (np.ndarray): 4D compatibility tensor

**Returns**: `np.ndarray` - Initialized probability matrix

**Algorithm**: Row-normalize compatibility matrix (same-fragment entries zeroed)

---

#### `compute_support(probs: np.ndarray, compat_matrix: np.ndarray) -> np.ndarray`

Compute contextual support Q(i, λ) for every unit-label pair.

**Parameters**:
- `probs` (np.ndarray): Current probability matrix
- `compat_matrix` (np.ndarray): Compatibility tensor

**Returns**: `np.ndarray` - Support matrix (same shape)

**Formula**: Q[i,a,j,b] = Σ_{k,c} Σ_{l,d} P[k,c,l,d] × compat[j,b,l,d]

---

#### `update_probabilities(probs: np.ndarray, support: np.ndarray) -> np.ndarray`

Apply relaxation labeling update rule (Lecture 53).

**Parameters**:
- `probs` (np.ndarray): Current probabilities
- `support` (np.ndarray): Contextual support

**Returns**: `np.ndarray` - Updated probabilities

**Formula**: P ← P × (1 + Q) / Σ[P × (1 + Q)]

---

## Shape Descriptors Module

**Module**: `src/shape_descriptors.py`

Implements Fourier descriptors and PCA orientation normalization (Lectures 72, 74).

### Functions

#### `compute_fourier_descriptors(contour, n_descriptors=32) -> np.ndarray`

Compute truncated Fourier descriptors (Lecture 72).

**Parameters**:
- `contour` (np.ndarray): Boundary pixels (N, 2)
- `n_descriptors` (int): Number of low-frequency coefficients to keep

**Returns**: `np.ndarray` - Magnitude coefficients (n_descriptors,)

**Algorithm**:
1. Encode boundary as complex signal: z[n] = x[n] + jy[n]
2. Compute DFT: Z = FFT(z)
3. Normalize: Z[0]=0 (translation), |Z[1]|=1 (scale)
4. Return magnitudes |Z[1..n_descriptors]| (rotation-invariant)

**Example**:
```python
from shape_descriptors import compute_fourier_descriptors

descriptors = compute_fourier_descriptors(contour, n_descriptors=16)
print(f"Fourier descriptors: {descriptors}")
```

---

#### `pca_normalize_contour(contour: np.ndarray) -> np.ndarray`

Rotate and center contour so principal axis aligns with x-axis (Lecture 74).

**Parameters**:
- `contour` (np.ndarray): Boundary pixels (N, 2)

**Returns**: `np.ndarray` - Normalized contour (N, 2)

**Algorithm**:
1. Center contour (subtract centroid)
2. Compute 2×2 scatter matrix
3. Eigendecomposition → principal axis
4. Rotate by -θ to align principal axis with x-axis
5. Shift to positive quadrant

**Purpose**: Orientation normalization before chain-code comparison

---

#### `pca_orientation(contour: np.ndarray) -> tuple`

Compute principal axis of contour via PCA (Lecture 74).

**Parameters**:
- `contour` (np.ndarray): Boundary pixels (N, 2)

**Returns**: `tuple[np.ndarray, float]`
- `centroid` (np.ndarray): Mean position (2,)
- `angle` (float): Principal axis angle in radians

---

#### `contour_to_complex_signal(contour: np.ndarray) -> np.ndarray`

Represent boundary as complex 1D signal.

**Parameters**:
- `contour` (np.ndarray): Boundary pixels (N, 2)

**Returns**: `np.ndarray` - Complex signal (N,) where z[n] = x[n] + jy[n]

---

#### `log_shape_summary(contour, name, n_descriptors=8) -> None`

Log brief shape summary (Fourier + PCA) for diagnostics.

**Parameters**:
- `contour` (np.ndarray): Boundary pixels
- `name` (str): Fragment name
- `n_descriptors` (int): Number of Fourier coefficients to show

**Side Effects**: Logs to console/file

---

## Visualization Module

**Module**: `src/visualize.py`

Produces annotated images using OpenCV and matplotlib.

### Functions

#### `render_fragment_grid(images, contours, fragment_names, output_path) -> None`

Render all fragments with contour overlays in grid layout.

**Parameters**:
- `images` (List[np.ndarray]): BGR images
- `contours` (List[np.ndarray]): Boundary contours
- `fragment_names` (List[str]): Fragment labels
- `output_path` (str): Output PNG file path

**Side Effects**: Saves multi-panel figure to disk

---

#### `render_compatibility_heatmap(compat_matrix, fragment_names, output_path) -> None`

Render inter-fragment compatibility as color heatmap.

**Parameters**:
- `compat_matrix` (np.ndarray): 4D compatibility tensor
- `fragment_names` (List[str]): Fragment labels
- `output_path` (str): Output PNG file path

**Algorithm**: Averages 4D matrix over segments to (n_frags × n_frags)

---

#### `render_assembly_proposal(images, contours, assembly, fragment_names, rank, output_path) -> None`

Render single assembly showing matched pairs side-by-side.

**Parameters**:
- `images`, `contours` (List): Fragment data
- `assembly` (dict): Assembly dictionary from `extract_top_assemblies`
- `fragment_names` (List[str]): Labels
- `rank` (int): Assembly rank (0, 1, 2 for top-3)
- `output_path` (str): Output PNG file path

**Layout**: Each row shows one matched pair

---

#### `render_convergence_plot(trace, output_path) -> None`

Plot relaxation labeling convergence trace.

**Parameters**:
- `trace` (List[float]): Per-iteration max delta from `run_relaxation`
- `output_path` (str): Output PNG file path

**Features**:
- Log y-axis for small deltas
- Convergence threshold marked as horizontal line

---

#### `draw_contour_overlay(image, contour) -> np.ndarray`

Draw extracted boundary contour on copy of fragment image.

**Parameters**:
- `image` (np.ndarray): BGR image
- `contour` (np.ndarray): Boundary pixels (N, 2)

**Returns**: `np.ndarray` - Image with contour overlay (green)

---

## Assembly Renderer Module

**Module**: `src/assembly_renderer.py`

Geometric assembly visualization with affine alignment (Lectures 23, 72).

### Functions

#### `render_assembly_sheet(images, contours, assembly, fragment_names, n_segments, output_path) -> None`

Render all matched pairs with geometric alignment.

**Parameters**:
- `images`, `contours` (List): Fragment data
- `assembly` (dict): Assembly dictionary
- `fragment_names` (List[str]): Labels
- `n_segments` (int): Number of boundary segments
- `output_path` (str): Output PNG file path

**Side Effects**: Saves multi-row figure with aligned fragments

---

#### `render_pair_assembly(img_i, contour_i, seg_a, img_j, contour_j, seg_b, n_segments, pair_score, name_i, name_j) -> np.ndarray`

Render fragment_j geometrically aligned to fragment_i.

**Parameters**:
- `img_i`, `contour_i`: First fragment
- `seg_a` (int): Segment index on fragment i
- `img_j`, `contour_j`: Second fragment
- `seg_b` (int): Segment index on fragment j
- `n_segments` (int): Total segments per fragment
- `pair_score` (float): Match score
- `name_i`, `name_j` (str): Fragment labels

**Returns**: `np.ndarray` - Composite image (cropped)

**Algorithm**:
1. Extract pixel segments
2. Compute centroids and directions
3. Build affine matrix (rotation + translation)
4. Warp fragment_j to align with fragment_i
5. Composite on white canvas
6. Highlight matching segments

---

#### `build_affine_matrix(src_centroid, src_angle, dst_centroid, dst_angle) -> np.ndarray`

Build 2×3 affine matrix for segment alignment.

**Parameters**:
- `src_centroid`, `dst_centroid` (np.ndarray): Centroids (2,)
- `src_angle`, `dst_angle` (float): Principal angles in radians

**Returns**: `np.ndarray` - Affine transform (2, 3)

**Formula**: Rotates src by (dst_angle + π - src_angle), then translates

---

#### `segment_centroid(pts: np.ndarray) -> np.ndarray`

Return mean (x, y) position of contour points.

---

#### `segment_direction_angle(pts: np.ndarray) -> float`

Return angle (radians) of principal axis.

**Algorithm**: Angle from first to last point

---

#### `get_pixel_segment(contour, seg_idx, n_segments) -> np.ndarray`

Return pixel coordinates for one boundary segment.

---

#### `overlay_on_canvas(canvas, fragment_img, offset_x, offset_y) -> np.ndarray`

Place fragment at offset on canvas using darkest-pixel compositing.

---

#### `draw_segment_highlight(canvas, pts, color) -> None`

Draw thick polyline along segment pixels.

---

#### `crop_to_content(image, padding=20) -> np.ndarray`

Crop white-background image to bounding box of content.

---

## Hard Discriminators Module

**Module**: `src/hard_discriminators.py`

Fast rejection criteria based on arXiv:2511.12976 and arXiv:2309.13512.

### Functions

#### `compute_edge_density(image: np.ndarray) -> float`

Compute edge density: fraction of pixels that are edges.

**Parameters**:
- `image` (np.ndarray): BGR or grayscale image

**Returns**: `float` - Edge density in [0, 1]

**Algorithm**: Canny(50, 150), count edge pixels / total pixels

**Reference**: arXiv:2511.12976 (MCAQ-YOLO)

---

#### `compute_texture_entropy(image: np.ndarray) -> float`

Compute Shannon entropy of grayscale histogram.

**Parameters**:
- `image` (np.ndarray): BGR or grayscale image

**Returns**: `float` - Entropy value (higher = more random)

**Reference**: arXiv:2511.12976

---

#### `hard_reject_check(image_i, image_j, bc_color, bc_texture) -> bool`

Fast hard rejection check. Returns True if pair should be rejected.

**Parameters**:
- `image_i`, `image_j` (np.ndarray): Fragment images
- `bc_color` (float): Bhattacharyya coefficient for color
- `bc_texture` (float): Bhattacharyya coefficient for texture

**Returns**: `bool` - True if rejected, False if passes

**Criteria**:
1. Edge density difference > threshold
2. Texture entropy difference > threshold
3. Combined appearance (color AND texture) below threshold

**Reference**: arXiv:2309.13512 (99.3% ensemble)

---

#### `should_early_stop_negative_tests(num_failed, num_tested) -> bool`

Determine if negative testing should stop early.

**Parameters**:
- `num_failed` (int): Number of failed tests
- `num_tested` (int): Number of tests run

**Returns**: `bool` - True if should stop

**Criterion**: If 90% of tests pass, stop early

---

## Ensemble Voting Module

**Module**: `src/ensemble_voting.py`

Multi-discriminator voting system from arXiv:2309.13512 (99.3% accuracy).

### Functions

#### `ensemble_verdict_five_way(raw_compat, bc_color, bc_texture, bc_gabor, edge_density_diff, entropy_diff) -> str`

5-way ensemble voting for final fragment pair verdict.

**Parameters**:
- `raw_compat` (float): Raw compatibility score [0, 1.25]
- `bc_color` (float): Color Bhattacharyya [0, 1]
- `bc_texture` (float): Texture Bhattacharyya [0, 1]
- `bc_gabor` (float): Gabor similarity [0, 1]
- `edge_density_diff` (float): Edge density difference [0, 1]
- `entropy_diff` (float): Entropy difference [0, ∞)

**Returns**: `str` - "MATCH", "WEAK_MATCH", or "NO_MATCH"

**Voters**:
1. Raw Compatibility (curvature + fourier + good-continuation)
2. Color Discriminator (Lab histogram)
3. Texture Discriminator (LBP)
4. Gabor Discriminator (frequency-domain texture)
5. Morphological Discriminator (edge density + entropy)

**Voting Logic** (pessimistic for archaeology):
- MATCH: Requires 3+ MATCH votes (60%)
- NO_MATCH: Requires 2+ NO_MATCH votes (40%)
- WEAK_MATCH: Otherwise

**Reference**: arXiv:2309.13512

---

#### `classify_by_threshold(score, match_thresh, weak_thresh) -> str`

Classify score into MATCH/WEAK_MATCH/NO_MATCH.

**Parameters**:
- `score` (float): Similarity score [0, 1]
- `match_thresh` (float): Threshold for confident match
- `weak_thresh` (float): Threshold for possible match

**Returns**: `str` - Verdict

---

#### `ensemble_verdict_weighted(scores: Dict[str, float], weights: Dict[str, float]) -> str`

Weighted voting with configurable discriminator weights.

**Parameters**:
- `scores` (Dict): Discriminator name → score
- `weights` (Dict): Discriminator name → weight

**Returns**: `str` - Verdict

---

#### `ensemble_verdict_hierarchical(scores: Dict[str, float]) -> str`

Hierarchical voting: color/texture first, then geometry.

**Parameters**:
- `scores` (Dict): Discriminator name → score

**Returns**: `str` - Verdict

**Strategy**:
1. If appearance (color × texture) fails → NO_MATCH immediately
2. Otherwise, use geometric + morphological votes

---

#### `get_ensemble_statistics(verdicts: List[str]) -> Dict[str, float]`

Compute ensemble voting statistics.

**Parameters**:
- `verdicts` (List[str]): List of voter verdicts

**Returns**: `Dict[str, float]` - Statistics:
  - `match_fraction`: Fraction of MATCH votes
  - `no_match_fraction`: Fraction of NO_MATCH votes
  - `weak_match_fraction`: Fraction of WEAK_MATCH votes
  - `agreement`: Fraction of voters agreeing with majority

---

## Type Definitions

### Common Types

```python
# Image types
BGRImage = np.ndarray        # (H, W, 3) uint8, OpenCV BGR format
GrayImage = np.ndarray       # (H, W) uint8, grayscale
BinaryMask = np.ndarray      # (H, W) uint8, values 0 or 255

# Contour types
Contour = np.ndarray         # (N, 2) int32, boundary pixel coordinates
ChainCode = List[int]        # Freeman 8-directional codes [0-7]
CurvatureProfile = np.ndarray  # (N,) float64, turning angles in radians

# Descriptor types
ColorSignature = np.ndarray   # (32,) float32, Lab histogram
TextureSignature = np.ndarray # (26,) float32, LBP histogram
GaborFeatures = np.ndarray    # (120,) float32, Gabor filter responses
HaralickFeatures = np.ndarray # (60,) float32, GLCM statistics
FourierDescriptors = np.ndarray  # (K,) float64, magnitude spectrum

# Compatibility types
CompatibilityMatrix = np.ndarray  # (n_frags, n_segs, n_frags, n_segs) float64
ProbabilityMatrix = np.ndarray    # Same shape as CompatibilityMatrix
SupportMatrix = np.ndarray        # Same shape as CompatibilityMatrix

# Assembly types
PairDict = Dict[str, Union[int, float, str]]  # Single matched pair
AssemblyDict = Dict[str, Union[List[PairDict], float, str, int]]  # Full assembly
```

### Constants

```python
# Preprocessing (preprocessing.py)
GAUSSIAN_KERNEL_SIZE = (5, 5)
GAUSSIAN_SIGMA = 1.5
MIN_CONTOUR_AREA = 500
MORPH_KERNEL_SIZE = 7

# Chain Code (chain_code.py)
DIRECTION_DELTAS = {0: (1,0), 1: (1,1), ..., 7: (1,-1)}  # Freeman 8-dir

# Compatibility (compatibility.py)
GOOD_CONTINUATION_WEIGHT = 0.10
FOURIER_WEIGHT = 0.25
COLOR_PENALTY_WEIGHT = 0.80
COLOR_HIST_BINS_L = 16
COLOR_HIST_BINS_A = 8
COLOR_HIST_BINS_B = 8

# Relaxation (relaxation.py)
MAX_ITERATIONS = 50
CONVERGENCE_THRESHOLD = 1e-4
MATCH_SCORE_THRESHOLD = 0.75
WEAK_MATCH_SCORE_THRESHOLD = 0.60
ASSEMBLY_CONFIDENCE_THRESHOLD = 0.65

# Shape Descriptors (shape_descriptors.py)
FOURIER_DESCRIPTOR_ORDER = 32

# Visualization (visualize.py)
CONTOUR_COLOR = (0, 200, 100)  # Green in BGR
FIGURE_DPI = 120
CONTOUR_THICKNESS = 2

# Assembly Renderer (assembly_renderer.py)
CANVAS_PAD_FACTOR = 2.5
HIGHLIGHT_THICKNESS = 3
COLOR_SEG_A = (0, 210, 90)   # Green
COLOR_SEG_B = (0, 100, 230)  # Orange
```

---

## Usage Examples

### Complete Pipeline Example

```python
#!/usr/bin/env python3
"""Example: Run complete reconstruction pipeline"""

import argparse
from main import run_pipeline, build_arg_parser

# Method 1: Command-line style
parser = build_arg_parser()
args = parser.parse_args([
    '--input', 'data/sample',
    '--output', 'outputs/results',
    '--log', 'outputs/logs'
])
run_pipeline(args)

# Method 2: Programmatic
args = argparse.Namespace(
    input='data/my_fragments',
    output='outputs/my_results',
    log='outputs/logs'
)
run_pipeline(args)
```

### Custom Preprocessing Example

```python
"""Example: Custom preprocessing with manual steps"""

from preprocessing import (
    load_image,
    apply_gaussian_blur,
    canny_silhouette,
    extract_largest_contour
)

# Load and preprocess manually
image = load_image('fragment.png')
blurred = apply_gaussian_blur(image)
mask = canny_silhouette(blurred)
if mask is not None:
    contour = extract_largest_contour(mask)
    print(f"Extracted contour: {len(contour)} points")
```

### Chain Code Analysis Example

```python
"""Example: Extract and compare chain codes"""

from preprocessing import preprocess_fragment
from chain_code import encode_fragment, normalize_chain_code
from compatibility import segment_compatibility

# Process two fragments
img1, contour1 = preprocess_fragment('frag1.png')
img2, contour2 = preprocess_fragment('frag2.png')

# Extract chain codes
chain1, segs1 = encode_fragment(contour1, n_segments=4)
chain2, segs2 = encode_fragment(contour2, n_segments=4)

# Compare first segments
score = segment_compatibility(segs1[0], segs2[0])
print(f"Segment similarity: {score:.3f}")
```

### Custom Compatibility Matrix Example

```python
"""Example: Build compatibility matrix with custom settings"""

from preprocessing import preprocess_fragment
from chain_code import encode_fragment, contour_to_pixel_segments
from compatibility import build_compatibility_matrix
import cv2

# Load fragments
fragment_paths = ['frag1.png', 'frag2.png', 'frag3.png']
images, contours, all_segments, all_pixel_segs = [], [], [], []

for path in fragment_paths:
    img, contour = preprocess_fragment(path)
    _, segments = encode_fragment(contour, n_segments=4)
    pixel_segs = contour_to_pixel_segments(contour, 4)

    images.append(img)
    contours.append(contour)
    all_segments.append(segments)
    all_pixel_segs.append(pixel_segs)

# Build compatibility matrix
compat = build_compatibility_matrix(all_segments, all_pixel_segs, images)
print(f"Compatibility shape: {compat.shape}")
print(f"Mean compatibility: {compat.mean():.4f}")
```

### Relaxation Labeling Example

```python
"""Example: Run relaxation labeling and extract assemblies"""

from relaxation import run_relaxation, extract_top_assemblies
import numpy as np

# Assume compat_matrix is already computed
compat_matrix = np.load('compat_matrix.npy')

# Run relaxation
probs, trace = run_relaxation(compat_matrix)
print(f"Converged in {len(trace)} iterations")

# Extract top assemblies
assemblies = extract_top_assemblies(probs, n_top=3, compat_matrix=compat_matrix)

for i, assembly in enumerate(assemblies):
    print(f"\nAssembly #{i+1}: {assembly['verdict']}")
    print(f"  Confidence: {assembly['confidence']:.4f}")
    print(f"  Pairs: {len(assembly['pairs'])}")
    print(f"  Match/Weak/No: {assembly['n_match']}/{assembly['n_weak']}/{assembly['n_no_match']}")
```

### Visualization Example

```python
"""Example: Render all visualization outputs"""

from visualize import (
    render_fragment_grid,
    render_compatibility_heatmap,
    render_convergence_plot,
    render_assembly_proposal
)

# Assume data is already loaded
render_fragment_grid(
    images, contours, fragment_names,
    'outputs/fragments.png'
)

render_compatibility_heatmap(
    compat_matrix, fragment_names,
    'outputs/heatmap.png'
)

render_convergence_plot(
    trace,
    'outputs/convergence.png'
)

for i, assembly in enumerate(assemblies):
    render_assembly_proposal(
        images, contours, assembly, fragment_names, i,
        f'outputs/assembly_{i+1}.png'
    )
```

---

## Error Handling

### Common Exceptions

```python
# FileNotFoundError
try:
    image, contour = preprocess_fragment('missing.png')
except FileNotFoundError as e:
    print(f"Image not found: {e}")

# ValueError - No contour found
try:
    contour = extract_largest_contour(binary_mask)
except ValueError as e:
    print(f"Contour extraction failed: {e}")

# ValueError - Contour too small
try:
    contour = extract_largest_contour(mask)
except ValueError as e:
    print(f"Contour too small: {e}")
```

### Validation

```python
# Validate compatibility matrix shape
def validate_compat_matrix(compat, n_frags, n_segs):
    expected = (n_frags, n_segs, n_frags, n_segs)
    if compat.shape != expected:
        raise ValueError(f"Expected shape {expected}, got {compat.shape}")

# Validate contour
def validate_contour(contour):
    if contour.ndim != 2 or contour.shape[1] != 2:
        raise ValueError(f"Contour must be (N, 2), got {contour.shape}")
    if len(contour) < 10:
        raise ValueError(f"Contour too short: {len(contour)} points")
```

---

## Performance Notes

### Time Complexity

| Function | Complexity | Bottleneck |
|----------|-----------|------------|
| `preprocess_fragment` | O(H×W) | Gaussian blur, Canny |
| `encode_fragment` | O(N) | Chain code generation |
| `profile_similarity` | O(N log N) | FFT cross-correlation |
| `build_compatibility_matrix` | O(F²×S²×N log N) | All pairs, all segments |
| `run_relaxation` | O(I×F²×S²) | I iterations over full matrix |
| `extract_top_assemblies` | O(K×F²×S²) | K assemblies |

Where:
- H, W: Image height, width
- N: Contour length
- F: Number of fragments
- S: Number of segments per fragment
- I: Relaxation iterations (typically 10-30)
- K: Number of assemblies to extract

### Memory Usage

```python
# Typical memory footprint for 5 fragments, 4 segments each
n_frags = 5
n_segs = 4

# Compatibility matrix: (5, 4, 5, 4) × 8 bytes = 1,600 bytes
# Probability matrix: same size = 1,600 bytes
# Images: 5 × (512×512×3) × 1 byte ≈ 3.9 MB
# Total: ~4 MB

# For 10 fragments, 4 segments:
# Compatibility: (10, 4, 10, 4) × 8 = 12,800 bytes
# Total: ~6 MB
```

### Optimization Tips

1. **Reduce Image Size**: Resize large images before processing
   ```python
   max_size = 1024
   if max(image.shape[:2]) > max_size:
       scale = max_size / max(image.shape[:2])
       image = cv2.resize(image, None, fx=scale, fy=scale)
   ```

2. **Reduce Segments**: Use fewer segments for faster compatibility computation
   ```python
   # 4 segments: 16 pairs per fragment pair
   # 8 segments: 64 pairs per fragment pair
   n_segments = 4  # Recommended
   ```

3. **Early Termination**: Use color pre-check to skip expensive computation
   ```python
   if detect_mixed_source_fragments(images)[0]:
       return "NO_MATCH"  # Skip compatibility matrix
   ```

---

## Changelog

### Version 1.0 (2026-04-08)
- Initial API reference creation
- Documented all 67 public functions across 10 modules
- Added usage examples and type definitions
- Added performance notes and optimization tips

---

## Contributing

To add new API functions:

1. Add comprehensive docstring with:
   - Purpose and algorithm description
   - Parameter types and meanings
   - Return value specification
   - Lecture or research reference (if applicable)
   - Usage example

2. Update this API reference with:
   - Function signature
   - Parameter table
   - Return value description
   - Algorithm notes
   - Example code

3. Add unit tests in `tests/test_pipeline.py`

---

## License

This API reference is part of the Archaeological Fragment Reconstruction System, an academic project for the Introduction to Computational and Biological Vision (ICBV) course.

---

**Document Version**: 1.0
**Last Updated**: 2026-04-08
**Total Functions Documented**: 67
**Total Modules**: 10
