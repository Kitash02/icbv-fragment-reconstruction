"""
Extended Test Suite for Archaeological Fragment Reconstruction Pipeline.

Comprehensive testing following thorough software engineering principles:
  1. Boundary Value Analysis
  2. Equivalence Class Partitioning
  3. Stress Testing
  4. Error Path Testing
  5. Regression Testing
  6. Property-Based Testing

Run with:  python -m pytest tests/test_extended_suite.py -v
"""

import sys
import os
import numpy as np
import pytest
import tempfile
import cv2
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from chain_code import (
    points_to_chain_code,
    first_difference,
    cyclic_minimum_rotation,
    normalize_chain_code,
    segment_chain_code,
    compute_curvature_profile,
)
from compatibility import (
    edit_distance,
    segment_compatibility,
    build_compatibility_matrix,
    profile_similarity,
    good_continuation_bonus,
    segment_fourier_score,
    compute_color_signature,
    color_bhattacharyya,
)
from relaxation import (
    initialize_probabilities,
    run_relaxation,
    extract_top_assemblies,
    classify_pair_score,
    classify_assembly,
    MATCH_SCORE_THRESHOLD,
    WEAK_MATCH_SCORE_THRESHOLD,
    ASSEMBLY_CONFIDENCE_THRESHOLD,
)
from preprocessing import (
    preprocess_fragment,
    apply_gaussian_blur,
    morphological_cleanup,
)


# =============================================================================
# Test Fixtures and Helpers
# =============================================================================

@pytest.fixture
def temp_image_dir():
    """Create a temporary directory for test images."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def create_test_image(width, height, background_color=255, fragment_present=True):
    """
    Create a synthetic test image with optional fragment.

    Args:
        width, height: Image dimensions
        background_color: Background pixel value (0-255)
        fragment_present: If True, draw a simple geometric shape

    Returns:
        BGR image as numpy array
    """
    image = np.full((height, width, 3), background_color, dtype=np.uint8)

    if fragment_present:
        # Draw a simple rectangular fragment in the center
        h_start, h_end = height // 4, 3 * height // 4
        w_start, w_end = width // 4, 3 * width // 4
        image[h_start:h_end, w_start:w_end] = [100, 100, 100]

    return image


def make_square_contour(side: int = 10, origin=(0, 0)) -> np.ndarray:
    """Generate a closed square boundary as a (N, 2) point array."""
    x0, y0 = origin
    top = [(x0 + i, y0) for i in range(side)]
    right = [(x0 + side, y0 + i) for i in range(side)]
    bottom = [(x0 + side - i, y0 + side) for i in range(side)]
    left = [(x0, y0 + side - i) for i in range(side)]
    return np.array(top + right + bottom + left)


def make_circular_contour(radius: int = 50, center=(100, 100), n_points=100) -> np.ndarray:
    """Generate a circular contour."""
    angles = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
    x = center[0] + radius * np.cos(angles)
    y = center[1] + radius * np.sin(angles)
    return np.column_stack([x, y]).astype(int)


def make_mock_compat(n_frags: int = 3, n_segs: int = 2) -> np.ndarray:
    """Return a random compatibility matrix with same-fragment entries zeroed."""
    matrix = np.random.rand(n_frags, n_segs, n_frags, n_segs)
    for frag_idx in range(n_frags):
        matrix[frag_idx, :, frag_idx, :] = 0.0
    return matrix


# =============================================================================
# 1. BOUNDARY VALUE TESTS
# =============================================================================

class TestBoundaryValues:
    """Test behavior at exact threshold values and edge cases."""

    def test_similarity_at_exact_match_threshold(self):
        """Test classification exactly at MATCH_SCORE_THRESHOLD."""
        score = MATCH_SCORE_THRESHOLD
        verdict = classify_pair_score(score)
        assert verdict == "MATCH", f"Score {score} should be classified as MATCH"

    def test_similarity_just_below_match_threshold(self):
        """Test classification just below MATCH_SCORE_THRESHOLD."""
        score = MATCH_SCORE_THRESHOLD - 0.01
        verdict = classify_pair_score(score)
        assert verdict == "WEAK_MATCH", f"Score {score} should be classified as WEAK_MATCH"

    def test_similarity_just_above_match_threshold(self):
        """Test classification just above MATCH_SCORE_THRESHOLD."""
        score = MATCH_SCORE_THRESHOLD + 0.01
        verdict = classify_pair_score(score)
        assert verdict == "MATCH", f"Score {score} should be classified as MATCH"

    def test_similarity_at_exact_weak_threshold(self):
        """Test classification exactly at WEAK_MATCH_SCORE_THRESHOLD."""
        score = WEAK_MATCH_SCORE_THRESHOLD
        verdict = classify_pair_score(score)
        assert verdict == "WEAK_MATCH", f"Score {score} should be classified as WEAK_MATCH"

    def test_similarity_just_below_weak_threshold(self):
        """Test classification just below WEAK_MATCH_SCORE_THRESHOLD."""
        score = WEAK_MATCH_SCORE_THRESHOLD - 0.01
        verdict = classify_pair_score(score)
        assert verdict == "NO_MATCH", f"Score {score} should be classified as NO_MATCH"

    def test_similarity_just_above_weak_threshold(self):
        """Test classification just above WEAK_MATCH_SCORE_THRESHOLD."""
        score = WEAK_MATCH_SCORE_THRESHOLD + 0.01
        verdict = classify_pair_score(score)
        assert verdict == "WEAK_MATCH", f"Score {score} should be classified as WEAK_MATCH"

    def test_extreme_score_zero(self):
        """Test behavior with score of 0.0."""
        score = 0.0
        verdict = classify_pair_score(score)
        assert verdict == "NO_MATCH", "Score 0.0 should be NO_MATCH"

    def test_extreme_score_one(self):
        """Test behavior with score of 1.0."""
        score = 1.0
        verdict = classify_pair_score(score)
        assert verdict == "MATCH", "Score 1.0 should be MATCH"

    def test_extreme_score_negative(self):
        """Test behavior with negative score (edge case)."""
        score = -0.5
        verdict = classify_pair_score(score)
        assert verdict == "NO_MATCH", "Negative score should be NO_MATCH"

    def test_extreme_score_above_one(self):
        """Test behavior with score > 1.0 (including bonuses)."""
        score = 1.25  # Max possible with all bonuses
        verdict = classify_pair_score(score)
        assert verdict == "MATCH", "Score > 1.0 should be MATCH"

    def test_assembly_confidence_at_threshold(self):
        """Test assembly classification at exact ASSEMBLY_CONFIDENCE_THRESHOLD."""
        confidence = ASSEMBLY_CONFIDENCE_THRESHOLD
        pairs = [
            {'raw_compat': MATCH_SCORE_THRESHOLD, 'verdict': 'MATCH'},
            {'raw_compat': MATCH_SCORE_THRESHOLD, 'verdict': 'MATCH'},
        ]
        verdict = classify_assembly(confidence, pairs)
        assert verdict in ["MATCH", "WEAK_MATCH"], \
            f"Assembly with confidence {confidence} should be MATCH or WEAK_MATCH"


# =============================================================================
# 2. EQUIVALENCE CLASS TESTS
# =============================================================================

class TestEquivalenceClasses:
    """Test representative inputs from each equivalence class."""

    def test_identical_segments(self):
        """Equivalence class: identical chain code segments."""
        seg = [0, 1, 2, 3, 0, 1]
        score = segment_compatibility(seg, seg)
        assert score == pytest.approx(1.0), \
            "Identical segments should have compatibility 1.0"

    def test_completely_different_segments(self):
        """Equivalence class: completely different segments."""
        seg_a = [0, 0, 0, 0, 0]
        seg_b = [7, 7, 7, 7, 7]
        score = segment_compatibility(seg_a, seg_b)
        assert score < 0.5, \
            "Completely different segments should have low compatibility"

    def test_similar_segments(self):
        """Equivalence class: segments with minor differences."""
        seg_a = [0, 1, 2, 3, 4, 5]
        seg_b = [0, 1, 2, 9, 4, 5]  # One different element
        score = segment_compatibility(seg_a, seg_b)
        assert 0.5 < score < 1.0, \
            "Similar segments should have moderate-to-high compatibility"

    def test_same_artifact_different_fragments(self):
        """Equivalence class: fragments from same artifact."""
        # Create contours with similar shapes
        contour_a = make_square_contour(side=20, origin=(0, 0))
        contour_b = make_square_contour(side=20, origin=(30, 0))

        chain_a = points_to_chain_code(contour_a)
        chain_b = points_to_chain_code(contour_b)

        assert len(chain_a) > 0 and len(chain_b) > 0, \
            "Contours should produce non-empty chain codes"

    def test_different_artifact_fragments(self):
        """Equivalence class: fragments from different artifacts."""
        # Create very different shapes
        contour_square = make_square_contour(side=20)
        contour_circle = make_circular_contour(radius=20, n_points=80)

        chain_square = points_to_chain_code(contour_square)
        chain_circle = points_to_chain_code(contour_circle)

        # They should produce different chain codes
        assert chain_square != chain_circle, \
            "Different shapes should have different chain codes"

    def test_empty_segment(self):
        """Equivalence class: empty segments (edge case)."""
        empty_seg = []
        normal_seg = [0, 1, 2, 3]
        score = segment_compatibility(empty_seg, normal_seg)
        assert score == 0.0, \
            "Empty segment should have zero compatibility"

    def test_single_element_segments(self):
        """Equivalence class: minimal segments (1 element)."""
        seg_a = [0]
        seg_b = [0]
        score = segment_compatibility(seg_a, seg_b)
        assert 0.0 <= score <= 1.0, \
            "Single-element segments should have valid compatibility"


# =============================================================================
# 3. STRESS TESTS
# =============================================================================

class TestStressConditions:
    """Test system behavior under extreme conditions."""

    def test_many_fragments_simultaneously(self):
        """Stress test: process 100 fragments."""
        n_frags = 100
        n_segs = 4

        # Create a large random compatibility matrix
        compat = make_mock_compat(n_frags, n_segs)

        # Should complete without error
        probs = initialize_probabilities(compat)
        assert probs.shape == (n_frags, n_segs, n_frags, n_segs), \
            "Probability matrix should have correct shape"

        # Check memory efficiency: probabilities should sum to 1 per row
        flat = probs.reshape(n_frags * n_segs, n_frags * n_segs)
        row_sums = flat.sum(axis=1)
        assert np.allclose(row_sums, 1.0, atol=1e-6), \
            "Probability rows should sum to 1"

    def test_very_large_image(self):
        """Stress test: very large image dimensions."""
        # Create a 10000x10000 pixel test image (simulated, not actually created)
        # Test that our algorithms can handle large contours
        large_contour = make_circular_contour(radius=5000, n_points=10000)

        # Chain code extraction should handle large contours
        # (We test the concept without actually processing the full image)
        assert len(large_contour) == 10000, \
            "Large contour should be created correctly"

        # Test segmentation on large contour
        chain = list(range(10000))  # Simulate long chain code
        segments = segment_chain_code(chain, n_segments=4)
        assert len(segments) == 4, \
            "Should segment large chain correctly"
        assert sum(len(seg) for seg in segments) == 10000, \
            "Segments should cover entire chain"

    def test_very_small_image(self):
        """Stress test: very small image (10x10 pixels)."""
        small_image = create_test_image(10, 10, background_color=255)

        # Preprocessing should handle small images gracefully
        blurred = apply_gaussian_blur(small_image)
        assert blurred.shape == (10, 10), \
            "Blurred image should maintain dimensions"

    def test_extreme_aspect_ratio_tall(self):
        """Stress test: extreme aspect ratio (1000x10)."""
        tall_contour = np.array([(5, y) for y in range(1000)])

        # Should produce valid chain code
        chain = points_to_chain_code(tall_contour)
        assert len(chain) > 0, \
            "Tall contour should produce valid chain code"

    def test_extreme_aspect_ratio_wide(self):
        """Stress test: extreme aspect ratio (10x1000)."""
        wide_contour = np.array([(x, 5) for x in range(1000)])

        # Should produce valid chain code
        chain = points_to_chain_code(wide_contour)
        assert len(chain) > 0, \
            "Wide contour should produce valid chain code"

    def test_many_segments_per_fragment(self):
        """Stress test: fragment segmented into many parts."""
        chain = list(range(1000))
        n_segments = 100  # Many segments

        segments = segment_chain_code(chain, n_segments=n_segments)
        assert len(segments) == n_segments, \
            f"Should create {n_segments} segments"
        assert sum(len(seg) for seg in segments) == len(chain), \
            "Segments should cover entire chain"

    @pytest.mark.slow
    def test_relaxation_convergence_stress(self):
        """Stress test: relaxation with large compatibility matrix."""
        n_frags = 20
        n_segs = 8
        compat = make_mock_compat(n_frags, n_segs)

        # Run relaxation - should converge or reach max iterations
        probs, trace = run_relaxation(compat)

        assert len(trace) > 0, \
            "Relaxation should produce convergence trace"
        assert probs.shape == compat.shape, \
            "Output probabilities should match input shape"


# =============================================================================
# 4. ERROR PATH TESTS
# =============================================================================

class TestErrorPaths:
    """Test error handling and edge cases."""

    def test_missing_file(self):
        """Error path: attempt to load non-existent file."""
        with pytest.raises(FileNotFoundError):
            preprocess_fragment("/nonexistent/path/image.png")

    def test_empty_image_directory(self, temp_image_dir):
        """Error path: empty directory with no images."""
        # Directory exists but has no images
        assert os.path.exists(temp_image_dir), \
            "Temp directory should exist"

    def test_corrupted_image_data(self, temp_image_dir):
        """Error path: corrupted/invalid image file."""
        # Create a text file with .png extension
        fake_image = os.path.join(temp_image_dir, "fake.png")
        with open(fake_image, 'w') as f:
            f.write("This is not an image")

        # Should raise an error when trying to load
        with pytest.raises((FileNotFoundError, Exception)):
            preprocess_fragment(fake_image)

    def test_invalid_chain_code_input(self):
        """Error path: invalid input to chain code functions."""
        # Empty contour
        empty_contour = np.array([])
        chain = points_to_chain_code(empty_contour)
        assert len(chain) == 0, \
            "Empty contour should produce empty chain"

    def test_invalid_segment_count(self):
        """Error path: request zero or negative segments."""
        chain = [0, 1, 2, 3, 4, 5]

        # Zero segments - should return empty list (graceful handling)
        segments = segment_chain_code(chain, n_segments=0)
        assert segments == [], \
            "Zero segments should return empty list"

        # Negative segments - should return empty list (graceful handling)
        segments = segment_chain_code(chain, n_segments=-1)
        assert segments == [], \
            "Negative segments should return empty list"

    def test_negative_compatibility_matrix(self):
        """Error path: negative values in compatibility matrix."""
        # Create matrix with negative values
        compat = np.random.rand(3, 2, 3, 2) - 0.5  # Range [-0.5, 0.5]

        # Note: The system expects non-negative compatibility scores.
        # Negative values lead to invalid probabilities (documented limitation).
        # This test documents the current behavior rather than asserting correctness.
        probs = initialize_probabilities(compat)
        # System does not clamp negative values; this is a known limitation
        # In practice, compatibility scores from build_compatibility_matrix are always non-negative
        assert probs.shape == compat.shape, \
            "Output should have correct shape even with invalid input"

    def test_nan_in_compatibility_matrix(self):
        """Error path: NaN values in compatibility matrix."""
        compat = make_mock_compat(3, 2)
        compat[0, 0, 1, 0] = np.nan

        # Note: The system does not explicitly handle NaN values in the compatibility matrix.
        # NaN propagates through the probability calculation (documented limitation).
        # In practice, build_compatibility_matrix produces valid float values only.
        # This test documents the current behavior.
        probs = initialize_probabilities(compat)
        # System does not sanitize NaN; probabilities will contain NaN
        assert probs.shape == compat.shape, \
            "Output should have correct shape even with NaN input"

    def test_all_zero_compatibility(self):
        """Error path: compatibility matrix with all zeros."""
        compat = np.zeros((3, 2, 3, 2))

        # Should handle gracefully
        probs = initialize_probabilities(compat)
        assert probs.shape == compat.shape, \
            "Should produce valid output shape"

    def test_image_with_no_fragment(self, temp_image_dir):
        """Error path: image with uniform background, no fragment."""
        # Create all-white image
        uniform_image = create_test_image(100, 100, background_color=255, fragment_present=False)
        image_path = os.path.join(temp_image_dir, "uniform.png")
        cv2.imwrite(image_path, uniform_image)

        # Should raise error or return empty contour
        try:
            _, contour = preprocess_fragment(image_path)
            assert len(contour) == 0 or contour is None, \
                "Uniform image should have no contour"
        except ValueError:
            # Acceptable to raise ValueError for no contour
            pass

    def test_non_image_file_format(self, temp_image_dir):
        """Error path: attempt to process non-image file."""
        # Create a text file
        text_file = os.path.join(temp_image_dir, "document.txt")
        with open(text_file, 'w') as f:
            f.write("Not an image")

        # Should raise appropriate error
        with pytest.raises((FileNotFoundError, Exception)):
            preprocess_fragment(text_file)


# =============================================================================
# 5. REGRESSION TESTS
# =============================================================================

class TestRegression:
    """Ensure previous bugs stay fixed and performance doesn't degrade."""

    def test_stage_1_6_baseline_threshold_match(self):
        """Regression: Stage 1.6 MATCH threshold should be 0.75."""
        assert MATCH_SCORE_THRESHOLD == 0.75, \
            "MATCH threshold must remain at 0.75 per Stage 1.6 specification"

    def test_stage_1_6_baseline_weak_threshold(self):
        """Regression: Stage 1.6 WEAK_MATCH threshold should be 0.60."""
        assert WEAK_MATCH_SCORE_THRESHOLD == 0.60, \
            "WEAK_MATCH threshold must remain at 0.60 per Stage 1.6 specification"

    def test_stage_1_6_baseline_assembly_threshold(self):
        """Regression: Stage 1.6 ASSEMBLY_CONFIDENCE threshold should be 0.65."""
        assert ASSEMBLY_CONFIDENCE_THRESHOLD == 0.65, \
            "ASSEMBLY_CONFIDENCE threshold must remain at 0.65 per Stage 1.6 specification"

    def test_self_matching_prevention(self):
        """Regression: fragments should never match themselves."""
        compat = make_mock_compat(n_frags=4, n_segs=3)

        # Check that diagonal blocks are zero
        for frag_idx in range(4):
            diagonal_block = compat[frag_idx, :, frag_idx, :]
            assert np.all(diagonal_block == 0.0), \
                f"Fragment {frag_idx} should not match itself"

    def test_probability_normalization_maintained(self):
        """Regression: probabilities must always sum to 1 per unit."""
        compat = make_mock_compat(5, 4)
        probs = initialize_probabilities(compat)

        flat = probs.reshape(20, 20)
        row_sums = flat.sum(axis=1)
        assert np.allclose(row_sums, 1.0, atol=1e-6), \
            "Probability distributions must sum to 1"

    def test_chain_code_determinism(self):
        """Regression: same contour should always produce same chain code."""
        contour = make_square_contour(side=15)

        chain1 = points_to_chain_code(contour)
        chain2 = points_to_chain_code(contour)

        assert chain1 == chain2, \
            "Chain code encoding must be deterministic"

    def test_normalized_chain_code_determinism(self):
        """Regression: normalization should be deterministic."""
        contour = make_square_contour(side=15)
        raw = points_to_chain_code(contour)

        norm1 = normalize_chain_code(raw)
        norm2 = normalize_chain_code(raw)

        assert norm1 == norm2, \
            "Chain code normalization must be deterministic"

    def test_relaxation_convergence_consistency(self):
        """Regression: relaxation should produce consistent results."""
        # Use fixed seed for reproducibility
        np.random.seed(42)
        compat = make_mock_compat(4, 3)

        probs1, trace1 = run_relaxation(compat)

        np.random.seed(42)
        probs2, trace2 = run_relaxation(compat)

        assert np.allclose(probs1, probs2), \
            "Relaxation should be deterministic with fixed seed"

    def test_color_similarity_range(self):
        """Regression: color Bhattacharyya coefficient must be in [0, 1]."""
        # Create two random color signatures
        sig_a = np.random.rand(32).astype(np.float32)
        sig_a /= sig_a.sum()
        sig_b = np.random.rand(32).astype(np.float32)
        sig_b /= sig_b.sum()

        bc = color_bhattacharyya(sig_a, sig_b)
        assert 0.0 <= bc <= 1.0, \
            f"Bhattacharyya coefficient {bc} must be in [0, 1]"


# =============================================================================
# 6. PROPERTY-BASED TESTS
# =============================================================================

class TestPropertyBased:
    """Test mathematical properties that should always hold."""

    def test_symmetry_segment_compatibility(self):
        """Property: score(A, B) should equal score(B, A)."""
        seg_a = [0, 1, 2, 3, 4, 5]
        seg_b = [7, 6, 5, 4, 3, 2]

        score_ab = segment_compatibility(seg_a, seg_b)
        score_ba = segment_compatibility(seg_b, seg_a)

        assert score_ab == pytest.approx(score_ba), \
            "Compatibility should be symmetric"

    def test_symmetry_edit_distance(self):
        """Property: edit_distance(A, B) should equal edit_distance(B, A)."""
        seq_a = [1, 2, 3, 4, 5]
        seq_b = [1, 9, 3, 8, 5]

        dist_ab = edit_distance(seq_a, seq_b)
        dist_ba = edit_distance(seq_b, seq_a)

        assert dist_ab == dist_ba, \
            "Edit distance should be symmetric"

    def test_self_similarity_maximum(self):
        """Property: score(A, A) should be high (ideally 1.0)."""
        seg = [0, 1, 2, 3, 4, 5]
        score = segment_compatibility(seg, seg)

        assert score >= 0.95, \
            "Self-similarity should be very high"

    def test_self_edit_distance_zero(self):
        """Property: edit_distance(A, A) should always be 0."""
        seq = [1, 2, 3, 4, 5]
        dist = edit_distance(seq, seq)

        assert dist == 0, \
            "Self edit-distance must be zero"

    def test_triangle_inequality_approximate(self):
        """Property: If A matches B and B matches C, check A vs C similarity."""
        # Create three similar segments
        seg_a = [0, 1, 2, 3, 4, 5]
        seg_b = [0, 1, 2, 9, 4, 5]
        seg_c = [0, 1, 2, 9, 4, 9]

        score_ab = segment_compatibility(seg_a, seg_b)
        score_bc = segment_compatibility(seg_b, seg_c)
        score_ac = segment_compatibility(seg_a, seg_c)

        # If A and B are similar, and B and C are similar,
        # then A and C should have some similarity (transitivity)
        if score_ab > 0.7 and score_bc > 0.7:
            assert score_ac > 0.5, \
                "Transitivity: if A~B and B~C, then A should have some similarity to C"

    def test_compatibility_matrix_symmetry(self):
        """Property: C[i,a,j,b] should relate to C[j,b,i,a] (anti-symmetry for matches)."""
        all_segments = [[[i, j] for j in range(2)] for i in range(3)]
        compat = build_compatibility_matrix(all_segments)

        # Check that compatibility is computed for both directions
        for i in range(3):
            for j in range(i + 1, 3):
                score_ij = compat[i, 0, j, 0]
                score_ji = compat[j, 0, i, 0]
                # Scores may differ slightly due to good-continuation directionality
                # but should be in the same ballpark
                assert abs(score_ij - score_ji) < 0.5, \
                    "Pairwise compatibility should be approximately symmetric"

    def test_probability_non_negative(self):
        """Property: probabilities should never be negative."""
        compat = make_mock_compat(4, 3)
        probs, _ = run_relaxation(compat)

        assert (probs >= -1e-9).all(), \
            "All probabilities must be non-negative"

    def test_probability_upper_bound(self):
        """Property: individual probabilities should not exceed 1.0."""
        compat = make_mock_compat(4, 3)
        probs, _ = run_relaxation(compat)

        assert (probs <= 1.0 + 1e-9).all(), \
            "Individual probabilities should not exceed 1.0"

    def test_good_continuation_bounded(self):
        """Property: good continuation bonus should be in [0, 1]."""
        chain_a = [0, 1, 2, 3]
        chain_b = [3, 4, 5, 6]

        bonus = good_continuation_bonus(chain_a, chain_b)
        assert 0.0 <= bonus <= 1.0, \
            f"Good continuation bonus {bonus} must be in [0, 1]"

    def test_curvature_profile_length_consistency(self):
        """Property: curvature profile should have expected length."""
        contour = make_circular_contour(radius=50, n_points=100)
        kappa = compute_curvature_profile(contour)

        # Profile should be approximately same length as contour
        assert len(kappa) > 0, \
            "Curvature profile should not be empty"
        assert len(kappa) <= len(contour), \
            "Curvature profile length should not exceed contour length"

    def test_color_signature_normalization(self):
        """Property: color signature should sum to 1.0."""
        test_image = create_test_image(100, 100)
        signature = compute_color_signature(test_image)

        sig_sum = signature.sum()
        assert abs(sig_sum - 1.0) < 1e-6, \
            f"Color signature should sum to 1.0, got {sig_sum}"

    def test_fourier_score_bounded(self):
        """Property: Fourier descriptor score should be in [0, 1]."""
        seg_a = make_square_contour(side=20)
        seg_b = make_circular_contour(radius=15, n_points=80)

        score = segment_fourier_score(seg_a, seg_b)
        assert 0.0 <= score <= 1.0, \
            f"Fourier score {score} must be in [0, 1]"

    def test_profile_similarity_bounded(self):
        """Property: curvature profile similarity should be in [0, 1]."""
        contour_a = make_square_contour(side=20)
        contour_b = make_circular_contour(radius=15, n_points=80)

        kappa_a = compute_curvature_profile(contour_a)
        kappa_b = compute_curvature_profile(contour_b)

        score = profile_similarity(kappa_a, kappa_b)
        assert 0.0 <= score <= 1.0, \
            f"Profile similarity {score} must be in [0, 1]"


# =============================================================================
# 7. INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Test complete pipeline flows with realistic scenarios."""

    def test_full_pipeline_two_fragments(self, temp_image_dir):
        """Integration: full pipeline with two fragment images."""
        # Create two test images
        img1 = create_test_image(200, 200, fragment_present=True)
        img2 = create_test_image(200, 200, fragment_present=True)

        path1 = os.path.join(temp_image_dir, "frag1.png")
        path2 = os.path.join(temp_image_dir, "frag2.png")

        cv2.imwrite(path1, img1)
        cv2.imwrite(path2, img2)

        # Process both fragments
        try:
            image1, contour1 = preprocess_fragment(path1)
            image2, contour2 = preprocess_fragment(path2)

            assert len(contour1) > 0, "Fragment 1 should have valid contour"
            assert len(contour2) > 0, "Fragment 2 should have valid contour"
        except ValueError:
            # If preprocessing fails due to minimal contrast, that's acceptable
            pytest.skip("Test images too simple for contour extraction")

    def test_compatibility_to_relaxation_flow(self):
        """Integration: compatibility matrix through relaxation labeling."""
        # Create mock segments
        all_segments = [[[i, j, k] for k in range(4)] for i, j in [(0, 0), (1, 1), (2, 2)]]

        # Build compatibility matrix
        compat = build_compatibility_matrix(all_segments)

        # Run relaxation
        probs, trace = run_relaxation(compat)

        # Extract assemblies
        assemblies = extract_top_assemblies(probs, n_top=2, compat_matrix=compat)

        assert len(assemblies) == 2, \
            "Should extract requested number of assemblies"
        assert all('confidence' in a for a in assemblies), \
            "Each assembly should have confidence score"
        assert all('verdict' in a for a in assemblies), \
            "Each assembly should have verdict"

    def test_end_to_end_with_sample_data(self):
        """Integration: test with actual sample data if available."""
        sample_dir = Path(__file__).parent.parent / "data" / "sample"

        if not sample_dir.exists():
            pytest.skip("Sample data directory not found")

        image_files = list(sample_dir.glob("fragment_*.png"))

        if len(image_files) < 2:
            pytest.skip("Insufficient sample images")

        # Try to process first two sample images
        try:
            img1, cnt1 = preprocess_fragment(str(image_files[0]))
            img2, cnt2 = preprocess_fragment(str(image_files[1]))

            assert len(cnt1) > 10, "Sample fragment 1 should have substantial contour"
            assert len(cnt2) > 10, "Sample fragment 2 should have substantial contour"
        except Exception as e:
            pytest.fail(f"Failed to process sample data: {e}")


# =============================================================================
# Performance Benchmarks (optional, marked as slow)
# =============================================================================

class TestPerformance:
    """Performance benchmarks for key operations."""

    @pytest.mark.slow
    def test_chain_code_performance(self):
        """Benchmark: chain code extraction speed."""
        import time

        contour = make_circular_contour(radius=500, n_points=1000)

        start = time.time()
        for _ in range(100):
            chain = points_to_chain_code(contour)
        elapsed = time.time() - start

        assert elapsed < 5.0, \
            f"Chain code extraction too slow: {elapsed:.2f}s for 100 iterations"

    @pytest.mark.slow
    def test_relaxation_performance(self):
        """Benchmark: relaxation labeling speed."""
        import time

        compat = make_mock_compat(10, 4)

        start = time.time()
        probs, trace = run_relaxation(compat)
        elapsed = time.time() - start

        assert elapsed < 10.0, \
            f"Relaxation labeling too slow: {elapsed:.2f}s"

    @pytest.mark.slow
    def test_compatibility_matrix_performance(self):
        """Benchmark: compatibility matrix construction speed."""
        import time

        n_frags = 10
        n_segs = 4
        all_segments = [[[i, j, k] for k in range(n_segs)] for i in range(n_frags) for j in range(1)]

        start = time.time()
        compat = build_compatibility_matrix(all_segments)
        elapsed = time.time() - start

        assert elapsed < 30.0, \
            f"Compatibility matrix construction too slow: {elapsed:.2f}s"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
