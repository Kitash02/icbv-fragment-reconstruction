"""
Visualization of fragment contours and proposed assembly hypotheses.

Produces annotated images using OpenCV and matplotlib, as demonstrated
throughout the course for displaying edge detection and grouping results.
Renders: fragment contour overlays, pairwise compatibility heatmap,
relaxation labeling convergence plot, and top-K assembly proposals.
"""

import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import logging
from typing import List

logger = logging.getLogger(__name__)

CONTOUR_COLOR = (0, 200, 100)   # green (BGR)
FIGURE_DPI = 120
CONTOUR_THICKNESS = 2


def draw_contour_overlay(image: np.ndarray, contour: np.ndarray) -> np.ndarray:
    """Draw the extracted boundary contour on a copy of the fragment image."""
    overlay = image.copy()
    contour_cv = contour.reshape(-1, 1, 2).astype(np.int32)
    cv2.drawContours(overlay, [contour_cv], -1, CONTOUR_COLOR, CONTOUR_THICKNESS)
    return overlay


def render_fragment_grid(
    images: List[np.ndarray],
    contours: List[np.ndarray],
    fragment_names: List[str],
    output_path: str,
) -> None:
    """
    Render all loaded fragments with contour overlays in a grid layout.

    Saves a single PNG to output_path. The grid width is capped at four
    columns for readability.
    """
    n = len(images)
    cols = min(4, n)
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(
        rows, cols, figsize=(cols * 3, rows * 3), dpi=FIGURE_DPI
    )
    axes_flat = np.array(axes).flatten()

    for ax_idx, (img, contour, name) in enumerate(
        zip(images, contours, fragment_names)
    ):
        overlay = draw_contour_overlay(img, contour)
        rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
        axes_flat[ax_idx].imshow(rgb)
        axes_flat[ax_idx].set_title(name, fontsize=8)
        axes_flat[ax_idx].axis('off')

    for ax_idx in range(n, len(axes_flat)):
        axes_flat[ax_idx].axis('off')

    plt.suptitle("Extracted Fragment Contours", fontsize=11, y=1.01)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    logger.info("Saved fragment grid -> %s", output_path)


def render_compatibility_heatmap(
    compat_matrix: np.ndarray,
    fragment_names: List[str],
    output_path: str,
) -> None:
    """
    Render the inter-fragment compatibility matrix as a colour heatmap.

    The 4D matrix is averaged over segment pairs to produce an
    (n_frags × n_frags) summary suitable for display.
    """
    n_frags = compat_matrix.shape[0]
    summary = compat_matrix.mean(axis=(1, 3))

    fig_size = max(4, n_frags)
    fig, ax = plt.subplots(figsize=(fig_size, fig_size), dpi=FIGURE_DPI)
    im = ax.imshow(summary, cmap='YlOrRd', vmin=0, vmax=1)
    plt.colorbar(im, ax=ax, label='Mean compatibility score')
    ax.set_xticks(range(n_frags))
    ax.set_yticks(range(n_frags))
    ax.set_xticklabels(fragment_names, rotation=45, ha='right', fontsize=8)
    ax.set_yticklabels(fragment_names, fontsize=8)
    ax.set_title("Pairwise Fragment Compatibility", fontsize=11)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    logger.info("Saved compatibility heatmap -> %s", output_path)


def render_assembly_proposal(
    images: List[np.ndarray],
    contours: List[np.ndarray],
    assembly: dict,
    fragment_names: List[str],
    rank: int,
    output_path: str,
) -> None:
    """
    Render a single assembly proposal, showing matched fragment pairs side by side.

    Each row shows one proposed pair, annotated with the relevant segment
    index and per-pair compatibility score.
    """
    pairs = assembly['pairs']
    confidence = assembly['confidence']
    n_rows = min(len(pairs), 4)

    if n_rows == 0:
        return

    fig, axes = plt.subplots(n_rows, 2, figsize=(6, n_rows * 3), dpi=FIGURE_DPI)
    if n_rows == 1:
        axes = axes[np.newaxis, :]

    for row_idx, pair in enumerate(pairs[:n_rows]):
        for col_idx, (frag_key, seg_key) in enumerate(
            [('frag_i', 'seg_a'), ('frag_j', 'seg_b')]
        ):
            frag_idx = pair[frag_key]
            overlay = draw_contour_overlay(images[frag_idx], contours[frag_idx])
            rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
            axes[row_idx, col_idx].imshow(rgb)
            title = f"{fragment_names[frag_idx]}  [seg {pair[seg_key]}]"
            axes[row_idx, col_idx].set_title(title, fontsize=8)
            axes[row_idx, col_idx].axis('off')

    plt.suptitle(
        f"Assembly #{rank + 1}  —  confidence {confidence:.3f}",
        fontsize=10
    )
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    logger.info("Saved assembly proposal #%d -> %s", rank + 1, output_path)


def render_convergence_plot(trace: List[float], output_path: str) -> None:
    """
    Plot the relaxation labeling convergence trace and save it.

    The y-axis uses a logarithmic scale to make small final deltas visible.
    The convergence threshold is marked as a horizontal reference line.
    """
    fig, ax = plt.subplots(figsize=(6, 3), dpi=FIGURE_DPI)
    ax.plot(
        range(1, len(trace) + 1), trace,
        marker='o', linewidth=1.5, markersize=3, color='steelblue',
        label='Max Δ probability'
    )
    ax.axhline(
        y=1e-4, color='tomato', linestyle='--', linewidth=1.2,
        label='Convergence threshold (1e-4)'
    )
    ax.set_xlabel('Iteration')
    ax.set_ylabel('Max Δ probability')
    ax.set_title('Relaxation Labeling Convergence')
    ax.set_yscale('log')
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    logger.info("Saved convergence plot -> %s", output_path)
