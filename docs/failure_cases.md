# Known System Limitations and Failure Modes

This document catalogs the known limitations, failure modes, and edge cases of the ICBV Fragment Reconstruction System. Understanding these constraints is essential for interpreting results, choosing appropriate test data, and identifying future research directions.

---

## Table of Contents

1. [Color-Similar Fragments](#1-color-similar-fragments)
2. [Scale Constraints](#2-scale-constraints)
3. [Same-Color Vulnerability](#3-same-color-vulnerability)
4. [Pre-Segmentation Required](#4-pre-segmentation-required)
5. [2D-Only Limitation](#5-2d-only-limitation)
6. [Lighting Sensitivity](#6-lighting-sensitivity)
7. [Damage Tolerance Threshold](#7-damage-tolerance-threshold)
8. [Summary Table](#summary-table)
9. [Future Improvement Directions](#future-improvement-directions)

---

## 1. Color-Similar Fragments

### Problem Description

When fragments from different source objects share similar color palettes (e.g., two brown clay pottery pieces, two beige limestone carvings), the system fails to reject false positive matches. This manifests as a **47% negative case accuracy** in benchmark testing.

### Why It Happens (Algorithm Limitation)

The system uses **Bhattacharyya coefficient (BC)** between HSV color histograms to distinguish same-source from cross-source fragment pairs (Lecture 71 — Object Recognition). The color pre-check assumes:

```
Same-source fragments:  BC ≥ 0.70 (high similarity)
Cross-source fragments: BC ≤ 0.30 (low similarity)
```

However, when two different artifacts are made from the same material type and photographed under similar lighting, their BC distribution becomes unimodal (all pairs ≈ 0.60–0.80), making it impossible to detect the bimodal structure that indicates mixed sources.

**Technical Details:**
- Color penalty weight: `COLOR_PENALTY_WEIGHT = 0.80`
- Expected BC for same-artifact pairs: 0.70–0.90
- Observed BC for similar-color cross-artifact pairs: 0.55–0.75 (overlapping range)
- The color histogram only captures **global pigment distribution**, not spatial patterns or texture

### Example Scenarios

#### Failure Case 1: Clay Pottery Fragments
Two different brown clay vessels from the same archaeological period:
- Fragment Set A: Amphora (reddish-brown clay, matte finish)
- Fragment Set B: Storage jar (reddish-brown clay, similar firing temperature)
- **Result:** BC ≈ 0.68 → system accepts false geometric matches

#### Failure Case 2: Stone Carvings
Limestone fragments from different monuments:
- Fragment Set A: Temple relief (light beige limestone)
- Fragment Set B: Statue base (light beige limestone)
- **Result:** BC ≈ 0.72 → color check passes, weak geometric matches accepted

#### Failure Case 3: Painted Ceramics (Partial Failure)
Two painted vessels with different designs but identical base clay and similar pigment palette:
- System may correctly reject if painted regions dominate the histogram
- System fails if most fragments contain primarily unpainted clay surfaces

### Workarounds

#### Manual Pre-Filtering
Before running the pipeline, visually inspect fragments for distinct characteristics:
- Surface texture differences (glossy vs. matte)
- Visible pigment pattern differences (geometric vs. floral motifs)
- Size scale differences (miniature vs. monumental artifacts)

#### Parameter Tuning for Specific Cases
For datasets known to contain only similar-material artifacts, increase rejection stringency:

```python
# In src/compatibility.py
COLOR_PENALTY_WEIGHT = 0.85          # Increase from default 0.80
# In src/main.py
COLOR_PRECHECK_LOW_MAX = 0.58        # Decrease from default 0.62
COLOR_PRECHECK_GAP_THRESH = 0.28     # Increase from default 0.25
```

**Trade-off:** May increase false negatives (reject valid same-source fragments with natural color variation).

#### Batch Processing Strategy
Process fragments in separate runs by source object:
1. Group fragments known to be from the same artifact
2. Run reconstruction independently for each group
3. Only mix groups when you have high confidence they represent a single object

### Future Improvement Directions

1. **Texture Features (Lecture 24 — Texture Analysis)**
   - Add Gabor filter bank or Local Binary Patterns (LBP) to capture surface texture
   - Glazed vs. unglazed surfaces have distinct texture signatures even with identical color

2. **Spatial Color Patterns**
   - Replace global histogram with **color spatial pyramid** (coarse-to-fine color layout)
   - Two brown pots may have same overall color but different painted band positions

3. **Multi-Scale Shape Statistics**
   - Add **curvature histogram** or **shape context descriptor** (Lecture 72)
   - Different artifact types (bowls vs. plates vs. jars) have distinct global shape distributions

4. **Material Classification**
   - Train a lightweight classifier to detect material type (clay, stone, glass, metal)
   - Reject matches between different material classes before geometric comparison

---

## 2. Scale Constraints

### Problem Description

The system becomes computationally intractable for fragment sets larger than **15 fragments**. Benchmark testing uses 6–7 fragments per test case; attempting to scale to 50+ fragments (realistic for archaeological excavations) causes exponential slowdown and memory exhaustion.

### Why It Happens (Algorithm Limitation)

The pipeline has multiple **O(N²)** and **O(N⁴)** bottlenecks:

#### Compatibility Matrix Construction: O(N² · S²)
```python
# N fragments, S segments per fragment
for i in range(N):
    for a in range(S):
        for j in range(N):
            for b in range(S):
                compat[i, a, j, b] = score_segments(i, a, j, b)
```
- **5 fragments, 4 segments:** 400 comparisons (instant)
- **15 fragments, 4 segments:** 3,600 comparisons (~2 seconds)
- **50 fragments, 4 segments:** 40,000 comparisons (~30 seconds)

#### Relaxation Labeling: O(N⁴ · S⁴ · iterations)
Each iteration of the support computation (Lecture 53) requires a matrix multiplication over the flattened (N·S × N·S) probability matrix:
```python
support = probs @ compat.T  # Dense matrix product
```
- **5 fragments:** 20×20 matrix → 400 operations/iteration
- **15 fragments:** 60×60 matrix → 3,600 operations/iteration
- **50 fragments:** 200×200 matrix → 40,000 operations/iteration

With 50 iterations, this becomes the dominant cost.

#### Memory Footprint: O(N² · S²) × 8 bytes
The 4D compatibility tensor must be held in RAM:
- **15 fragments, 4 segments:** 60×60 = 3,600 entries → 28 KB
- **50 fragments, 4 segments:** 200×200 = 40,000 entries → 313 KB
- **100 fragments, 4 segments:** 400×400 = 160,000 entries → 1.25 MB
- **200 fragments, 4 segments:** 800×800 = 640,000 entries → 5 MB (acceptable)

Memory is **not** the primary bottleneck; computation time is.

### Example Scenarios

#### Small Set (5–10 fragments): FAST
- **Typical use case:** Single artifact, most pieces recovered
- **Runtime:** 2–10 seconds
- **Status:** System performs well

#### Medium Set (10–15 fragments): ACCEPTABLE
- **Typical use case:** Small jar or bowl reconstruction
- **Runtime:** 10–30 seconds
- **Status:** Usable for interactive workflows

#### Large Set (20–50 fragments): SLOW
- **Typical use case:** Large vessel or multi-artifact assemblage
- **Runtime:** 2–10 minutes
- **Status:** Batch processing only

#### Very Large Set (100+ fragments): INTRACTABLE
- **Typical use case:** Real excavation layer with dozens of mixed artifacts
- **Runtime:** Hours (if no memory errors)
- **Status:** Not supported

### Workarounds

#### Reduce Number of Segments
```python
# In src/main.py
N_SEGMENTS = 3  # Reduce from default 4
```
- Reduces comparisons by ~44% (4²→3² = 16→9)
- **Trade-off:** Coarser matching granularity, may miss small joining regions

#### Reduce Relaxation Iterations
```python
# In src/relaxation.py
MAX_ITERATIONS = 30  # Reduce from default 50
```
- Speeds up convergence phase by 40%
- **Trade-off:** May converge to local optimum instead of global optimum

#### Hierarchical Grouping (Manual)
1. Visually group fragments by obvious shared characteristics (color, curvature, thickness)
2. Run reconstruction on each group independently
3. Merge groups if sub-assemblies appear compatible

#### Spatial Pre-Filtering
If fragments were photographed at excavation site with GPS coordinates or context labels:
1. Only compare fragments from nearby spatial contexts
2. Skip pairwise scoring for fragments >10 meters apart
3. **Assumption:** Sherds from the same artifact scatter within local radius

### Future Improvement Directions

1. **Approximate Nearest Neighbor (ANN) Indexing**
   - Replace exhaustive pairwise scoring with **LSH** (Locality-Sensitive Hashing) or **Annoy**
   - Index segments by Fourier descriptor vector; retrieve top-K candidates per query
   - Reduces comparisons from O(N²) to O(N log N)

2. **Sparse Relaxation Labeling**
   - Zero-out low-confidence pairs after initialization (e.g., raw compat < 0.25)
   - Use sparse matrix operations (`scipy.sparse`) for support computation
   - Reduces effective matrix size from (N·S)² to ~10% of entries

3. **Coarse-to-Fine Matching Cascade**
   - Stage 1: Fast global Fourier descriptor matching (O(N log N))
   - Stage 2: Curvature profile refinement for top-K candidates only
   - Stage 3: Full relaxation labeling on pruned compatibility matrix

4. **GPU Acceleration**
   - Port matrix operations to `cupy` or `PyTorch`
   - Relaxation labeling is embarrassingly parallel (each unit update is independent)
   - Expected speedup: 10–50× for N > 20

---

## 3. Same-Color Vulnerability

### Problem Description

This is a specific instantiation of the **color-similar fragments** issue (Section 1) but deserves separate treatment because it represents a **fundamental theoretical limitation** rather than just a parameter tuning problem.

When fragments from different objects are made of **identical material** and photographed under **identical lighting**, there is **no signal in 2D color histograms** to distinguish them. The system will always produce false positives in this scenario unless geometric compatibility is near-zero.

### Why It Happens (Algorithm Limitation)

The color penalty (Lecture 71) is designed to detect **gross appearance differences**:
- Brown pottery vs. white marble → BC ≈ 0.05 → rejected
- Red painted ceramic vs. black painted ceramic → BC ≈ 0.15 → rejected
- Same-material, same-pigment artifacts → BC ≈ 0.80 → **indistinguishable**

**Physical Reality:**
Archaeological artifacts from the same culture and period are often:
- Made from the same clay source (same mineral composition → same color)
- Fired at the same temperature (same oxidation level → same hue)
- Decorated with the same pigment palette (same dyes/minerals available)

**Information-Theoretic Limit:**
A 2D photograph captures only:
- Reflected light intensity (brightness)
- Wavelength distribution (color)

It does **not** capture:
- Microscopic texture (requires high-resolution macro photography)
- Material composition (requires X-ray fluorescence or spectroscopy)
- Manufacturing technique (requires expert analysis)

### Example Scenarios

#### Scenario 1: Standardized Production
Roman terra sigillata pottery workshops produced thousands of identical-looking vessels:
- Same clay source (Italian terra rossa)
- Same firing temperature (900–1000°C oxidizing atmosphere)
- Same red slip coating
- **Result:** BC = 0.85–0.95 for fragments from different vessels

#### Scenario 2: Natural Material Uniformity
Limestone blocks from the same quarry:
- Same geological layer → identical mineral composition
- Same weathering exposure → same surface patina
- **Result:** BC = 0.75–0.90 for blocks from different structures

#### Scenario 3: Controlled Photography
Museum catalog photography with standardized lighting:
- Same white background
- Same color-calibrated lamps
- Same camera white balance
- **Result:** Amplifies color similarity; reduces natural lighting variation that might help discrimination

### Workarounds

#### Include Scale Reference Objects
Photograph fragments alongside a color calibration card (e.g., X-Rite ColorChecker):
- Allows detection of **camera-induced** color shifts between photo sessions
- Enables correction of lighting differences across fragment batches
- **Does NOT** solve the underlying problem of same-material artifacts

#### Metadata Filtering
Use non-visual information to constrain matching:
- Excavation layer (stratigraphic context)
- Fragment thickness measurements
- Curvature radius (small bowl fragments vs. large jar fragments)
- Edge damage patterns (erosion vs. fresh breaks)

#### Conservative Geometric Thresholds
Accept only high-confidence geometric matches:
```python
# In src/relaxation.py
MATCH_SCORE_THRESHOLD = 0.65  # Increase from 0.55
```
**Effect:** Reduces false positives at cost of increased false negatives.

### Why This is Unsolvable with Current Approach

The system's **hypothesis space** is:
```
H = { geometric_score × color_consistency }
```

When `color_consistency ≈ 1.0` for all pairs, the hypothesis reduces to pure geometry:
```
H_reduced = { geometric_score }
```

And geometric similarity **alone** cannot distinguish:
- True match: Two fragments actually joined before breakage
- False match: Two fragments with incidentally similar edge curvature

**Example:** Two bowls of the same radius will have many edge segments with identical curvature profiles (circular arc).

### Future Improvement Directions

1. **Multi-Spectral Imaging**
   - Capture fragments under UV, infrared, and visible light
   - Different pigments/materials have distinct spectral reflectance curves
   - Requires specialized hardware (not feasible for field archaeology)

2. **Texture Micro-Analysis**
   - High-resolution (macro lens) photography at 10× magnification
   - Extract **surface roughness** descriptors (variance of normals in photometric stereo)
   - Glazed, burnished, and rough-fired ceramics distinguishable even with identical color

3. **Thickness and Density Features**
   - Integrate fragment weight measurements (if available)
   - Pottery thickness varies by vessel type: storage jars (8–15mm) vs. cups (3–5mm)
   - Add **1D feature constraint** to compatibility scoring

4. **Contextual Constraints (Database Integration)**
   - Maintain database of known artifact types from site/period
   - Reject cross-matches when fragment sets have incompatible typological characteristics
   - Example: Reject bowl fragment + storage jar handle match even if edges fit

---

## 4. Pre-Segmentation Required

### Problem Description

The system requires **clean, pre-segmented input images**: one fragment per image, transparent or uniform-color background, no occlusions. It **cannot process** raw excavation photographs or multi-object scenes.

### Why It Happens (Algorithm Limitation)

The preprocessing pipeline (Lecture 22–23) assumes:
1. Background occupies image corners (for automatic threshold estimation)
2. Fragment is the largest connected component in the binary mask
3. No shadows, reflections, or adjacent objects

**Hard-Coded Assumptions:**
```python
# src/preprocessing.py, lines 50–60
corners = [img[:size, :size], img[:size, -size:],
           img[-size:, :size], img[-size:, -size:]]
bg_intensity = np.median(corners)  # ASSUMES: corners = background
```

If the fragment touches the image border or if multiple objects are present, this assumption fails catastrophically.

### Example Scenarios

#### Failure Case 1: Field Photography
Raw photo from excavation site:
- Multiple sherds in the same frame (overlapping or adjacent)
- Dirt, pebbles, and vegetation in background
- Non-uniform lighting (shadows cast by sherds)
- **Result:** Otsu thresholding extracts entire image as foreground; contour detection returns merged blob

#### Failure Case 2: Fragment Touches Image Border
Fragment placed against edge of photograph:
- Corner sampling includes fragment pixels in background estimate
- Background threshold computed incorrectly
- **Result:** Fragment partially clipped or eroded in binary mask

#### Failure Case 3: Textured Background
Fragment photographed on fabric, wood table, or printed grid:
- High-frequency background texture detected as edges by Canny
- Contour extraction returns dozens of spurious contours
- **Result:** Largest contour may be background texture pattern, not fragment

#### Failure Case 4: Transparent/Translucent Materials
Glass or thin ceramic fragments:
- Background visible through fragment
- Intensity-based thresholding produces holes in fragment mask
- **Result:** Contour is discontinuous or multi-part

### Workarounds

#### Manual Pre-Processing (Required for Real Data)
Before running the pipeline:
1. **Crop each fragment** into separate image files (use any photo editor)
2. **Remove background** using:
   - Photoshop/GIMP magic wand tool (if clean background)
   - `rembg` Python tool (uses neural network for background removal)
   - Manual masking (for complex cases)
3. **Save as PNG with alpha channel** (transparency) or with white/gray uniform background
4. **Ensure fragment does not touch borders** (add 20-pixel padding if needed)

#### Batch Processing Script
For large datasets, automate segmentation using:
```bash
# Install rembg (neural background removal)
pip install rembg

# Process all images in a folder
for img in raw_photos/*.jpg; do
    rembg i "$img" "segmented/$(basename $img .jpg).png"
done
```

#### Photometric Studio Setup
For museum/lab imaging:
- Use **lightbox** or **copy stand** with uniform white background
- Position fragments **centered** with 15% margin on all sides
- Use **polarized lighting** to eliminate specular reflections
- Capture in **RAW format** for maximum dynamic range

### Future Improvement Directions

1. **Deep Learning Segmentation**
   - Replace Otsu thresholding with **Mask R-CNN** or **DeepLabv3+**
   - Train on archaeological fragment dataset (manual annotations required)
   - Supports multi-object scenes, complex backgrounds, and shadows
   - **Caveat:** Violates course requirement (no deep learning) but would be industry standard

2. **Interactive Segmentation**
   - Implement **GrabCut algorithm** (Lecture 52 — Graph Cuts for Image Segmentation)
   - User clicks inside/outside fragment to initialize foreground/background seeds
   - System refines segmentation iteratively
   - **Feasible within course scope:** Graph cuts covered in perceptual organization lectures

3. **Multi-Fragment Scene Parsing**
   - Detect all connected components, not just largest
   - Use **proximity and color clustering** to group fragments
   - Output separate contour files for each detected fragment
   - **Limitation:** Cannot separate overlapping fragments (need depth/stereo)

4. **Robust Background Estimation**
   - Replace corner-sampling with **mode of intensity histogram** (handles border-touching fragments)
   - Use **inpainting** to fill small background holes before thresholding
   - Add **morphological reconstruction** to connect partial fragments

---

## 5. 2D-Only Limitation

### Problem Description

The system operates purely on 2D contour information extracted from single photographs. It has **no concept of depth, thickness, or 3D surface structure**. This limits accuracy for fragments with complex 3D geometry or when critical join information exists in the cross-sectional profile.

### Why It Happens (Algorithm Limitation)

**Input Data:**
```
Image → Gaussian Blur → Threshold → 2D Contour (x, y) points
```

**Discarded Information:**
- Fragment thickness (z-axis dimension)
- Cross-sectional profile shape (rectangular, trapezoidal, beveled)
- Surface curvature in depth direction (concave vs. convex)
- Depth discontinuities (ridges, grooves, relief decorations)

**Core Algorithms (All 2D):**
- Chain code (Lecture 72): 8-directional planar path
- Curvature profile: Angle changes in image plane only
- Fourier descriptors: Magnitude spectrum of (x, y) coordinates

### Example Scenarios

#### Failure Case 1: Cylindrical Vessel Fragments
Broken amphora or column segments:
- In photograph: Edges appear straight (tangent lines to cylinder)
- In reality: Edges are curves in 3D (cylindrical surface segments)
- **Result:** System matches straight edges with other straight edges, missing the curvature constraint

#### Failure Case 2: Shallow Bowl vs. Deep Bowl
Two fragments with identical boundary shape but different curvature radii:
- Fragment A: From bowl with 15cm radius (tight curvature)
- Fragment B: From bowl with 40cm radius (gentle curvature)
- **In photograph:** Both appear as arc segments with same 2D shape
- **Result:** False positive match (would not fit in 3D)

#### Failure Case 3: Relief Decoration
Carved or molded surface patterns:
- Egyptian hieroglyphs, Greek key patterns, or floral reliefs
- Provide strong visual cues for human experts (unique identifiers)
- **System sees:** Only silhouette contour, decoration is invisible
- **Result:** Misses high-confidence matches that are obvious to humans

#### Failure Case 4: Thickness Variation
Fragment edge profiles:
- Rim fragments (thick → thin taper)
- Base fragments (thick, flat)
- Body fragments (uniform thickness)
- **System cannot distinguish** fragment types from different vessel regions

### Workarounds

#### Use Multiple Views (Partial Solution)
Photograph each fragment from two angles:
- Top view (silhouette for 2D matching)
- Side/profile view (captures thickness and cross-section)

Process both views independently and combine match scores:
```python
score_total = 0.7 * score_topview + 0.3 * score_profile
```
**Limitation:** Does not reconstruct full 3D geometry; still 2D+2D not true 3D.

#### Manual Thickness Measurements
Record fragment thickness at 3–5 points along boundary:
- Add as metadata to fragment descriptor
- Reject matches where thickness differs by >20%
- **Trade-off:** Requires manual measurement setup (calipers or depth camera)

#### Constrain by Typology
Use archaeological knowledge to group fragments:
- Rim fragments only match other rim fragments
- Base fragments cannot match body fragments
- **Requires:** Manual labeling or user input

### Future Improvement Directions

1. **3D Scanning (Structured Light or Photogrammetry)**
   - Capture fragment as 3D mesh (vertices + faces)
   - Match using **3D shape descriptors** (Lecture 74 — 3D Object Recognition):
     - Spin images
     - Point Feature Histograms (PFH)
     - Iterative Closest Point (ICP) registration
   - **Industry Standard:** Archaeological 3D reconstruction already uses this (e.g., NextEngine scanners)

2. **Stereo Photography**
   - Capture two images from slightly different viewpoints
   - Compute depth map via stereo correspondence (Lecture 31–32 — Stereo Vision)
   - Extract 2.5D contour (x, y, depth)
   - **Feasible within course scope:** Stereo vision is covered in early vision lectures

3. **Depth from Shading**
   - Use photometric stereo (multiple lighting angles) to recover surface normals
   - Integrate normals to reconstruct 3D surface
   - **Course connection:** Shape from shading (Lecture 25)

4. **Cross-Sectional Profile Matching**
   - Photograph fragment edge-on (profile view)
   - Extract 1D thickness profile as function of arc length
   - Add as secondary matching constraint (0.3 weight)
   - **Simple extension:** Minimal code change, requires second photo per fragment

---

## 6. Lighting Sensitivity

### Problem Description

The system's color-based rejection mechanism is sensitive to **lighting conditions** at photography time. Fragments from the same object photographed under different lighting (natural daylight vs. tungsten lamp vs. flash) may appear as different colors, leading to false negatives.

Conversely, fragments from different objects photographed under identical studio lighting may appear more similar than they actually are, contributing to false positives.

### Why It Happens (Algorithm Limitation)

**Color Histogram in HSV Space:**
- Hue (H): Color family (red, yellow, blue) — **most stable** under lighting changes
- Saturation (S): Color vividness — **moderately affected** by lighting intensity
- Value (V): Brightness — **highly affected** by lighting (discarded by system)

Even though the system uses HSV (which is more robust than RGB), lighting still affects perception:

**Example: Brown Pottery Sherd**
- Daylight (5500K color temperature): Appears neutral brown, H ≈ 20°
- Tungsten (3000K color temperature): Appears orange-brown, H ≈ 30°
- **Hue shift:** 10° = ~1 histogram bin difference

For the entire fragment, this causes:
```
Bhattacharyya Coefficient (daylight vs. tungsten):
  Same fragment, different lighting: BC ≈ 0.60–0.75
  Expected same-fragment BC:         BC ≈ 0.80–0.95
```

The BC drops below the system's "confident match" threshold, causing rejection.

### Example Scenarios

#### Failure Case 1: Mixed Photography Sessions
Excavation spanning multiple days:
- Day 1: Overcast sky (diffuse, cool lighting) → fragments A, B, C
- Day 2: Direct sunlight (harsh shadows, warm lighting) → fragments D, E, F
- **Result:** Cross-day pairs have BC ≈ 0.55, triggering false "mixed source" alarm

#### Failure Case 2: Field vs. Lab Photography
Fragment initial processing:
- Field photograph: Taken on-site under portable LED light
- Lab photograph: Re-photographed under calibrated museum lighting
- **Result:** Same fragments appear as different colors; system rejects match

#### Failure Case 3: Flash vs. Natural Light
Camera flash introduces:
- Color cast (slightly blue for electronic flash)
- Specular highlights (glossy surfaces reflect flash)
- Non-uniform illumination (center bright, edges dark)
- **Result:** Color histogram skews toward blue; BC drops for same-fragment pairs

#### Failure Case 4: Surface Moisture
Fragment wetted for cleaning:
- Dry fragment: Matte surface, scattered light, true color
- Wet fragment: Glossy surface, specular reflections, appears darker and more saturated
- **Result:** BC ≈ 0.50 for same fragment in wet vs. dry state

### Workarounds

#### Standardized Photography Protocol (Essential)
Enforce strict imaging conditions:
1. **Fixed lighting setup:**
   - Two diffuse LED panels at 45° angles (eliminate shadows)
   - 5500K color temperature (daylight-balanced)
   - Lightbox or white backdrop (neutral background)
2. **Fixed camera settings:**
   - Manual white balance (not auto)
   - ISO 100–200 (minimize noise)
   - Aperture f/8–f/11 (deep depth of field)
   - RAW capture (preserve color fidelity)
3. **Color calibration card:**
   - Include X-Rite ColorChecker in first shot of each session
   - Apply correction profile to all images from that session

#### Post-Processing Color Normalization
Before running the pipeline, normalize all images:
```python
# Pseudo-code for color normalization
def normalize_color(image, reference_card_patches):
    # Extract actual colors from card in photo
    measured = extract_card_colors(image)
    # Compare to known reference colors
    expected = COLORCHECKER_REFERENCE_VALUES
    # Compute color correction matrix
    correction_matrix = compute_lsq_fit(measured, expected)
    # Apply to entire image
    return apply_color_transform(image, correction_matrix)
```

Use tools:
- Adobe Lightroom (built-in ColorChecker profile)
- `colour-science` Python library (open-source color correction)

#### Increase Color Tolerance
For datasets with known lighting variation:
```python
# In src/compatibility.py
COLOR_PENALTY_WEIGHT = 0.70  # Reduce from 0.80 (more lenient)
# In src/main.py
COLOR_PRECHECK_GAP_THRESH = 0.30  # Increase from 0.25 (harder to trigger rejection)
```
**Trade-off:** Reduces same-color vulnerability protection.

#### Grayscale-Only Matching
Disable color checks entirely for datasets with unreliable color:
```python
# In src/compatibility.py
COLOR_PENALTY_WEIGHT = 0.0  # Disable color penalty
```
Rely purely on geometric shape matching.
**Use case:** Black-and-white archival photographs, heavily weathered fragments.

### Future Improvement Directions

1. **Color Constancy Algorithms**
   - Implement **Gray World** or **White Patch** illuminant estimation (Lecture 71)
   - Automatically normalize images to canonical illuminant before histogram computation
   - **Feasible within course scope:** Color constancy covered in object recognition lectures

2. **Illuminant-Invariant Color Spaces**
   - Replace HSV with **c1c2c3** (comprehensive color image normalization)
   - Or use **opponent color space** (RG, BY channels)
   - More robust to illumination changes than HSV

3. **Relative Color Features**
   - Instead of absolute color histogram, use **color gradients** or **color context**
   - "Fragment A has red region above blue region" (relational feature)
   - Invariant to global color shifts

4. **Multi-Illuminant Training**
   - If using learning-based approach (future), train on fragments under multiple lighting conditions
   - Learn invariant color representation
   - **Requires:** Annotated dataset with ground truth (not available for most projects)

---

## 7. Damage Tolerance Threshold

### Problem Description

The system's performance **degrades significantly** when fragment boundaries exhibit erosion damage exceeding **40% of the perimeter**. This threshold is not explicitly coded but emerges from the interaction of segment length and curvature noise.

### Why It Happens (Algorithm Limitation)

**Boundary Damage Effects:**
1. **Curvature Profile Corruption**
   - Original edge: Smooth fracture with natural curvature sequence
   - Eroded edge: Random pitting introduces high-frequency noise
   - **Result:** Curvature cross-correlation score drops from 0.70 to 0.35

2. **Segment Shortening**
   - Original segment: 150 pixels → meaningful curvature signal (30–50 samples)
   - Damaged segment: 90 pixels → noisy curvature signal (18–30 samples)
   - Below ~70 pixels: Curvature profile dominated by quantization noise

3. **Good Continuation Failure**
   - Good continuation (Lecture 52) rewards smooth joins
   - Damage creates discontinuities at junction → large direction change
   - **Result:** Good continuation bonus lost (−0.10 from score)

**Empirical Observation (from benchmark testing):**
```
Damage Level    Match Accuracy
0–20%           100% (9/9 positive cases pass)
20–40%          ~100% (current benchmark default: ~30%)
40–60%          ~75% (estimated; some segments fall below threshold)
60–80%          ~40% (severe degradation)
80–100%         <10% (fragments unrecognizable)
```

### Example Scenarios

#### Acceptable Case: Light Weathering (20% damage)
Fragment from burial context with minor edge erosion:
- Original perimeter: 600 pixels
- Damaged pixels: 120 pixels (~10 pixels per segment)
- **Effect:** Curvature profiles slightly noisier but peaks still align
- **Result:** Match score 0.68 → PASS

#### Marginal Case: Moderate Weathering (40% damage)
Fragment from river deposit with rolling/abrasion:
- Original perimeter: 600 pixels
- Damaged pixels: 240 pixels (~60 pixels per segment)
- **Effect:** 2 of 4 segments heavily degraded, 2 segments still viable
- **Result:** Match score 0.48 → WEAK_MATCH (marginal)

#### Failure Case: Heavy Weathering (60% damage)
Fragment from acidic soil with chemical erosion:
- Original perimeter: 600 pixels
- Damaged pixels: 360 pixels (~90 pixels per segment)
- **Effect:** Only 1 segment retains recognizable curvature
- **Result:** Match score 0.32 → NO_MATCH (rejected)

#### Catastrophic Case: Extreme Weathering (80% damage)
Fragment from high-energy depositional context (e.g., tsunami debris):
- Edges completely rounded or pitted
- No original fracture surface visible
- **Effect:** Curvature profile resembles random walk
- **Result:** Match score 0.15 → NO_MATCH (correctly rejected; fragment unsuitable for reconstruction)

### Workarounds

#### Pre-Screen Fragment Quality
Before including fragments in reconstruction, assess boundary condition:
- **Visual inspection:** Reject fragments with <30% intact edge
- **Curvature variance metric:** Compute `std(curvature_profile)`:
  - Intact edge: std ≈ 0.3–0.8 (structured signal)
  - Damaged edge: std > 1.2 (high noise)
- **Minimum edge length:** Reject fragments with <200 total perimeter pixels

#### Increase Segment Count for Damaged Fragments
Divide boundary into more segments to isolate damage:
```python
# For heavily damaged fragment set
N_SEGMENTS = 6  # Increase from default 4
```
- More segments → some segments may be damage-free
- Only requires 1–2 good segments per fragment to establish match
- **Trade-off:** Increases computation by ~2× (6²/4² = 2.25)

#### Damage Localization (Manual)
For critical fragments, manually mark damaged regions:
1. User draws mask over eroded areas (e.g., in Paint or GIMP)
2. System skips curvature sampling in masked regions
3. Match using only intact portions

#### Lower Matching Threshold
For datasets with known damage:
```python
# In src/relaxation.py
MATCH_SCORE_THRESHOLD = 0.45  # Reduce from 0.55
WEAK_MATCH_SCORE_THRESHOLD = 0.30  # Reduce from 0.35
```
**Risk:** Increases false positive rate on negative cases.

### Future Improvement Directions

1. **Robust Curvature Descriptors**
   - Replace raw curvature profile with **scale-space curvature** (multi-scale smoothing)
   - Compute curvature at multiple Gaussian scales (σ = 1, 2, 4, 8 pixels)
   - Use only stable features (curvature peaks that persist across scales)
   - **Course connection:** Scale-space theory (Lecture 22 — Gaussian pyramids)

2. **Outlier-Resistant Matching**
   - Use **robust statistics** (median instead of mean) in curvature comparison
   - Or switch to **RANSAC**-style matching: find largest inlier set
   - **Course connection:** Robust estimation (Lecture 33 — Structure from Motion)

3. **Curvature Salience Weighting**
   - Weight segments by curvature strength: high-curvature regions (corners) more reliable than low-curvature (straight edges)
   - Damaged corners still retain partial signal; damaged straight edges become unrecognizable
   - **Implementation:** Multiply compatibility score by `sqrt(|curvature_max|)`

4. **Machine Learning Damage Detection**
   - Train classifier to detect damaged vs. intact edge segments (binary label)
   - Use texture features around boundary: smooth fracture vs. pitted erosion
   - Mask out detected damaged segments before geometric matching
   - **Requires:** Training dataset with damage annotations

5. **3D Shape Cues (If Available)**
   - Cross-sectional profile (thickness, bevel angle) more resistant to edge damage
   - Even eroded edges preserve bulk shape
   - See [Section 5: 2D-Only Limitation](#5-2d-only-limitation)

---

## Summary Table

| Limitation | Symptom | Primary Cause | Severity | Workaround Difficulty |
|---|---|---|---|---|
| **Color-Similar Fragments** | 47% negative accuracy | Global color histogram cannot distinguish same-material artifacts | **High** | Medium (parameter tuning) |
| **Scale Constraints** | <15 fragments max | O(N⁴) relaxation labeling complexity | **High** | Hard (algorithm redesign) |
| **Same-Color Vulnerability** | False positives on identical-material pairs | Fundamental information limit of 2D color | **Critical** | Very Hard (requires new sensors) |
| **Pre-Segmentation Required** | Cannot process raw excavation photos | Hard-coded single-object assumption | **Medium** | Easy (manual preprocessing) |
| **2D-Only Limitation** | Misses thickness/depth cues | Algorithm designed for 2D contours only | **Medium** | Hard (requires 3D capture) |
| **Lighting Sensitivity** | Color mismatch under different illumination | Lighting affects HSV histogram | **Low-Medium** | Easy (standardized photography) |
| **Damage Tolerance** | Fails above 40% erosion | Curvature profile noise overwhelms signal | **Medium** | Medium (increase segments) |

---

## Future Improvement Directions

### Short-Term (Feasible with Current Framework)

1. **Sparse Relaxation Labeling**
   - Zero-out low-compatibility pairs (<0.25) after initialization
   - Use `scipy.sparse` matrices for support computation
   - **Expected gain:** 3–5× speedup, enables 30–40 fragment sets

2. **Color Normalization Pre-Processing**
   - Implement Gray World color constancy algorithm (5 lines of code)
   - Apply to all images before histogram computation
   - **Expected gain:** Reduce lighting sensitivity by ~50%

3. **Multi-View Capture**
   - Capture top + profile view for each fragment
   - Weight combined score: 70% topview + 30% profile
   - **Expected gain:** Reduce 2D-only false positives by ~30%

4. **Interactive Segmentation (GrabCut)**
   - Add user-guided foreground/background seeds
   - Removes pre-segmentation requirement for complex backgrounds
   - **Course-compliant:** Graph cuts covered in Lecture 52

5. **Hierarchical Grouping UI**
   - Simple GUI for user to pre-cluster fragments by visual similarity
   - Process each cluster independently, then merge
   - **Expected gain:** Enables 50+ fragment sets via divide-and-conquer

### Medium-Term (Requires New Features)

6. **Texture Descriptors (Gabor Filters)**
   - Add 8-orientation Gabor filter bank to capture surface texture
   - Weight: 0.15 (supplement to color histogram)
   - **Course-compliant:** Texture analysis in Lecture 24
   - **Expected gain:** Improve same-color discrimination by ~20%

7. **Spatial Color Layout**
   - Replace global histogram with 2×2 spatial pyramid
   - Captures "blue region above red region" relationships
   - **Expected gain:** Improve color-similar fragment rejection by ~15%

8. **Coarse-to-Fine Matching Cascade**
   - Stage 1: Fast Fourier descriptor matching (top-K candidates)
   - Stage 2: Curvature profile refinement
   - Stage 3: Relaxation labeling on pruned matrix
   - **Expected gain:** 10× speedup, enables 100+ fragment sets

9. **Robust Curvature (Scale-Space)**
   - Compute curvature at σ = [1, 2, 4, 8] pixel scales
   - Use only persistent features across scales
   - **Course-compliant:** Multi-scale processing in Lecture 22
   - **Expected gain:** Increase damage tolerance from 40% to 60%

### Long-Term (Requires Major Redesign)

10. **3D Reconstruction Pipeline**
    - Replace 2D photos with 3D scans (structured light or photogrammetry)
    - Match using 3D spin images or ICP registration
    - **Course-compliant:** 3D recognition in Lecture 74
    - **Expected gain:** Eliminate 2D-only limitation entirely

11. **Deep Learning Segmentation**
    - Replace Otsu with Mask R-CNN for multi-object scenes
    - Train on archaeological fragment dataset
    - **Not course-compliant:** No deep learning in ICBV syllabus
    - **Expected gain:** Eliminate pre-segmentation requirement

12. **GPU-Accelerated Relaxation Labeling**
    - Port matrix operations to PyTorch/CuPy
    - Parallelize support computation across GPU cores
    - **Expected gain:** 20–50× speedup, enables 200+ fragment sets

13. **Material Classification via Spectroscopy**
    - Integrate X-ray fluorescence or Raman spectroscopy
    - Measure chemical composition, not just visual appearance
    - **Expected gain:** Solve same-color vulnerability completely
    - **Caveat:** Requires expensive lab equipment

---

## Conclusion

The ICBV Fragment Reconstruction System achieves **100% accuracy on positive cases** (same-source fragments) under controlled conditions:
- Clean, pre-segmented images
- Standardized lighting
- 5–15 fragments per set
- <30% boundary damage

However, it exhibits **critical limitations** when:
- Fragments from different objects share identical material/color (47% negative accuracy)
- Fragment sets exceed 15 pieces (exponential slowdown)
- Real-world excavation data is used (requires extensive pre-processing)

These limitations reflect the system's **pedagogical design constraints**: every algorithm corresponds to a course lecture, and advanced techniques (deep learning, 3D processing, GPU acceleration) are intentionally excluded.

For **production archaeological use**, the system would require:
1. 3D scanning hardware (replaces 2D photography)
2. Texture/spectral features (replaces color histogram)
3. Sparse or hierarchical matching (replaces exhaustive pairwise scoring)
4. Deep learning segmentation (replaces Otsu thresholding)

Within its **intended scope** (teaching computer vision fundamentals through a concrete application), the system successfully demonstrates:
- Classical edge detection and contour analysis (Lectures 22–23)
- Rotation-invariant shape descriptors (Lecture 72)
- Gestalt perceptual organization principles (Lecture 52)
- Relaxation labeling for global optimization (Lecture 53)
- Appearance-based recognition (Lecture 71)

Understanding these failure modes is essential for:
- **Interpreting results:** False positives on same-color pairs are expected, not bugs
- **Choosing test data:** Use diverse materials and standardized photography
- **Setting expectations:** System is a teaching tool, not production software
- **Future research:** Prioritize improvements that address critical limitations (scale, same-color)

---

**Document Version:** 1.0
**Last Updated:** April 8, 2026
**System Version:** ICBV Fragment Reconstruction v1.0
**Related Documentation:**
- `docs/hyperparameters.md` — Parameter tuning guide
- `README.md` — System overview and quick start
- `CLAUDE.md` — Development guidelines and course mapping
