"""
Preprocessing pipeline for archaeological fragment images.

Implements the full early vision pipeline from Lectures 21-23:
  - Gaussian smoothing          (Lecture 22, Linear Systems and Filtering)
  - Sobel gradient magnitude    (Lecture 23, Edge Detection Fundamentals)
  - Canny edge detector         (Lecture 23, Edge Detection Fundamentals)
  - Otsu / adaptive threshold   (Lecture 22)
  - Morphological cleanup       (binary image processing)
  - cv2.findContours             (Lecture 23)

Designed to handle both clean synthetic images (white background) and
real-world archaeological photographs with uneven lighting, shadows,
and textured surfaces.

The preprocessing strategy is:
  1. Gaussian blur to suppress noise (Lecture 22).
  2. Compute Sobel gradient magnitude to quantify local edge strength.
  3. Run Canny on the blurred image to get a thin edge map.
  4. Fill the Canny boundary to create a binary silhouette mask.
  5. Fall back to Otsu / adaptive threshold if Canny yields no usable region.
  6. Morphological cleanup, then contour extraction.
"""

import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

GAUSSIAN_KERNEL_SIZE = (5, 5)
GAUSSIAN_SIGMA = 1.5
MIN_CONTOUR_AREA = 500
CORNER_SAMPLE_SIZE = 30     # pixels: size of corner patches used to detect background
MORPH_KERNEL_SIZE = 7

# Canny parameters — low/high threshold ratio follows the 1:3 rule from Lecture 23
CANNY_SIGMA_SCALE = 0.33    # controls automatic threshold selection from median


def load_image(path: str) -> np.ndarray:
    """Load a fragment image from disk as a BGR numpy array (alpha stripped)."""
    image = cv2.imread(path, cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Could not load image: {path}")
    logger.info("Loaded image %s — shape %s", path, image.shape)
    return image


def apply_gaussian_blur(image: np.ndarray) -> np.ndarray:
    """
    Convert to grayscale and apply Gaussian smoothing (Lecture 22).

    The Gaussian kernel suppresses high-frequency noise before edge detection.
    A fixed sigma is suitable for most fragment photographs at standard
    scanning or photography resolutions.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.GaussianBlur(gray, GAUSSIAN_KERNEL_SIZE, GAUSSIAN_SIGMA)


def compute_sobel_magnitude(blurred: np.ndarray) -> np.ndarray:
    """
    Compute the Sobel gradient magnitude map (Lecture 23).

    Applies the Sobel operator in x and y directions and combines them as
    M = sqrt(Gx^2 + Gy^2). The resulting map shows edge strength at every
    pixel and is used both as a diagnostic and to inform Canny thresholds.
    Returned values are normalised to [0, 255].
    """
    gx = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = np.sqrt(gx ** 2 + gy ** 2)
    normalised = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX)
    return normalised.astype(np.uint8)


def canny_silhouette(blurred: np.ndarray) -> np.ndarray:
    """
    Detect fragment boundary with the Canny edge detector (Lecture 23).

    Thresholds are set automatically from the median pixel intensity using
    the 1:3 lower-to-upper ratio recommended in the course material.
    The thin edge map is then flood-filled to produce a solid silhouette mask.
    Returns a binary mask (uint8, 0/255) or None if no usable region is found.
    """
    median_val = float(np.median(blurred))
    low  = max(0,   int((1.0 - CANNY_SIGMA_SCALE) * median_val))
    high = min(255, int((1.0 + CANNY_SIGMA_SCALE) * median_val))
    edges = cv2.Canny(blurred, low, high)

    logger.info("Canny thresholds: low=%d, high=%d", low, high)

    # Flood-fill from all four corners (assumed background) to create mask
    h, w = edges.shape
    filled = edges.copy()
    seed_points = [(0, 0), (0, h - 1), (w - 1, 0), (w - 1, h - 1)]
    flood_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
    for sx, sy in seed_points:
        cv2.floodFill(filled, flood_mask, (sx, sy), 128)

    # Pixels not reached by flood are inside the fragment
    interior = np.where(filled == 0, 255, 0).astype(np.uint8)
    interior = cv2.bitwise_or(interior, edges)

    contours, _ = cv2.findContours(interior, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours or max(cv2.contourArea(c) for c in contours) < MIN_CONTOUR_AREA:
        return None

    # Render only the largest filled contour as the silhouette
    silhouette = np.zeros_like(blurred)
    largest = max(contours, key=cv2.contourArea)
    cv2.drawContours(silhouette, [largest], -1, 255, thickness=cv2.FILLED)
    return silhouette


def detect_background_brightness(image: np.ndarray) -> float:
    """
    Estimate background brightness by sampling image corners.

    Corners are assumed to contain background pixels rather than fragment
    pixels. Returns the mean intensity (0–255); values above 128 indicate
    a light background.
    """
    s = CORNER_SAMPLE_SIZE
    corners = [
        image[:s, :s],
        image[:s, -s:],
        image[-s:, :s],
        image[-s:, -s:],
    ]
    return float(np.mean([patch.mean() for patch in corners]))


def otsu_threshold(blurred: np.ndarray, light_background: bool) -> np.ndarray:
    """
    Apply Otsu's global binarization.

    THRESH_BINARY_INV is used for light backgrounds (fragment is darker
    than the background). THRESH_BINARY is used for dark backgrounds.
    """
    if light_background:
        _, binary = cv2.threshold(
            blurred, 0, 255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
        )
    else:
        _, binary = cv2.threshold(
            blurred, 0, 255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU,
        )
    return binary


def adaptive_threshold(blurred: np.ndarray, light_background: bool) -> np.ndarray:
    """
    Apply local adaptive binarization for uneven illumination.

    Useful for real photographs where lighting varies across the image
    (e.g., shadows cast by the fragment edges).
    """
    mode = cv2.THRESH_BINARY_INV if light_background else cv2.THRESH_BINARY
    return cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        mode, 25, 6,
    )


def morphological_cleanup(binary_mask: np.ndarray) -> np.ndarray:
    """
    Apply closing then opening to the binary mask.

    Closing fills small holes inside the fragment silhouette; opening
    removes thin noise spurs from the boundary. Uses an elliptical kernel
    to avoid axis-aligned artefacts.
    """
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (MORPH_KERNEL_SIZE, MORPH_KERNEL_SIZE)
    )
    closed = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel, iterations=1)
    return opened


def best_binary_mask(blurred: np.ndarray, light_background: bool) -> np.ndarray:
    """
    Choose the binarization strategy that yields the largest clean region.

    Tries Otsu and adaptive thresholding; selects the result whose largest
    connected component has the greater area. This handles both evenly lit
    and shadowed fragment photographs automatically.
    """
    otsu_mask = otsu_threshold(blurred, light_background)
    adaptive_mask = adaptive_threshold(blurred, light_background)

    def largest_component_area(mask: np.ndarray) -> float:
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return 0.0
        return float(max(cv2.contourArea(c) for c in contours))

    if largest_component_area(otsu_mask) >= largest_component_area(adaptive_mask):
        chosen, method = otsu_mask, "Otsu"
    else:
        chosen, method = adaptive_mask, "adaptive"

    logger.info("Binarization: selected %s threshold", method)
    return chosen


def extract_largest_contour(binary_mask: np.ndarray) -> np.ndarray:
    """
    Extract the outermost boundary of the largest connected region.

    Uses CHAIN_APPROX_NONE to retain every boundary pixel — required for
    accurate Freeman chain code encoding (Lecture 72). Returns points as a
    (N, 2) array of (x, y) coordinates.
    """
    clean_mask = morphological_cleanup(binary_mask)
    contours, _ = cv2.findContours(
        clean_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
    )
    if not contours:
        raise ValueError("No contours found after binarization and cleanup.")

    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < MIN_CONTOUR_AREA:
        raise ValueError(
            "Largest contour is too small. "
            "Check that the fragment occupies a meaningful portion of the image."
        )

    points = largest.reshape(-1, 2)
    logger.info("Extracted contour with %d boundary points", len(points))
    return points


def alpha_channel_mask(image_bgra: np.ndarray) -> np.ndarray:
    """
    Extract a binary silhouette from an RGBA image's alpha channel.

    Fragments produced by generate_benchmark_data.py have a precise alpha
    mask baked in. Using it directly avoids any edge-detection error and
    gives the cleanest possible contour for algorithmic benchmarking.

    Returns a uint8 mask (0 / 255) the same height and width as the input.
    """
    alpha = image_bgra[:, :, 3]
    _, binary = cv2.threshold(alpha, 127, 255, cv2.THRESH_BINARY)
    return binary


def preprocess_fragment(path: str):
    """
    Full preprocessing pipeline for a single fragment image.

    Strategy (in order):
      0. If the image has an alpha channel (RGBA), use it directly as the
         binary silhouette mask — this is exact for benchmark fragments and
         requires no edge detection.
      1. Otherwise: Gaussian blur (Lecture 22).
      2. Sobel gradient magnitude computed and logged (Lecture 23).
      3. Canny edge detector attempted (Lecture 23); if it yields a clean
         silhouette that is used directly.
      4. Otherwise fall back to Otsu / adaptive threshold (Lecture 22).
      5. Morphological cleanup.
      6. Largest-contour extraction (Lecture 23).

    Handles both light-background and dark-background images automatically.
    Returns the original BGR image and boundary contour as (N, 2) array.
    """
    # Load with alpha channel if present
    image_full = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if image_full is None:
        raise FileNotFoundError(f"Could not load image: {path}")

    # --- Path 0: RGBA with alpha mask (benchmark fragments) ---
    if image_full.ndim == 3 and image_full.shape[2] == 4:
        logger.info("RGBA fragment detected — using alpha channel as silhouette mask")
        image_bgr = cv2.cvtColor(image_full, cv2.COLOR_BGRA2BGR)
        alpha_mask = alpha_channel_mask(image_full)
        contour = extract_largest_contour(alpha_mask)
        return image_bgr, contour

    # --- Path 1: standard BGR image (real photograph) ---
    image = image_full if image_full.ndim == 3 else cv2.cvtColor(image_full, cv2.COLOR_GRAY2BGR)
    logger.info("Loaded image %s — shape %s", path, image.shape)

    blurred = apply_gaussian_blur(image)
    sobel_mag = compute_sobel_magnitude(blurred)
    logger.info(
        "Sobel gradient — mean=%.1f, max=%.1f",
        float(sobel_mag.mean()), float(sobel_mag.max())
    )

    # Attempt Canny-based silhouette first (preferred for real images)
    canny_mask = canny_silhouette(blurred)
    if canny_mask is not None:
        logger.info("Using Canny silhouette mask")
        contour = extract_largest_contour(canny_mask)
    else:
        logger.info("Canny yielded no usable region; falling back to threshold")
        bg_brightness = detect_background_brightness(blurred)
        light_bg = bg_brightness > 128
        logger.info(
            "Background brightness: %.1f -> %s background",
            bg_brightness, "light" if light_bg else "dark"
        )
        binary_mask = best_binary_mask(blurred, light_bg)
        contour = extract_largest_contour(binary_mask)

    return image, contour
