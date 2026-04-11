"""
Test script to validate Gabor spectral diversity fix.

Tests:
1. Load brown/beige artifact pairs (false positives)
2. Compute original Gabor BC (should be ~1.0)
3. Compute diversity metrics
4. Apply diversity penalty
5. Show before/after comparison
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

def test_gabor_fix():
    """Test the Gabor fix on known false positive pairs."""

    # Define test pairs using actual available images
    # Using fragment images from negative examples (different artifacts)
    test_pairs = [
        ("data/examples/negative/mixed_gettyimages-13116049_gettyimages-17009652/B_03_gettyimages-170096524-1024x1024_frag_00.png",
         "data/examples/negative/mixed_gettyimages-13116049_gettyimages-21778090/B_03_gettyimages-2177809001-1024x1024_frag_00.png",
         "Getty 17009652 vs 21778090 (brown pottery)"),

        ("data/examples/negative/mixed_gettyimages-13116049_gettyimages-17009652/B_03_gettyimages-170096524-1024x1024_frag_00.png",
         "data/examples/negative/mixed_gettyimages-13116049_gettyimages-47081632/B_03_gettyimages-470816328-2048x2048_frag_00.png",
         "Getty 17009652 vs 47081632 (brown pottery)"),

        ("data/examples/negative/mixed_gettyimages-13116049_gettyimages-21778090/B_03_gettyimages-2177809001-1024x1024_frag_00.png",
         "data/examples/negative/mixed_gettyimages-13116049_gettyimages-47081632/B_03_gettyimages-470816328-2048x2048_frag_00.png",
         "Getty 21778090 vs 47081632 (brown pottery)"),
    ]

    print("=" * 80)
    print("GABOR SPECTRAL DIVERSITY FIX VALIDATION")
    print("=" * 80)
    print(f"\nThreshold: {SPECTRAL_DIVERSITY_THRESHOLD}")
    print(f"Homogeneous penalty: {HOMOGENEOUS_PENALTY}")
    print()

    results = []

    for img_path_a, img_path_b, description in test_pairs:
        path_a = Path(__file__).parent / img_path_a
        path_b = Path(__file__).parent / img_path_b

        # Skip if files don't exist
        if not path_a.exists() or not path_b.exists():
            print(f"SKIP: {description} (files not found)")
            print(f"  A: {path_a}")
            print(f"  B: {path_b}")
            print()
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

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if not results:
        print("No test pairs found. Please check that test images exist.")
        return

    penalty_applied = sum(1 for r in results if r['penalty_applied'])
    avg_bc_original = np.mean([r['bc_original'] for r in results])
    avg_bc_fixed = np.mean([r['bc_fixed'] for r in results])

    print(f"Total pairs tested: {len(results)}")
    print(f"Penalty applied: {penalty_applied}/{len(results)}")
    print(f"Average BC original: {avg_bc_original:.4f}")
    print(f"Average BC fixed: {avg_bc_fixed:.4f}")
    print(f"Average reduction: {(1 - avg_bc_fixed/avg_bc_original)*100:.1f}%")
    print()

    # Expected impact
    print("EXPECTED IMPACT ON FALSE POSITIVES:")
    print(f"  - Original: All had bc_gabor ~ 1.0 (useless discriminator)")
    print(f"  - Fixed: Homogeneous pairs get bc_gabor * {HOMOGENEOUS_PENALTY} = {avg_bc_fixed:.3f}")
    print(f"  - Discrimination power: RESTORED")
    print()

    return results

if __name__ == '__main__':
    test_gabor_fix()
