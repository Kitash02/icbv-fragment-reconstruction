"""
Freeman Chain Code encoding and normalization for fragment boundary contours.

Implements the 2D shape representation described in Lecture 72
(Object Recognition — 2D Shape Analysis). The chain code provides a
compact, translation-invariant boundary descriptor.

Rotation invariance strategy (layered):
  1. First-difference encoding:  invariant to rotations that are multiples
     of 45° (the discrete Freeman grid step). d[i] = (c[i]-c[i-1]) mod 8
     encodes turns, not absolute directions (Lecture 72).
  2. PCA orientation normalization (shape_descriptors.py): rotates the
     whole contour to align its principal axis with the x-axis before
     encoding. Reduces gross orientation differences (Lecture 74).
  3. Local segment normalization (this module, rotate_segment_to_horizontal):
     Rotates each boundary *segment* individually so its spine vector
     (first→last pixel) is horizontal before chain-code encoding. This
     achieves continuous rotation invariance at the sub-contour level,
     independent of the whole-fragment orientation. Critical for matching
     fragments that were photographed at different angles.
  4. Anti-parallel comparison (compatibility.py): when checking whether
     two segments can be joined, the matching edge of fragment B is
     traversed in the reverse direction. The compatibility scorer therefore
     compares chain_a against both chain_b and reversed chain_b, taking
     the maximum — this is the physically correct join model.

Starting-point invariance is achieved through cyclic-minimum normalization
applied to the first-difference code.
"""

import numpy as np
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Freeman 8-connectivity: direction code → (dx, dy) in image coordinates.
# y increases downward following the OpenCV convention.
DIRECTION_DELTAS: dict = {
    0: (1,  0),   # right
    1: (1,  1),   # right-down
    2: (0,  1),   # down
    3: (-1, 1),   # left-down
    4: (-1, 0),   # left
    5: (-1, -1),  # left-up
    6: (0, -1),   # up
    7: (1, -1),   # right-up
}

DELTA_TO_DIRECTION: dict = {delta: code for code, delta in DIRECTION_DELTAS.items()}


def points_to_chain_code(contour_points: np.ndarray) -> List[int]:
    """
    Convert consecutive boundary pixel positions to Freeman 8-directional codes.

    Each adjacent pair of points is mapped to one of the eight directions (0–7).
    Pairs whose delta does not correspond to a unit step are skipped; this
    handles occasional non-adjacent points returned by OpenCV.
    """
    chain: List[int] = []
    n_points = len(contour_points)
    for idx in range(n_points):
        current = contour_points[idx]
        next_pt = contour_points[(idx + 1) % n_points]
        delta = (int(next_pt[0]) - int(current[0]),
                 int(next_pt[1]) - int(current[1]))
        code = DELTA_TO_DIRECTION.get(delta)
        if code is not None:
            chain.append(code)
    return chain


def first_difference(chain: List[int]) -> List[int]:
    """
    Compute the first-difference chain code for rotation invariance.

    d[i] = (c[i] - c[i-1]) mod 8 encodes direction changes rather than
    absolute directions, making the descriptor invariant to rigid rotation
    of the fragment in the image plane (Lecture 72).
    """
    if len(chain) < 2:
        return list(chain)
    return [(chain[i] - chain[i - 1]) % 8 for i in range(1, len(chain))]


def cyclic_minimum_rotation(sequence: List[int]) -> List[int]:
    """
    Return the lexicographically smallest cyclic rotation of the sequence.

    Scanning all rotations of the doubled sequence removes dependency on
    the arbitrary starting pixel of the contour traversal (Lecture 72).
    """
    if not sequence:
        return []
    n = len(sequence)
    doubled = sequence + sequence
    min_rotation = sequence[:]
    for start in range(1, n):
        candidate = doubled[start: start + n]
        if candidate < min_rotation:
            min_rotation = candidate
    return min_rotation


def normalize_chain_code(chain: List[int]) -> List[int]:
    """
    Produce a fully normalized chain code descriptor.

    Applies first-difference encoding (rotation invariant) followed by
    cyclic-minimum rotation (starting-point invariant), as described in
    Lecture 72.
    """
    diff_code = first_difference(chain)
    normalized = cyclic_minimum_rotation(diff_code)
    return normalized


def segment_chain_code(chain: List[int], n_segments: int) -> List[List[int]]:
    """
    Divide the chain code into n_segments equal-length boundary segments.

    Each segment is a candidate matching edge of the fragment. Equal-length
    division is reproducible and does not require domain knowledge about
    which part of the boundary is a fracture surface.
    """
    if not chain or n_segments <= 0:
        return []
    segment_length = max(1, len(chain) // n_segments)
    segments: List[List[int]] = []
    for seg_idx in range(n_segments):
        start = seg_idx * segment_length
        end = start + segment_length if seg_idx < n_segments - 1 else len(chain)
        segments.append(chain[start:end])
    return segments


def contour_to_pixel_segments(
    contour_points: np.ndarray,
    n_segments: int,
) -> List[np.ndarray]:
    """
    Divide the contour point array into n_segments equal groups.

    Returns a list of (k, 2) arrays of (x, y) pixel coordinates, one per
    segment. The division mirrors segment_chain_code so that pixel segment i
    corresponds exactly to chain code segment i.
    """
    n = len(contour_points)
    seg_len = max(1, n // n_segments)
    pixel_segs: List[np.ndarray] = []
    for seg_idx in range(n_segments):
        start = seg_idx * seg_len
        end = start + seg_len if seg_idx < n_segments - 1 else n
        pixel_segs.append(contour_points[start:end])
    return pixel_segs


def rotate_segment_to_horizontal(pixel_segment: np.ndarray) -> np.ndarray:
    """
    Rotate a pixel segment so its spine vector becomes horizontal.

    The "spine" is the vector from the segment's first pixel to its last.
    Rotating by -θ (where θ is the spine angle) maps the spine to the
    positive x-axis, giving orientation invariance independent of the
    fragment's absolute position in the image.

    After rotation the coordinates are re-quantized to the integer grid so
    that points_to_chain_code can operate on them. Translation is removed
    (centroid shifted to origin) before the rotation and not restored
    afterwards — chain codes are translation-invariant by construction.

    This implements the local rotation normalization step described in the
    module docstring (point 3 of the invariance strategy).
    """
    pts = pixel_segment.astype(np.float64)
    if len(pts) < 2:
        return pixel_segment.copy()

    spine = pts[-1] - pts[0]
    spine_len = np.linalg.norm(spine)
    if spine_len < 1e-6:
        return pixel_segment.copy()

    theta = np.arctan2(spine[1], spine[0])
    cos_t, sin_t = np.cos(-theta), np.sin(-theta)

    # Rotation matrix (2D, counterclockwise by -theta to flatten spine)
    rot = np.array([[cos_t, -sin_t], [sin_t, cos_t]])
    centroid = pts.mean(axis=0)
    rotated = (rot @ (pts - centroid).T).T

    # Shift so all coordinates are non-negative, then round to integer grid
    rotated -= rotated.min(axis=0)
    return np.round(rotated).astype(np.int32)


def encode_segment_with_local_rotation(pixel_segment: np.ndarray) -> List[int]:
    """
    Encode one boundary segment as a locally rotation-normalized chain code.

    Applies rotate_segment_to_horizontal before chain-code encoding so that
    the resulting code is independent of the segment's absolute orientation.
    The first-difference and cyclic-minimum normalizations are then applied
    on top for full invariance (Lecture 72).
    """
    rotated = rotate_segment_to_horizontal(pixel_segment)
    raw_chain = points_to_chain_code(rotated)
    return normalize_chain_code(raw_chain)


def compute_curvature_profile(pixel_segment: np.ndarray) -> np.ndarray:
    """
    Compute the discrete curvature (turning-angle) profile of a pixel segment.

    This is the continuous analog of the first-difference chain code
    (Lecture 72). While first-difference encodes turns as integers in {0..7},
    this function computes the exact signed turning angle between consecutive
    tangent vectors:

        κ(i) = atan2( v[i] × v[i-1], v[i] · v[i-1] )

    where v[i] = p[i+1] - p[i] is the forward tangent at step i.

    Properties:
      - Translation invariant: only differences of positions are used.
      - Rotation invariant: rotating the segment adds a constant to absolute
        tangent angles, but consecutive tangent *differences* are unchanged.
      - No quantization: floating-point, no grid rounding artifacts.

    Returns a 1-D float array of length len(pixel_segment) - 2.
    A flat/straight segment gives values near 0; a sharp corner gives ±π/2.
    """
    pts = pixel_segment.astype(np.float64)
    if len(pts) < 3:
        return np.zeros(max(len(pts) - 1, 1))

    # Forward tangent vectors
    tangents = np.diff(pts, axis=0)                          # (n-1, 2)
    norms = np.linalg.norm(tangents, axis=1, keepdims=True)
    norms = np.where(norms < 1e-8, 1.0, norms)
    tangents_unit = tangents / norms                          # (n-1, 2)

    # Signed turning angle between consecutive unit tangents
    t_prev = tangents_unit[:-1]                              # (n-2, 2)
    t_next = tangents_unit[1:]                               # (n-2, 2)
    cross = t_prev[:, 0] * t_next[:, 1] - t_prev[:, 1] * t_next[:, 0]
    dot   = (t_prev * t_next).sum(axis=1)
    kappa = np.arctan2(cross, dot)                           # (n-2,) radians

    return kappa


def encode_fragment(
    contour_points: np.ndarray,
    n_segments: int = 4
) -> Tuple[List[int], List[List[int]]]:
    """
    Full chain code pipeline for a single fragment contour.

    Returns the normalized full chain code and its boundary segments.
    Segments are encoded using encode_segment_with_local_rotation so that
    each one is individually rotation-normalized (Lecture 72 + local
    orientation invariance).

    Logs an 80-character preview of the chain code as required by the
    logging specification.
    """
    raw_chain = points_to_chain_code(contour_points)
    normalized = normalize_chain_code(raw_chain)

    # Split pixel contour and encode each segment with local rotation
    pixel_segs = contour_to_pixel_segments(contour_points, n_segments)
    segments = [encode_segment_with_local_rotation(ps) for ps in pixel_segs]

    preview = str(normalized[:80])
    logger.info(
        "Chain code: length=%d, segments=%d, preview=%s",
        len(normalized), len(segments), preview
    )
    return normalized, segments
