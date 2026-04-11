#!/usr/bin/env python3
"""
stage_timing.py
---------------
Measures execution time for each major stage of the pipeline on a single test case.

Usage:
    python stage_timing.py [test_folder_path]
"""

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

from preprocessing import preprocess_fragment
from chain_code import encode_fragment, contour_to_pixel_segments
from compatibility import build_compatibility_matrix
from relaxation import run_relaxation, extract_top_assemblies
from visualize import render_fragment_grid, render_compatibility_heatmap, render_assembly_proposal, render_convergence_plot
from assembly_renderer import render_assembly_sheet
from shape_descriptors import pca_normalize_contour

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'}
N_SEGMENTS = 4
N_TOP_ASSEMBLIES = 3


def time_stage(name, func, *args, **kwargs):
    """Time a function call and return result + elapsed time."""
    print(f"  Running: {name}...", end=' ', flush=True)
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    print(f"{elapsed:.3f}s")
    return result, elapsed


def profile_stages(test_folder):
    """Profile each pipeline stage on a single test case."""

    print("\n" + "="*80)
    print("  STAGE-BY-STAGE TIMING ANALYSIS")
    print("="*80)
    print(f"  Test folder: {test_folder}")
    print("="*80 + "\n")

    # Collect fragment images
    fragment_paths = sorted(
        p for p in test_folder.iterdir()
        if p.suffix.lower() in IMAGE_EXTENSIONS and not p.name.startswith(".")
    )

    if not fragment_paths:
        print(f"Error: No images found in {test_folder}")
        return

    print(f"Found {len(fragment_paths)} fragments\n")

    timings = {}

    # Stage 1: Preprocessing
    print("STAGE 1: PREPROCESSING")
    images, contours, all_segments, all_pixel_segs = [], [], [], []

    preprocess_total = 0.0
    for fpath in fragment_paths:
        (image, contour), t = time_stage(
            f"  - {fpath.name}",
            preprocess_fragment,
            str(fpath)
        )
        preprocess_total += t

        # PCA normalization
        pca_contour, t_pca = time_stage(
            "    PCA normalization",
            pca_normalize_contour,
            contour
        )
        preprocess_total += t_pca

        images.append(image)
        contours.append(contour)

    timings['preprocessing'] = preprocess_total
    print(f"  TOTAL PREPROCESSING: {preprocess_total:.3f}s\n")

    # Stage 2: Feature extraction (chain code + segments)
    print("STAGE 2: FEATURE EXTRACTION")
    feature_total = 0.0

    for i, contour in enumerate(contours):
        pca_contour = pca_normalize_contour(contour)

        _, t_encode = time_stage(
            f"  - Fragment {i+1} chain code",
            encode_fragment,
            pca_contour,
            n_segments=N_SEGMENTS
        )
        feature_total += t_encode

        (_, segments), _ = time_stage(
            "    (rerun for segments)",
            encode_fragment,
            pca_contour,
            n_segments=N_SEGMENTS
        )

        pixel_segs, t_pixel = time_stage(
            "    Pixel segments",
            contour_to_pixel_segments,
            contour,
            N_SEGMENTS
        )
        feature_total += t_pixel

        all_segments.append(segments)
        all_pixel_segs.append(pixel_segs)

    timings['feature_extraction'] = feature_total
    print(f"  TOTAL FEATURE EXTRACTION: {feature_total:.3f}s\n")

    # Stage 3: Compatibility matrix
    print("STAGE 3: COMPATIBILITY SCORING")
    compat_matrix, t_compat = time_stage(
        "  Building compatibility matrix",
        build_compatibility_matrix,
        all_segments,
        all_pixel_segs,
        images
    )
    timings['compatibility'] = t_compat
    print(f"  TOTAL COMPATIBILITY: {t_compat:.3f}s\n")

    # Stage 4: Relaxation
    print("STAGE 4: RELAXATION LABELING")
    (probs, trace), t_relax = time_stage(
        "  Running relaxation",
        run_relaxation,
        compat_matrix
    )
    timings['relaxation'] = t_relax
    print(f"  TOTAL RELAXATION: {t_relax:.3f}s")
    print(f"  ({len(trace)} iterations)\n")

    # Stage 5: Assembly extraction
    print("STAGE 5: ASSEMBLY EXTRACTION")
    assemblies, t_extract = time_stage(
        "  Extracting top assemblies",
        extract_top_assemblies,
        probs,
        n_top=N_TOP_ASSEMBLIES,
        compat_matrix=compat_matrix
    )
    timings['assembly_extraction'] = t_extract
    print(f"  TOTAL EXTRACTION: {t_extract:.3f}s\n")

    # Stage 6: Visualization (optional, but included in actual runs)
    print("STAGE 6: VISUALIZATION")
    viz_total = 0.0

    output_dir = ROOT / "outputs" / "stage_timing_test"
    output_dir.mkdir(parents=True, exist_ok=True)

    names = [p.stem for p in fragment_paths]

    _, t = time_stage(
        "  Fragment grid",
        render_fragment_grid,
        images, contours, names,
        str(output_dir / "fragments.png")
    )
    viz_total += t

    _, t = time_stage(
        "  Compatibility heatmap",
        render_compatibility_heatmap,
        compat_matrix, names,
        str(output_dir / "heatmap.png")
    )
    viz_total += t

    _, t = time_stage(
        "  Convergence plot",
        render_convergence_plot,
        trace,
        str(output_dir / "convergence.png")
    )
    viz_total += t

    for rank, assembly in enumerate(assemblies):
        _, t = time_stage(
            f"  Assembly {rank+1} proposal",
            render_assembly_proposal,
            images, contours, assembly, names, rank,
            str(output_dir / f"assembly_{rank+1:02d}.png")
        )
        viz_total += t

        _, t = time_stage(
            f"  Assembly {rank+1} geometric",
            render_assembly_sheet,
            images, contours, assembly, names, N_SEGMENTS,
            str(output_dir / f"assembly_{rank+1:02d}_geometric.png")
        )
        viz_total += t

    timings['visualization'] = viz_total
    print(f"  TOTAL VISUALIZATION: {viz_total:.3f}s\n")

    # Summary
    print("="*80)
    print("  TIMING SUMMARY")
    print("="*80)

    total = sum(timings.values())

    for stage, t in timings.items():
        pct = (t / total * 100) if total > 0 else 0
        print(f"  {stage:<25} {t:>8.3f}s   {pct:>6.1f}%")

    print("-"*80)
    print(f"  {'TOTAL':<25} {total:>8.3f}s   {100.0:>6.1f}%")
    print("="*80 + "\n")

    return timings, total


def main():
    parser = argparse.ArgumentParser(
        description="Time each pipeline stage on a single test case"
    )
    parser.add_argument(
        'test_folder',
        nargs='?',
        default='data/examples/positive/abstract_art_3frags',
        help='Path to test case folder'
    )

    args = parser.parse_args()
    test_folder = Path(args.test_folder)

    if not test_folder.exists():
        print(f"Error: Test folder not found: {test_folder}")
        sys.exit(1)

    profile_stages(test_folder)


if __name__ == "__main__":
    main()
