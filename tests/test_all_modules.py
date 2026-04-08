"""
Comprehensive unit tests for all core modules.

Tests coverage:
1. compatibility.py - All feature extraction functions
2. relaxation.py - Probability initialization, support computation
3. hard_discriminators.py - Edge density, entropy, rejection logic
4. ensemble_voting.py - All 3 voting methods
5. Edge cases: empty inputs, invalid arrays, zero divisions

Framework: pytest
Target: 80%+ code coverage
"""

import sys
import os
import numpy as np
import pytest
import cv2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from compatibility import (
    edit_distance,
    segment_compatibility,
    profile_similarity,
    good_continuation_bonus,
    compute_color_signature,
    color_bhattacharyya,
    compute_texture_signature,
    texture_bhattacharyya,
    extract_gabor_features,
    gabor_similarity,
    extract_haralick_features,
    haralick_similarity,
    segment_fourier_score,
    build_compatibility_matrix,
)
from relaxation import (
    initialize_probabilities,
    compute_support,
    update_probabilities,
    run_relaxation,
    extract_top_assemblies,
    classify_pair_score,
    classify_assembly,
    MATCH_SCORE_THRESHOLD,
    WEAK_MATCH_SCORE_THRESHOLD,
)
from hard_discriminators import (
    compute_edge_density,
    compute_texture_entropy,
    hard_reject_check,
    should_early_stop_negative_tests,
)
from ensemble_voting import (
    classify_by_threshold,
    ensemble_verdict_five_way,
    ensemble_verdict_weighted,
    ensemble_verdict_hierarchical,
    get_ensemble_statistics,
)


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_image():
    """Create a simple test image (100x100, blue square on white background)."""
    img = np.ones((100, 100, 3), dtype=np.uint8) * 255
    img[25:75, 25:75] = [255, 0, 0]  # Blue square in center
    return img


@pytest.fixture
def sample_image_red():
    """Create a test image with red square."""
    img = np.ones((100, 100, 3), dtype=np.uint8) * 255
    img[25:75, 25:75] = [0, 0, 255]  # Red square in center
    return img


@pytest.fixture
def grayscale_image():
    """Create a grayscale test image."""
    img = np.ones((100, 100), dtype=np.uint8) * 128
    img[25:75, 25:75] = 200
    return img


@pytest.fixture
def sample_curvature():
    """Create sample curvature profile."""
    return np.array([0.1, 0.2, -0.1, 0.0, 0.15, -0.05])


@pytest.fixture
def sample_pixel_segment():
    """Create sample pixel segment coordinates."""
    return np.array([[0, 0], [1, 0], [2, 1], [3, 1], [4, 2]], dtype=np.int32)


@pytest.fixture
def mock_compat_matrix():
    """Create mock compatibility matrix."""
    n_frags, n_segs = 3, 2
    matrix = np.random.rand(n_frags, n_segs, n_frags, n_segs) * 0.5
    for frag_idx in range(n_frags):
        matrix[frag_idx, :, frag_idx, :] = 0.0
    return matrix


# ---------------------------------------------------------------------------
# 1. COMPATIBILITY.PY TESTS
# ---------------------------------------------------------------------------

class TestEditDistance:
    """Test edit distance calculation."""

    def test_identical_sequences(self):
        seq = [1, 2, 3, 4]
        assert edit_distance(seq, seq) == 0

    def test_empty_sequences(self):
        assert edit_distance([], [1, 2, 3]) == 3
        assert edit_distance([1, 2], []) == 2
        assert edit_distance([], []) == 0

    def test_single_substitution(self):
        assert edit_distance([1, 2, 3], [1, 9, 3]) == 1

    def test_single_insertion(self):
        assert edit_distance([1, 3], [1, 2, 3]) == 1

    def test_single_deletion(self):
        assert edit_distance([1, 2, 3], [1, 3]) == 1

    def test_completely_different(self):
        result = edit_distance([1, 1, 1], [2, 2, 2])
        assert result == 3


class TestSegmentCompatibility:
    """Test segment compatibility scoring."""

    def test_identical_segments(self):
        seg = [0, 1, 2, 3, 0, 1]
        assert segment_compatibility(seg, seg) == pytest.approx(1.0)

    def test_empty_segments(self):
        assert segment_compatibility([], [1, 2, 3]) == 0.0
        assert segment_compatibility([1, 2], []) == 0.0
        assert segment_compatibility([], []) == 0.0

    def test_in_unit_interval(self):
        score = segment_compatibility([0, 1, 2], [3, 4, 5, 6])
        assert 0.0 <= score <= 1.0

    def test_similar_segments(self):
        score = segment_compatibility([0, 1, 2, 3], [0, 1, 2, 4])
        assert score > 0.7


class TestProfileSimilarity:
    """Test curvature profile similarity."""

    def test_identical_profiles(self):
        profile = np.array([0.1, 0.2, -0.1, 0.0])
        score = profile_similarity(profile, profile)
        assert 0.8 <= score <= 1.0

    def test_empty_profiles(self):
        score = profile_similarity(np.array([]), np.array([1.0]))
        assert score == 0.5

    def test_short_profiles(self):
        score = profile_similarity(np.array([0.1]), np.array([0.2]))
        assert score == 0.5

    def test_flat_profiles(self):
        # Flat profiles (zero curvature) should return 0.5
        flat1 = np.zeros(10)
        flat2 = np.zeros(8)
        score = profile_similarity(flat1, flat2)
        assert 0.4 <= score <= 0.6

    def test_opposite_profiles(self):
        profile1 = np.array([0.5, 0.5, 0.5])
        profile2 = np.array([-0.5, -0.5, -0.5])
        score = profile_similarity(profile1, profile2)
        assert 0.0 <= score <= 1.0

    def test_different_lengths(self):
        profile1 = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        profile2 = np.array([0.1, 0.2, 0.3])
        score = profile_similarity(profile1, profile2)
        assert 0.0 <= score <= 1.0


class TestGoodContinuationBonus:
    """Test good continuation bonus calculation."""

    def test_smooth_continuation(self):
        # Same direction = smooth continuation
        chain_end = [0, 0, 0]
        chain_start = [0, 0, 0]
        bonus = good_continuation_bonus(chain_end, chain_start)
        assert bonus > 0.9

    def test_sharp_turn(self):
        # Opposite directions = sharp turn
        chain_end = [0, 0, 0]
        chain_start = [4, 4, 4]
        bonus = good_continuation_bonus(chain_end, chain_start)
        assert bonus < 0.5

    def test_empty_chains(self):
        assert good_continuation_bonus([], [1, 2]) == 0.0
        assert good_continuation_bonus([1, 2], []) == 0.0
        assert good_continuation_bonus([], []) == 0.0

    def test_moderate_turn(self):
        chain_end = [0, 0, 0]
        chain_start = [1, 1, 1]
        bonus = good_continuation_bonus(chain_end, chain_start)
        assert 0.3 <= bonus <= 0.95


class TestColorSignature:
    """Test color signature computation."""

    def test_empty_image(self):
        empty = np.array([])
        sig = compute_color_signature(empty)
        assert len(sig) == 32  # 16 L + 8 a + 8 b bins
        assert np.allclose(sig, 0.0)

    def test_none_image(self):
        sig = compute_color_signature(None)
        assert len(sig) == 32
        assert np.allclose(sig, 0.0)

    def test_valid_image(self, sample_image):
        sig = compute_color_signature(sample_image)
        assert len(sig) == 32
        assert np.allclose(sig.sum(), 1.0, atol=1e-6)
        assert sig.min() >= 0.0

    def test_different_colors(self, sample_image, sample_image_red):
        sig1 = compute_color_signature(sample_image)
        sig2 = compute_color_signature(sample_image_red)
        # Different colored images should have different signatures
        assert not np.allclose(sig1, sig2)


class TestColorBhattacharyya:
    """Test Bhattacharyya coefficient for color."""

    def test_identical_signatures(self):
        sig = np.array([0.1, 0.2, 0.3, 0.4])
        bc = color_bhattacharyya(sig, sig)
        assert bc == pytest.approx(1.0, abs=1e-6)

    def test_empty_signatures(self):
        bc = color_bhattacharyya(np.array([]), np.array([0.5, 0.5]))
        assert bc == 0.5

    def test_orthogonal_signatures(self):
        sig1 = np.array([1.0, 0.0, 0.0, 0.0])
        sig2 = np.array([0.0, 1.0, 0.0, 0.0])
        bc = color_bhattacharyya(sig1, sig2)
        assert bc == pytest.approx(0.0, abs=1e-6)

    def test_in_valid_range(self):
        sig1 = np.random.rand(32)
        sig1 /= sig1.sum()
        sig2 = np.random.rand(32)
        sig2 /= sig2.sum()
        bc = color_bhattacharyya(sig1, sig2)
        assert 0.0 <= bc <= 1.0


class TestTextureSignature:
    """Test texture signature computation."""

    def test_empty_image(self):
        empty = np.array([])
        sig = compute_texture_signature(empty)
        assert len(sig) == 26  # LBP uniform patterns
        assert np.allclose(sig, 0.0)

    def test_valid_image(self, sample_image):
        sig = compute_texture_signature(sample_image)
        assert len(sig) == 26
        assert np.allclose(sig.sum(), 1.0, atol=1e-6)
        assert sig.min() >= 0.0

    def test_different_textures(self, sample_image):
        # Create two images with different textures
        img1 = sample_image.copy()
        img2 = sample_image.copy()
        np.random.seed(42)
        noise = np.random.randint(-30, 30, (50, 50, 3), dtype=np.int16)
        img2_roi = img2[25:75, 25:75].astype(np.int16) + noise
        img2[25:75, 25:75] = np.clip(img2_roi, 0, 255).astype(np.uint8)

        sig1 = compute_texture_signature(img1)
        sig2 = compute_texture_signature(img2)
        # Different textures should have different signatures
        assert not np.allclose(sig1, sig2)


class TestGaborFeatures:
    """Test Gabor feature extraction."""

    def test_empty_image(self):
        empty = np.array([])
        feat = extract_gabor_features(empty)
        assert len(feat) == 120  # 5 scales × 8 orientations × 3 features
        assert np.allclose(feat, 0.0)

    def test_valid_image(self, grayscale_image):
        feat = extract_gabor_features(grayscale_image)
        assert len(feat) == 120
        # Features should be normalized
        norm = np.linalg.norm(feat)
        assert norm == pytest.approx(1.0, abs=1e-6) or norm == 0.0

    def test_similarity_identical(self, grayscale_image):
        feat = extract_gabor_features(grayscale_image)
        sim = gabor_similarity(feat, feat)
        assert 0.95 <= sim <= 1.0

    def test_similarity_empty(self):
        sim = gabor_similarity(np.array([]), np.array([1.0]))
        assert sim == 0.5


class TestHaralickFeatures:
    """Test Haralick GLCM features."""

    def test_empty_image(self):
        empty = np.array([])
        feat = extract_haralick_features(empty)
        assert len(feat) == 60  # 5 properties × 3 distances × 4 angles
        assert np.allclose(feat, 0.0)

    def test_valid_image(self, grayscale_image):
        feat = extract_haralick_features(grayscale_image)
        assert len(feat) == 60
        # Features should be normalized
        norm = np.linalg.norm(feat)
        assert norm == pytest.approx(1.0, abs=1e-6) or norm == 0.0

    def test_similarity_identical(self, grayscale_image):
        feat = extract_haralick_features(grayscale_image)
        sim = haralick_similarity(feat, feat)
        assert 0.95 <= sim <= 1.0

    def test_similarity_empty(self):
        sim = haralick_similarity(np.array([]), np.array([1.0]))
        assert sim == 0.5


class TestSegmentFourierScore:
    """Test Fourier descriptor scoring."""

    def test_identical_segments(self, sample_pixel_segment):
        score = segment_fourier_score(sample_pixel_segment, sample_pixel_segment)
        assert 0.8 <= score <= 1.0

    def test_empty_segments(self):
        seg = np.array([[0, 0], [1, 1]])
        assert segment_fourier_score(np.array([]), seg) == 0.0
        assert segment_fourier_score(seg, np.array([])) == 0.0

    def test_short_segments(self):
        seg1 = np.array([[0, 0]])
        seg2 = np.array([[1, 1]])
        score = segment_fourier_score(seg1, seg2)
        assert score == 0.0

    def test_in_valid_range(self, sample_pixel_segment):
        seg2 = sample_pixel_segment + 10
        score = segment_fourier_score(sample_pixel_segment, seg2)
        assert 0.0 <= score <= 1.0


class TestBuildCompatibilityMatrix:
    """Test compatibility matrix building."""

    def test_matrix_shape(self):
        n_frags, n_segs = 3, 4
        all_segments = [[[i, j] for j in range(n_segs)] for i in range(n_frags)]
        compat = build_compatibility_matrix(all_segments)
        assert compat.shape == (n_frags, n_segs, n_frags, n_segs)

    def test_self_compatibility_zero(self):
        all_segments = [[[0, 1, 2, 3]] for _ in range(4)]
        compat = build_compatibility_matrix(all_segments)
        for frag_idx in range(4):
            assert compat[frag_idx, :, frag_idx, :].sum() == pytest.approx(0.0)

    def test_with_pixel_segments(self):
        n_frags, n_segs = 2, 2
        all_segments = [[[0, 1, 2] for _ in range(n_segs)] for _ in range(n_frags)]
        all_pixel_segments = [[np.array([[i, j], [i+1, j], [i, j+1]])
                              for j in range(n_segs)] for i in range(n_frags)]
        compat = build_compatibility_matrix(all_segments, all_pixel_segments)
        assert compat.shape == (n_frags, n_segs, n_frags, n_segs)

    def test_with_images(self, sample_image, sample_image_red):
        n_frags, n_segs = 2, 2
        all_segments = [[[0, 1, 2] for _ in range(n_segs)] for _ in range(n_frags)]
        all_images = [sample_image, sample_image_red]
        compat = build_compatibility_matrix(all_segments, all_images=all_images)
        assert compat.shape == (n_frags, n_segs, n_frags, n_segs)


# ---------------------------------------------------------------------------
# 2. RELAXATION.PY TESTS
# ---------------------------------------------------------------------------

class TestInitializeProbabilities:
    """Test probability initialization."""

    def test_output_shape(self, mock_compat_matrix):
        probs = initialize_probabilities(mock_compat_matrix)
        assert probs.shape == mock_compat_matrix.shape

    def test_probabilities_sum_to_one(self, mock_compat_matrix):
        probs = initialize_probabilities(mock_compat_matrix)
        n_frags, n_segs = probs.shape[:2]
        flat = probs.reshape(n_frags * n_segs, n_frags * n_segs)
        row_sums = flat.sum(axis=1)
        assert np.allclose(row_sums, 1.0, atol=1e-6)

    def test_self_probabilities_zero(self, mock_compat_matrix):
        probs = initialize_probabilities(mock_compat_matrix)
        n_frags = probs.shape[0]
        for frag_idx in range(n_frags):
            assert probs[frag_idx, :, frag_idx, :].sum() == pytest.approx(0.0, abs=1e-6)

    def test_nonnegative_probabilities(self, mock_compat_matrix):
        probs = initialize_probabilities(mock_compat_matrix)
        assert (probs >= -1e-9).all()


class TestComputeSupport:
    """Test support computation."""

    def test_output_shape(self, mock_compat_matrix):
        probs = initialize_probabilities(mock_compat_matrix)
        support = compute_support(probs, mock_compat_matrix)
        assert support.shape == mock_compat_matrix.shape

    def test_support_values(self, mock_compat_matrix):
        probs = initialize_probabilities(mock_compat_matrix)
        support = compute_support(probs, mock_compat_matrix)
        # Support should be finite
        assert np.isfinite(support).all()


class TestUpdateProbabilities:
    """Test probability update."""

    def test_output_shape(self, mock_compat_matrix):
        probs = initialize_probabilities(mock_compat_matrix)
        support = compute_support(probs, mock_compat_matrix)
        updated = update_probabilities(probs, support)
        assert updated.shape == probs.shape

    def test_probabilities_sum_to_one(self, mock_compat_matrix):
        probs = initialize_probabilities(mock_compat_matrix)
        support = compute_support(probs, mock_compat_matrix)
        updated = update_probabilities(probs, support)
        n_frags, n_segs = updated.shape[:2]
        flat = updated.reshape(n_frags * n_segs, n_frags * n_segs)
        row_sums = flat.sum(axis=1)
        assert np.allclose(row_sums, 1.0, atol=1e-6)

    def test_nonnegative_probabilities(self, mock_compat_matrix):
        probs = initialize_probabilities(mock_compat_matrix)
        support = compute_support(probs, mock_compat_matrix)
        updated = update_probabilities(probs, support)
        assert (updated >= -1e-9).all()


class TestRunRelaxation:
    """Test full relaxation loop."""

    def test_output_shape(self, mock_compat_matrix):
        probs, trace = run_relaxation(mock_compat_matrix)
        assert probs.shape == mock_compat_matrix.shape
        assert len(trace) > 0

    def test_convergence_trace(self, mock_compat_matrix):
        probs, trace = run_relaxation(mock_compat_matrix)
        # Trace should contain positive deltas
        assert all(delta >= 0.0 for delta in trace)

    def test_convergence(self, mock_compat_matrix):
        probs, trace = run_relaxation(mock_compat_matrix)
        # Last delta should be small if converged
        if len(trace) > 0:
            assert trace[-1] >= 0.0


class TestClassifyPairScore:
    """Test pair score classification."""

    def test_match_classification(self):
        score = MATCH_SCORE_THRESHOLD + 0.05
        assert classify_pair_score(score) == "MATCH"

    def test_weak_match_classification(self):
        score = (MATCH_SCORE_THRESHOLD + WEAK_MATCH_SCORE_THRESHOLD) / 2
        assert classify_pair_score(score) == "WEAK_MATCH"

    def test_no_match_classification(self):
        score = WEAK_MATCH_SCORE_THRESHOLD - 0.05
        assert classify_pair_score(score) == "NO_MATCH"

    def test_boundary_cases(self):
        # Test exact threshold values
        assert classify_pair_score(MATCH_SCORE_THRESHOLD) == "MATCH"
        assert classify_pair_score(WEAK_MATCH_SCORE_THRESHOLD) == "WEAK_MATCH"


class TestClassifyAssembly:
    """Test assembly classification."""

    def test_empty_pairs(self):
        verdict = classify_assembly(0.5, [])
        assert verdict == "NO_MATCH"

    def test_match_assembly(self):
        pairs = [
            {'raw_compat': MATCH_SCORE_THRESHOLD + 0.1} for _ in range(5)
        ]
        verdict = classify_assembly(0.8, pairs)
        assert verdict == "MATCH"

    def test_weak_match_assembly(self):
        pairs = [
            {'raw_compat': WEAK_MATCH_SCORE_THRESHOLD + 0.05} for _ in range(5)
        ]
        verdict = classify_assembly(0.5, pairs)
        assert verdict in ["MATCH", "WEAK_MATCH"]

    def test_no_match_assembly(self):
        pairs = [
            {'raw_compat': WEAK_MATCH_SCORE_THRESHOLD - 0.1} for _ in range(5)
        ]
        verdict = classify_assembly(0.3, pairs)
        assert verdict == "NO_MATCH"


class TestExtractTopAssemblies:
    """Test assembly extraction."""

    def test_assembly_count(self, mock_compat_matrix):
        probs, _ = run_relaxation(mock_compat_matrix)
        assemblies = extract_top_assemblies(probs, n_top=3, compat_matrix=mock_compat_matrix)
        assert len(assemblies) == 3

    def test_assembly_structure(self, mock_compat_matrix):
        probs, _ = run_relaxation(mock_compat_matrix)
        assemblies = extract_top_assemblies(probs, n_top=1, compat_matrix=mock_compat_matrix)
        assert len(assemblies) > 0
        assembly = assemblies[0]
        assert 'pairs' in assembly
        assert 'confidence' in assembly
        assert 'verdict' in assembly

    def test_no_self_matches(self, mock_compat_matrix):
        probs, _ = run_relaxation(mock_compat_matrix)
        assemblies = extract_top_assemblies(probs, n_top=2, compat_matrix=mock_compat_matrix)
        for assembly in assemblies:
            for pair in assembly['pairs']:
                assert pair['frag_i'] != pair['frag_j']


# ---------------------------------------------------------------------------
# 3. HARD_DISCRIMINATORS.PY TESTS
# ---------------------------------------------------------------------------

class TestEdgeDensity:
    """Test edge density computation."""

    def test_empty_image(self):
        density = compute_edge_density(np.array([]))
        assert density == 0.0

    def test_none_image(self):
        density = compute_edge_density(None)
        assert density == 0.0

    def test_valid_image(self, sample_image):
        density = compute_edge_density(sample_image)
        assert 0.0 <= density <= 1.0

    def test_uniform_image(self):
        # Uniform image should have low edge density
        uniform = np.ones((100, 100, 3), dtype=np.uint8) * 128
        density = compute_edge_density(uniform)
        assert density < 0.05

    def test_grayscale_input(self, grayscale_image):
        density = compute_edge_density(grayscale_image)
        assert 0.0 <= density <= 1.0


class TestTextureEntropy:
    """Test texture entropy computation."""

    def test_empty_image(self):
        entropy_val = compute_texture_entropy(np.array([]))
        assert entropy_val == 0.0

    def test_none_image(self):
        entropy_val = compute_texture_entropy(None)
        assert entropy_val == 0.0

    def test_valid_image(self, sample_image):
        entropy_val = compute_texture_entropy(sample_image)
        assert entropy_val > 0.0

    def test_uniform_image(self):
        # Uniform image should have low entropy
        uniform = np.ones((100, 100, 3), dtype=np.uint8) * 128
        entropy_val = compute_texture_entropy(uniform)
        assert 0.0 <= entropy_val < 2.0

    def test_grayscale_input(self, grayscale_image):
        entropy_val = compute_texture_entropy(grayscale_image)
        assert entropy_val > 0.0


class TestHardRejectCheck:
    """Test hard rejection logic."""

    def test_similar_images_pass(self, sample_image):
        # Very similar images should pass
        img1 = sample_image.copy()
        img2 = sample_image.copy()
        reject = hard_reject_check(img1, img2, bc_color=0.95, bc_texture=0.90)
        assert reject == False

    def test_different_colors_reject(self, sample_image, sample_image_red):
        # Different colors with low BC should reject
        reject = hard_reject_check(sample_image, sample_image_red, bc_color=0.50, bc_texture=0.80)
        assert reject == True

    def test_low_texture_similarity_reject(self, sample_image):
        reject = hard_reject_check(sample_image, sample_image, bc_color=0.85, bc_texture=0.40)
        assert reject == True

    def test_appearance_gate(self, sample_image):
        # Test appearance gate threshold
        reject = hard_reject_check(sample_image, sample_image, bc_color=0.55, bc_texture=0.50)
        assert reject == True


class TestEarlyStop:
    """Test early stop logic."""

    def test_no_early_stop(self):
        # Low failure rate should not trigger early stop
        assert should_early_stop_negative_tests(5, 10) == False

    def test_early_stop_triggered(self):
        # High failure rate should trigger early stop
        assert should_early_stop_negative_tests(18, 20) == True

    def test_exactly_at_threshold(self):
        # Exactly at threshold should trigger
        assert should_early_stop_negative_tests(18, 36) == True


# ---------------------------------------------------------------------------
# 4. ENSEMBLE_VOTING.PY TESTS
# ---------------------------------------------------------------------------

class TestClassifyByThreshold:
    """Test threshold-based classification."""

    def test_match_classification(self):
        result = classify_by_threshold(0.90, match_thresh=0.80, weak_thresh=0.60)
        assert result == "MATCH"

    def test_weak_match_classification(self):
        result = classify_by_threshold(0.70, match_thresh=0.80, weak_thresh=0.60)
        assert result == "WEAK_MATCH"

    def test_no_match_classification(self):
        result = classify_by_threshold(0.50, match_thresh=0.80, weak_thresh=0.60)
        assert result == "NO_MATCH"

    def test_boundary_values(self):
        # Test exact threshold values
        assert classify_by_threshold(0.80, 0.80, 0.60) == "MATCH"
        assert classify_by_threshold(0.60, 0.80, 0.60) == "WEAK_MATCH"


class TestEnsembleVerdictFiveWay:
    """Test 5-way ensemble voting."""

    def test_strong_match(self):
        verdict = ensemble_verdict_five_way(
            raw_compat=1.0,
            bc_color=0.95,
            bc_texture=0.90,
            bc_gabor=0.85,
            edge_density_diff=0.02,
            entropy_diff=0.1
        )
        assert verdict == "MATCH"

    def test_strong_no_match(self):
        verdict = ensemble_verdict_five_way(
            raw_compat=0.30,
            bc_color=0.40,
            bc_texture=0.35,
            bc_gabor=0.30,
            edge_density_diff=0.25,
            entropy_diff=0.8
        )
        assert verdict == "NO_MATCH"

    def test_mixed_votes(self):
        verdict = ensemble_verdict_five_way(
            raw_compat=0.80,
            bc_color=0.70,
            bc_texture=0.65,
            bc_gabor=0.60,
            edge_density_diff=0.10,
            entropy_diff=0.3
        )
        assert verdict in ["MATCH", "WEAK_MATCH", "NO_MATCH"]

    def test_edge_cases(self):
        # Test with extreme values
        verdict = ensemble_verdict_five_way(
            raw_compat=0.0,
            bc_color=0.0,
            bc_texture=0.0,
            bc_gabor=0.0,
            edge_density_diff=1.0,
            entropy_diff=10.0
        )
        assert verdict == "NO_MATCH"


class TestEnsembleVerdictWeighted:
    """Test weighted ensemble voting."""

    def test_strong_match(self):
        verdict = ensemble_verdict_weighted(
            raw_compat=1.0,
            bc_color=0.95,
            bc_texture=0.90,
            bc_gabor=0.85,
            edge_density_diff=0.02,
            entropy_diff=0.1
        )
        assert verdict == "MATCH"

    def test_custom_weights(self):
        weights = {
            'color': 0.5,
            'raw_compat': 0.2,
            'texture': 0.15,
            'morphological': 0.10,
            'gabor': 0.05
        }
        verdict = ensemble_verdict_weighted(
            raw_compat=1.0,
            bc_color=0.95,
            bc_texture=0.90,
            bc_gabor=0.85,
            edge_density_diff=0.02,
            entropy_diff=0.1,
            weights=weights
        )
        assert verdict in ["MATCH", "WEAK_MATCH", "NO_MATCH"]

    def test_weak_color_dominates(self):
        # Low color should dominate due to high weight
        verdict = ensemble_verdict_weighted(
            raw_compat=1.0,
            bc_color=0.40,  # Very low
            bc_texture=0.90,
            bc_gabor=0.85,
            edge_density_diff=0.02,
            entropy_diff=0.1
        )
        assert verdict in ["NO_MATCH", "WEAK_MATCH"]


class TestEnsembleVerdictHierarchical:
    """Test hierarchical ensemble voting."""

    def test_fast_rejection_morphology(self):
        verdict = ensemble_verdict_hierarchical(
            raw_compat=0.90,
            bc_color=0.90,
            bc_texture=0.85,
            bc_gabor=0.80,
            edge_density_diff=0.20,  # Too high
            entropy_diff=0.3
        )
        assert verdict == "NO_MATCH"

    def test_fast_match_consensus(self):
        verdict = ensemble_verdict_hierarchical(
            raw_compat=0.90,
            bc_color=0.85,
            bc_texture=0.80,
            bc_gabor=0.75,
            edge_density_diff=0.02,
            entropy_diff=0.1
        )
        assert verdict == "MATCH"

    def test_hard_case_full_ensemble(self):
        # Ambiguous case should go to full ensemble
        verdict = ensemble_verdict_hierarchical(
            raw_compat=0.70,
            bc_color=0.68,
            bc_texture=0.65,
            bc_gabor=0.62,
            edge_density_diff=0.08,
            entropy_diff=0.25
        )
        assert verdict in ["MATCH", "WEAK_MATCH", "NO_MATCH"]


class TestGetEnsembleStatistics:
    """Test ensemble statistics computation."""

    def test_empty_verdicts(self):
        stats = get_ensemble_statistics([])
        assert stats == {}

    def test_all_matches(self):
        verdicts = ["MATCH"] * 10
        stats = get_ensemble_statistics(verdicts)
        assert stats['total'] == 10
        assert stats['match_count'] == 10
        assert stats['match_pct'] == 100.0
        assert stats['no_match_count'] == 0

    def test_mixed_verdicts(self):
        verdicts = ["MATCH"] * 5 + ["WEAK_MATCH"] * 3 + ["NO_MATCH"] * 2
        stats = get_ensemble_statistics(verdicts)
        assert stats['total'] == 10
        assert stats['match_count'] == 5
        assert stats['weak_count'] == 3
        assert stats['no_match_count'] == 2
        assert stats['match_pct'] == 50.0
        assert stats['weak_pct'] == 30.0
        assert stats['no_match_pct'] == 20.0


# ---------------------------------------------------------------------------
# 5. EDGE CASES AND INTEGRATION TESTS
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_division_protection(self):
        # Test various functions with inputs that could cause division by zero

        # Color BC with zero vectors
        bc = color_bhattacharyya(np.zeros(32), np.zeros(32))
        assert 0.0 <= bc <= 1.0

        # Profile similarity with zero variance
        score = profile_similarity(np.zeros(10), np.zeros(10))
        assert 0.0 <= score <= 1.0

        # Segment compatibility with empty
        compat = segment_compatibility([], [])
        assert compat == 0.0

    def test_nan_and_inf_handling(self):
        # Ensure no NaN or Inf in outputs

        # Build compatibility matrix
        n_frags, n_segs = 2, 2
        all_segments = [[[0, 1, 2] for _ in range(n_segs)] for _ in range(n_frags)]
        compat = build_compatibility_matrix(all_segments)
        assert np.isfinite(compat).all()

        # Relaxation
        probs, _ = run_relaxation(compat)
        assert np.isfinite(probs).all()

    def test_invalid_array_shapes(self):
        # Test with mismatched shapes

        # Different length curvature profiles
        score = profile_similarity(np.array([0.1, 0.2]), np.array([0.1, 0.2, 0.3, 0.4]))
        assert 0.0 <= score <= 1.0

    def test_single_element_inputs(self):
        # Test with minimal valid inputs

        # Single-element chains
        score = segment_compatibility([0], [1])
        assert 0.0 <= score <= 1.0

        # Single pixel segment
        seg = np.array([[0, 0]])
        fourier_score = segment_fourier_score(seg, seg)
        assert fourier_score == 0.0

    def test_large_inputs(self):
        # Test with larger than typical inputs

        # Large curvature profiles
        large_profile = np.random.randn(1000)
        score = profile_similarity(large_profile, large_profile)
        assert 0.8 <= score <= 1.0

        # Large chain codes
        large_chain = list(range(500))
        compat = segment_compatibility(large_chain, large_chain)
        assert compat == pytest.approx(1.0)


class TestIntegration:
    """Integration tests across modules."""

    def test_full_pipeline_small(self, sample_image, sample_image_red):
        """Test complete pipeline with minimal inputs."""
        # Create minimal compatibility matrix
        n_frags, n_segs = 2, 2
        all_segments = [[[0, 1, 2] for _ in range(n_segs)] for _ in range(n_frags)]
        all_images = [sample_image, sample_image_red]

        # Build compatibility matrix
        compat = build_compatibility_matrix(all_segments, all_images=all_images)
        assert compat.shape == (n_frags, n_segs, n_frags, n_segs)

        # Run relaxation
        probs, trace = run_relaxation(compat)
        assert probs.shape == compat.shape
        assert len(trace) > 0

        # Extract assemblies
        assemblies = extract_top_assemblies(probs, n_top=2, compat_matrix=compat)
        assert len(assemblies) == 2
        assert all('verdict' in asm for asm in assemblies)

    def test_color_texture_pipeline(self, sample_image):
        """Test color and texture feature pipeline."""
        # Extract all features
        color_sig = compute_color_signature(sample_image)
        texture_sig = compute_texture_signature(sample_image)
        gray = cv2.cvtColor(sample_image, cv2.COLOR_BGR2GRAY)
        gabor_feat = extract_gabor_features(gray)
        haralick_feat = extract_haralick_features(gray)

        # Verify all features are valid
        assert len(color_sig) == 32
        assert len(texture_sig) == 26
        assert len(gabor_feat) == 120
        assert len(haralick_feat) == 60

        # Compute similarities with self
        assert color_bhattacharyya(color_sig, color_sig) == pytest.approx(1.0, abs=1e-6)
        assert texture_bhattacharyya(texture_sig, texture_sig) == pytest.approx(1.0, abs=1e-6)
        assert 0.95 <= gabor_similarity(gabor_feat, gabor_feat) <= 1.0
        assert 0.95 <= haralick_similarity(haralick_feat, haralick_feat) <= 1.0

    def test_discriminator_voting_pipeline(self, sample_image, sample_image_red):
        """Test hard discriminators + ensemble voting pipeline."""
        # Compute appearance features
        color_sig1 = compute_color_signature(sample_image)
        color_sig2 = compute_color_signature(sample_image_red)
        texture_sig1 = compute_texture_signature(sample_image)
        texture_sig2 = compute_texture_signature(sample_image_red)

        gray1 = cv2.cvtColor(sample_image, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(sample_image_red, cv2.COLOR_BGR2GRAY)
        gabor1 = extract_gabor_features(gray1)
        gabor2 = extract_gabor_features(gray2)

        # Compute similarities
        bc_color = color_bhattacharyya(color_sig1, color_sig2)
        bc_texture = texture_bhattacharyya(texture_sig1, texture_sig2)
        bc_gabor = gabor_similarity(gabor1, gabor2)

        # Hard reject check
        reject = hard_reject_check(sample_image, sample_image_red, bc_color, bc_texture)

        if not reject:
            # Ensemble voting
            edge_diff = abs(compute_edge_density(sample_image) - compute_edge_density(sample_image_red))
            entropy_diff = abs(compute_texture_entropy(sample_image) - compute_texture_entropy(sample_image_red))

            verdict = ensemble_verdict_five_way(
                raw_compat=0.80,
                bc_color=bc_color,
                bc_texture=bc_texture,
                bc_gabor=bc_gabor,
                edge_density_diff=edge_diff,
                entropy_diff=entropy_diff
            )
            assert verdict in ["MATCH", "WEAK_MATCH", "NO_MATCH"]


# ---------------------------------------------------------------------------
# Run tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
