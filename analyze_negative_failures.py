#!/usr/bin/env python3
"""
Analyze why ALL negative test cases fail.
"""

import sys
import numpy as np
from pathlib import Path
import cv2

sys.path.insert(0, str(Path(__file__).parent / "src"))

from preprocessing import preprocess_fragment
from compatibility import compute_color_signature, color_bhattacharyya, build_compatibility_matrix
from chain_code import encode_fragment

def analyze_negative_case(folder_path: Path):
    """Analyze a single negative test case."""
    print(f"\n{'='*80}")
    print(f"ANALYZING: {folder_path.name}")
    print(f"{'='*80}")

    # Load all fragments
    image_files = sorted([f for f in folder_path.iterdir() if f.suffix.lower() in ['.png', '.jpg', '.jpeg']])
    print(f"Found {len(image_files)} fragments")

    # Group fragments by source image (A_ vs B_)
    group_a = [f for f in image_files if f.name.startswith('A_')]
    group_b = [f for f in image_files if f.name.startswith('B_')]
    print(f"  Group A (source 1): {len(group_a)} fragments")
    print(f"  Group B (source 2): {len(group_b)} fragments")

    # Load images
    images = []
    labels = []
    for f in image_files:
        img = cv2.imread(str(f), cv2.IMREAD_UNCHANGED)
        if img is None:
            print(f"  ERROR: Could not load {f.name}")
            continue
        images.append(img)
        labels.append('A' if f.name.startswith('A_') else 'B')

    if len(images) < 2:
        print("  ERROR: Not enough images loaded")
        return

    # Compute color signatures
    print(f"\nCOMPUTING COLOR SIGNATURES...")
    color_sigs = [compute_color_signature(img) for img in images]

    # Compute all pairwise BC scores
    n = len(color_sigs)
    bc_scores = []
    bc_within_a = []
    bc_within_b = []
    bc_cross = []

    for i in range(n):
        for j in range(i+1, n):
            bc = color_bhattacharyya(color_sigs[i], color_sigs[j])
            bc_scores.append(bc)

            if labels[i] == 'A' and labels[j] == 'A':
                bc_within_a.append(bc)
            elif labels[i] == 'B' and labels[j] == 'B':
                bc_within_b.append(bc)
            else:
                bc_cross.append(bc)

    print(f"\nCOLOR BC STATISTICS:")
    print(f"  All pairs:        mean={np.mean(bc_scores):.3f}, min={np.min(bc_scores):.3f}, max={np.max(bc_scores):.3f}")
    if bc_within_a:
        print(f"  Within group A:   mean={np.mean(bc_within_a):.3f}, min={np.min(bc_within_a):.3f}, max={np.max(bc_within_a):.3f}")
    if bc_within_b:
        print(f"  Within group B:   mean={np.mean(bc_within_b):.3f}, min={np.min(bc_within_b):.3f}, max={np.max(bc_within_b):.3f}")
    if bc_cross:
        print(f"  Cross-group (A-B): mean={np.mean(bc_cross):.3f}, min={np.min(bc_cross):.3f}, max={np.max(bc_cross):.3f}")

    # Check if color pre-check should have caught this
    sorted_bc = sorted(bc_scores)
    gaps = [(sorted_bc[k+1] - sorted_bc[k], k) for k in range(len(sorted_bc)-1)]
    max_gap, gap_pos = max(gaps) if gaps else (0.0, 0)
    low_group_max = sorted_bc[gap_pos] if gaps else 0.0

    print(f"\nCOLOR PRE-CHECK ANALYSIS:")
    print(f"  Max gap in BC distribution: {max_gap:.3f}")
    print(f"  Low group max BC: {low_group_max:.3f}")
    print(f"  Would pre-check reject? gap>0.25 AND low_max<0.62: {max_gap >= 0.25 and low_group_max <= 0.62}")

    # Now do geometric analysis
    print(f"\nCOMPUTING GEOMETRIC FEATURES...")

    # Preprocess and extract chain codes
    fragments_data = []
    for img in images:
        try:
            _, contour, _ = preprocess_fragment(img)
            if contour is None or len(contour) < 20:
                print("  WARNING: Contour too small or missing")
                continue
            chain_rep = encode_fragment(contour, n_segments=4)
            fragments_data.append((img, contour, chain_rep))
        except Exception as e:
            print(f"  ERROR processing fragment: {e}")
            continue

    if len(fragments_data) < 2:
        print("  ERROR: Not enough fragments processed")
        return

    print(f"  Successfully processed {len(fragments_data)} fragments")

    # Build compatibility matrix
    compat_matrix = build_compatibility_matrix(fragments_data)

    # Analyze compatibility scores
    print(f"\nGEOMETRIC COMPATIBILITY STATISTICS:")

    # Mask out self-comparisons
    n_frags = compat_matrix.shape[0]
    n_segs = compat_matrix.shape[1]

    all_scores = []
    for i in range(n_frags):
        for a in range(n_segs):
            for j in range(n_frags):
                for b in range(n_segs):
                    if i != j:
                        all_scores.append(compat_matrix[i, a, j, b])

    all_scores = np.array(all_scores)
    print(f"  All compatibility scores:  mean={np.mean(all_scores):.3f}, min={np.min(all_scores):.3f}, max={np.max(all_scores):.3f}")
    print(f"  Scores > 0.70 (MATCH threshold): {np.sum(all_scores > 0.70)} / {len(all_scores)} ({100*np.sum(all_scores > 0.70)/len(all_scores):.1f}%)")
    print(f"  Scores > 0.60 (ASSEMBLY threshold): {np.sum(all_scores > 0.60)} / {len(all_scores)} ({100*np.sum(all_scores > 0.60)/len(all_scores):.1f}%)")
    print(f"  Scores > 0.50 (WEAK threshold): {np.sum(all_scores > 0.50)} / {len(all_scores)} ({100*np.sum(all_scores > 0.50)/len(all_scores):.1f}%)")

    # Find max compatibility score
    max_score = np.max(all_scores)
    max_idx = np.unravel_index(np.argmax(compat_matrix), compat_matrix.shape)
    print(f"\n  Maximum compatibility: {max_score:.3f}")
    print(f"    Between fragment {max_idx[0]} seg {max_idx[1]} <-> fragment {max_idx[2]} seg {max_idx[3]}")
    if max_idx[0] < len(labels) and max_idx[2] < len(labels):
        print(f"    Group: {labels[max_idx[0]]} <-> {labels[max_idx[2]]}")

    return {
        'folder': folder_path.name,
        'bc_mean': np.mean(bc_scores),
        'bc_cross_mean': np.mean(bc_cross) if bc_cross else 0.0,
        'bc_gap': max_gap,
        'compat_mean': np.mean(all_scores),
        'compat_max': max_score,
        'pct_above_match': 100*np.sum(all_scores > 0.70)/len(all_scores),
    }


if __name__ == "__main__":
    negative_dir = Path("data/examples/negative")

    if not negative_dir.exists():
        print(f"ERROR: {negative_dir} not found")
        sys.exit(1)

    # Analyze first 5 negative cases
    folders = sorted(negative_dir.iterdir())[:5]

    results = []
    for folder in folders:
        if folder.is_dir():
            try:
                result = analyze_negative_case(folder)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"\nERROR analyzing {folder.name}: {e}")
                import traceback
                traceback.print_exc()

    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY OF {len(results)} NEGATIVE CASES")
    print(f"{'='*80}")

    if results:
        print(f"\nColor BC (lower = more different):")
        print(f"  Mean of all BC:      {np.mean([r['bc_mean'] for r in results]):.3f}")
        print(f"  Mean of cross BC:    {np.mean([r['bc_cross_mean'] for r in results]):.3f}")
        print(f"  Mean gap:            {np.mean([r['bc_gap'] for r in results]):.3f}")

        print(f"\nGeometric Compatibility (higher = more similar):")
        print(f"  Mean of all scores:  {np.mean([r['compat_mean'] for r in results]):.3f}")
        print(f"  Mean of max scores:  {np.mean([r['compat_max'] for r in results]):.3f}")
        print(f"  Mean % above 0.70:   {np.mean([r['pct_above_match'] for r in results]):.1f}%")

        print(f"\nROOT CAUSE:")
        avg_max_compat = np.mean([r['compat_max'] for r in results])
        if avg_max_compat > 0.60:
            print(f"  ✗ GEOMETRIC SCORES TOO HIGH!")
            print(f"    Average max compatibility: {avg_max_compat:.3f}")
            print(f"    This exceeds assembly threshold of 0.60")
            print(f"    Even fragments from different pottery show high geometric similarity")
        else:
            print(f"  ? Geometric scores seem OK (avg max: {avg_max_compat:.3f})")
