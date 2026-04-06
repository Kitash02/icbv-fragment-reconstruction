"""
Geometric assembly renderer for proposed fragment joins.

For each matched pair (fragment_i, segment_a) → (fragment_j, segment_b),
computes an affine transform (rotation + translation) that aligns the
matching boundary segments, then composites both fragments on a shared
canvas.

The alignment algorithm:
  1. Extract pixel coordinates of each matching segment from the contour.
  2. Compute the centroid and principal direction of each segment.
  3. Build a 2×3 affine matrix that maps fragment_j's segment centroid
     to fragment_i's segment centroid and rotates so the directions are
     antiparallel (edges face each other when joined).
  4. Apply cv2.warpAffine to fragment_j and overlay on a white canvas
     that already contains fragment_i.

This directly illustrates the geometric matching principle that underpins
the compatibility scoring (Lectures 23 and 72) and produces an intuitive
visual output for human review.
"""

import cv2
import numpy as np
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

CANVAS_PAD_FACTOR = 2.5   # canvas size relative to each fragment dimension
HIGHLIGHT_THICKNESS = 3
COLOR_SEG_A = (0, 210, 90)    # green  — segment on fragment i (BGR)
COLOR_SEG_B = (0, 100, 230)   # orange — segment on fragment j (BGR)
TEXT_COLOR = (40, 40, 40)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def segment_centroid(pts: np.ndarray) -> np.ndarray:
    """Return the mean (x, y) position of a set of contour points."""
    return pts.mean(axis=0).astype(float)


def segment_direction_angle(pts: np.ndarray) -> float:
    """
    Return the angle (radians) of the principal axis of a boundary segment.

    Estimated as the angle from the first to the last point in the segment.
    Falls back to 0 for degenerate (single-point) segments.
    """
    if len(pts) < 2:
        return 0.0
    vec = pts[-1].astype(float) - pts[0].astype(float)
    norm = float(np.linalg.norm(vec))
    return float(np.arctan2(vec[1], vec[0])) if norm > 1e-6 else 0.0


def build_affine_matrix(
    src_centroid: np.ndarray,
    src_angle: float,
    dst_centroid: np.ndarray,
    dst_angle: float,
) -> np.ndarray:
    """
    Build a 2×3 affine matrix that rotates src and translates it to dst.

    The rotation aligns src_angle with (dst_angle + π), because matching
    edges face each other: when two fragments join, one edge's outward
    normal is the reverse of the other's.
    """
    rotation = (dst_angle + np.pi) - src_angle
    cos_r = float(np.cos(rotation))
    sin_r = float(np.sin(rotation))

    tx = dst_centroid[0] - (cos_r * src_centroid[0] - sin_r * src_centroid[1])
    ty = dst_centroid[1] - (sin_r * src_centroid[0] + cos_r * src_centroid[1])

    return np.float32([[cos_r, -sin_r, tx],
                       [sin_r,  cos_r, ty]])


# ---------------------------------------------------------------------------
# Pixel segment extraction
# ---------------------------------------------------------------------------

def get_pixel_segment(
    contour: np.ndarray,
    seg_idx: int,
    n_segments: int,
) -> np.ndarray:
    """
    Return the (k, 2) pixel coordinate array for one boundary segment.

    The division mirrors segment_chain_code in chain_code.py so that
    chain code segment i and pixel segment i correspond to the same
    part of the boundary.
    """
    n = len(contour)
    seg_len = max(1, n // n_segments)
    start = seg_idx * seg_len
    end = start + seg_len if seg_idx < n_segments - 1 else n
    return contour[start:end]


# ---------------------------------------------------------------------------
# Compositing
# ---------------------------------------------------------------------------

def overlay_on_canvas(
    canvas: np.ndarray,
    fragment_img: np.ndarray,
    offset_x: int,
    offset_y: int,
) -> np.ndarray:
    """
    Place fragment_img at (offset_x, offset_y) on canvas using darkest-pixel compositing.

    Taking the element-wise minimum preserves dark fragment pixels from both
    images against the shared white background without blending artefacts.
    """
    h, w = fragment_img.shape[:2]
    ch, cw = canvas.shape[:2]
    x1, y1 = max(0, offset_x), max(0, offset_y)
    x2, y2 = min(cw, offset_x + w), min(ch, offset_y + h)
    sx1, sy1 = x1 - offset_x, y1 - offset_y
    sx2, sy2 = sx1 + (x2 - x1), sy1 + (y2 - y1)
    if x2 > x1 and y2 > y1:
        canvas[y1:y2, x1:x2] = np.minimum(
            canvas[y1:y2, x1:x2],
            fragment_img[sy1:sy2, sx1:sx2],
        )
    return canvas


def draw_segment_highlight(
    canvas: np.ndarray,
    pts: np.ndarray,
    color: Tuple[int, int, int],
) -> None:
    """Draw a thick polyline along segment pixel coordinates on the canvas."""
    if len(pts) < 2:
        return
    pts_int = pts.astype(np.int32).reshape(-1, 1, 2)
    cv2.polylines(canvas, [pts_int], isClosed=False, color=color,
                  thickness=HIGHLIGHT_THICKNESS, lineType=cv2.LINE_AA)


def crop_to_content(
    image: np.ndarray,
    padding: int = 20,
) -> np.ndarray:
    """Crop a white-background image to the bounding box of non-white pixels."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    non_white = np.where(gray < 250)
    if len(non_white[0]) == 0:
        return image
    y_min, y_max = int(non_white[0].min()), int(non_white[0].max())
    x_min, x_max = int(non_white[1].min()), int(non_white[1].max())
    h, w = image.shape[:2]
    y1 = max(0, y_min - padding)
    y2 = min(h, y_max + padding)
    x1 = max(0, x_min - padding)
    x2 = min(w, x_max + padding)
    return image[y1:y2, x1:x2]


# ---------------------------------------------------------------------------
# Main rendering function
# ---------------------------------------------------------------------------

def render_pair_assembly(
    img_i: np.ndarray,
    contour_i: np.ndarray,
    seg_a: int,
    img_j: np.ndarray,
    contour_j: np.ndarray,
    seg_b: int,
    n_segments: int,
    pair_score: float,
    name_i: str = "A",
    name_j: str = "B",
) -> Optional[np.ndarray]:
    """
    Render fragment_j geometrically aligned to fragment_i at their matching edges.

    Computes an affine transform that maps fragment_j's segment_b onto
    fragment_i's segment_a, then composites both on a white canvas.
    Highlights the matching segments in contrasting colours.

    Returns the cropped composite image, or None if alignment cannot be
    computed (degenerate segments).
    """
    pts_a = get_pixel_segment(contour_i, seg_a, n_segments)
    pts_b = get_pixel_segment(contour_j, seg_b, n_segments)

    if len(pts_a) < 2 or len(pts_b) < 2:
        logger.warning("Segment too short for geometric assembly; skipping pair.")
        return None

    ca = segment_centroid(pts_a)
    cb = segment_centroid(pts_b)
    angle_a = segment_direction_angle(pts_a)
    angle_b = segment_direction_angle(pts_b)

    # Canvas: large enough to fit both fragments after any rotation
    h_max = max(img_i.shape[0], img_j.shape[0])
    w_max = max(img_i.shape[1], img_j.shape[1])
    canvas_h = int(h_max * CANVAS_PAD_FACTOR)
    canvas_w = int(w_max * CANVAS_PAD_FACTOR)

    # Fragment_i goes in the centre of the canvas
    off_x = int((canvas_w - img_i.shape[1]) // 2)
    off_y = int((canvas_h - img_i.shape[0]) // 2)

    # Adjust centroid_a for the canvas offset
    ca_canvas = ca + np.array([off_x, off_y], dtype=float)

    # Affine matrix: maps fragment_j pixel coords → canvas coords
    M = build_affine_matrix(cb, angle_b, ca_canvas, angle_a)

    # Warp fragment_j onto a canvas-sized image
    warped_j = cv2.warpAffine(
        img_j, M, (canvas_w, canvas_h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )

    # Build canvas with fragment_i
    canvas = np.full((canvas_h, canvas_w, 3), 255, dtype=np.uint8)
    canvas = overlay_on_canvas(canvas, img_i, off_x, off_y)

    # Overlay warped fragment_j
    canvas = np.minimum(canvas, warped_j)

    # Highlight matching segments
    draw_segment_highlight(canvas, pts_a + np.array([off_x, off_y]), COLOR_SEG_A)

    # Transform pts_b to canvas coordinates for highlighting
    ones = np.ones((len(pts_b), 1), dtype=float)
    pts_b_h = np.hstack([pts_b.astype(float), ones])
    pts_b_canvas = (M[:, :2] @ pts_b.T + M[:, 2:3]).T
    draw_segment_highlight(canvas, pts_b_canvas, COLOR_SEG_B)

    # Annotate
    label = f"{name_i}[seg{seg_a}] + {name_j}[seg{seg_b}]  score={pair_score:.3f}"
    cv2.putText(canvas, label, (15, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, TEXT_COLOR, 1, cv2.LINE_AA)

    return crop_to_content(canvas)


def render_assembly_sheet(
    images: List[np.ndarray],
    contours: List[np.ndarray],
    assembly: dict,
    fragment_names: List[str],
    n_segments: int,
    output_path: str,
) -> None:
    """
    Render all matched pairs in a single assembly from a relaxation labeling result.

    Each row shows one proposed pair with fragments geometrically aligned.
    The sheet is saved to output_path.
    """
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg

    pairs = assembly['pairs'][:4]   # cap at 4 rows for readability
    if not pairs:
        return

    pair_images = []
    for pair in pairs:
        fi, sa = pair['frag_i'], pair['seg_a']
        fj, sb = pair['frag_j'], pair['seg_b']
        assembled = render_pair_assembly(
            images[fi], contours[fi], sa,
            images[fj], contours[fj], sb,
            n_segments, pair['score'],
            fragment_names[fi], fragment_names[fj],
        )
        if assembled is not None:
            pair_images.append(assembled)

    if not pair_images:
        return

    n_rows = len(pair_images)
    fig, axes = plt.subplots(n_rows, 1, figsize=(8, n_rows * 3.5), dpi=110)
    if n_rows == 1:
        axes = [axes]

    for ax, img in zip(axes, pair_images):
        ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        ax.axis('off')

    conf = assembly.get('confidence', 0.0)
    plt.suptitle(f"Geometric Assembly  —  confidence {conf:.3f}", fontsize=11)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    logger.info("Saved geometric assembly sheet → %s", output_path)
