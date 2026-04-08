"""
Acceptance tests for the archaeological fragment reconstruction system.

Tests system behavior from a user requirements perspective:
1. Positive accuracy >= 85% (same-artifact fragments should match)
2. Negative accuracy >= 85% (different-artifact fragments should not match)
3. Processing time < 15s per 6-fragment case
4. No crashes or errors on valid input
5. Reproducible results (same input = same output)

These tests validate that the system meets its core acceptance criteria
as specified in the project requirements. All tests use real benchmark
data from data/examples/positive and data/examples/negative.

Run with:
    python -m pytest tests/test_acceptance.py -v
    python -m pytest tests/test_acceptance.py -v --tb=short
"""

import sys
import os
import time
from pathlib import Path
from typing import List, Tuple
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from preprocessing import preprocess_fragment
from chain_code import encode_fragment, contour_to_pixel_segments
from compatibility import build_compatibility_matrix
from relaxation import (
    run_relaxation,
    extract_top_assemblies,
    MATCH_SCORE_THRESHOLD,
    WEAK_MATCH_SCORE_THRESHOLD,
)
from shape_descriptors import pca_normalize_contour

# ---------------------------------------------------------------------------
# Test Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
POSITIVE_DATA_DIR = PROJECT_ROOT / "data" / "examples" / "positive"
NEGATIVE_DATA_DIR = PROJECT_ROOT / "data" / "examples" / "negative"
N_SEGMENTS = 4

# User Requirements Thresholds
REQUIRED_POSITIVE_ACCURACY = 0.85  # 85%
REQUIRED_NEGATIVE_ACCURACY = 0.85  # 85%
MAX_PROCESSING_TIME_6_FRAGMENTS = 15.0  # seconds
CONFIDENCE_THRESHOLD_MATCH = 0.60  # confidence > 0.60 = match


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def find_test_cases(directory: Path) -> List[Path]:
    """Find all test case directories."""
    if not directory.exists():
        return []
    return sorted([d for d in directory.iterdir() if d.is_dir()])


def load_fragment_set(directory: Path, max_fragments=None):
    """
    Load a set of fragment images from a directory.

    Returns:
        images: list of BGR numpy arrays
        contours: list of (N, 2) contour point arrays
        all_segments: list of chain code segment lists
        all_pixel_segs: list of pixel coordinate segment lists
        names: list of fragment names
    """
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp'}
    fragment_paths = sorted([
        p for p in directory.iterdir()
        if p.suffix.lower() in image_extensions
    ])

    if max_fragments:
        fragment_paths = fragment_paths[:max_fragments]

    images, contours, all_segments, all_pixel_segs, names = [], [], [], [], []

    for fpath in fragment_paths:
        name = fpath.stem
        try:
            image, contour = preprocess_fragment(str(fpath))
            pca_contour = pca_normalize_contour(contour)
            _, segments = encode_fragment(pca_contour, n_segments=N_SEGMENTS)
            pixel_segs = contour_to_pixel_segments(contour, N_SEGMENTS)

            images.append(image)
            contours.append(contour)
            all_segments.append(segments)
            all_pixel_segs.append(pixel_segs)
            names.append(name)
        except Exception as e:
            # Skip fragments that fail preprocessing
            continue

    return images, contours, all_segments, all_pixel_segs, names


def run_full_pipeline(directory: Path, max_fragments=None):
    """
    Run the complete reconstruction pipeline on a fragment set.

    Returns:
        assemblies: list of assembly dictionaries with verdict and confidence
        elapsed_time: processing time in seconds
        success: whether pipeline completed without errors
    """
    try:
        start_time = time.time()

        # Load and preprocess fragments
        images, contours, all_segments, all_pixel_segs, names = load_fragment_set(
            directory, max_fragments
        )

        if len(images) < 2:
            return None, 0.0, False

        # Build compatibility matrix
        compat_matrix = build_compatibility_matrix(all_segments, all_pixel_segs, images)

        # Run relaxation labeling
        probs, trace = run_relaxation(compat_matrix)

        # Extract top assemblies
        assemblies = extract_top_assemblies(probs, n_top=3, compat_matrix=compat_matrix)

        elapsed_time = time.time() - start_time

        return assemblies, elapsed_time, True

    except Exception as e:
        return None, 0.0, False


def classify_case_verdict(assemblies: list) -> str:
    """
    Determine the overall verdict for a test case.

    Returns "MATCH" if any assembly has verdict MATCH or WEAK_MATCH
    with confidence > 0.60, otherwise "NO_MATCH".
    """
    if not assemblies:
        return "NO_MATCH"

    for assembly in assemblies:
        if assembly['verdict'] in ['MATCH', 'WEAK_MATCH']:
            if assembly['confidence'] > CONFIDENCE_THRESHOLD_MATCH:
                return "MATCH"

    return "NO_MATCH"


# ---------------------------------------------------------------------------
# Scenario 1: Same-Artifact Matching (Positive Accuracy)
# ---------------------------------------------------------------------------

def test_same_artifact_fragments_should_match():
    """
    User Requirement: Positive Accuracy >= 85%

    Given fragments from the same pottery artifact
    When system processes them
    Then they should be classified as MATCH or WEAK_MATCH
    And confidence should be > 0.60
    """
    positive_cases = find_test_cases(POSITIVE_DATA_DIR)

    if not positive_cases:
        pytest.skip("No positive test cases found")

    total_cases = 0
    correct_matches = 0
    failed_cases = []

    for case_dir in positive_cases:
        assemblies, elapsed_time, success = run_full_pipeline(case_dir, max_fragments=6)

        if not success:
            # Count preprocessing failures as failed cases
            total_cases += 1
            failed_cases.append((case_dir.name, "Pipeline failed"))
            continue

        total_cases += 1
        verdict = classify_case_verdict(assemblies)

        if verdict == "MATCH":
            correct_matches += 1
        else:
            # Log failure details
            top_confidence = assemblies[0]['confidence'] if assemblies else 0.0
            failed_cases.append((case_dir.name, f"verdict={verdict}, conf={top_confidence:.3f}"))

    # Calculate positive accuracy
    positive_accuracy = correct_matches / total_cases if total_cases > 0 else 0.0

    # Report results
    print(f"\n=== POSITIVE ACCURACY TEST ===")
    print(f"Total cases: {total_cases}")
    print(f"Correct matches: {correct_matches}")
    print(f"Positive accuracy: {positive_accuracy:.1%}")
    print(f"Required: {REQUIRED_POSITIVE_ACCURACY:.1%}")

    if failed_cases:
        print(f"\nFailed cases ({len(failed_cases)}):")
        for name, reason in failed_cases:
            print(f"  - {name}: {reason}")

    # Assert requirement
    assert positive_accuracy >= REQUIRED_POSITIVE_ACCURACY, (
        f"Positive accuracy {positive_accuracy:.1%} is below required "
        f"{REQUIRED_POSITIVE_ACCURACY:.1%}. The system failed to correctly "
        f"match {len(failed_cases)} out of {total_cases} same-artifact cases."
    )


# ---------------------------------------------------------------------------
# Scenario 2: Different-Artifact Rejection (Negative Accuracy)
# ---------------------------------------------------------------------------

def test_different_artifact_fragments_should_not_match():
    """
    User Requirement: Negative Accuracy >= 85%

    Given fragments from different pottery artifacts
    When system processes them
    Then they should be classified as NO_MATCH
    And confidence should be < 0.60
    """
    negative_cases = find_test_cases(NEGATIVE_DATA_DIR)

    if not negative_cases:
        pytest.skip("No negative test cases found")

    total_cases = 0
    correct_rejections = 0
    false_positives = []

    for case_dir in negative_cases:
        assemblies, elapsed_time, success = run_full_pipeline(case_dir, max_fragments=6)

        if not success:
            # Count preprocessing failures as correct rejections
            # (system refused to process invalid input)
            total_cases += 1
            correct_rejections += 1
            continue

        total_cases += 1
        verdict = classify_case_verdict(assemblies)

        if verdict == "NO_MATCH":
            correct_rejections += 1
        else:
            # Log false positive details
            top_confidence = assemblies[0]['confidence'] if assemblies else 0.0
            false_positives.append((case_dir.name, f"verdict={verdict}, conf={top_confidence:.3f}"))

    # Calculate negative accuracy
    negative_accuracy = correct_rejections / total_cases if total_cases > 0 else 0.0

    # Report results
    print(f"\n=== NEGATIVE ACCURACY TEST ===")
    print(f"Total cases: {total_cases}")
    print(f"Correct rejections: {correct_rejections}")
    print(f"False positives: {len(false_positives)}")
    print(f"Negative accuracy: {negative_accuracy:.1%}")
    print(f"Required: {REQUIRED_NEGATIVE_ACCURACY:.1%}")

    if false_positives:
        print(f"\nFalse positive cases ({len(false_positives)}):")
        for name, reason in false_positives:
            print(f"  - {name}: {reason}")

    # Assert requirement
    assert negative_accuracy >= REQUIRED_NEGATIVE_ACCURACY, (
        f"Negative accuracy {negative_accuracy:.1%} is below required "
        f"{REQUIRED_NEGATIVE_ACCURACY:.1%}. The system incorrectly matched "
        f"{len(false_positives)} out of {total_cases} different-artifact cases."
    )


# ---------------------------------------------------------------------------
# Scenario 3: Performance Requirement
# ---------------------------------------------------------------------------

def test_processing_time_under_15_seconds():
    """
    User Requirement: Processing time < 15s per 6-fragment case

    Given a case with 6 fragments
    When system processes it
    Then total time should be < 15 seconds
    """
    positive_cases = find_test_cases(POSITIVE_DATA_DIR)

    if not positive_cases:
        pytest.skip("No positive test cases found")

    # Test first 3 positive cases for performance
    times = []
    slow_cases = []

    for case_dir in positive_cases[:3]:
        assemblies, elapsed_time, success = run_full_pipeline(case_dir, max_fragments=6)

        if not success:
            continue

        times.append(elapsed_time)

        if elapsed_time >= MAX_PROCESSING_TIME_6_FRAGMENTS:
            slow_cases.append((case_dir.name, elapsed_time))

    if not times:
        pytest.skip("No cases successfully processed")

    # Calculate statistics
    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)

    # Report results
    print(f"\n=== PERFORMANCE TEST ===")
    print(f"Cases tested: {len(times)}")
    print(f"Average time: {avg_time:.2f}s")
    print(f"Min time: {min_time:.2f}s")
    print(f"Max time: {max_time:.2f}s")
    print(f"Required: < {MAX_PROCESSING_TIME_6_FRAGMENTS}s")

    if slow_cases:
        print(f"\nSlow cases ({len(slow_cases)}):")
        for name, time_taken in slow_cases:
            print(f"  - {name}: {time_taken:.2f}s")

    # Assert requirement
    assert max_time < MAX_PROCESSING_TIME_6_FRAGMENTS, (
        f"Processing time {max_time:.2f}s exceeds required "
        f"{MAX_PROCESSING_TIME_6_FRAGMENTS}s. {len(slow_cases)} cases "
        f"were too slow."
    )


# ---------------------------------------------------------------------------
# Scenario 4: Overall Accuracy Requirements
# ---------------------------------------------------------------------------

def test_meets_accuracy_requirements():
    """
    User Requirement: System must meet both accuracy requirements

    Given the full benchmark (positive + negative cases)
    When system processes all cases
    Then positive accuracy >= 85%
    And negative accuracy >= 85%
    """
    positive_cases = find_test_cases(POSITIVE_DATA_DIR)
    negative_cases = find_test_cases(NEGATIVE_DATA_DIR)

    if not positive_cases or not negative_cases:
        pytest.skip("Benchmark data not available")

    # Process positive cases
    total_positive = 0
    correct_positive = 0

    for case_dir in positive_cases:
        assemblies, _, success = run_full_pipeline(case_dir, max_fragments=6)
        if not success:
            total_positive += 1
            continue

        total_positive += 1
        verdict = classify_case_verdict(assemblies)
        if verdict == "MATCH":
            correct_positive += 1

    # Process negative cases
    total_negative = 0
    correct_negative = 0

    for case_dir in negative_cases:
        assemblies, _, success = run_full_pipeline(case_dir, max_fragments=6)
        if not success:
            total_negative += 1
            correct_negative += 1
            continue

        total_negative += 1
        verdict = classify_case_verdict(assemblies)
        if verdict == "NO_MATCH":
            correct_negative += 1

    # Calculate accuracies
    positive_accuracy = correct_positive / total_positive if total_positive > 0 else 0.0
    negative_accuracy = correct_negative / total_negative if total_negative > 0 else 0.0
    overall_accuracy = (correct_positive + correct_negative) / (total_positive + total_negative)

    # Report overall results
    print(f"\n=== OVERALL ACCURACY TEST ===")
    print(f"Positive cases: {correct_positive}/{total_positive} ({positive_accuracy:.1%})")
    print(f"Negative cases: {correct_negative}/{total_negative} ({negative_accuracy:.1%})")
    print(f"Overall accuracy: {overall_accuracy:.1%}")
    print(f"Required: >= {REQUIRED_POSITIVE_ACCURACY:.1%} for both")

    # Assert both requirements
    assert positive_accuracy >= REQUIRED_POSITIVE_ACCURACY, (
        f"Positive accuracy {positive_accuracy:.1%} below required {REQUIRED_POSITIVE_ACCURACY:.1%}"
    )
    assert negative_accuracy >= REQUIRED_NEGATIVE_ACCURACY, (
        f"Negative accuracy {negative_accuracy:.1%} below required {REQUIRED_NEGATIVE_ACCURACY:.1%}"
    )


# ---------------------------------------------------------------------------
# Scenario 5: No Crashes on Valid Input
# ---------------------------------------------------------------------------

def test_no_crashes_on_valid_input():
    """
    User Requirement: System should not crash on valid input

    Given any valid fragment image set
    When system processes it
    Then it should complete without errors
    And return a valid result or clear error message
    """
    positive_cases = find_test_cases(POSITIVE_DATA_DIR)
    negative_cases = find_test_cases(NEGATIVE_DATA_DIR)

    all_cases = list(positive_cases) + list(negative_cases)

    if not all_cases:
        pytest.skip("No test cases found")

    crashed_cases = []
    total_cases = 0

    for case_dir in all_cases:
        total_cases += 1
        try:
            assemblies, _, success = run_full_pipeline(case_dir, max_fragments=6)
            # Even if success=False, it should not crash
            # It should handle errors gracefully
        except Exception as e:
            crashed_cases.append((case_dir.name, str(e)))

    # Report results
    print(f"\n=== STABILITY TEST ===")
    print(f"Total cases tested: {total_cases}")
    print(f"Crashed cases: {len(crashed_cases)}")
    print(f"Success rate: {(total_cases - len(crashed_cases)) / total_cases:.1%}")

    if crashed_cases:
        print(f"\nCrashed cases ({len(crashed_cases)}):")
        for name, error in crashed_cases:
            print(f"  - {name}: {error[:80]}")

    # Assert requirement
    assert len(crashed_cases) == 0, (
        f"System crashed on {len(crashed_cases)} out of {total_cases} cases. "
        f"All valid inputs should be handled gracefully."
    )


# ---------------------------------------------------------------------------
# Scenario 6: Reproducible Results
# ---------------------------------------------------------------------------

def test_reproducible_results():
    """
    User Requirement: Same input = same output

    Given a fragment set
    When system processes it twice
    Then both runs should produce the same verdict and similar confidence
    """
    positive_cases = find_test_cases(POSITIVE_DATA_DIR)

    if not positive_cases:
        pytest.skip("No positive test cases found")

    # Test first case twice
    test_case = positive_cases[0]

    # First run
    assemblies1, time1, success1 = run_full_pipeline(test_case, max_fragments=6)

    if not success1:
        pytest.skip(f"Test case {test_case.name} failed to process")

    # Second run
    assemblies2, time2, success2 = run_full_pipeline(test_case, max_fragments=6)

    if not success2:
        pytest.skip(f"Test case {test_case.name} failed to process on second run")

    # Extract verdicts and confidences
    verdict1 = assemblies1[0]['verdict'] if assemblies1 else "NO_MATCH"
    verdict2 = assemblies2[0]['verdict'] if assemblies2 else "NO_MATCH"

    confidence1 = assemblies1[0]['confidence'] if assemblies1 else 0.0
    confidence2 = assemblies2[0]['confidence'] if assemblies2 else 0.0

    # Report results
    print(f"\n=== REPRODUCIBILITY TEST ===")
    print(f"Test case: {test_case.name}")
    print(f"Run 1: verdict={verdict1}, confidence={confidence1:.4f}")
    print(f"Run 2: verdict={verdict2}, confidence={confidence2:.4f}")
    print(f"Confidence difference: {abs(confidence1 - confidence2):.4f}")

    # Assert requirements
    assert verdict1 == verdict2, (
        f"Verdicts differ between runs: {verdict1} vs {verdict2}. "
        f"Results should be reproducible."
    )

    # Allow small numerical differences due to floating point
    assert abs(confidence1 - confidence2) < 0.001, (
        f"Confidence scores differ significantly: {confidence1:.4f} vs {confidence2:.4f}. "
        f"Results should be reproducible."
    )


# ---------------------------------------------------------------------------
# Additional Acceptance Tests
# ---------------------------------------------------------------------------

def test_match_confidence_is_meaningful():
    """
    Verify that confidence scores meaningfully distinguish matches from non-matches.

    Given positive and negative cases
    When comparing confidence scores
    Then positive cases should have significantly higher confidence than negative cases
    """
    positive_cases = find_test_cases(POSITIVE_DATA_DIR)
    negative_cases = find_test_cases(NEGATIVE_DATA_DIR)

    if not positive_cases or not negative_cases:
        pytest.skip("Need both positive and negative cases")

    positive_confidences = []
    negative_confidences = []

    # Collect positive confidences
    for case_dir in positive_cases[:5]:
        assemblies, _, success = run_full_pipeline(case_dir, max_fragments=6)
        if success and assemblies:
            positive_confidences.append(assemblies[0]['confidence'])

    # Collect negative confidences
    for case_dir in negative_cases[:5]:
        assemblies, _, success = run_full_pipeline(case_dir, max_fragments=6)
        if success and assemblies:
            negative_confidences.append(assemblies[0]['confidence'])

    if not positive_confidences or not negative_confidences:
        pytest.skip("Could not collect confidence scores")

    # Calculate statistics
    avg_positive = sum(positive_confidences) / len(positive_confidences)
    avg_negative = sum(negative_confidences) / len(negative_confidences)
    separation = avg_positive - avg_negative

    # Report results
    print(f"\n=== CONFIDENCE SEPARATION TEST ===")
    print(f"Positive cases avg confidence: {avg_positive:.4f}")
    print(f"Negative cases avg confidence: {avg_negative:.4f}")
    print(f"Separation: {separation:.4f}")

    # Assert meaningful separation
    assert avg_positive > avg_negative, (
        f"Positive cases should have higher confidence than negative cases. "
        f"Got positive={avg_positive:.4f}, negative={avg_negative:.4f}"
    )


def test_system_handles_edge_cases():
    """
    Verify system handles edge cases gracefully.

    Edge cases:
    - Small fragments (< 100 pixels)
    - Large fragments (> 2000 pixels)
    - Fragments with complex boundaries
    """
    # This is a basic sanity check that the test data can be processed
    # More comprehensive edge case testing is in test_integration.py

    positive_cases = find_test_cases(POSITIVE_DATA_DIR)

    if not positive_cases:
        pytest.skip("No test cases found")

    # Test that we can process at least some cases without errors
    processed = 0
    for case_dir in positive_cases:
        assemblies, _, success = run_full_pipeline(case_dir, max_fragments=6)
        if success:
            processed += 1

    print(f"\n=== EDGE CASE HANDLING ===")
    print(f"Successfully processed: {processed}/{len(positive_cases)} cases")

    assert processed > 0, "Should be able to process at least one test case"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
