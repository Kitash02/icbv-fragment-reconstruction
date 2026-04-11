"""
Test script to validate Gabor spectral diversity fix on BOTH positive and negative pairs.
"""

import sys
import cv2
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from compatibility_gabor_fixed import (
    compute_gabor_signature,
    compute_gabor_spectral_diversity,
    appearance_bhattacharyya,
    appearance_bhattacharyya_with_diversity,
    SPECTRAL_DIVERSITY_THRESHOLD,
    HOMOGENEOUS_PENALTY
)

def load_image(path: str) -> np.ndarray:
    """Load image from path."""
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Cannot load {path}")
    return img

def test_comprehensive():
    """Test on both positive (same artifact) and negative (different artifacts) pairs."""

    print("=" * 80)
    print("GABOR SPECTRAL DIVERSITY FIX - COMPREHENSIVE VALIDATION")
    print("=" * 80)
    print(f"\nThreshold: {SPECTRAL_DIVERSITY_THRESHOLD}")
    print(f"Homogeneous penalty: {HOMOGENEOUS_PENALTY}")
    print()

    # Test negative pairs (should have penalty applied)
    print("=" * 80)
    print("NEGATIVE PAIRS (different artifacts - should have penalty)")
    print("=" * 80)
    print()

    negative_pairs = [
        ("data/examples/negative/mixed_gettyimages-13116049_gettyimages-17009652/B_03_gettyimages-170096524-1024x1024_frag_00.png",
         "data/examples/negative/mixed_gettyimages-13116049_gettyimages-21778090/B_03_gettyimages-2177809001-1024x1024_frag_00.png",
         "Getty 17009652 vs 21778090"),

        ("data/examples/negative/mixed_gettyimages-13116049_gettyimages-17009652/B_03_gettyimages-170096524-1024x1024_frag_00.png",
         "data/examples/negative/mixed_gettyimages-13116049_gettyimages-47081632/B_03_gettyimages-470816328-2048x2048_frag_00.png",
         "Getty 17009652 vs 47081632"),

        ("data/examples/negative/mixed_gettyimages-13116049_gettyimages-21778090/B_03_gettyimages-2177809001-1024x1024_frag_00.png",
         "data/examples/negative/mixed_gettyimages-13116049_gettyimages-47081632/B_03_gettyimages-470816328-2048x2048_frag_00.png",
         "Getty 21778090 vs 47081632"),
    ]

    negative_results = test_pairs(negative_pairs, "NEGATIVE")

    # Test positive pairs (should NOT have penalty)
    print("\n" + "=" * 80)
    print("POSITIVE PAIRS (same artifact - should NOT have penalty)")
    print("=" * 80)
    print()

    positive_pairs = [
        ("data/examples/positive/gettyimages-170096524-1024x1024/gettyimages-170096524-1024x1024_frag_00.png",
         "data/examples/positive/gettyimages-170096524-1024x1024/gettyimages-170096524-1024x1024_frag_01.png",
         "Getty 170096524 frag 0 vs 1"),

        ("data/examples/positive/gettyimages-170096524-1024x1024/gettyimages-170096524-1024x1024_frag_02.png",
         "data/examples/positive/gettyimages-170096524-1024x1024/gettyimages-170096524-1024x1024_frag_03.png",
         "Getty 170096524 frag 2 vs 3"),

        ("data/examples/positive/gettyimages-1311604917-1024x1024/gettyimages-1311604917-1024x1024_frag_01.png",
         "data/examples/positive/gettyimages-1311604917-1024x1024/gettyimages-1311604917-1024x1024_frag_02.png",
         "Getty 1311604917 frag 1 vs 2"),
    ]

    positive_results = test_pairs(positive_pairs, "POSITIVE")

    # Final comparison
    print("\n" + "=" * 80)
    print("FINAL COMPARISON")
    print("=" * 80)

    if negative_results:
        neg_penalty_rate = sum(1 for r in negative_results if r['penalty_applied']) / len(negative_results)
        neg_avg_bc_original = np.mean([r['bc_original'] for r in negative_results])
        neg_avg_bc_fixed = np.mean([r['bc_fixed'] for r in negative_results])

        print(f"\nNEGATIVE PAIRS ({len(negative_results)} pairs):")
        print(f"  Penalty applied: {neg_penalty_rate*100:.0f}%")
        print(f"  Avg BC original: {neg_avg_bc_original:.4f}")
        print(f"  Avg BC fixed:    {neg_avg_bc_fixed:.4f}")
        print(f"  Reduction:       {(1-neg_avg_bc_fixed/neg_avg_bc_original)*100:.1f}%")

    if positive_results:
        pos_penalty_rate = sum(1 for r in positive_results if r['penalty_applied']) / len(positive_results)
        pos_avg_bc_original = np.mean([r['bc_original'] for r in positive_results])
        pos_avg_bc_fixed = np.mean([r['bc_fixed'] for r in positive_results])

        print(f"\nPOSITIVE PAIRS ({len(positive_results)} pairs):")
        print(f"  Penalty applied: {pos_penalty_rate*100:.0f}%")
        print(f"  Avg BC original: {pos_avg_bc_original:.4f}")
        print(f"  Avg BC fixed:    {pos_avg_bc_fixed:.4f}")
        print(f"  Change:          {(pos_avg_bc_fixed/pos_avg_bc_original-1)*100:.1f}%")

    print("\n" + "=" * 80)
    print("EXPECTED IMPACT:")
    print("=" * 80)
    print("Negative pairs: BC reduced by 50% (discrimination restored)")
    print("Positive pairs: BC unchanged or minimally affected")
    print("Overall: Should eliminate 4-5 of 7 false positives")
    print("Target accuracy: 85-88% (from current 77.8%)")
    print()


def test_pairs(pairs, label):
    """Test a list of image pairs."""
    results = []

    for img_path_a, img_path_b, description in pairs:
        path_a = Path(__file__).parent / img_path_a
        path_b = Path(__file__).parent / img_path_b

        # Skip if files don't exist
        if not path_a.exists() or not path_b.exists():
            print(f"SKIP: {description} (files not found)")
            continue

        print(f"Testing: {description}")
        print(f"  A: {path_a.name}")
        print(f"  B: {path_b.name}")

        # Load images
        img_a = load_image(str(path_a))
        img_b = load_image(str(path_b))

        # Compute Gabor signatures
        gabor_sig_a = compute_gabor_signature(img_a)
        gabor_sig_b = compute_gabor_signature(img_b)

        # Compute diversities
        diversity_a = compute_gabor_spectral_diversity(gabor_sig_a)
        diversity_b = compute_gabor_spectral_diversity(gabor_sig_b)

        # Compute original BC (without diversity)
        bc_original = appearance_bhattacharyya(gabor_sig_a, gabor_sig_b)

        # Compute fixed BC (with diversity)
        bc_fixed = appearance_bhattacharyya_with_diversity(
            gabor_sig_a, gabor_sig_b,
            diversity_a, diversity_b
        )

        # Determine if penalty was applied
        both_homogeneous = (diversity_a < SPECTRAL_DIVERSITY_THRESHOLD and
                           diversity_b < SPECTRAL_DIVERSITY_THRESHOLD)

        print(f"  Diversity A: {diversity_a:.4f} {'(homogeneous)' if diversity_a < SPECTRAL_DIVERSITY_THRESHOLD else '(structured)'}")
        print(f"  Diversity B: {diversity_b:.4f} {'(homogeneous)' if diversity_b < SPECTRAL_DIVERSITY_THRESHOLD else '(structured)'}")
        print(f"  BC original: {bc_original:.4f}")
        print(f"  BC fixed:    {bc_fixed:.4f}")
        print(f"  Penalty:     {bc_fixed/bc_original if bc_original > 0 else 1.0:.2f}x")
        print(f"  Status:      {'PENALTY APPLIED' if both_homogeneous else 'NO PENALTY'}")
        print()

        results.append({
            'description': description,
            'diversity_a': diversity_a,
            'diversity_b': diversity_b,
            'bc_original': bc_original,
            'bc_fixed': bc_fixed,
            'penalty_applied': both_homogeneous
        })

    return results


if __name__ == '__main__':
    test_comprehensive()
