# Archaeological Fragment Reconstruction System
**Final Project — Introduction to Computational and Biological Vision (ICBV)**

---

## What This Project Does

Imagine finding hundreds of broken pottery shards at an excavation site. A conservator would spend weeks trying to figure out which pieces belong together and how they fit. This project automates that process using computer vision.

Given a set of photographs of individual broken fragments (on a transparent or white background), the system:

1. **Extracts the boundary** of each fragment from its image.
2. **Encodes the boundary shape** into a compact geometric representation.
3. **Scores every possible pairing** of fragment edges — deciding how likely it is that two edges were once joined.
4. **Searches for the best assembly** using iterative constraint propagation.
5. **Outputs annotated images** showing which fragments likely belong together, and how.

The system is designed around a concrete academic constraint: every major algorithm directly corresponds to a lecture from the ICBV course. See the [Algorithm Map](#algorithm-map) below.

---

## Quick Start

```bash
# 1 — Install dependencies (once)
pip install -r requirements.txt

# 2 — Run on the built-in sample (5 pre-made fragments)
python src/main.py --input data/sample --output outputs/results --log outputs/logs

# 3 — Run on your own fragment images
python src/main.py --input /path/to/your/fragments --output outputs/results --log outputs/logs

# 4 — Run the full benchmark test suite
python run_test.py --no-rotate

# 5 — Unit tests
python -m pytest tests/
```

---

## Requirements

```
opencv-python
numpy
matplotlib
scipy
Pillow
```

Install with: `pip install -r requirements.txt`

Python 3.8 or later. No GPU, no deep learning frameworks.

---

## Directory Structure

```
icbl_final_project/
│
├── src/                        Core pipeline — all the actual algorithms
│   ├── main.py                 Entry point; ties all stages together
│   ├── preprocessing.py        Image loading, Gaussian blur, thresholding, contour extraction
│   ├── chain_code.py           Freeman chain code encoding, curvature profiles, segment splitting
│   ├── compatibility.py        Pairwise edge-compatibility scoring (shape + color)
│   ├── relaxation.py           Relaxation labeling — iterative assembly search
│   ├── visualize.py            Result rendering: heatmaps, contour overlays, convergence plots
│   ├── assembly_renderer.py    Geometric assembly sheet output
│   └── shape_descriptors.py    PCA-based contour normalization
│
├── data/
│   ├── raw/                    Source images — the original archaeological photographs
│   ├── sample/                 5 pre-made fragments for a quick demo run
│   └── examples/
│       ├── positive/           Test cases where fragments ARE from the same image → expect MATCH
│       └── negative/           Test cases mixing fragments from DIFFERENT images → expect NO_MATCH
│
├── outputs/
│   ├── logs/                   Per-run log files (timestamped, e.g. run_20240404_143021.log)
│   ├── results/                Pipeline output images from main.py runs
│   ├── test_logs/              Logs from run_test.py benchmark runs
│   └── test_results/           Assembly images from benchmark runs
│
├── docs/                       ICBV lecture notes (read-only reference material)
├── tests/
│   └── test_pipeline.py        Unit tests for each module
│
├── generate_benchmark_data.py  Splits a source image into realistic fragments
├── setup_examples.py           Generates the full data/examples/ test suite from data/raw/
├── run_test.py                 Runs the complete benchmark and prints a PASS/FAIL table
├── requirements.txt
└── README.md                   This file
```

---

## How to Run — In Detail

### Run on your own images

Place your fragment images (PNG or JPG, one fragment per file, white or transparent background) in any folder, then run:

```bash
python src/main.py --input /your/fragment/folder --output outputs/results --log outputs/logs
```

The pipeline will print a `[RESULT]` line to the terminal and write all outputs to `outputs/results/`.

### Generate your own test fragments from a source image

```bash
# Split an image into 6–8 fragments, drop 1 (missing piece), add 30% damage
python generate_benchmark_data.py \
  --input data/raw \
  --output my_test_fragments \
  --min-frags 6 --max-frags 8 \
  --drop-frags 1 \
  --damage-prob 0.3

# Key options:
#   --drop-frags N     Randomly omit N fragments (simulates lost/unrecovered pieces)
#   --damage-prob P    Probability that each fragment gets erosion damage applied
#   --max-size PX      Resize images to at most PX pixels (default 1024; affects speed)
#   --displacement F   Fracture jaggedness 1–20 (default 10; higher = more irregular edges)
#   --seed N           Fix random seed for reproducibility
```

### Regenerate the complete test suite

```bash
python setup_examples.py   # reads data/raw/, writes data/examples/
```

This creates:
- **9 positive cases** — one folder per raw image, each containing 6–7 fragments from that image (1 dropped, ~30% damaged)
- **36 negative cases** — every pairwise combination of raw images, with fragments mixed from two different sources

### Run the benchmark

```bash
# Full suite with random rotation of each fragment
python run_test.py

# Without rotation (faster; easier to inspect results)
python run_test.py --no-rotate

# Only positive cases
python run_test.py --positive-only --no-rotate

# Only negative cases
python run_test.py --negative-only --no-rotate
```

The benchmark prints a formatted table like this:

```
====================================================================================================
  RECONSTRUCTION TEST RESULTS  (NO rotation)
====================================================================================================
  Test Case                                     Type    Frags    Verdict      Conf  Time(s)  Pass?
  ──────────────────────────────────────────────────────────────────────────────────────────────────
  scroll                                      positive    6      ✓ MATCH      0.07      5.0  PASS
  shard_01_british                            positive    6      ✓ MATCH      0.08      4.1  PASS
  mixed_scroll_shard_01_british               negative    6    ✗ NO_MATCH     —         0.2  PASS
  ...
```

---

## What the Pipeline Outputs

For each run, the pipeline writes to the specified `--output` folder:

| File | What it shows |
|---|---|
| `fragment_contours.png` | All input fragments with extracted boundaries overlaid |
| `compatibility_heatmap.png` | Color-coded matrix of pairwise edge similarity scores |
| `convergence_plot.png` | How the relaxation algorithm converged iteration by iteration |
| `assembly_01.png` … `assembly_03.png` | Top-3 proposed assemblies with match scores |
| `assembly_01_geometric.png` … | Fragments arranged in their proposed positions |

The terminal (and log file) always ends with a `[RESULT]` line:

```
[RESULT] MATCH FOUND verdict=MATCH pairs: 10 match 0 weak — 3 of 3 proposed assemblies accepted.
[RESULT] NO MATCH FOUND — fewer than 40% of fragment pairs exceed the compatibility threshold.
```

---

## Algorithm Map

Every component maps directly to a lecture from the ICBV course:

| Stage | What it does | Algorithm | Lecture |
|---|---|---|---|
| **Preprocessing** | Load image, blur, threshold, extract contour | Gaussian blur + Otsu thresholding | 22 (Linear Filtering) |
| **Contour extraction** | Find the outer boundary of the fragment | `cv2.findContours` (Canny-based) | 23 (Edge Detection) |
| **Shape encoding** | Represent the boundary as a compact code | Freeman 8-directional chain code | 72 (2D Shape Analysis) |
| **Rotation normalization** | Make the representation rotation-invariant | PCA alignment + cyclic-minimum chain | 72 + 74 (Appearance Recognition) |
| **Edge compatibility** | Score how well two edges could fit together | Curvature cross-correlation (FFT) + Fourier descriptors | 72 + 23 |
| **Color consistency** | Reject fragments from different source images | Bhattacharyya color-histogram distance | 71 (Object Recognition) |
| **Good continuation** | Reward smooth joins at fragment boundaries | Gestalt good-continuation principle | 52 (Perceptual Organization) |
| **Assembly search** | Find the globally best matching | Relaxation labeling (iterative belief propagation) | 53 (Curve Inference) |
| **Hypothesis pruning** | Filter out low-confidence assemblies | Interpretation-tree style acceptance threshold | 73 (Interpretation Trees) |

### Key algorithmic ideas in plain English

**Curvature cross-correlation (edge compatibility):** Instead of asking "do these edges look similar?", the algorithm asks "does the sequence of left/right turns along edge A match the reverse sequence along edge B?" — because when two broken pieces fit together, one edge is literally the mirror-reverse of the other. The comparison is done via FFT for speed, and is invariant to the absolute orientation of each fragment.

**Relaxation labeling (assembly search):** Each fragment edge starts with equal probability of matching any other edge. At each iteration, an edge's match probability is updated based on whether its *neighbors* (the other edges on the same fragment and on the proposed partner fragment) also support the same match. Consistent matches reinforce each other; contradictory ones cancel out. After 30–50 iterations the probabilities converge to a stable assignment.

**Color pre-check:** Before running the expensive geometric pipeline, the system checks whether the set of fragments has a bimodal color distribution — a clear sign that two distinct source images are present. If detected, the pipeline returns NO_MATCH immediately without running relaxation labeling.

---

## Benchmark Results

Running `python run_test.py --no-rotate` on the built-in `data/examples/` suite:

| Category | Cases | Pass rate | Notes |
|---|---|---|---|
| **Positive** (same-image) | 9 | **9/9 (100%)** | 6–7 fragments each, 1 dropped, 30% damaged |
| **Negative** (mixed-image) | 36 | **~19/36 (53%)** | Fails when two images share similar color palettes |

The 17 failing negative cases all involve image pairs with similar overall appearance (e.g., two different pottery fragments with nearly identical clay color). This is a known limitation: the color histogram signal cannot distinguish between same-artifact fragments and different-artifact fragments of the same material type. A future improvement would add texture or gradient features.

---

## Known Limitations

- **No 3D data.** The system works only on 2D photographs of pre-segmented fragments (clean background required).
- **Same-color false positives.** Fragments from two different objects of the same material (e.g., two brown clay pots) may not be rejected by the color pre-check.
- **Scale.** The system is designed for 5–15 fragments. Scaling to hundreds of fragments would require a faster matching strategy (e.g., ANN indexing instead of exhaustive pairwise scoring).
- **Real excavation photos.** Fragment images must be pre-segmented (one fragment per image, clean background). Raw field photographs are not supported.

---

## File Descriptions

| File | Role |
|---|---|
| `src/main.py` | Orchestrates the full pipeline; handles CLI arguments, logging, and output |
| `src/preprocessing.py` | Loads RGBA fragment images, applies Gaussian blur, extracts binary mask and contour |
| `src/chain_code.py` | Computes Freeman chain codes, curvature profiles, and splits contours into segments |
| `src/compatibility.py` | Builds the 4D compatibility tensor; implements curvature cross-correlation, Fourier descriptors, good-continuation bonus, and color histogram penalty |
| `src/relaxation.py` | Implements the relaxation labeling update rule, convergence detection, assembly extraction, and verdict classification |
| `src/visualize.py` | Renders all output images: contour overlays, heatmaps, assembly proposals, convergence plots |
| `src/assembly_renderer.py` | Produces the geometric assembly sheet (fragments placed in proposed positions) |
| `src/shape_descriptors.py` | PCA-based contour normalization for consistent orientation |
| `generate_benchmark_data.py` | Voronoi-based fragment generator with fracture-like boundaries, missing pieces, and erosion damage |
| `setup_examples.py` | One-shot script to build `data/examples/` from `data/raw/` |
| `run_test.py` | Runs the full benchmark and prints a PASS/FAIL summary table |
| `tests/test_pipeline.py` | Unit tests for preprocessing, chain code, compatibility, and relaxation modules |
