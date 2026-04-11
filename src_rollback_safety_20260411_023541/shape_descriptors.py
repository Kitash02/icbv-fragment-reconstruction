"""
Supplementary shape descriptors: Fourier Descriptors and PCA orientation.

Implements two additional shape analysis tools from the course:

  Fourier Descriptors (Lecture 72 — 2D Shape Analysis):
    The boundary is treated as a 1-D complex signal z[n] = x[n] + i·y[n].
    Its DFT coefficients encode the shape at multiple frequency scales:
    low-order coefficients capture global form; high-order capture fine
    boundary detail. Truncating to the first K coefficients gives a
    compact, rotation- and scale-invariant shape signature.

  PCA Orientation Normalization (Lecture 74 — Appearance-Based Recognition):
    Applies eigendecomposition to the contour's 2-D scatter matrix to find
    the principal axis of the boundary point cloud. Rotating the contour so
    that its principal axis aligns with the x-axis removes arbitrary
    orientation differences before chain-code comparison.

Both descriptors complement the Freeman chain code: Fourier descriptors
capture global shape compactly; PCA normalization improves rotation
invariance beyond the cyclic-minimum trick.
"""

import numpy as np
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Number of low-frequency Fourier coefficients kept for the compact descriptor
FOURIER_DESCRIPTOR_ORDER = 32


# ---------------------------------------------------------------------------
# Fourier Descriptors  (Lecture 72)
# ---------------------------------------------------------------------------

def contour_to_complex_signal(contour: np.ndarray) -> np.ndarray:
    """
    Represent the boundary as a complex 1-D signal z[n] = x[n] + j·y[n].

    This encoding allows the DFT to treat the boundary as a periodic signal
    whose frequency components characterise shape at different scales
    (Lecture 72).
    """
    return contour[:, 0].astype(float) + 1j * contour[:, 1].astype(float)


def compute_fourier_descriptors(
    contour: np.ndarray,
    n_descriptors: int = FOURIER_DESCRIPTOR_ORDER,
) -> np.ndarray:
    """
    Compute truncated Fourier descriptors of a boundary contour (Lecture 72).

    Steps:
      1. Encode boundary as complex signal z[n].
      2. Compute DFT: Z = FFT(z).
      3. Normalise for translation (Z[0] = 0), scale (|Z[1]| = 1),
         and starting-point (phase of Z[1] = 0).
      4. Return the first n_descriptors magnitude coefficients (rotation-invariant).

    The magnitudes |Z[k]| are invariant to rigid transformations, making them
    directly comparable between differently oriented fragments.
    """
    z = contour_to_complex_signal(contour)
    Z = np.fft.fft(z)

    # Translation invariance: discard DC component
    Z[0] = 0.0

    # Scale invariance: normalise by |Z[1]|
    scale = abs(Z[1])
    if scale < 1e-8:
        logger.warning("Fourier descriptor: degenerate contour (scale ~= 0).")
        return np.zeros(n_descriptors)
    Z /= scale

    # Return magnitude of first n_descriptors coefficients (rotation-invariant)
    descriptors = np.abs(Z[1: n_descriptors + 1])
    logger.info(
        "Fourier descriptors: %d coefficients, energy ratio=%.4f",
        n_descriptors,
        float(np.sum(descriptors ** 2) / (np.sum(np.abs(Z) ** 2) + 1e-12)),
    )
    return descriptors


# ---------------------------------------------------------------------------
# PCA Orientation Normalization  (Lecture 74)
# ---------------------------------------------------------------------------

def pca_orientation(contour: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Compute the principal axis of the contour point cloud via PCA (Lecture 74).

    Centers the contour, forms the 2×2 scatter matrix, and finds eigenvectors.
    Returns:
      centroid     — (2,) array, mean position of boundary points
      angle        — angle (radians) of the first principal component w.r.t. x-axis
    """
    pts = contour.astype(float)
    centroid = pts.mean(axis=0)
    centered = pts - centroid

    scatter = (centered.T @ centered) / max(len(pts) - 1, 1)
    eigenvalues, eigenvectors = np.linalg.eigh(scatter)

    # Principal axis = eigenvector with largest eigenvalue
    principal = eigenvectors[:, np.argmax(eigenvalues)]
    angle = float(np.arctan2(principal[1], principal[0]))

    logger.info(
        "PCA orientation: centroid=(%.1f, %.1f), angle=%.3f rad (%.1f°)",
        centroid[0], centroid[1], angle, float(np.degrees(angle))
    )
    return centroid, angle


def pca_normalize_contour(contour: np.ndarray) -> np.ndarray:
    """
    Rotate and center a contour so its principal axis aligns with the x-axis.

    Implements the appearance-based rotation normalization described in
    Lecture 74. After normalization, two fragments with similar shapes will
    have similar contour point clouds regardless of their original orientation
    in the photograph.
    """
    centroid, angle = pca_orientation(contour)
    pts = contour.astype(float) - centroid

    cos_a, sin_a = np.cos(-angle), np.sin(-angle)
    rotation = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
    normalized = (rotation @ pts.T).T

    # Shift so all coordinates are non-negative
    normalized -= normalized.min(axis=0)
    return normalized.astype(np.int32)


def log_shape_summary(
    contour: np.ndarray,
    name: str,
    n_descriptors: int = 8,
) -> None:
    """
    Log a brief shape summary (Fourier energy + PCA angle) for one fragment.

    Useful for comparing fragments qualitatively in the run log.
    """
    descs = compute_fourier_descriptors(contour, n_descriptors)
    _, angle = pca_orientation(contour)
    logger.info(
        "Shape summary [%s]: Fourier=%s  PCA_angle=%.2f°",
        name,
        np.array2string(descs[:4], precision=3, suppress_small=True),
        float(np.degrees(angle)),
    )
