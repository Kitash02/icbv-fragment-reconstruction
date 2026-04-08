# BACKUP SOLUTIONS AND ALTERNATIVE APPROACHES

**Document Purpose:** Complete alternative algorithms for autonomous fallback when primary approaches fail

**Fallback Trigger Conditions:**
- Feature shows poor separation (Cohen's d < 0.5)
- Bhattacharyya Coefficient too high for cross-source pairs (> 0.85)
- High variance within same-source pairs (std > 0.20)
- Accuracy targets not met after parameter tuning

---

## 1. TEXTURE ALTERNATIVES (If LBP Fails)

### When to Switch from LBP

**Trigger Conditions:**
```python
def should_switch_from_lbp(bc_same_source, bc_diff_source):
    """
    Determine if LBP provides sufficient discrimination
    """
    mean_same = np.mean(bc_same_source)
    mean_diff = np.mean(bc_diff_source)

    # Poor separation
    if mean_diff > 0.85:
        return True, "No discrimination - diff-source BC too high"

    # Insufficient gap
    if (mean_same - mean_diff) < 0.15:
        return True, "Insufficient separation - gap < 0.15"

    # High variance (noisy feature)
    if np.std(bc_same_source) > 0.20:
        return True, "High variance - unstable feature"

    return False, "LBP acceptable"
```

---

### ALTERNATIVE 1: GLCM (Gray-Level Co-occurrence Matrix)

**Description:** Haralick texture features from spatial pixel relationships

**Advantages over LBP:**
- More robust to illumination changes
- Captures spatial relationships (not just local patterns)
- Produces compact feature vector (4-14 features)

**Disadvantages:**
- Slower computation (full image co-occurrence)
- Less rotation invariant
- More parameters to tune

**Implementation:**

```python
import numpy as np
from skimage.feature import graycomatrix, graycoprops

def compute_glcm_features(image_gray, distances=[1, 2, 3],
                          angles=[0, np.pi/4, np.pi/2, 3*np.pi/4]):
    """
    Compute Haralick texture features using GLCM

    Parameters:
    -----------
    image_gray : ndarray
        Grayscale image (8-bit)
    distances : list
        Pixel pair distances (default: [1, 2, 3])
    angles : list
        Pixel pair angles in radians (default: 0, 45, 90, 135 degrees)

    Returns:
    --------
    features : ndarray
        [contrast, dissimilarity, homogeneity, energy, correlation, ASM]
    """
    # Ensure 8-bit range
    if image_gray.max() > 255:
        image_gray = (image_gray * 255).astype(np.uint8)

    # Compute GLCM
    glcm = graycomatrix(
        image_gray,
        distances=distances,
        angles=angles,
        levels=256,
        symmetric=True,
        normed=True
    )

    # Extract features (average over distances and angles)
    features = []

    # 1. Contrast: measures local intensity variation
    contrast = graycoprops(glcm, 'contrast').mean()
    features.append(contrast)

    # 2. Dissimilarity: similar to contrast but linear
    dissimilarity = graycoprops(glcm, 'dissimilarity').mean()
    features.append(dissimilarity)

    # 3. Homogeneity: measures uniformity
    homogeneity = graycoprops(glcm, 'homogeneity').mean()
    features.append(homogeneity)

    # 4. Energy: measures textural uniformity
    energy = graycoprops(glcm, 'energy').mean()
    features.append(energy)

    # 5. Correlation: measures linear dependency
    correlation = graycoprops(glcm, 'correlation').mean()
    features.append(correlation)

    # 6. ASM (Angular Second Moment): similar to energy
    asm = graycoprops(glcm, 'ASM').mean()
    features.append(asm)

    return np.array(features)


def compute_glcm_similarity(features1, features2):
    """
    Compute similarity between two GLCM feature vectors

    Returns: similarity score [0, 1], higher = more similar
    """
    # Euclidean distance
    distance = np.linalg.norm(features1 - features2)

    # Normalize by feature vector magnitude
    max_distance = np.linalg.norm(features1) + np.linalg.norm(features2)

    if max_distance < 1e-8:
        return 1.0

    # Convert distance to similarity
    similarity = 1.0 / (1.0 + distance / max_distance)

    return similarity


def integrate_glcm_into_pipeline(fragment1, fragment2):
    """
    Replace LBP with GLCM in compatibility matrix computation
    """
    # Extract fragment images
    img1_gray = cv2.cvtColor(fragment1.image, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(fragment2.image, cv2.COLOR_BGR2GRAY)

    # Compute GLCM features
    glcm1 = compute_glcm_features(img1_gray)
    glcm2 = compute_glcm_features(img2_gray)

    # Compute similarity
    texture_similarity = compute_glcm_similarity(glcm1, glcm2)

    # Apply exponential penalty (like LBP)
    texture_penalty = texture_similarity ** 2.0

    return texture_penalty
```

**Parameter Recommendations:**

```python
GLCM_CONFIG_PRIMARY = {
    'distances': [1, 2, 3],  # Multi-scale (1-3 pixels)
    'angles': [0, np.pi/4, np.pi/2, 3*np.pi/4],  # 4 orientations
    'levels': 256,  # Full 8-bit range
    'exponential_power': 2.0
}

GLCM_CONFIG_FAST = {
    'distances': [1, 2],  # Fewer scales
    'angles': [0, np.pi/2],  # 2 orientations only
    'levels': 64,  # Quantize to 64 levels (faster)
    'exponential_power': 2.0
}

GLCM_CONFIG_FINE = {
    'distances': [1, 2, 3, 4, 5],  # More scales
    'angles': [0, np.pi/4, np.pi/2, 3*np.pi/4],
    'levels': 256,
    'exponential_power': 2.5  # Stronger penalty
}
```

**When to use GLCM:**
- LBP BC shows no separation (cross-source BC > 0.85)
- Pottery has coarse texture (few uniform patterns)
- Need compact feature vector (6 values vs 26 histogram bins)

---

### ALTERNATIVE 2: Gabor Filters

**Description:** Multi-scale, multi-orientation filter bank for texture analysis

**Advantages over LBP:**
- Excellent for directional textures (wheel marks, coiling)
- Multi-scale (captures both fine and coarse patterns)
- Biologically inspired (similar to visual cortex)

**Disadvantages:**
- More computationally expensive
- Many parameters (frequency, orientation, bandwidth)
- Filter bank design requires domain knowledge

**Implementation:**

```python
from skimage.filters import gabor

def compute_gabor_features(image_gray, frequencies=[0.1, 0.2, 0.4],
                          thetas=[0, np.pi/4, np.pi/2, 3*np.pi/4]):
    """
    Compute Gabor filter bank features

    Parameters:
    -----------
    image_gray : ndarray
        Grayscale image (normalized to [0, 1])
    frequencies : list
        Filter frequencies (cycles per pixel)
    thetas : list
        Filter orientations (radians)

    Returns:
    --------
    features : ndarray
        [mean, std] for each (frequency, orientation) combination
    """
    # Normalize image
    image_norm = image_gray.astype(float) / 255.0

    features = []

    for freq in frequencies:
        for theta in thetas:
            # Apply Gabor filter
            filtered_real, filtered_imag = gabor(
                image_norm,
                frequency=freq,
                theta=theta,
                bandwidth=1.0,  # Standard bandwidth
                sigma_x=None,   # Auto-compute from frequency
                sigma_y=None
            )

            # Compute response magnitude
            magnitude = np.sqrt(filtered_real**2 + filtered_imag**2)

            # Extract statistics
            features.append(magnitude.mean())
            features.append(magnitude.std())

    return np.array(features)


def compute_gabor_similarity(features1, features2):
    """
    Compute similarity between Gabor feature vectors
    """
    # Cosine similarity (better for high-dimensional features)
    dot_product = np.dot(features1, features2)
    norm_product = np.linalg.norm(features1) * np.linalg.norm(features2)

    if norm_product < 1e-8:
        return 0.0

    similarity = dot_product / norm_product

    # Map [-1, 1] to [0, 1]
    similarity = (similarity + 1.0) / 2.0

    return similarity


def integrate_gabor_into_pipeline(fragment1, fragment2):
    """
    Replace LBP with Gabor in compatibility matrix
    """
    img1_gray = cv2.cvtColor(fragment1.image, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(fragment2.image, cv2.COLOR_BGR2GRAY)

    gabor1 = compute_gabor_features(img1_gray)
    gabor2 = compute_gabor_features(img2_gray)

    texture_similarity = compute_gabor_similarity(gabor1, gabor2)
    texture_penalty = texture_similarity ** 2.0

    return texture_penalty
```

**Parameter Recommendations:**

```python
GABOR_CONFIG_PRIMARY = {
    'frequencies': [0.1, 0.2, 0.4],  # Low, mid, high
    'thetas': [0, np.pi/4, np.pi/2, 3*np.pi/4],  # 4 orientations
    'bandwidth': 1.0,  # Standard
    'exponential_power': 2.0
}
# Feature size: 3 freq * 4 orient * 2 stats = 24 features

GABOR_CONFIG_DIRECTIONAL = {
    'frequencies': [0.2],  # Single scale
    'thetas': [0, np.pi/8, np.pi/4, 3*np.pi/8, np.pi/2,
               5*np.pi/8, 3*np.pi/4, 7*np.pi/8],  # 8 orientations
    'bandwidth': 1.0,
    'exponential_power': 2.5
}
# Use for: Strong directional patterns (wheel marks)

GABOR_CONFIG_MULTISCALE = {
    'frequencies': [0.05, 0.1, 0.2, 0.4, 0.8],  # 5 scales
    'thetas': [0, np.pi/2],  # 2 orientations only
    'bandwidth': 1.0,
    'exponential_power': 2.0
}
# Use for: Scale-dependent texture
```

**When to use Gabor:**
- Pottery has strong directional texture (wheel marks, brush strokes)
- LBP fails to capture orientation information
- Multi-scale analysis needed

---

### ALTERNATIVE 3: HOG (Histogram of Oriented Gradients)

**Description:** Edge orientation histogram (originally for object detection)

**Advantages:**
- Captures edge structure and texture simultaneously
- Robust to illumination changes
- Fast computation

**Disadvantages:**
- Designed for object detection (not texture matching)
- Large feature vectors (can be 1000+ dimensions)
- Less established for fragment matching

**Implementation:**

```python
from skimage.feature import hog

def compute_hog_features(image_gray):
    """
    Compute HOG features for texture characterization

    Returns:
    --------
    features : ndarray
        HOG descriptor (normalized histogram)
    """
    features = hog(
        image_gray,
        orientations=9,          # 9 orientation bins
        pixels_per_cell=(16, 16),  # Cell size
        cells_per_block=(2, 2),    # Block normalization
        block_norm='L2-Hys',       # Histogram normalization
        visualize=False,
        feature_vector=True
    )

    return features


def compute_hog_similarity(features1, features2):
    """
    Compute similarity using cosine distance
    """
    dot_product = np.dot(features1, features2)
    norm_product = np.linalg.norm(features1) * np.linalg.norm(features2)

    if norm_product < 1e-8:
        return 0.0

    similarity = dot_product / norm_product
    similarity = (similarity + 1.0) / 2.0

    return similarity
```

**When to use HOG:**
- Need to capture both edge and texture
- Fragments have distinctive shape + texture combination
- Fast computation required

---

## 2. COLOR ALTERNATIVES (If Lab Fails)

### When to Switch from Lab

**Trigger Conditions:**
```python
def should_switch_from_lab(bc_same_source, bc_diff_source):
    """
    Determine if Lab provides sufficient discrimination
    """
    mean_same = np.mean(bc_same_source)
    mean_diff = np.mean(bc_diff_source)

    # Poor separation
    if mean_diff > 0.85:
        return True, "No discrimination"

    # Too similar across all pairs
    if mean_same > 0.95 and mean_diff > 0.85:
        return True, "All pairs too similar - may need different color space"

    return False, "Lab acceptable"
```

---

### ALTERNATIVE 1: Opponent Color Space

**Description:** Red-Green, Blue-Yellow, Intensity channels (biologically inspired)

**Advantages over Lab:**
- Decorrelates color channels better for some materials
- More robust to chromatic adaptation
- Better for earth tones (brown, tan, ochre)

**Implementation:**

```python
def compute_opponent_color_features(image_bgr):
    """
    Compute opponent color space features

    Opponent color space:
    - I (Intensity): (R + G + B) / 3
    - RG (Red-Green): R - G
    - BY (Blue-Yellow): 0.5*(R + G) - B

    Returns:
    --------
    features : ndarray
        [I_mean, I_std, RG_mean, RG_std, BY_mean, BY_std]
    """
    # Convert BGR to RGB
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB).astype(float)

    R = rgb[:, :, 0]
    G = rgb[:, :, 1]
    B = rgb[:, :, 2]

    # Compute opponent channels
    I = (R + G + B) / 3.0
    RG = R - G
    BY = 0.5 * (R + G) - B

    # Extract statistics
    features = np.array([
        I.mean(),
        I.std(),
        RG.mean(),
        RG.std(),
        BY.mean(),
        BY.std()
    ])

    return features


def compute_opponent_color_histogram(image_bgr, bins_I=16, bins_RG=8, bins_BY=8):
    """
    Compute 3D histogram in opponent color space

    Returns:
    --------
    histogram : ndarray
        Flattened 3D histogram (normalized)
    """
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB).astype(float)

    R = rgb[:, :, 0]
    G = rgb[:, :, 1]
    B = rgb[:, :, 2]

    # Compute opponent channels
    I = (R + G + B) / 3.0
    RG = R - G
    BY = 0.5 * (R + G) - B

    # Normalize to [0, 255] range
    I = np.clip(I, 0, 255).astype(np.uint8)
    RG = np.clip(RG + 128, 0, 255).astype(np.uint8)  # Shift to positive
    BY = np.clip(BY + 128, 0, 255).astype(np.uint8)

    # Compute 3D histogram
    hist, _ = np.histogramdd(
        np.column_stack([I.ravel(), RG.ravel(), BY.ravel()]),
        bins=[bins_I, bins_RG, bins_BY],
        range=[[0, 256], [0, 256], [0, 256]]
    )

    # Normalize
    hist = hist.flatten()
    hist = hist / (hist.sum() + 1e-8)

    return hist


def compute_opponent_similarity(hist1, hist2):
    """
    Compute Bhattacharyya Coefficient for opponent histograms
    """
    bc = np.sum(np.sqrt(hist1 * hist2))
    return bc


def integrate_opponent_into_pipeline(fragment1, fragment2):
    """
    Replace Lab with Opponent Color in compatibility matrix
    """
    hist1 = compute_opponent_color_histogram(fragment1.image)
    hist2 = compute_opponent_color_histogram(fragment2.image)

    color_similarity = compute_opponent_similarity(hist1, hist2)
    color_penalty = color_similarity ** 2.5

    return color_penalty
```

**Parameter Recommendations:**

```python
OPPONENT_CONFIG_PRIMARY = {
    'bins_I': 16,   # Intensity (similar to Lab L)
    'bins_RG': 8,   # Red-Green
    'bins_BY': 8,   # Blue-Yellow
    'exponential_power': 2.5
}

OPPONENT_CONFIG_COARSE = {
    'bins_I': 12,
    'bins_RG': 6,
    'bins_BY': 6,
    'exponential_power': 2.5
}

OPPONENT_CONFIG_FINE = {
    'bins_I': 20,
    'bins_RG': 10,
    'bins_BY': 10,
    'exponential_power': 2.5
}
```

**When to use Opponent Color:**
- Lab shows poor separation for earth tones
- Need better decorrelation of color channels
- Pottery has subtle hue variations

---

### ALTERNATIVE 2: Normalized RGB

**Description:** RGB normalized by sum (removes illumination intensity)

**Advantages:**
- Illumination invariant
- Simple computation
- Good for materials with consistent hue but varying brightness

**Implementation:**

```python
def compute_normalized_rgb_histogram(image_bgr, bins_per_channel=16):
    """
    Compute histogram in normalized RGB space

    Normalized RGB:
    - r = R / (R + G + B)
    - g = G / (R + G + B)
    - b = B / (R + G + B)
    Note: r + g + b = 1, so only 2 channels independent

    Returns:
    --------
    histogram : ndarray
        2D histogram (r, g) - b is redundant
    """
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB).astype(float)

    # Compute sum
    rgb_sum = rgb.sum(axis=2, keepdims=True) + 1e-8

    # Normalize
    rgb_norm = rgb / rgb_sum

    # Extract r and g channels (b is redundant)
    r = rgb_norm[:, :, 0]
    g = rgb_norm[:, :, 1]

    # Compute 2D histogram
    hist, _, _ = np.histogram2d(
        r.ravel(),
        g.ravel(),
        bins=[bins_per_channel, bins_per_channel],
        range=[[0, 1], [0, 1]]
    )

    # Normalize
    hist = hist.flatten()
    hist = hist / (hist.sum() + 1e-8)

    return hist


def integrate_normalized_rgb_into_pipeline(fragment1, fragment2):
    """
    Replace Lab with Normalized RGB
    """
    hist1 = compute_normalized_rgb_histogram(fragment1.image)
    hist2 = compute_normalized_rgb_histogram(fragment2.image)

    bc = np.sum(np.sqrt(hist1 * hist2))
    color_penalty = bc ** 2.5

    return color_penalty
```

**When to use Normalized RGB:**
- Fragments have varying illumination (outdoor photos)
- Consistent hue but different brightness
- Simpler alternative to Lab

---

### ALTERNATIVE 3: HSV with Better Binning

**Description:** Keep HSV but optimize bin allocation

**Current Issue:** Equal bins across H, S, V may not be optimal

**Improved Strategy:**

```python
def compute_adaptive_hsv_histogram(image_bgr):
    """
    HSV histogram with non-uniform binning

    Strategy:
    - H (Hue): More bins in earth-tone range (10-40 degrees)
    - S (Saturation): Fewer bins (pottery low saturation)
    - V (Value): More bins (main discrimination axis)
    """
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

    H = hsv[:, :, 0]  # 0-179 in OpenCV
    S = hsv[:, :, 1]  # 0-255
    V = hsv[:, :, 2]  # 0-255

    # Define non-uniform bins
    # H: Focus on earth tones (10-40 degrees → 5-20 in OpenCV scale)
    h_bins = np.array([0, 5, 10, 15, 20, 30, 60, 90, 120, 150, 180])
    s_bins = np.linspace(0, 256, 9)  # 8 bins (low saturation)
    v_bins = np.linspace(0, 256, 17)  # 16 bins (main axis)

    # Compute 3D histogram with non-uniform bins
    hist, _ = np.histogramdd(
        np.column_stack([H.ravel(), S.ravel(), V.ravel()]),
        bins=[h_bins, s_bins, v_bins]
    )

    # Normalize
    hist = hist.flatten()
    hist = hist / (hist.sum() + 1e-8)

    return hist


def integrate_adaptive_hsv_into_pipeline(fragment1, fragment2):
    """
    Replace uniform HSV with adaptive HSV
    """
    hist1 = compute_adaptive_hsv_histogram(fragment1.image)
    hist2 = compute_adaptive_hsv_histogram(fragment2.image)

    bc = np.sum(np.sqrt(hist1 * hist2))
    color_penalty = bc ** 2.5

    return color_penalty
```

**When to use Adaptive HSV:**
- Lab provides minimal improvement over HSV
- Earth-tone hue range very limited
- Want to stay with familiar color space

---

## 3. COMPLEXITY ALTERNATIVES (If Fractal Fails)

### When to Switch from Fractal

**Trigger Conditions:**
```python
def should_switch_from_fractal(fractal_same_source, fractal_diff_source):
    """
    Determine if fractal dimension provides reliable discrimination
    """
    # High variance (unstable)
    if np.std(fractal_same_source) > 0.15:
        return True, "High variance - unreliable feature"

    # Poor separation
    mean_same = np.mean(fractal_same_source)
    mean_diff = np.mean(fractal_diff_source)

    if abs(mean_same - mean_diff) < 0.05:
        return True, "Insufficient separation"

    return False, "Fractal acceptable"
```

---

### ALTERNATIVE 1: Perimeter-to-Area Ratio

**Description:** Simple geometric complexity measure

**Advantages:**
- Fast computation
- Stable (low variance)
- Intuitive interpretation

**Implementation:**

```python
def compute_complexity_ratio(contour):
    """
    Compute normalized perimeter-to-area ratio

    Normalized by circle:
    - Circle: ratio = 1.0
    - More complex shapes: ratio > 1.0

    Returns:
    --------
    complexity : float
        Normalized complexity (1.0 = circle)
    """
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, closed=True)

    if area < 1e-8:
        return 1.0

    # Theoretical circle with same area
    circle_perimeter = 2 * np.sqrt(np.pi * area)

    # Normalize
    complexity = perimeter / circle_perimeter

    return complexity


def compute_complexity_similarity(complexity1, complexity2):
    """
    Compute similarity between complexity values

    Returns:
    --------
    similarity : float
        [0, 1], higher = more similar
    """
    # Absolute difference
    diff = abs(complexity1 - complexity2)

    # Convert to similarity (decay function)
    similarity = np.exp(-diff)

    return similarity


def integrate_complexity_into_pipeline(fragment1, fragment2):
    """
    Replace fractal with complexity ratio
    """
    comp1 = compute_complexity_ratio(fragment1.contour)
    comp2 = compute_complexity_ratio(fragment2.contour)

    complexity_similarity = compute_complexity_similarity(comp1, comp2)
    complexity_penalty = complexity_similarity ** 0.5

    return complexity_penalty
```

**When to use Complexity Ratio:**
- Fractal dimension too noisy
- Need simple, stable metric
- Edge complexity mainly due to overall shape (not fine texture)

---

### ALTERNATIVE 2: Bending Energy

**Description:** Integral of squared curvature (measures edge smoothness)

**Advantages:**
- Physically motivated (elastic energy)
- Captures smoothness vs roughness
- Less sensitive to noise than fractal

**Implementation:**

```python
def compute_bending_energy(contour):
    """
    Compute bending energy from curvature profile

    Bending energy = ∫ κ² ds
    where κ is curvature

    Returns:
    --------
    energy : float
        Total bending energy (higher = more curved/complex)
    """
    # Compute curvature
    curvature = compute_curvature(contour)

    # Bending energy: integral of curvature squared
    energy = np.sum(curvature ** 2)

    # Normalize by contour length
    perimeter = cv2.arcLength(contour, closed=True)
    energy_normalized = energy / (perimeter + 1e-8)

    return energy_normalized


def compute_curvature(contour):
    """
    Compute discrete curvature at each point

    Curvature κ = |dθ/ds| where θ is tangent angle
    """
    # Extract points
    points = contour.squeeze()

    if len(points) < 3:
        return np.array([0.0])

    # Compute tangent angles
    angles = []
    for i in range(len(points)):
        p_prev = points[(i - 1) % len(points)]
        p_curr = points[i]
        p_next = points[(i + 1) % len(points)]

        # Vectors
        v1 = p_curr - p_prev
        v2 = p_next - p_curr

        # Angles
        angle1 = np.arctan2(v1[1], v1[0])
        angle2 = np.arctan2(v2[1], v2[0])

        # Angle change
        d_angle = angle2 - angle1

        # Wrap to [-π, π]
        d_angle = (d_angle + np.pi) % (2 * np.pi) - np.pi

        angles.append(abs(d_angle))

    return np.array(angles)


def compute_bending_similarity(energy1, energy2):
    """
    Compute similarity between bending energies
    """
    # Log ratio (more stable for large values)
    ratio = (energy1 + 1e-8) / (energy2 + 1e-8)
    log_ratio = np.log(ratio)

    # Convert to similarity
    similarity = np.exp(-abs(log_ratio))

    return similarity


def integrate_bending_into_pipeline(fragment1, fragment2):
    """
    Replace fractal with bending energy
    """
    energy1 = compute_bending_energy(fragment1.contour)
    energy2 = compute_bending_energy(fragment2.contour)

    bending_similarity = compute_bending_similarity(energy1, energy2)
    bending_penalty = bending_similarity ** 0.5

    return bending_penalty
```

**When to use Bending Energy:**
- Fractal too noisy
- Need smooth vs rough discrimination
- Physically meaningful feature

---

### ALTERNATIVE 3: Multi-Scale Edge Histogram

**Description:** Edge orientation histogram at multiple scales

**Implementation:**

```python
def compute_multiscale_edge_histogram(image_gray, scales=[1, 2, 4]):
    """
    Compute edge orientation histogram at multiple scales

    Returns:
    --------
    histogram : ndarray
        Concatenated histograms from all scales
    """
    histograms = []

    for scale in scales:
        # Blur at current scale
        if scale > 1:
            blurred = cv2.GaussianBlur(image_gray, (0, 0), sigmaX=scale)
        else:
            blurred = image_gray

        # Compute gradients
        gx = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)

        # Compute magnitude and orientation
        magnitude = np.sqrt(gx**2 + gy**2)
        orientation = np.arctan2(gy, gx)

        # Histogram of orientations (weighted by magnitude)
        hist, _ = np.histogram(
            orientation,
            bins=12,  # 12 bins (30° each)
            range=(-np.pi, np.pi),
            weights=magnitude
        )

        # Normalize
        hist = hist / (hist.sum() + 1e-8)
        histograms.append(hist)

    # Concatenate all scales
    combined = np.concatenate(histograms)

    return combined


def integrate_multiscale_edge_into_pipeline(fragment1, fragment2):
    """
    Replace fractal with multi-scale edge histogram
    """
    img1_gray = cv2.cvtColor(fragment1.image, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(fragment2.image, cv2.COLOR_BGR2GRAY)

    hist1 = compute_multiscale_edge_histogram(img1_gray)
    hist2 = compute_multiscale_edge_histogram(img2_gray)

    bc = np.sum(np.sqrt(hist1 * hist2))
    edge_penalty = bc ** 0.5

    return edge_penalty
```

**When to use Multi-Scale Edge:**
- Need edge characterization beyond fractal
- Orientation important (tool marks)
- Multi-scale discrimination needed

---

## 4. COMPLETE FALLBACK DECISION TREE

### Autonomous Decision Logic

```python
class BackupSolutionManager:
    """
    Manages automatic fallback to alternative algorithms
    """

    def __init__(self):
        self.texture_method = 'lbp'  # primary
        self.color_method = 'lab'    # primary
        self.complexity_method = 'fractal'  # primary

        self.texture_config = LBP_CONFIG_PRIMARY
        self.color_config = LAB_HISTOGRAM_CONFIG_PRIMARY
        self.complexity_config = FRACTAL_SCALES_PRIMARY


    def evaluate_texture_performance(self, bc_same, bc_diff):
        """
        Evaluate texture feature and switch if needed
        """
        mean_same = np.mean(bc_same)
        mean_diff = np.mean(bc_diff)
        separation = mean_same - mean_diff
        variance = np.std(bc_same)

        if mean_diff > 0.85:
            print("SWITCHING: LBP → GLCM (poor separation)")
            self.texture_method = 'glcm'
            self.texture_config = GLCM_CONFIG_PRIMARY
            return 'glcm'

        elif variance > 0.20:
            print("SWITCHING: LBP → Gabor (high variance)")
            self.texture_method = 'gabor'
            self.texture_config = GABOR_CONFIG_PRIMARY
            return 'gabor'

        elif separation < 0.10:
            print("SWITCHING: LBP → HOG (insufficient separation)")
            self.texture_method = 'hog'
            return 'hog'

        else:
            print("KEEPING: LBP texture")
            return 'lbp'


    def evaluate_color_performance(self, bc_same, bc_diff):
        """
        Evaluate color feature and switch if needed
        """
        mean_same = np.mean(bc_same)
        mean_diff = np.mean(bc_diff)

        if mean_diff > 0.85:
            print("SWITCHING: Lab → Opponent Color (poor separation)")
            self.color_method = 'opponent'
            self.color_config = OPPONENT_CONFIG_PRIMARY
            return 'opponent'

        elif mean_same > 0.95 and mean_diff > 0.85:
            print("SWITCHING: Lab → Normalized RGB (all too similar)")
            self.color_method = 'normalized_rgb'
            return 'normalized_rgb'

        else:
            print("KEEPING: Lab color")
            return 'lab'


    def evaluate_complexity_performance(self, values_same, values_diff):
        """
        Evaluate complexity feature and switch if needed
        """
        variance_same = np.std(values_same)
        mean_same = np.mean(values_same)
        mean_diff = np.mean(values_diff)

        if variance_same > 0.15:
            print("SWITCHING: Fractal → Complexity Ratio (high variance)")
            self.complexity_method = 'complexity_ratio'
            return 'complexity_ratio'

        elif abs(mean_same - mean_diff) < 0.05:
            print("SWITCHING: Fractal → Bending Energy (poor separation)")
            self.complexity_method = 'bending_energy'
            return 'bending_energy'

        else:
            print("KEEPING: Fractal dimension")
            return 'fractal'


    def get_current_configuration(self):
        """
        Return current configuration for implementation
        """
        return {
            'texture': {
                'method': self.texture_method,
                'config': self.texture_config
            },
            'color': {
                'method': self.color_method,
                'config': self.color_config
            },
            'complexity': {
                'method': self.complexity_method,
                'config': self.complexity_config
            }
        }
```

---

## 5. IMPLEMENTATION TEMPLATE

### Generic Feature Integration Function

```python
def compute_feature_penalty(fragment1, fragment2, feature_type, config):
    """
    Generic function to compute feature penalty with automatic fallback

    Parameters:
    -----------
    fragment1, fragment2 : Fragment objects
    feature_type : str
        'texture', 'color', or 'complexity'
    config : dict
        Configuration from BackupSolutionManager

    Returns:
    --------
    penalty : float
        Feature penalty [0, 1]
    """
    if feature_type == 'texture':
        method = config['method']

        if method == 'lbp':
            # Primary LBP implementation
            return compute_lbp_penalty(fragment1, fragment2, config['config'])

        elif method == 'glcm':
            return integrate_glcm_into_pipeline(fragment1, fragment2)

        elif method == 'gabor':
            return integrate_gabor_into_pipeline(fragment1, fragment2)

        elif method == 'hog':
            # HOG implementation
            pass

    elif feature_type == 'color':
        method = config['method']

        if method == 'lab':
            # Primary Lab implementation
            return compute_lab_penalty(fragment1, fragment2, config['config'])

        elif method == 'opponent':
            return integrate_opponent_into_pipeline(fragment1, fragment2)

        elif method == 'normalized_rgb':
            return integrate_normalized_rgb_into_pipeline(fragment1, fragment2)

        elif method == 'adaptive_hsv':
            return integrate_adaptive_hsv_into_pipeline(fragment1, fragment2)

    elif feature_type == 'complexity':
        method = config['method']

        if method == 'fractal':
            # Primary fractal implementation
            return compute_fractal_penalty(fragment1, fragment2, config['config'])

        elif method == 'complexity_ratio':
            return integrate_complexity_into_pipeline(fragment1, fragment2)

        elif method == 'bending_energy':
            return integrate_bending_into_pipeline(fragment1, fragment2)

        elif method == 'multiscale_edge':
            return integrate_multiscale_edge_into_pipeline(fragment1, fragment2)
```

---

## 6. TESTING STRATEGY FOR ALTERNATIVES

### Validation Protocol

```python
def validate_alternative_feature(feature_function, pairs_same, pairs_diff):
    """
    Validate an alternative feature before committing to it

    Parameters:
    -----------
    feature_function : callable
        Function that computes feature for a pair
    pairs_same : list
        List of (fragment1, fragment2) same-source pairs
    pairs_diff : list
        List of (fragment1, fragment2) different-source pairs

    Returns:
    --------
    metrics : dict
        Validation metrics
    """
    # Compute features for all pairs
    scores_same = [feature_function(f1, f2) for f1, f2 in pairs_same]
    scores_diff = [feature_function(f1, f2) for f1, f2 in pairs_diff]

    # Cohen's d (effect size)
    cohens_d = compute_separation(scores_same, scores_diff)

    # Mean and variance
    mean_same = np.mean(scores_same)
    mean_diff = np.mean(scores_diff)
    std_same = np.std(scores_same)
    std_diff = np.std(scores_diff)

    # Separation gap
    gap = mean_same - mean_diff

    # Decision
    if cohens_d > 0.8:
        decision = "EXCELLENT - large effect"
    elif cohens_d > 0.5:
        decision = "ACCEPTABLE - medium effect"
    else:
        decision = "POOR - small effect, try another alternative"

    return {
        'cohens_d': cohens_d,
        'mean_same': mean_same,
        'mean_diff': mean_diff,
        'std_same': std_same,
        'std_diff': std_diff,
        'gap': gap,
        'decision': decision
    }
```

---

## 7. SUMMARY TABLE

### Quick Reference: When to Use Each Alternative

| Current | Issue | Alternative | When to Use |
|---------|-------|-------------|-------------|
| **LBP** | BC > 0.85 cross-source | **GLCM** | Coarse texture, need compact features |
| **LBP** | High variance (>0.20) | **Gabor** | Directional patterns (wheel marks) |
| **LBP** | Small separation (<0.10) | **HOG** | Edge + texture combined |
| **Lab** | BC > 0.85 cross-source | **Opponent Color** | Earth tones, subtle hue |
| **Lab** | All pairs too similar | **Normalized RGB** | Illumination variations |
| **Lab** | Minimal improvement | **Adaptive HSV** | Stay with familiar space |
| **Fractal** | High std (>0.15) | **Complexity Ratio** | Need stable metric |
| **Fractal** | Poor separation (<0.05) | **Bending Energy** | Smooth vs rough edges |
| **Fractal** | Unreliable | **Multi-Scale Edge** | Orientation patterns |

---

**Document Version:** 1.0
**Date:** 2026-04-08
**Status:** Ready for autonomous implementation
**Next Steps:** Create decision trees document (DECISION_TREES.md)
