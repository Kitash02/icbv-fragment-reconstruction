"""
Entry point for the archaeological fragment reconstruction pipeline.

Orchestrates the full processing chain:
  1. Preprocessing — Gaussian blur + Otsu threshold (Lectures 21-23)
  2. Chain code extraction and normalization (Lecture 72)
  3. Pairwise compatibility scoring with good-continuation bonus (Lectures 23, 52, 72)
  4. Relaxation labeling assembly search (Lecture 53)
  5. Visualization of results

Usage:
    python src/main.py --input data/sample --output outputs/results --log outputs/logs
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from preprocessing import preprocess_fragment
from chain_code import encode_fragment
from compatibility import (
    build_compatibility_matrix,
    compute_color_signature,
    color_bhattacharyya,
)
from relaxation import (
    run_relaxation,
    extract_top_assemblies,
    MATCH_SCORE_THRESHOLD,
    WEAK_MATCH_SCORE_THRESHOLD,
    ASSEMBLY_CONFIDENCE_THRESHOLD,
)
from visualize import (
    render_fragment_grid,
    render_compatibility_heatmap,
    render_assembly_proposal,
    render_convergence_plot,
)
from assembly_renderer import render_assembly_sheet
from chain_code import contour_to_pixel_segments
from shape_descriptors import pca_normalize_contour, log_shape_summary

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp'}
N_SEGMENTS = 4
N_TOP_ASSEMBLIES = 3

# Color pre-check thresholds (Lecture 71 — appearance-based rejection)
# Conservative values chosen to avoid false positives on positive test cases.
# Fragment sets with a clear bimodal BC distribution (one group with low mutual
# similarity) are immediately rejected before the expensive geometric pipeline.
COLOR_PRECHECK_GAP_THRESH = 0.25    # minimum gap between low and high BC group
COLOR_PRECHECK_LOW_MAX = 0.62       # max allowed BC in the "low" group


def detect_mixed_source_fragments(images: list) -> tuple:
    """
    Detect whether the fragment set contains images from multiple source images.

    Computes the pairwise Bhattacharyya color-histogram similarity matrix and
    checks for a bimodal distribution: a clear gap between a "low" BC cluster
    (cross-image pairs) and a "high" BC cluster (within-image pairs).

    Implements the Lecture 71 intuition that fragments of the same artifact
    share the same pigment palette, so their pairwise color similarity should
    form a unimodal high-BC distribution.

    Returns
    -------
    is_mixed : bool — True if bimodal structure detected.
    min_bc   : float — minimum pairwise BC (diagnostic).
    max_gap  : float — largest gap in sorted BC values (diagnostic).
    """
    if len(images) < 3:
        return False, 1.0, 0.0

    sigs = [compute_color_signature(img) for img in images]
    n = len(sigs)
    bcs = sorted(
        color_bhattacharyya(sigs[i], sigs[j])
        for i in range(n)
        for j in range(i + 1, n)
    )

    gaps = [(bcs[k + 1] - bcs[k], k) for k in range(len(bcs) - 1)]
    max_gap, gap_pos = max(gaps)
    low_group_max = bcs[gap_pos]

    is_mixed = (max_gap >= COLOR_PRECHECK_GAP_THRESH
                and low_group_max <= COLOR_PRECHECK_LOW_MAX)
    return is_mixed, float(bcs[0]), float(max_gap)


def setup_logging(log_dir: str) -> logging.Logger:
    """
    Configure file and console logging with a timestamped log file.

    INFO and above go to both the log file and stdout, matching the
    logging specification in CLAUDE.md.
    """
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = os.path.join(log_dir, f'run_{timestamp}.log')

    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(),
        ],
    )
    root_logger = logging.getLogger('main')
    root_logger.info("Log file: %s", log_path)
    return root_logger


def collect_fragment_paths(input_dir: str) -> list:
    """Return a sorted list of image file paths found in input_dir."""
    paths = sorted(
        p for p in Path(input_dir).iterdir()
        if p.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not paths:
        raise FileNotFoundError(f"No images found in: {input_dir}")
    return paths


def log_compatibility_matrix(
    matrix: np.ndarray,
    names: list,
    run_logger: logging.Logger,
) -> None:
    """Write the full pairwise compatibility matrix (mean over segments) to the log."""
    n_frags = matrix.shape[0]
    summary = matrix.mean(axis=(1, 3))
    run_logger.info("Pairwise compatibility matrix (mean over segments):")
    header = "         " + "  ".join(f"{n:>10}" for n in names)
    run_logger.info(header)
    for row_idx in range(n_frags):
        values = "  ".join(
            f"{summary[row_idx, col_idx]:10.4f}" for col_idx in range(n_frags)
        )
        run_logger.info("%8s  %s", names[row_idx], values)


def log_assembly_report(
    assemblies: list,
    run_logger: logging.Logger,
) -> None:
    """
    Log a structured match/no-match report for every proposed assembly.

    Uses the verdicts produced by relaxation.classify_assembly and
    relaxation.classify_pair_score to give clear success/failure feedback
    for each fragment pair.

    Match criteria (see relaxation.py for constants):
      Per-pair verdict:
        MATCH       — raw compatibility ≥ {match_thr:.2f}
        WEAK_MATCH  — raw compatibility ∈ [{weak_thr:.2f}, {match_thr:.2f})
        NO_MATCH    — raw compatibility < {weak_thr:.2f}
      Assembly verdict:
        MATCH       — avg confidence ≥ {conf_thr:.2f} AND majority of pairs
                      are MATCH / WEAK_MATCH
        WEAK_MATCH  — avg confidence ≥ {conf_thr:.2f} but pairs mixed
        NO_MATCH    — avg confidence < {conf_thr:.2f} (fragments incompatible)
    """.format(
        match_thr=MATCH_SCORE_THRESHOLD,
        weak_thr=WEAK_MATCH_SCORE_THRESHOLD,
        conf_thr=ASSEMBLY_CONFIDENCE_THRESHOLD,
    )
    run_logger.info("=" * 60)
    run_logger.info(
        "MATCH REPORT  (per-pair thresholds: MATCH≥%.2f  WEAK≥%.2f | "
        "assembly: ≥60%% MATCH pairs → MATCH, ≥40%% valid → WEAK_MATCH)",
        MATCH_SCORE_THRESHOLD, WEAK_MATCH_SCORE_THRESHOLD,
    )
    run_logger.info("=" * 60)

    any_match = False
    for rank, assembly in enumerate(assemblies):
        verdict = assembly['verdict']
        confidence = assembly['confidence']
        n_m = assembly['n_match']
        n_w = assembly['n_weak']
        n_n = assembly['n_no_match']

        run_logger.info(
            "Assembly #%d  verdict=%-10s  confidence=%.4f  "
            "pairs: %d MATCH / %d WEAK / %d NO_MATCH",
            rank + 1, verdict, confidence, n_m, n_w, n_n,
        )

        if verdict != 'NO_MATCH':
            any_match = True

        for pair in assembly['pairs']:
            run_logger.info(
                "  frag%d[seg%d] ↔ frag%d[seg%d]  "
                "raw=%.4f  prob=%.4f  [%s]",
                pair['frag_i'], pair['seg_a'],
                pair['frag_j'], pair['seg_b'],
                pair['raw_compat'], pair['score'],
                pair['verdict'],
            )

    run_logger.info("=" * 60)
    if not any_match:
        run_logger.warning(
            "NO MATCH FOUND: all %d proposed assemblies have fewer than 40%% "
            "of their pairs above the WEAK_MATCH threshold (%.2f). "
            "The fragments in this input folder appear geometrically incompatible, "
            "or the images could not be segmented cleanly enough for chain-code comparison.",
            len(assemblies), WEAK_MATCH_SCORE_THRESHOLD,
        )
        print(
            "\n[RESULT] NO MATCH FOUND — fewer than 40%% of fragment pairs exceed "
            "the compatibility threshold.\nCheck that:\n"
            "  1. Each image contains exactly one fragment on a clean background.\n"
            "  2. The fragments in this folder are pieces of the same artifact.\n"
            "  3. The images have sufficient resolution (≥ 300 px per side).\n"
        )
    else:
        accepted = [a for a in assemblies if a['verdict'] != 'NO_MATCH']
        # Best verdict among accepted assemblies (MATCH > WEAK_MATCH)
        best_verdict = "MATCH" if any(a['verdict'] == 'MATCH' for a in accepted) else "WEAK_MATCH"
        best_assembly = max(accepted, key=lambda a: a['confidence'])
        n_match = best_assembly['n_match']
        n_weak  = best_assembly['n_weak']
        print(
            f"\n[RESULT] MATCH FOUND verdict={best_verdict} "
            f"pairs: {n_match} match {n_weak} weak — "
            f"{len(accepted)} of {len(assemblies)} proposed assemblies accepted.\n"
        )


def run_pipeline(args: argparse.Namespace) -> None:
    """Execute the full reconstruction pipeline and write all outputs."""
    run_logger = setup_logging(args.log)
    os.makedirs(args.output, exist_ok=True)
    start_time = time.time()

    fragment_paths = collect_fragment_paths(args.input)
    run_logger.info("Found %d fragment images in %s", len(fragment_paths), args.input)

    images, contours, all_segments, all_pixel_segs, names = [], [], [], [], []

    for fpath in fragment_paths:
        name = fpath.stem
        image, contour = preprocess_fragment(str(fpath))

        # PCA orientation normalization (Lecture 74) — logged for diagnostics
        log_shape_summary(contour, name)
        pca_contour = pca_normalize_contour(contour)

        _, segments = encode_fragment(pca_contour, n_segments=N_SEGMENTS)
        pixel_segs = contour_to_pixel_segments(contour, N_SEGMENTS)

        images.append(image)
        contours.append(contour)
        all_segments.append(segments)
        all_pixel_segs.append(pixel_segs)
        names.append(name)
        run_logger.info(
            "Fragment %-20s  size=%dx%d  contour=%d pts  segments=%d",
            name, image.shape[1], image.shape[0], len(contour), len(segments),
        )

    # ── Color pre-check: reject fragments from different source images ──────
    # Computes pairwise Bhattacharyya BC matrix and looks for a bimodal gap.
    # A clear low-BC cluster (cross-image pairs) indicates mixed-source input.
    # This check runs before the expensive geometric pipeline to save time.
    is_mixed, min_bc, bc_gap = detect_mixed_source_fragments(images)
    run_logger.info(
        "Color pre-check (Lecture 71): min_BC=%.3f  max_gap=%.3f  is_mixed=%s",
        min_bc, bc_gap, is_mixed,
    )
    if is_mixed:
        run_logger.warning(
            "Bimodal color distribution detected (gap=%.3f, min_BC=%.3f). "
            "Fragments appear to come from different source images — "
            "NO MATCH returned without running geometric pipeline.",
            bc_gap, min_bc,
        )
        print(
            f"\n[RESULT] NO MATCH FOUND verdict=NO_MATCH_COLOR — "
            f"bimodal color distribution (gap={bc_gap:.3f}, min_BC={min_bc:.3f}) "
            f"indicates fragments from different source images.\n"
        )
        return

    compat_matrix = build_compatibility_matrix(all_segments, all_pixel_segs, images)
    log_compatibility_matrix(compat_matrix, names, run_logger)

    probs, trace = run_relaxation(compat_matrix)
    run_logger.info(
        "Convergence trace (%d iterations): %s",
        len(trace),
        ", ".join(f"{v:.6f}" for v in trace),
    )

    assemblies = extract_top_assemblies(
        probs, n_top=N_TOP_ASSEMBLIES, compat_matrix=compat_matrix
    )
    log_assembly_report(assemblies, run_logger)

    render_fragment_grid(
        images, contours, names,
        os.path.join(args.output, 'fragment_contours.png'),
    )
    render_compatibility_heatmap(
        compat_matrix, names,
        os.path.join(args.output, 'compatibility_heatmap.png'),
    )
    render_convergence_plot(
        trace,
        os.path.join(args.output, 'convergence.png'),
    )
    for rank, assembly in enumerate(assemblies):
        out_path = os.path.join(args.output, f'assembly_{rank + 1:02d}.png')
        render_assembly_proposal(images, contours, assembly, names, rank, out_path)

    # Geometric assembly visualisation — shows fragments placed side-by-side
    # with matching edges aligned via affine transform
    for rank, assembly in enumerate(assemblies):
        geo_path = os.path.join(args.output, f'assembly_{rank + 1:02d}_geometric.png')
        render_assembly_sheet(
            images, contours, assembly, names, N_SEGMENTS, geo_path
        )

    elapsed = time.time() - start_time
    run_logger.info("Pipeline completed in %.2f seconds.", elapsed)


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Archaeological Fragment Reconstruction — ICBV Final Project"
    )
    parser.add_argument(
        '--input', required=True,
        help='Folder containing fragment PNG/JPG images (one fragment per image)',
    )
    parser.add_argument(
        '--output', default='outputs/results',
        help='Output folder for result images (default: outputs/results)',
    )
    parser.add_argument(
        '--log', default='outputs/logs',
        help='Output folder for log files (default: outputs/logs)',
    )
    return parser


if __name__ == '__main__':
    run_pipeline(build_arg_parser().parse_args())
