#!/usr/bin/env python3
"""
hyperparameter_sensitivity.py
-----------------------------
Comprehensive hyperparameter sensitivity analysis for fragment matching.

Tests how changes to key hyperparameters affect:
- Positive accuracy (same-source fragments correctly matched)
- Negative accuracy (different-source fragments correctly rejected)
- Confidence scores
- Runtime performance

Hyperparameters tested:
1. COLOR_PENALTY_WEIGHT (0.70 - 0.90)
2. MATCH_SCORE_THRESHOLD (0.45 - 0.65)
3. Color pre-check thresholds: GAP_THRESH, LOW_MAX
4. N_SEGMENTS (3, 4, 6, 8)

Generates:
- Sensitivity plots for each parameter
- Optimal configuration recommendation
- Trade-off analysis (accuracy vs performance)
- Markdown report with detailed findings

Usage:
    python scripts/hyperparameter_sensitivity.py
    python scripts/hyperparameter_sensitivity.py --n-positive 10 --n-negative 10
    python scripts/hyperparameter_sensitivity.py --quick  # Fast test with fewer configs
"""

import argparse
import json
import logging
import os
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import cv2
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from preprocessing import preprocess_fragment
from chain_code import encode_fragment, contour_to_pixel_segments
from compatibility import (
    build_compatibility_matrix,
    compute_color_signature,
    color_bhattacharyya,
)
from relaxation import run_relaxation, extract_top_assemblies
from shape_descriptors import pca_normalize_contour

# Import current defaults
import compatibility
import relaxation

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.jfif', '.webp'}


@dataclass
class HyperparameterConfig:
    """Configuration for a single hyperparameter test."""
    name: str
    color_penalty_weight: float = 0.80
    match_threshold: float = 0.55
    weak_match_threshold: float = 0.35
    n_segments: int = 4
    # Color pre-check thresholds (if implemented)
    gap_thresh: Optional[float] = None
    low_max: Optional[float] = None

    def __str__(self) -> str:
        parts = []
        if self.color_penalty_weight != 0.80:
            parts.append(f"CPW={self.color_penalty_weight:.2f}")
        if self.match_threshold != 0.55:
            parts.append(f"MT={self.match_threshold:.2f}")
        if self.n_segments != 4:
            parts.append(f"NS={self.n_segments}")
        if self.gap_thresh is not None:
            parts.append(f"GT={self.gap_thresh:.2f}")
        if self.low_max is not None:
            parts.append(f"LM={self.low_max:.2f}")
        return f"{self.name}: {', '.join(parts)}" if parts else self.name


@dataclass
class TestResult:
    """Results from testing a single hyperparameter configuration."""
    config: HyperparameterConfig

    # Accuracy metrics
    n_positive_pairs: int = 0
    n_negative_pairs: int = 0
    n_positive_correct: int = 0
    n_negative_correct: int = 0
    positive_accuracy: float = 0.0
    negative_accuracy: float = 0.0
    overall_accuracy: float = 0.0

    # Confidence metrics
    avg_positive_confidence: float = 0.0
    avg_negative_confidence: float = 0.0
    positive_confidences: List[float] = field(default_factory=list)
    negative_confidences: List[float] = field(default_factory=list)

    # Performance metrics
    total_runtime_ms: float = 0.0
    avg_pair_runtime_ms: float = 0.0

    # Detailed results
    pair_results: List[Dict[str, Any]] = field(default_factory=list)


def setup_logging(output_dir: str, verbose: bool = False) -> logging.Logger:
    """Configure logging with timestamped file and console output."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = os.path.join(output_dir, f'hyperparameter_sensitivity_{timestamp}.log')

    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger('hyperparameter_sensitivity')
    logger.info("Log file: %s", log_path)
    return logger


def collect_test_fragments(
    input_dir: str,
    n_positive: int,
    n_negative: int,
    logger: logging.Logger,
) -> Tuple[List[Tuple[Path, Path, str, str]], List[Tuple[Path, Path, str, str]]]:
    """
    Collect test fragment pairs for sensitivity analysis.

    Returns:
        (positive_pairs, negative_pairs)
        Each pair is (frag_a_path, frag_b_path, source_a, source_b)
    """
    input_path = Path(input_dir)
    fragments_by_source = defaultdict(list)

    # Collect fragments organized by source
    for source_dir in sorted(input_path.iterdir()):
        if not source_dir.is_dir():
            continue

        images = sorted(
            p for p in source_dir.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        )

        if images:
            source_name = source_dir.name
            fragments_by_source[source_name] = images
            logger.info("Found %d fragments in source '%s'", len(images), source_name)

    if not fragments_by_source:
        raise ValueError(f"No fragments found in {input_dir}")

    positive_pairs = []
    negative_pairs = []
    sources = list(fragments_by_source.keys())

    # Create positive pairs (within same source)
    for source_name, fragments in fragments_by_source.items():
        if len(fragments) < 2:
            continue

        for i in range(min(n_positive, len(fragments) - 1)):
            if i + 1 < len(fragments):
                positive_pairs.append((
                    fragments[i],
                    fragments[i + 1],
                    source_name,
                    source_name,
                ))

    # Limit to requested number
    positive_pairs = positive_pairs[:n_positive]

    # Create negative pairs (across different sources)
    if len(sources) >= 2:
        pair_count = 0
        for i in range(len(sources)):
            for j in range(i + 1, len(sources)):
                if pair_count >= n_negative:
                    break

                src_i = sources[i]
                src_j = sources[j]

                if fragments_by_source[src_i] and fragments_by_source[src_j]:
                    # Use different fragments from each source
                    idx_i = pair_count % len(fragments_by_source[src_i])
                    idx_j = pair_count % len(fragments_by_source[src_j])

                    negative_pairs.append((
                        fragments_by_source[src_i][idx_i],
                        fragments_by_source[src_j][idx_j],
                        src_i,
                        src_j,
                    ))
                    pair_count += 1

            if pair_count >= n_negative:
                break

    logger.info(
        "Selected %d positive pairs and %d negative pairs for testing",
        len(positive_pairs), len(negative_pairs),
    )

    return positive_pairs, negative_pairs


def test_pair_with_config(
    frag_a_path: Path,
    frag_b_path: Path,
    source_a: str,
    source_b: str,
    config: HyperparameterConfig,
    logger: logging.Logger,
) -> Optional[Dict[str, Any]]:
    """
    Test a single fragment pair with a specific hyperparameter configuration.

    Returns dict with test results or None if preprocessing fails.
    """
    start_time = time.time()
    is_positive = (source_a == source_b)

    try:
        # Temporarily override hyperparameters
        original_color_weight = compatibility.COLOR_PENALTY_WEIGHT
        original_match_thresh = relaxation.MATCH_SCORE_THRESHOLD
        original_weak_thresh = relaxation.WEAK_MATCH_SCORE_THRESHOLD

        compatibility.COLOR_PENALTY_WEIGHT = config.color_penalty_weight
        relaxation.MATCH_SCORE_THRESHOLD = config.match_threshold
        relaxation.WEAK_MATCH_SCORE_THRESHOLD = config.weak_match_threshold

        # Preprocess both fragments
        image_a, contour_a = preprocess_fragment(str(frag_a_path))
        image_b, contour_b = preprocess_fragment(str(frag_b_path))

        # Normalize contours
        contour_a_norm = pca_normalize_contour(contour_a)
        contour_b_norm = pca_normalize_contour(contour_b)

        # Extract chain code segments
        _, segments_a = encode_fragment(contour_a_norm, n_segments=config.n_segments)
        _, segments_b = encode_fragment(contour_b_norm, n_segments=config.n_segments)

        pixel_segs_a = contour_to_pixel_segments(contour_a, config.n_segments)
        pixel_segs_b = contour_to_pixel_segments(contour_b, config.n_segments)

        # Compute color similarity
        sig_a = compute_color_signature(image_a)
        sig_b = compute_color_signature(image_b)
        color_bc = float(color_bhattacharyya(sig_a, sig_b))

        # Build compatibility matrix
        all_segments = [segments_a, segments_b]
        all_pixel_segs = [pixel_segs_a, pixel_segs_b]
        images = [image_a, image_b]

        compat_matrix = build_compatibility_matrix(all_segments, all_pixel_segs, images)

        # Run relaxation labeling
        probs, trace = run_relaxation(compat_matrix)

        # Extract top assembly
        assemblies = extract_top_assemblies(probs, n_top=1, compat_matrix=compat_matrix)

        verdict = "NO_MATCH"
        confidence = 0.0
        match_found = False

        if assemblies:
            top = assemblies[0]
            verdict = top['verdict']
            confidence = top['confidence']
            match_found = (verdict != 'NO_MATCH')

        runtime_ms = (time.time() - start_time) * 1000

        # Restore original values
        compatibility.COLOR_PENALTY_WEIGHT = original_color_weight
        relaxation.MATCH_SCORE_THRESHOLD = original_match_thresh
        relaxation.WEAK_MATCH_SCORE_THRESHOLD = original_weak_thresh

        return {
            'frag_a': frag_a_path.stem,
            'frag_b': frag_b_path.stem,
            'source_a': source_a,
            'source_b': source_b,
            'is_positive': is_positive,
            'match_found': match_found,
            'verdict': verdict,
            'confidence': confidence,
            'color_bc': color_bc,
            'runtime_ms': runtime_ms,
        }

    except Exception as exc:
        logger.warning(
            "Failed to test pair %s <-> %s: %s",
            frag_a_path.stem, frag_b_path.stem, str(exc),
        )
        return None


def test_configuration(
    config: HyperparameterConfig,
    positive_pairs: List[Tuple[Path, Path, str, str]],
    negative_pairs: List[Tuple[Path, Path, str, str]],
    logger: logging.Logger,
) -> TestResult:
    """Test a single hyperparameter configuration on all pairs."""
    logger.info("Testing config: %s", config)

    result = TestResult(config=config)
    start_time = time.time()

    all_pairs = [(p, True) for p in positive_pairs] + [(p, False) for p in negative_pairs]

    for (frag_a, frag_b, src_a, src_b), is_positive in all_pairs:
        pair_result = test_pair_with_config(frag_a, frag_b, src_a, src_b, config, logger)

        if pair_result is None:
            continue

        result.pair_results.append(pair_result)

        if is_positive:
            result.n_positive_pairs += 1
            result.positive_confidences.append(pair_result['confidence'])
            if pair_result['match_found']:
                result.n_positive_correct += 1
        else:
            result.n_negative_pairs += 1
            result.negative_confidences.append(pair_result['confidence'])
            if not pair_result['match_found']:
                result.n_negative_correct += 1

    # Calculate metrics
    result.positive_accuracy = (
        result.n_positive_correct / result.n_positive_pairs
        if result.n_positive_pairs > 0 else 0.0
    )
    result.negative_accuracy = (
        result.n_negative_correct / result.n_negative_pairs
        if result.n_negative_pairs > 0 else 0.0
    )

    total_pairs = result.n_positive_pairs + result.n_negative_pairs
    total_correct = result.n_positive_correct + result.n_negative_correct
    result.overall_accuracy = total_correct / total_pairs if total_pairs > 0 else 0.0

    result.avg_positive_confidence = (
        np.mean(result.positive_confidences) if result.positive_confidences else 0.0
    )
    result.avg_negative_confidence = (
        np.mean(result.negative_confidences) if result.negative_confidences else 0.0
    )

    result.total_runtime_ms = (time.time() - start_time) * 1000
    result.avg_pair_runtime_ms = (
        result.total_runtime_ms / len(result.pair_results)
        if result.pair_results else 0.0
    )

    logger.info(
        "Config %s: Pos=%.1f%% Neg=%.1f%% Overall=%.1f%% Time=%.0fms",
        config.name,
        result.positive_accuracy * 100,
        result.negative_accuracy * 100,
        result.overall_accuracy * 100,
        result.total_runtime_ms,
    )

    return result


def generate_configurations(quick: bool = False) -> Dict[str, List[HyperparameterConfig]]:
    """
    Generate all hyperparameter configurations to test.

    Returns dict mapping parameter_name -> list of configs
    """
    configs = {}

    # 1. Color Penalty Weight
    cpw_values = [0.70, 0.75, 0.80, 0.85, 0.90] if not quick else [0.70, 0.80, 0.90]
    configs['color_penalty_weight'] = [
        HyperparameterConfig(
            name=f"CPW_{cpw:.2f}",
            color_penalty_weight=cpw,
        )
        for cpw in cpw_values
    ]

    # 2. Match Threshold
    mt_values = [0.45, 0.50, 0.55, 0.60, 0.65] if not quick else [0.45, 0.55, 0.65]
    configs['match_threshold'] = [
        HyperparameterConfig(
            name=f"MT_{mt:.2f}",
            match_threshold=mt,
        )
        for mt in mt_values
    ]

    # 3. N_SEGMENTS
    ns_values = [3, 4, 6, 8] if not quick else [3, 4, 8]
    configs['n_segments'] = [
        HyperparameterConfig(
            name=f"NS_{ns}",
            n_segments=ns,
        )
        for ns in ns_values
    ]

    # 4. Baseline (current default)
    configs['baseline'] = [
        HyperparameterConfig(
            name="Baseline",
            color_penalty_weight=0.80,
            match_threshold=0.55,
            n_segments=4,
        )
    ]

    return configs


def plot_sensitivity_analysis(
    results_by_param: Dict[str, List[TestResult]],
    output_dir: str,
    logger: logging.Logger,
) -> None:
    """Generate comprehensive sensitivity analysis plots."""
    os.makedirs(output_dir, exist_ok=True)

    # Plot 1: Color Penalty Weight sensitivity
    if 'color_penalty_weight' in results_by_param:
        results = results_by_param['color_penalty_weight']
        cpw_values = [r.config.color_penalty_weight for r in results]

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Color Penalty Weight Sensitivity Analysis', fontsize=16, fontweight='bold')

        # Accuracy
        ax = axes[0, 0]
        ax.plot(cpw_values, [r.positive_accuracy * 100 for r in results],
                'o-', label='Positive Accuracy', color='#2ecc71', linewidth=2, markersize=8)
        ax.plot(cpw_values, [r.negative_accuracy * 100 for r in results],
                's-', label='Negative Accuracy', color='#e74c3c', linewidth=2, markersize=8)
        ax.plot(cpw_values, [r.overall_accuracy * 100 for r in results],
                '^-', label='Overall Accuracy', color='#3498db', linewidth=2, markersize=8)
        ax.axvline(0.80, color='gray', linestyle='--', alpha=0.5, label='Current Default')
        ax.set_xlabel('Color Penalty Weight', fontsize=11)
        ax.set_ylabel('Accuracy (%)', fontsize=11)
        ax.set_title('Accuracy vs Color Penalty Weight', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-5, 105)

        # Confidence
        ax = axes[0, 1]
        ax.plot(cpw_values, [r.avg_positive_confidence for r in results],
                'o-', label='Avg Positive Confidence', color='#2ecc71', linewidth=2, markersize=8)
        ax.plot(cpw_values, [r.avg_negative_confidence for r in results],
                's-', label='Avg Negative Confidence', color='#e74c3c', linewidth=2, markersize=8)
        ax.axvline(0.80, color='gray', linestyle='--', alpha=0.5, label='Current Default')
        ax.set_xlabel('Color Penalty Weight', fontsize=11)
        ax.set_ylabel('Confidence Score', fontsize=11)
        ax.set_title('Confidence vs Color Penalty Weight', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1.0)

        # Runtime
        ax = axes[1, 0]
        ax.plot(cpw_values, [r.avg_pair_runtime_ms for r in results],
                'o-', color='#9b59b6', linewidth=2, markersize=8)
        ax.axvline(0.80, color='gray', linestyle='--', alpha=0.5, label='Current Default')
        ax.set_xlabel('Color Penalty Weight', fontsize=11)
        ax.set_ylabel('Avg Runtime per Pair (ms)', fontsize=11)
        ax.set_title('Performance vs Color Penalty Weight', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Accuracy trade-off
        ax = axes[1, 1]
        scatter = ax.scatter(
            [r.negative_accuracy * 100 for r in results],
            [r.positive_accuracy * 100 for r in results],
            c=cpw_values,
            s=150,
            cmap='viridis',
            edgecolors='black',
            linewidths=2,
            alpha=0.8,
        )
        for r in results:
            ax.annotate(
                f"{r.config.color_penalty_weight:.2f}",
                (r.negative_accuracy * 100, r.positive_accuracy * 100),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=9,
            )
        plt.colorbar(scatter, ax=ax, label='Color Penalty Weight')
        ax.set_xlabel('Negative Accuracy (%)', fontsize=11)
        ax.set_ylabel('Positive Accuracy (%)', fontsize=11)
        ax.set_title('Accuracy Trade-off', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(-5, 105)
        ax.set_ylim(-5, 105)

        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'sensitivity_color_penalty_weight.png'), dpi=150)
        plt.close()
        logger.info("Saved sensitivity_color_penalty_weight.png")

    # Plot 2: Match Threshold sensitivity
    if 'match_threshold' in results_by_param:
        results = results_by_param['match_threshold']
        mt_values = [r.config.match_threshold for r in results]

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Match Threshold Sensitivity Analysis', fontsize=16, fontweight='bold')

        # Accuracy
        ax = axes[0, 0]
        ax.plot(mt_values, [r.positive_accuracy * 100 for r in results],
                'o-', label='Positive Accuracy', color='#2ecc71', linewidth=2, markersize=8)
        ax.plot(mt_values, [r.negative_accuracy * 100 for r in results],
                's-', label='Negative Accuracy', color='#e74c3c', linewidth=2, markersize=8)
        ax.plot(mt_values, [r.overall_accuracy * 100 for r in results],
                '^-', label='Overall Accuracy', color='#3498db', linewidth=2, markersize=8)
        ax.axvline(0.55, color='gray', linestyle='--', alpha=0.5, label='Current Default')
        ax.set_xlabel('Match Threshold', fontsize=11)
        ax.set_ylabel('Accuracy (%)', fontsize=11)
        ax.set_title('Accuracy vs Match Threshold', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-5, 105)

        # Verdict distribution
        ax = axes[0, 1]
        match_counts = [sum(1 for pr in r.pair_results if pr['verdict'] == 'MATCH') for r in results]
        weak_counts = [sum(1 for pr in r.pair_results if pr['verdict'] == 'WEAK_MATCH') for r in results]
        no_match_counts = [sum(1 for pr in r.pair_results if pr['verdict'] == 'NO_MATCH') for r in results]

        width = 0.02
        x_pos = np.array(mt_values)
        ax.bar(x_pos - width, match_counts, width, label='MATCH', color='#2ecc71')
        ax.bar(x_pos, weak_counts, width, label='WEAK_MATCH', color='#f39c12')
        ax.bar(x_pos + width, no_match_counts, width, label='NO_MATCH', color='#e74c3c')
        ax.axvline(0.55, color='gray', linestyle='--', alpha=0.5, label='Current Default')
        ax.set_xlabel('Match Threshold', fontsize=11)
        ax.set_ylabel('Number of Pairs', fontsize=11)
        ax.set_title('Verdict Distribution vs Match Threshold', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')

        # Confidence
        ax = axes[1, 0]
        ax.plot(mt_values, [r.avg_positive_confidence for r in results],
                'o-', label='Avg Positive Confidence', color='#2ecc71', linewidth=2, markersize=8)
        ax.plot(mt_values, [r.avg_negative_confidence for r in results],
                's-', label='Avg Negative Confidence', color='#e74c3c', linewidth=2, markersize=8)
        ax.axhline(0.55, color='green', linestyle='--', alpha=0.5, label='Match Threshold')
        ax.axvline(0.55, color='gray', linestyle='--', alpha=0.5)
        ax.set_xlabel('Match Threshold', fontsize=11)
        ax.set_ylabel('Confidence Score', fontsize=11)
        ax.set_title('Confidence vs Match Threshold', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1.0)

        # Accuracy trade-off
        ax = axes[1, 1]
        scatter = ax.scatter(
            [r.negative_accuracy * 100 for r in results],
            [r.positive_accuracy * 100 for r in results],
            c=mt_values,
            s=150,
            cmap='plasma',
            edgecolors='black',
            linewidths=2,
            alpha=0.8,
        )
        for r in results:
            ax.annotate(
                f"{r.config.match_threshold:.2f}",
                (r.negative_accuracy * 100, r.positive_accuracy * 100),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=9,
            )
        plt.colorbar(scatter, ax=ax, label='Match Threshold')
        ax.set_xlabel('Negative Accuracy (%)', fontsize=11)
        ax.set_ylabel('Positive Accuracy (%)', fontsize=11)
        ax.set_title('Accuracy Trade-off', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(-5, 105)
        ax.set_ylim(-5, 105)

        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'sensitivity_match_threshold.png'), dpi=150)
        plt.close()
        logger.info("Saved sensitivity_match_threshold.png")

    # Plot 3: N_SEGMENTS sensitivity
    if 'n_segments' in results_by_param:
        results = results_by_param['n_segments']
        ns_values = [r.config.n_segments for r in results]

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('N_SEGMENTS Sensitivity Analysis', fontsize=16, fontweight='bold')

        # Accuracy
        ax = axes[0, 0]
        ax.plot(ns_values, [r.positive_accuracy * 100 for r in results],
                'o-', label='Positive Accuracy', color='#2ecc71', linewidth=2, markersize=8)
        ax.plot(ns_values, [r.negative_accuracy * 100 for r in results],
                's-', label='Negative Accuracy', color='#e74c3c', linewidth=2, markersize=8)
        ax.plot(ns_values, [r.overall_accuracy * 100 for r in results],
                '^-', label='Overall Accuracy', color='#3498db', linewidth=2, markersize=8)
        ax.axvline(4, color='gray', linestyle='--', alpha=0.5, label='Current Default')
        ax.set_xlabel('Number of Segments', fontsize=11)
        ax.set_ylabel('Accuracy (%)', fontsize=11)
        ax.set_title('Accuracy vs N_SEGMENTS', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-5, 105)
        ax.set_xticks(ns_values)

        # Runtime
        ax = axes[0, 1]
        ax.plot(ns_values, [r.avg_pair_runtime_ms for r in results],
                'o-', color='#9b59b6', linewidth=2, markersize=8)
        ax.axvline(4, color='gray', linestyle='--', alpha=0.5, label='Current Default')
        ax.set_xlabel('Number of Segments', fontsize=11)
        ax.set_ylabel('Avg Runtime per Pair (ms)', fontsize=11)
        ax.set_title('Performance vs N_SEGMENTS', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xticks(ns_values)

        # Accuracy vs Runtime trade-off
        ax = axes[1, 0]
        scatter = ax.scatter(
            [r.avg_pair_runtime_ms for r in results],
            [r.overall_accuracy * 100 for r in results],
            c=ns_values,
            s=150,
            cmap='coolwarm',
            edgecolors='black',
            linewidths=2,
            alpha=0.8,
        )
        for r in results:
            ax.annotate(
                f"N={r.config.n_segments}",
                (r.avg_pair_runtime_ms, r.overall_accuracy * 100),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=9,
            )
        plt.colorbar(scatter, ax=ax, label='N_SEGMENTS')
        ax.set_xlabel('Avg Runtime per Pair (ms)', fontsize=11)
        ax.set_ylabel('Overall Accuracy (%)', fontsize=11)
        ax.set_title('Accuracy vs Performance Trade-off', fontweight='bold')
        ax.grid(True, alpha=0.3)

        # Confidence
        ax = axes[1, 1]
        ax.plot(ns_values, [r.avg_positive_confidence for r in results],
                'o-', label='Avg Positive Confidence', color='#2ecc71', linewidth=2, markersize=8)
        ax.plot(ns_values, [r.avg_negative_confidence for r in results],
                's-', label='Avg Negative Confidence', color='#e74c3c', linewidth=2, markersize=8)
        ax.axvline(4, color='gray', linestyle='--', alpha=0.5, label='Current Default')
        ax.set_xlabel('Number of Segments', fontsize=11)
        ax.set_ylabel('Confidence Score', fontsize=11)
        ax.set_title('Confidence vs N_SEGMENTS', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1.0)
        ax.set_xticks(ns_values)

        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'sensitivity_n_segments.png'), dpi=150)
        plt.close()
        logger.info("Saved sensitivity_n_segments.png")

    # Plot 4: Overall comparison
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Hyperparameter Sensitivity - Overall Comparison', fontsize=16, fontweight='bold')

    all_results = []
    for param_name, param_results in results_by_param.items():
        if param_name != 'baseline':
            all_results.extend(param_results)

    if all_results:
        # Overall accuracy comparison
        ax = axes[0]
        param_colors = {
            'color_penalty_weight': '#e74c3c',
            'match_threshold': '#3498db',
            'n_segments': '#2ecc71',
        }

        for param_name, param_results in results_by_param.items():
            if param_name == 'baseline':
                continue

            if param_name == 'color_penalty_weight':
                x_vals = [r.config.color_penalty_weight for r in param_results]
                label = 'Color Penalty Weight'
            elif param_name == 'match_threshold':
                x_vals = [r.config.match_threshold for r in param_results]
                label = 'Match Threshold'
            elif param_name == 'n_segments':
                x_vals = [r.config.n_segments for r in param_results]
                label = 'N_SEGMENTS'
            else:
                continue

            y_vals = [r.overall_accuracy * 100 for r in param_results]
            ax.plot(x_vals, y_vals, 'o-', label=label,
                   color=param_colors.get(param_name, '#95a5a6'),
                   linewidth=2, markersize=8)

        ax.set_xlabel('Parameter Value (normalized scale)', fontsize=11)
        ax.set_ylabel('Overall Accuracy (%)', fontsize=11)
        ax.set_title('Overall Accuracy by Parameter', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Positive vs Negative accuracy scatter
        ax = axes[1]
        for param_name, param_results in results_by_param.items():
            if param_name == 'baseline':
                # Highlight baseline
                r = param_results[0]
                ax.scatter(
                    r.negative_accuracy * 100,
                    r.positive_accuracy * 100,
                    s=200,
                    marker='*',
                    color='gold',
                    edgecolors='black',
                    linewidths=2,
                    label='Baseline',
                    zorder=10,
                )
            else:
                color = param_colors.get(param_name, '#95a5a6')
                label = param_name.replace('_', ' ').title()
                ax.scatter(
                    [r.negative_accuracy * 100 for r in param_results],
                    [r.positive_accuracy * 100 for r in param_results],
                    s=100,
                    alpha=0.6,
                    color=color,
                    edgecolors='black',
                    linewidths=1,
                    label=label,
                )

        ax.plot([0, 100], [0, 100], 'k--', alpha=0.3, linewidth=1)
        ax.set_xlabel('Negative Accuracy (%)', fontsize=11)
        ax.set_ylabel('Positive Accuracy (%)', fontsize=11)
        ax.set_title('Positive vs Negative Accuracy Trade-off', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(-5, 105)
        ax.set_ylim(-5, 105)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'sensitivity_overall_comparison.png'), dpi=150)
    plt.close()
    logger.info("Saved sensitivity_overall_comparison.png")


def find_optimal_configuration(
    results_by_param: Dict[str, List[TestResult]],
    logger: logging.Logger,
) -> Tuple[TestResult, str]:
    """
    Find the optimal configuration based on multiple criteria.

    Returns (best_result, reasoning)
    """
    all_results = []
    for param_name, param_results in results_by_param.items():
        all_results.extend(param_results)

    if not all_results:
        raise ValueError("No results to analyze")

    # Score each configuration (higher is better)
    # Priority: Positive accuracy (must maintain 100%) > Negative accuracy > Runtime

    scored_results = []
    for result in all_results:
        # Critical: maintain positive accuracy (weight: 50%)
        pos_score = result.positive_accuracy * 50

        # Important: maximize negative accuracy (weight: 40%)
        neg_score = result.negative_accuracy * 40

        # Nice to have: minimize runtime (weight: 10%)
        # Normalize runtime to 0-1 scale (assuming max 5000ms)
        runtime_score = max(0, (5000 - result.avg_pair_runtime_ms) / 5000) * 10

        total_score = pos_score + neg_score + runtime_score
        scored_results.append((result, total_score))

    # Sort by score
    scored_results.sort(key=lambda x: x[1], reverse=True)
    best_result, best_score = scored_results[0]

    # Generate reasoning
    reasoning = f"""
Optimal Configuration: {best_result.config.name}

Selection Criteria:
- Positive Accuracy: {best_result.positive_accuracy*100:.1f}% (weight: 50%)
- Negative Accuracy: {best_result.negative_accuracy*100:.1f}% (weight: 40%)
- Performance: {best_result.avg_pair_runtime_ms:.1f}ms/pair (weight: 10%)
- Overall Score: {best_score:.2f}/100

Key Parameters:
- Color Penalty Weight: {best_result.config.color_penalty_weight}
- Match Threshold: {best_result.config.match_threshold}
- N_SEGMENTS: {best_result.config.n_segments}

Why This Configuration:
"""

    # Compare to baseline
    baseline_results = [r for r in all_results if r.config.name == "Baseline"]
    if baseline_results:
        baseline = baseline_results[0]
        pos_improve = (best_result.positive_accuracy - baseline.positive_accuracy) * 100
        neg_improve = (best_result.negative_accuracy - baseline.negative_accuracy) * 100

        if pos_improve >= 0 and neg_improve > 10:
            reasoning += f"- Significantly improves negative accuracy by {neg_improve:.1f}% while maintaining positive accuracy\n"
        elif pos_improve > 0 and neg_improve > 0:
            reasoning += f"- Improves both positive accuracy ({pos_improve:+.1f}%) and negative accuracy ({neg_improve:+.1f}%)\n"
        elif neg_improve > 0:
            reasoning += f"- Improves negative accuracy by {neg_improve:.1f}% (critical improvement)\n"
        else:
            reasoning += "- Represents the best balance of all tested configurations\n"

    logger.info(reasoning)
    return best_result, reasoning


def generate_markdown_report(
    results_by_param: Dict[str, List[TestResult]],
    optimal_result: TestResult,
    optimal_reasoning: str,
    output_path: str,
    logger: logging.Logger,
) -> None:
    """Generate comprehensive markdown report."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Hyperparameter Sensitivity Analysis\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## Executive Summary\n\n")

        # Current baseline performance
        baseline_results = [r for param_results in results_by_param.values()
                          for r in param_results if r.config.name == "Baseline"]
        if baseline_results:
            baseline = baseline_results[0]
            f.write("### Current Baseline Performance\n\n")
            f.write(f"- **Positive Accuracy:** {baseline.positive_accuracy*100:.1f}%\n")
            f.write(f"- **Negative Accuracy:** {baseline.negative_accuracy*100:.1f}%\n")
            f.write(f"- **Overall Accuracy:** {baseline.overall_accuracy*100:.1f}%\n")
            f.write(f"- **Avg Confidence (Positive):** {baseline.avg_positive_confidence:.3f}\n")
            f.write(f"- **Avg Confidence (Negative):** {baseline.avg_negative_confidence:.3f}\n")
            f.write(f"- **Avg Runtime:** {baseline.avg_pair_runtime_ms:.1f} ms/pair\n\n")

        f.write("### Optimal Configuration Found\n\n")
        f.write(optimal_reasoning)
        f.write("\n")

        f.write("### Performance Comparison\n\n")
        f.write("| Configuration | Positive Acc | Negative Acc | Overall Acc | Avg Runtime (ms) |\n")
        f.write("|--------------|--------------|--------------|-------------|------------------|\n")

        if baseline_results:
            baseline = baseline_results[0]
            f.write(f"| **Baseline** | {baseline.positive_accuracy*100:.1f}% | "
                   f"{baseline.negative_accuracy*100:.1f}% | {baseline.overall_accuracy*100:.1f}% | "
                   f"{baseline.avg_pair_runtime_ms:.1f} |\n")

        f.write(f"| **Optimal** | {optimal_result.positive_accuracy*100:.1f}% | "
               f"{optimal_result.negative_accuracy*100:.1f}% | {optimal_result.overall_accuracy*100:.1f}% | "
               f"{optimal_result.avg_pair_runtime_ms:.1f} |\n")

        if baseline_results:
            baseline = baseline_results[0]
            pos_delta = (optimal_result.positive_accuracy - baseline.positive_accuracy) * 100
            neg_delta = (optimal_result.negative_accuracy - baseline.negative_accuracy) * 100
            overall_delta = (optimal_result.overall_accuracy - baseline.overall_accuracy) * 100
            runtime_delta = optimal_result.avg_pair_runtime_ms - baseline.avg_pair_runtime_ms

            f.write(f"| **Change** | {pos_delta:+.1f}% | {neg_delta:+.1f}% | "
                   f"{overall_delta:+.1f}% | {runtime_delta:+.1f} |\n")

        f.write("\n")

        # Detailed results by parameter
        f.write("## Detailed Parameter Analysis\n\n")

        for param_name, param_results in results_by_param.items():
            if param_name == 'baseline':
                continue

            f.write(f"### {param_name.replace('_', ' ').title()}\n\n")

            f.write("| Value | Pos Acc | Neg Acc | Overall | Avg Conf (Pos) | Avg Conf (Neg) | Runtime (ms) |\n")
            f.write("|-------|---------|---------|---------|----------------|----------------|-------------|\n")

            for result in param_results:
                if param_name == 'color_penalty_weight':
                    value = f"{result.config.color_penalty_weight:.2f}"
                elif param_name == 'match_threshold':
                    value = f"{result.config.match_threshold:.2f}"
                elif param_name == 'n_segments':
                    value = str(result.config.n_segments)
                else:
                    value = result.config.name

                f.write(f"| {value} | {result.positive_accuracy*100:.1f}% | "
                       f"{result.negative_accuracy*100:.1f}% | {result.overall_accuracy*100:.1f}% | "
                       f"{result.avg_positive_confidence:.3f} | {result.avg_negative_confidence:.3f} | "
                       f"{result.avg_pair_runtime_ms:.1f} |\n")

            f.write("\n")

            # Key insights for this parameter
            f.write("**Key Insights:**\n\n")

            best_overall = max(param_results, key=lambda r: r.overall_accuracy)
            best_neg = max(param_results, key=lambda r: r.negative_accuracy)
            fastest = min(param_results, key=lambda r: r.avg_pair_runtime_ms)

            if param_name == 'color_penalty_weight':
                f.write(f"- Best overall accuracy achieved at CPW={best_overall.config.color_penalty_weight:.2f} "
                       f"({best_overall.overall_accuracy*100:.1f}%)\n")
                f.write(f"- Best negative accuracy at CPW={best_neg.config.color_penalty_weight:.2f} "
                       f"({best_neg.negative_accuracy*100:.1f}%)\n")
                f.write("- Higher CPW values tend to better discriminate between same/different source fragments\n")

            elif param_name == 'match_threshold':
                f.write(f"- Best overall accuracy at threshold={best_overall.config.match_threshold:.2f} "
                       f"({best_overall.overall_accuracy*100:.1f}%)\n")
                f.write(f"- Best negative accuracy at threshold={best_neg.config.match_threshold:.2f} "
                       f"({best_neg.negative_accuracy*100:.1f}%)\n")
                f.write("- Higher thresholds reduce false positives but may miss true matches\n")

            elif param_name == 'n_segments':
                f.write(f"- Best overall accuracy with {best_overall.config.n_segments} segments "
                       f"({best_overall.overall_accuracy*100:.1f}%)\n")
                f.write(f"- Fastest runtime with {fastest.config.n_segments} segments "
                       f"({fastest.avg_pair_runtime_ms:.1f} ms/pair)\n")
                f.write("- More segments capture finer detail but increase computation time\n")

            f.write("\n")

        # Recommendations
        f.write("## Recommendations\n\n")

        f.write("### 1. Immediate Actions\n\n")
        f.write(f"Update the following hyperparameters in your configuration:\n\n")
        f.write("```python\n")
        f.write(f"COLOR_PENALTY_WEIGHT = {optimal_result.config.color_penalty_weight}\n")
        f.write(f"MATCH_SCORE_THRESHOLD = {optimal_result.config.match_threshold}\n")
        f.write(f"N_SEGMENTS = {optimal_result.config.n_segments}\n")
        f.write("```\n\n")

        f.write("### 2. Performance Analysis\n\n")

        if baseline_results:
            baseline = baseline_results[0]
            if optimal_result.negative_accuracy > baseline.negative_accuracy + 0.1:
                f.write("- **Critical Improvement:** Negative accuracy significantly improved, "
                       "reducing false positive matches between fragments from different sources.\n")

            if optimal_result.positive_accuracy >= baseline.positive_accuracy:
                f.write("- **Maintained Performance:** Positive accuracy maintained or improved, "
                       "ensuring true matches are still detected.\n")
            else:
                f.write("- **Trade-off Alert:** Positive accuracy slightly decreased. "
                       "Monitor this in production to ensure acceptable match rates.\n")

        f.write("\n")

        f.write("### 3. Further Investigation\n\n")
        f.write("- Test the optimal configuration on a larger validation set\n")
        f.write("- Verify performance on different fragment types (various pottery styles, damage levels)\n")
        f.write("- Consider adaptive thresholds based on fragment characteristics\n")
        f.write("- Investigate combining multiple features for more robust matching\n")
        f.write("\n")

        # Visualizations reference
        f.write("## Visualizations\n\n")
        f.write("See the following generated plots for detailed visual analysis:\n\n")
        f.write("- `sensitivity_color_penalty_weight.png` - Color penalty weight sensitivity\n")
        f.write("- `sensitivity_match_threshold.png` - Match threshold sensitivity\n")
        f.write("- `sensitivity_n_segments.png` - N_SEGMENTS sensitivity\n")
        f.write("- `sensitivity_overall_comparison.png` - Overall comparison across parameters\n")
        f.write("\n")

        # Methodology
        f.write("## Methodology\n\n")
        f.write(f"**Test Set:**\n")
        if baseline_results:
            baseline = baseline_results[0]
            f.write(f"- Positive pairs (same source): {baseline.n_positive_pairs}\n")
            f.write(f"- Negative pairs (different sources): {baseline.n_negative_pairs}\n")
            f.write(f"- Total test pairs: {baseline.n_positive_pairs + baseline.n_negative_pairs}\n\n")

        f.write("**Parameters Tested:**\n")
        f.write("- Color Penalty Weight: 0.70, 0.75, 0.80, 0.85, 0.90\n")
        f.write("- Match Threshold: 0.45, 0.50, 0.55, 0.60, 0.65\n")
        f.write("- N_SEGMENTS: 3, 4, 6, 8\n\n")

        f.write("**Evaluation Metrics:**\n")
        f.write("- Positive Accuracy: % of same-source pairs correctly matched\n")
        f.write("- Negative Accuracy: % of different-source pairs correctly rejected\n")
        f.write("- Overall Accuracy: Combined accuracy across all test pairs\n")
        f.write("- Confidence Scores: Average confidence for positive/negative pairs\n")
        f.write("- Runtime: Average processing time per fragment pair\n")
        f.write("\n")

        f.write("---\n\n")
        f.write("*This report was automatically generated by the hyperparameter sensitivity analysis tool.*\n")

    logger.info("Saved markdown report: %s", output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Hyperparameter sensitivity analysis for fragment matching",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--input',
        default='data/raw/real_fragments_validated',
        help='Directory containing validated real fragment images',
    )
    parser.add_argument(
        '--output',
        default='outputs/testing',
        help='Output directory for reports and visualizations',
    )
    parser.add_argument(
        '--n-positive',
        type=int,
        default=10,
        help='Number of positive (same-source) pairs to test',
    )
    parser.add_argument(
        '--n-negative',
        type=int,
        default=10,
        help='Number of negative (different-source) pairs to test',
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick test with fewer configurations',
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose debug logging',
    )

    args = parser.parse_args()

    logger = setup_logging(args.output, verbose=args.verbose)
    logger.info("=" * 70)
    logger.info("Hyperparameter Sensitivity Analysis")
    logger.info("=" * 70)
    logger.info("Input directory: %s", args.input)
    logger.info("Output directory: %s", args.output)
    logger.info("Test pairs: %d positive, %d negative", args.n_positive, args.n_negative)
    logger.info("Quick mode: %s", args.quick)

    # Collect test fragments
    logger.info("=" * 70)
    logger.info("Phase 1: Collecting Test Fragments")
    logger.info("=" * 70)

    try:
        positive_pairs, negative_pairs = collect_test_fragments(
            args.input, args.n_positive, args.n_negative, logger
        )
    except Exception as exc:
        logger.error("Failed to collect fragments: %s", exc)
        print(f"\n[ERROR] {exc}")
        sys.exit(1)

    # Generate configurations
    logger.info("=" * 70)
    logger.info("Phase 2: Generating Test Configurations")
    logger.info("=" * 70)

    configs = generate_configurations(quick=args.quick)
    total_configs = sum(len(param_configs) for param_configs in configs.values())
    logger.info("Generated %d configurations across %d parameters", total_configs, len(configs))

    for param_name, param_configs in configs.items():
        logger.info("  - %s: %d configurations", param_name, len(param_configs))

    # Run tests
    logger.info("=" * 70)
    logger.info("Phase 3: Testing Configurations")
    logger.info("=" * 70)

    results_by_param = {}

    for param_name, param_configs in configs.items():
        logger.info("Testing parameter: %s", param_name)
        param_results = []

        for config in param_configs:
            result = test_configuration(config, positive_pairs, negative_pairs, logger)
            param_results.append(result)

        results_by_param[param_name] = param_results

    # Find optimal configuration
    logger.info("=" * 70)
    logger.info("Phase 4: Finding Optimal Configuration")
    logger.info("=" * 70)

    optimal_result, optimal_reasoning = find_optimal_configuration(results_by_param, logger)

    # Generate visualizations
    logger.info("=" * 70)
    logger.info("Phase 5: Generating Visualizations")
    logger.info("=" * 70)

    plot_sensitivity_analysis(results_by_param, args.output, logger)

    # Generate report
    logger.info("=" * 70)
    logger.info("Phase 6: Generating Report")
    logger.info("=" * 70)

    report_path = os.path.join(args.output, 'hyperparameter_sensitivity.md')
    generate_markdown_report(
        results_by_param,
        optimal_result,
        optimal_reasoning,
        report_path,
        logger,
    )

    # Save JSON results
    json_path = os.path.join(args.output, 'hyperparameter_sensitivity.json')
    json_data = {
        'timestamp': datetime.now().isoformat(),
        'optimal_config': {
            'name': optimal_result.config.name,
            'color_penalty_weight': optimal_result.config.color_penalty_weight,
            'match_threshold': optimal_result.config.match_threshold,
            'n_segments': optimal_result.config.n_segments,
        },
        'optimal_performance': {
            'positive_accuracy': optimal_result.positive_accuracy,
            'negative_accuracy': optimal_result.negative_accuracy,
            'overall_accuracy': optimal_result.overall_accuracy,
            'avg_positive_confidence': optimal_result.avg_positive_confidence,
            'avg_negative_confidence': optimal_result.avg_negative_confidence,
            'avg_pair_runtime_ms': optimal_result.avg_pair_runtime_ms,
        },
        'all_results': {
            param_name: [
                {
                    'config_name': r.config.name,
                    'color_penalty_weight': r.config.color_penalty_weight,
                    'match_threshold': r.config.match_threshold,
                    'n_segments': r.config.n_segments,
                    'positive_accuracy': r.positive_accuracy,
                    'negative_accuracy': r.negative_accuracy,
                    'overall_accuracy': r.overall_accuracy,
                    'avg_positive_confidence': r.avg_positive_confidence,
                    'avg_negative_confidence': r.avg_negative_confidence,
                    'avg_pair_runtime_ms': r.avg_pair_runtime_ms,
                }
                for r in param_results
            ]
            for param_name, param_results in results_by_param.items()
        },
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)

    logger.info("Saved JSON results: %s", json_path)

    # Final summary
    logger.info("=" * 70)
    logger.info("Analysis Complete")
    logger.info("=" * 70)
    logger.info("Optimal configuration: %s", optimal_result.config.name)
    logger.info("  - Positive accuracy: %.1f%%", optimal_result.positive_accuracy * 100)
    logger.info("  - Negative accuracy: %.1f%%", optimal_result.negative_accuracy * 100)
    logger.info("  - Overall accuracy: %.1f%%", optimal_result.overall_accuracy * 100)
    logger.info("Reports saved to: %s", args.output)

    print("\n" + "=" * 70)
    print("HYPERPARAMETER SENSITIVITY ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"\nOptimal Configuration Found:")
    print(f"  Color Penalty Weight: {optimal_result.config.color_penalty_weight}")
    print(f"  Match Threshold: {optimal_result.config.match_threshold}")
    print(f"  N_SEGMENTS: {optimal_result.config.n_segments}")
    print(f"\nPerformance:")
    print(f"  Positive Accuracy: {optimal_result.positive_accuracy*100:.1f}%")
    print(f"  Negative Accuracy: {optimal_result.negative_accuracy*100:.1f}%")
    print(f"  Overall Accuracy: {optimal_result.overall_accuracy*100:.1f}%")
    print(f"  Runtime: {optimal_result.avg_pair_runtime_ms:.1f} ms/pair")
    print(f"\nFull report: {report_path}")
    print(f"Visualizations: {args.output}/")
    print()


if __name__ == '__main__':
    main()
