"""
Unit tests for the archaeological fragment reconstruction pipeline.

Covers chain code encoding, compatibility scoring, and relaxation labeling.
All tests use synthetic data so no actual fragment images are required.
Run with:  python -m pytest tests/
"""

import sys
import os
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from chain_code import (
    points_to_chain_code,
    first_difference,
    cyclic_minimum_rotation,
    normalize_chain_code,
    segment_chain_code,
)
from compatibility import (
    edit_distance,
    segment_compatibility,
    build_compatibility_matrix,
)
from relaxation import (
    initialize_probabilities,
    run_relaxation,
    extract_top_assemblies,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_square_contour(side: int = 10, origin=(0, 0)) -> np.ndarray:
    """Generate a closed square boundary as a (N, 2) point array."""
    x0, y0 = origin
    top    = [(x0 + i, y0)          for i in range(side)]
    right  = [(x0 + side, y0 + i)   for i in range(side)]
    bottom = [(x0 + side - i, y0 + side) for i in range(side)]
    left   = [(x0, y0 + side - i)   for i in range(side)]
    return np.array(top + right + bottom + left)


def make_mock_compat(n_frags: int = 3, n_segs: int = 2) -> np.ndarray:
    """Return a random compatibility matrix with same-fragment entries zeroed."""
    matrix = np.random.rand(n_frags, n_segs, n_frags, n_segs)
    for frag_idx in range(n_frags):
        matrix[frag_idx, :, frag_idx, :] = 0.0
    return matrix


# ---------------------------------------------------------------------------
# Chain Code Tests
# ---------------------------------------------------------------------------

def test_chain_code_values_in_range():
    contour = make_square_contour()
    chain = points_to_chain_code(contour)
    assert all(0 <= code <= 7 for code in chain), \
        "All chain codes must be in the range [0, 7]"


def test_chain_code_nonempty_for_valid_contour():
    contour = make_square_contour(side=12)
    chain = points_to_chain_code(contour)
    assert len(chain) > 0


def test_first_difference_length():
    chain = [0, 1, 2, 3, 4]
    diff = first_difference(chain)
    assert len(diff) == len(chain) - 1


def test_first_difference_modulo_8():
    chain = [7, 1]
    diff = first_difference(chain)
    assert diff[0] == (1 - 7) % 8


def test_cyclic_minimum_is_smallest():
    sequence = [3, 1, 2, 0, 4]
    result = cyclic_minimum_rotation(sequence)
    n = len(sequence)
    doubled = sequence + sequence
    for start in range(n):
        candidate = doubled[start: start + n]
        assert result <= candidate, \
            f"Cyclic minimum {result} is not ≤ rotation starting at {start}: {candidate}"


def test_normalize_chain_code_deterministic():
    contour = make_square_contour()
    raw = points_to_chain_code(contour)
    assert normalize_chain_code(raw) == normalize_chain_code(raw)


def test_segment_chain_code_correct_count():
    chain = list(range(24))
    segments = segment_chain_code(chain, n_segments=4)
    assert len(segments) == 4


def test_segment_chain_code_covers_full_chain():
    chain = list(range(20))
    segments = segment_chain_code(chain, n_segments=4)
    reconstructed = [code for seg in segments for code in seg]
    assert reconstructed == chain, "Segments should cover the entire chain code"


# ---------------------------------------------------------------------------
# Compatibility Tests
# ---------------------------------------------------------------------------

def test_edit_distance_identical_sequences():
    seq = [1, 2, 3, 4]
    assert edit_distance(seq, seq) == 0


def test_edit_distance_empty_sequences():
    assert edit_distance([], [1, 2, 3]) == 3
    assert edit_distance([1, 2], []) == 2
    assert edit_distance([], []) == 0


def test_edit_distance_single_substitution():
    assert edit_distance([1, 2, 3], [1, 9, 3]) == 1


def test_edit_distance_single_insertion():
    assert edit_distance([1, 3], [1, 2, 3]) == 1


def test_segment_compatibility_identical():
    seg = [0, 1, 2, 3, 0, 1]
    assert segment_compatibility(seg, seg) == pytest.approx(1.0)


def test_segment_compatibility_in_unit_interval():
    score = segment_compatibility([0, 1, 2], [3, 4, 5, 6])
    assert 0.0 <= score <= 1.0


def test_compatibility_matrix_shape():
    n_frags, n_segs = 3, 4
    all_segments = [[[i, j] for j in range(n_segs)] for i in range(n_frags)]
    compat = build_compatibility_matrix(all_segments)
    assert compat.shape == (n_frags, n_segs, n_frags, n_segs)


def test_self_compatibility_is_zero():
    all_segments = [[[0, 1, 2, 3]] for _ in range(4)]
    compat = build_compatibility_matrix(all_segments)
    for frag_idx in range(4):
        assert compat[frag_idx, :, frag_idx, :].sum() == pytest.approx(0.0), \
            f"Self-compatibility of fragment {frag_idx} should be zero"


# ---------------------------------------------------------------------------
# Relaxation Labeling Tests
# ---------------------------------------------------------------------------

def test_initial_probabilities_sum_to_one():
    compat = make_mock_compat(n_frags=3, n_segs=2)
    probs = initialize_probabilities(compat)
    flat = probs.reshape(6, 6)
    row_sums = flat.sum(axis=1)
    assert np.allclose(row_sums, 1.0, atol=1e-6), \
        "Each unit's probability distribution must sum to 1"


def test_relaxation_output_shape():
    compat = make_mock_compat(n_frags=3, n_segs=2)
    probs, trace = run_relaxation(compat)
    assert probs.shape == compat.shape
    assert len(trace) > 0


def test_relaxation_probabilities_nonnegative():
    compat = make_mock_compat(n_frags=4, n_segs=2)
    probs, _ = run_relaxation(compat)
    assert (probs >= -1e-9).all(), "All probabilities must be non-negative"


def test_extract_assemblies_count():
    compat = make_mock_compat(n_frags=4, n_segs=3)
    probs, _ = run_relaxation(compat)
    assemblies = extract_top_assemblies(probs, n_top=3)
    assert len(assemblies) == 3


def test_assembly_confidence_nonnegative():
    compat = make_mock_compat(n_frags=4, n_segs=3)
    probs, _ = run_relaxation(compat)
    for assembly in extract_top_assemblies(probs, n_top=2):
        assert assembly['confidence'] >= 0.0


def test_assembly_no_self_matches():
    compat = make_mock_compat(n_frags=4, n_segs=3)
    probs, _ = run_relaxation(compat)
    for assembly in extract_top_assemblies(probs, n_top=2):
        for pair in assembly['pairs']:
            assert pair['frag_i'] != pair['frag_j'], \
                "A fragment must not be matched to itself"
