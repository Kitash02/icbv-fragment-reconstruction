# CLAUDE.md — Archaeological Fragment Reconstruction System
# Final Project: Introduction to Computational and Biological Vision (ICBV)

## Project Overview

This project implements an automatic system for reconstructing fragmented archaeological artifacts
from photographs. The problem is framed as a geometric puzzle: given images of broken sherds or
fragments, the system extracts their contours, represents them compactly, computes pairwise
compatibility scores, and proposes candidate assemblies using global constraint optimization.

The implementation draws directly on course material from ICBV. Every major algorithmic component
corresponds to a concept covered in the lectures; the mapping is documented in the section below.

---

## Reading the Course Material

Before writing any code, read the lecture notes in `docs/` in order. Pay attention to the
following lectures especially:

- **Lectures 21–23 (Early Vision):** Gaussian smoothing, linear filtering, edge detection
  (Roberts, Sobel, Canny). These feed directly into the preprocessing pipeline.
- **Lectures 51–53 (Perceptual Organization):** Relaxation labeling, good continuation, constraint
  propagation. The assembly stage is modeled on this framework.
- **Lecture 72 (2D Shape Analysis):** Chain codes, contour descriptors, rotation invariance.
  This is the core representation used for fragment matching.
- **Lectures 71 & 73 (Object Recognition):** Interpretation trees, hypothesis generation and
  pruning. Useful framing for the combinatorial search over assemblies.

The goal is to implement the project *in the spirit* of these lectures, not merely to cite them.
The algorithms should be recognizable to a grader who knows the course material.

---

## Algorithms and Their Course Mapping

| Component | Algorithm | Lecture source |
|---|---|---|
| Preprocessing | Gaussian blur + Otsu thresholding | Lecture 22 (Linear filtering) |
| Contour extraction | `cv2.findContours` (OpenCV) | Lecture 23 (Edge detection) |
| Contour representation | Freeman Chain Code (8-connectivity) | Lecture 72 (2D Shape Analysis) |
| Rotation normalization | Cyclic-minimum normalization of chain string | Lecture 72 |
| Edge compatibility score | Normalized chain-edit distance (custom) | Lecture 72 + Lecture 23 |
| Global assembly optimization | Relaxation Labeling (iterative constraint propagation) | Lecture 53 |
| Grouping constraints | Gestalt: good continuation + proximity | Lecture 52 |
| Visualization | Contour overlay with OpenCV + matplotlib | Throughout |

> **Implementation note:** Do not import or depend on the `RL_puzzle_solver` GitHub repository or
> any external puzzle-solver library. Implement relaxation labeling from scratch based on the
> course formulation — the algorithm is short and the grader will want to see the implementation.

---

## Scope and Realism

The system works on a small controlled dataset of fragment images (5–15 fragments per test case).
This is intentional: the focus is correctness of the algorithmic pipeline, not scale.

What the system does:
1. Accepts a folder of fragment images (PNG/JPG, white background, single fragment per image).
2. Extracts and normalizes each fragment's boundary chain code.
3. Computes pairwise edge-compatibility scores between all fragment boundary segments.
4. Runs relaxation labeling to iteratively refine assembly hypotheses.
5. Renders the top-k candidate assemblies as annotated images.

What the system does **not** need to do:
- Handle 3D scans or depth data.
- Process real excavation photographs with complex backgrounds (use pre-segmented images).
- Achieve state-of-the-art accuracy — a working, principled pipeline is the goal.

---

## Project Structure

```
icbl_final_project/
├── CLAUDE.md                  # This file
├── docs/                      # Course lecture notes (read-only, do not modify)
├── src/
│   ├── preprocessing.py       # Image loading, Gaussian blur, thresholding, contour extraction
│   ├── chain_code.py          # Freeman chain code encoding, cyclic normalization
│   ├── compatibility.py       # Pairwise edge-compatibility scoring
│   ├── relaxation.py          # Relaxation labeling implementation
│   ├── visualize.py           # Result rendering and assembly display
│   └── main.py                # Entry point: ties all stages together
├── data/
│   ├── fragments/             # Input fragment images (add your own test cases here)
│   └── sample/                # A small built-in sample set for quick testing
├── outputs/
│   ├── logs/                  # Per-run log files (timestamped)
│   └── results/               # Rendered assembly images (timestamped)
├── tests/
│   └── test_pipeline.py       # Basic sanity checks for each module
└── requirements.txt
```

Create this directory structure before writing any code.

---

## Running the Project

### Setup
```bash
pip install -r requirements.txt
```

`requirements.txt` should contain only:
```
opencv-python
numpy
matplotlib
scipy
Pillow
```

Do not add other dependencies without a clear reason tied to course material.

### Run on the sample dataset
```bash
python src/main.py --input data/sample --output outputs/results --log outputs/logs
```

### Run on custom fragment images
```bash
python src/main.py --input data/fragments/my_test_case --output outputs/results --log outputs/logs
```

### Run tests
```bash
python -m pytest tests/
```

---

## Logging

Every run must write a timestamped log file to `outputs/logs/`. The log must record:

- Which fragment images were loaded and their dimensions
- The chain code extracted for each fragment (truncated to 80 chars for readability)
- The full pairwise compatibility matrix
- The relaxation labeling convergence trace (score per iteration)
- The top-3 proposed assemblies with their confidence scores
- Total wall-clock time

Use Python's built-in `logging` module with `FileHandler`. Also mirror `INFO`-level messages to
stdout so the terminal shows progress during a run.

Example log filename format: `run_20240404_143021.log`

---

## Code Style

- Pure Python with NumPy/OpenCV; no deep learning frameworks.
- Each source file should have a module-level docstring explaining what it implements and which
  lecture it corresponds to.
- Function docstrings should reference the specific algorithm step they implement
  (e.g., `"Implements the chain code rotation normalization described in Lecture 72."`).
- No placeholder comments or TODO markers in submitted code.
- Variable names should be descriptive; avoid single-letter names except as loop indices.
- Keep each function under 40 lines; split logic into helpers where needed.

---

## Submission Checklist

Before submitting, verify:

- [ ] `python src/main.py --input data/sample ...` runs end-to-end without errors
- [ ] `outputs/logs/` contains at least one log file from a successful run
- [ ] `outputs/results/` contains rendered assembly images
- [ ] `python -m pytest tests/` passes all tests
- [ ] Every `.py` file has a module-level docstring referencing its lecture source
- [ ] `requirements.txt` is present and minimal
- [ ] `docs/` is present and unmodified
- [ ] No API keys, personal paths, or IDE-specific files are included

The submitted folder should be `icbl_final_project/` containing exactly the structure above.

---

## Algorithmic Notes for Implementation

### Chain Code (Lecture 72)
Encode each contour as a Freeman 8-directional chain. To achieve rotation invariance, normalize
the chain by finding its lexicographically smallest cyclic rotation. Two boundary segments are
directly comparable after this normalization by computing their edit distance.

### Compatibility Scoring
The compatibility between edge segment A of fragment i and edge segment B of fragment j is
computed as `1 - (edit_distance(A, B) / max(len(A), len(B)))`. A score near 1.0 means the
segments are geometrically similar and likely to be a true match.

### Relaxation Labeling (Lecture 53)
Each fragment-edge pair receives an initial label (tentative match partner). At each iteration,
the confidence of a label is updated based on the consistency of neighboring labels — if
surrounding fragments also agree on a compatible assembly, the label's confidence increases.
Iterate until convergence (delta < 1e-4) or a maximum of 50 iterations.

The update rule follows the course formulation:
```
P(i, λ) ← P(i, λ) · (1 + Q(i, λ)) / Σ_μ [P(i, μ) · (1 + Q(i, μ))]
```
where `Q(i, λ)` is the support from context (neighboring pair compatibilities).

### Good Continuation (Lecture 52)
When scoring candidate assemblies, apply a continuity bonus: assemblies where the joined boundary
forms a smooth curve (low curvature change at the join point) receive a higher overall score.
This directly instantiates the Gestalt principle of good continuation from Lecture 52.

---

## What Makes a Strong Project

A high-quality submission for this course will demonstrate:

1. **Algorithmic fidelity** — the implementation visibly matches the course algorithms, not just
   their outcomes. A grader reading `relaxation.py` should recognize the update rule from Lecture 53.
2. **Working end-to-end pipeline** — the system produces plausible assemblies on the sample data.
3. **Clear connection to course theory** — docstrings and log output make the mapping explicit.
4. **Clean, readable code** — no debugging artifacts, no commented-out blocks, no magic numbers.
5. **Reproducibility** — a fresh `pip install -r requirements.txt` followed by the run command
   should produce results without further configuration.
