#!/usr/bin/env python3
"""
test_negative_cases.py
----------------------
Comprehensive negative case testing for cross-source fragment rejection.

Mission: Test the system's ability to correctly reject fragment pairs from
different sources (different archaeological artifacts). Measures false positive
rate and analyzes patterns in incorrect matches.

Test Setup:
- 26 fragments from wikimedia_processed (same source)
- 20 fragments from wikimedia (different sources)
- 2 fragments from british_museum
- Generate ALL cross-source pairs (should be rejected)
- Run full pipeline and measure rejection accuracy

Outputs:
- False positive rate (incorrectly matched cross-source pairs)
- True negative rate (correctly rejected cross-source pairs)
- Confidence score distribution for all pairs
- Color BC distribution for cross-source pairs
- Detailed analysis of false positive cases
- Report: outputs/testing/negative_case_analysis.md

Usage:
    python scripts/test_negative_cases.py
    python scripts/test_negative_cases.py --verbose
    python scripts/test_negative_cases.py --max-pairs 100

Dependencies: opencv-python, numpy, matplotlib, scipy
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
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import cv2
import matplotlib.pyplot as plt
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from preprocessing import preprocess_fragment
from chain_code import encode_fragment, contour_to_pixel_segments
from compatibility import build_compatibility_matrix, compute_color_signature, color_bhattacharyya
from relaxation import run_relaxation, extract_top_assemblies
from shape_descriptors import pca_normalize_contour

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.jfif', '.webp'}
N_SEGMENTS = 4
N_TOP_ASSEMBLIES = 3

# Match thresholds (from relaxation.py)
MATCH_SCORE_THRESHOLD = 0.55
WEAK_MATCH_SCORE_THRESHOLD = 0.35
ASSEMBLY_CONFIDENCE_THRESHOLD = 0.45


@dataclass
class FragmentInfo:
    """Information about a single fragment."""
    path: Path
    name: str
    source: str
    image: Optional[np.ndarray] = None
    contour: Optional[np.ndarray] = None
    contour_norm: Optional[np.ndarray] = None
    segments: Optional[List] = None
    pixel_segments: Optional[List] = None
    color_signature: Optional[np.ndarray] = None
    preprocessing_success: bool = False
    error: Optional[str] = None


@dataclass
class NegativePairResult:
    """Results from testing a negative pair (cross-source)."""
    frag_a_name: str
    frag_b_name: str
    source_a: str
    source_b: str
    verdict: str  # "MATCH", "WEAK_MATCH", "NO_MATCH"
    confidence: float
    color_bc: float
    is_false_positive: bool  # True if verdict is MATCH or WEAK_MATCH
    execution_time_ms: float
    top_assembly: Optional[Dict[str, Any]] = None


@dataclass
class NegativeTestSummary:
    """Overall negative test summary."""
    n_sources: int = 0
    n_fragments_total: int = 0
    n_fragments_processed: int = 0
    n_preprocessing_failed: int = 0

    n_negative_pairs_tested: int = 0
    n_true_negatives: int = 0  # Correctly rejected
    n_false_positives: int = 0  # Incorrectly matched

    true_negative_rate: float = 0.0  # Should be ~100%
    false_positive_rate: float = 0.0  # Should be ~0%

    avg_confidence: float = 0.0
    median_confidence: float = 0.0
    avg_color_bc: float = 0.0
    median_color_bc: float = 0.0

    false_positive_results: List[NegativePairResult] = field(default_factory=list)
    all_results: List[NegativePairResult] = field(default_factory=list)

    fragments_by_source: Dict[str, List[FragmentInfo]] = field(default_factory=dict)


def setup_logging(output_dir: str, verbose: bool = False) -> logging.Logger:
    """Configure logging with timestamped file and console output."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = os.path.join(output_dir, f'negative_case_test_{timestamp}.log')

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
    logger = logging.getLogger('test_negative_cases')
    logger.info("Log file: %s", log_path)
    return logger


def collect_fragments_by_source(
    base_dir: str,
    logger: logging.Logger,
) -> Dict[str, List[Path]]:
    """
    Collect fragments organized by source directory.

    Expected structure:
        base_dir/
            wikimedia_processed/
                frag_001.jpg
                frag_002.jpg
            wikimedia/
                frag_a.jpg
                frag_b.jpg
            british_museum/
                frag_x.jpg

    Returns dict mapping source_name -> list of fragment paths
    """
    base_path = Path(base_dir)
    fragments_by_source = {}

    for source_dir in sorted(base_path.iterdir()):
        if not source_dir.is_dir():
            continue

        # Skip subdirectories and metadata files
        if source_dir.name in ['example1_auto', 'wikimedia']:
            continue

        images = sorted(
            p for p in source_dir.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        )

        if images:
            source_name = source_dir.name
            fragments_by_source[source_name] = images
            logger.info("Found %d fragments in source '%s'", len(images), source_name)

    return fragments_by_source


def preprocess_fragment_safe(
    frag_path: Path,
    source: str,
    logger: logging.Logger,
) -> FragmentInfo:
    """
    Safely preprocess a fragment and return FragmentInfo.

    Captures any errors and returns them in the FragmentInfo structure.
    """
    frag_info = FragmentInfo(
        path=frag_path,
        name=frag_path.stem,
        source=source,
    )

    try:
        image, contour = preprocess_fragment(str(frag_path))
        contour_norm = pca_normalize_contour(contour)
        _, segments = encode_fragment(contour_norm, n_segments=N_SEGMENTS)
        pixel_segs = contour_to_pixel_segments(contour, N_SEGMENTS)
        color_sig = compute_color_signature(image)

        frag_info.image = image
        frag_info.contour = contour
        frag_info.contour_norm = contour_norm
        frag_info.segments = segments
        frag_info.pixel_segments = pixel_segs
        frag_info.color_signature = color_sig
        frag_info.preprocessing_success = True

        logger.debug(
            "[OK] %s - %d contour points",
            frag_info.name, len(contour),
        )

    except Exception as exc:
        frag_info.preprocessing_success = False
        frag_info.error = str(exc)
        logger.warning(
            "[FAIL] %s - preprocessing failed: %s",
            frag_info.name, frag_info.error,
        )

    return frag_info


def test_negative_pair(
    frag_a: FragmentInfo,
    frag_b: FragmentInfo,
    logger: logging.Logger,
) -> Optional[NegativePairResult]:
    """
    Test a negative pair (cross-source) through the full pipeline.

    Returns NegativePairResult with verdict and confidence, or None if
    either fragment failed preprocessing.
    """
    if not frag_a.preprocessing_success or not frag_b.preprocessing_success:
        return None

    start_time = time.time()

    try:
        # Compute color similarity
        color_bc = float(color_bhattacharyya(frag_a.color_signature, frag_b.color_signature))

        # Build compatibility matrix
        all_segments = [frag_a.segments, frag_b.segments]
        all_pixel_segs = [frag_a.pixel_segments, frag_b.pixel_segments]
        images = [frag_a.image, frag_b.image]

        compat_matrix = build_compatibility_matrix(all_segments, all_pixel_segs, images)

        # Run relaxation labeling
        probs, trace = run_relaxation(compat_matrix)

        # Extract top assembly
        assemblies = extract_top_assemblies(
            probs, n_top=N_TOP_ASSEMBLIES, compat_matrix=compat_matrix
        )

        verdict = "NO_MATCH"
        confidence = 0.0
        top_assembly = None

        if assemblies:
            top = assemblies[0]
            verdict = top['verdict']
            confidence = top['confidence']
            top_assembly = top

        execution_time_ms = (time.time() - start_time) * 1000

        # This is a NEGATIVE pair (different sources)
        # So it should be rejected (NO_MATCH)
        is_false_positive = (verdict in ['MATCH', 'WEAK_MATCH'])

        result = NegativePairResult(
            frag_a_name=frag_a.name,
            frag_b_name=frag_b.name,
            source_a=frag_a.source,
            source_b=frag_b.source,
            verdict=verdict,
            confidence=confidence,
            color_bc=color_bc,
            is_false_positive=is_false_positive,
            execution_time_ms=execution_time_ms,
            top_assembly=top_assembly,
        )

        status = "[FAIL-FP]" if is_false_positive else "[OK-TN]"
        logger.info(
            "%s %s <-> %s (%s vs %s) - verdict=%s, conf=%.3f, color_BC=%.3f, %.0f ms",
            status, frag_a.name, frag_b.name, frag_a.source, frag_b.source,
            verdict, confidence, color_bc, execution_time_ms,
        )

        return result

    except Exception as exc:
        logger.warning(
            "[ERROR] %s <-> %s - pipeline failed: %s",
            frag_a.name, frag_b.name, str(exc),
        )
        return None


def generate_cross_source_pairs(
    fragments_by_source: Dict[str, List[FragmentInfo]],
    max_pairs: Optional[int],
    logger: logging.Logger,
) -> List[Tuple[FragmentInfo, FragmentInfo]]:
    """
    Generate all cross-source pairs (negative cases).

    These are pairs where the two fragments come from different sources
    and should be rejected by the system.

    If max_pairs is set, returns a random sample of that size.
    """
    negative_pairs = []
    sources = list(fragments_by_source.keys())

    for i in range(len(sources)):
        for j in range(i + 1, len(sources)):
            source_a = sources[i]
            source_b = sources[j]

            frags_a = fragments_by_source[source_a]
            frags_b = fragments_by_source[source_b]

            # All pairs between these two sources
            for frag_a in frags_a:
                for frag_b in frags_b:
                    negative_pairs.append((frag_a, frag_b))

    logger.info("Generated %d cross-source pairs (all should be rejected)", len(negative_pairs))

    # Optionally limit the number of pairs
    if max_pairs and len(negative_pairs) > max_pairs:
        import random
        random.seed(42)
        negative_pairs = random.sample(negative_pairs, max_pairs)
        logger.info("Limited to %d pairs for testing", max_pairs)

    return negative_pairs


def compute_summary_statistics(
    fragments_by_source: Dict[str, List[FragmentInfo]],
    pair_results: List[NegativePairResult],
) -> NegativeTestSummary:
    """Compute overall negative test summary statistics."""
    summary = NegativeTestSummary()

    summary.fragments_by_source = fragments_by_source
    summary.n_sources = len(fragments_by_source)
    summary.n_fragments_total = sum(len(frags) for frags in fragments_by_source.values())
    summary.n_fragments_processed = sum(
        sum(1 for f in frags if f.preprocessing_success)
        for frags in fragments_by_source.values()
    )
    summary.n_preprocessing_failed = summary.n_fragments_total - summary.n_fragments_processed

    summary.all_results = pair_results
    summary.n_negative_pairs_tested = len(pair_results)

    summary.n_true_negatives = sum(1 for r in pair_results if not r.is_false_positive)
    summary.n_false_positives = sum(1 for r in pair_results if r.is_false_positive)

    summary.true_negative_rate = (
        summary.n_true_negatives / summary.n_negative_pairs_tested
        if summary.n_negative_pairs_tested > 0 else 0.0
    )
    summary.false_positive_rate = (
        summary.n_false_positives / summary.n_negative_pairs_tested
        if summary.n_negative_pairs_tested > 0 else 0.0
    )

    confidences = [r.confidence for r in pair_results]
    color_bcs = [r.color_bc for r in pair_results]

    summary.avg_confidence = np.mean(confidences) if confidences else 0.0
    summary.median_confidence = np.median(confidences) if confidences else 0.0
    summary.avg_color_bc = np.mean(color_bcs) if color_bcs else 0.0
    summary.median_color_bc = np.median(color_bcs) if color_bcs else 0.0

    summary.false_positive_results = [r for r in pair_results if r.is_false_positive]

    return summary


def generate_visualizations(
    summary: NegativeTestSummary,
    output_dir: str,
    logger: logging.Logger,
) -> None:
    """Generate analysis plots and visualizations."""
    os.makedirs(output_dir, exist_ok=True)

    # 1. True Negative vs False Positive Rate
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))

    categories = ['True Negatives\n(Correctly Rejected)', 'False Positives\n(Incorrectly Matched)']
    rates = [summary.true_negative_rate * 100, summary.false_positive_rate * 100]
    colors = ['#2ecc71', '#e74c3c']

    bars = ax.bar(categories, rates, color=colors)
    ax.set_ylabel('Rate (%)', fontsize=12)
    ax.set_title('Negative Case Performance (Cross-Source Rejection)', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 105)

    for bar, rate in zip(bars, rates):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2., height + 1,
            f'{height:.1f}%\n({int(rate * summary.n_negative_pairs_tested / 100)}/{summary.n_negative_pairs_tested})',
            ha='center', va='bottom', fontsize=10, fontweight='bold'
        )

    ax.axhline(100, color='gray', linestyle='--', alpha=0.5, label='Target: 100% rejection')
    ax.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'negative_case_performance.png'), dpi=150)
    plt.close()
    logger.info("Saved negative_case_performance.png")

    # 2. Confidence score distribution
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    tn_confs = [r.confidence for r in summary.all_results if not r.is_false_positive]
    fp_confs = [r.confidence for r in summary.all_results if r.is_false_positive]

    if tn_confs:
        ax.hist(tn_confs, bins=30, alpha=0.7, label='True Negatives (correctly rejected)',
               color='#2ecc71', edgecolor='black')
    if fp_confs:
        ax.hist(fp_confs, bins=30, alpha=0.7, label='False Positives (incorrectly matched)',
               color='#e74c3c', edgecolor='black')

    ax.axvline(MATCH_SCORE_THRESHOLD, color='red', linestyle='--', linewidth=2,
              label=f'MATCH threshold ({MATCH_SCORE_THRESHOLD})')
    ax.axvline(WEAK_MATCH_SCORE_THRESHOLD, color='orange', linestyle='--', linewidth=2,
              label=f'WEAK_MATCH threshold ({WEAK_MATCH_SCORE_THRESHOLD})')

    ax.set_xlabel('Confidence Score', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('Confidence Score Distribution: Cross-Source Pairs', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'confidence_distribution.png'), dpi=150)
    plt.close()
    logger.info("Saved confidence_distribution.png")

    # 3. Color BC distribution
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    tn_colors = [r.color_bc for r in summary.all_results if not r.is_false_positive]
    fp_colors = [r.color_bc for r in summary.all_results if r.is_false_positive]

    if tn_colors:
        ax.hist(tn_colors, bins=30, alpha=0.7, label='True Negatives',
               color='#2ecc71', edgecolor='black')
    if fp_colors:
        ax.hist(fp_colors, bins=30, alpha=0.7, label='False Positives',
               color='#e74c3c', edgecolor='black')

    ax.set_xlabel('Color Bhattacharyya Coefficient', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('Color Similarity Distribution: Cross-Source Pairs', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'color_bc_distribution.png'), dpi=150)
    plt.close()
    logger.info("Saved color_bc_distribution.png")

    # 4. Color BC vs Confidence scatter plot
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    for result in summary.all_results:
        if result.is_false_positive:
            color = '#e74c3c'
            marker = 'x'
            label = 'False Positive'
            size = 150
            zorder = 10
        else:
            color = '#2ecc71'
            marker = 'o'
            label = 'True Negative'
            size = 50
            zorder = 5

        # Avoid duplicate labels
        if ax.collections and label in [t.get_label() for t in ax.collections]:
            label = None

        ax.scatter(
            result.color_bc, result.confidence,
            c=color, marker=marker, s=size, alpha=0.6,
            edgecolors='black', linewidths=1.5, label=label, zorder=zorder
        )

    ax.axhline(MATCH_SCORE_THRESHOLD, color='red', linestyle='--', alpha=0.7,
              label=f'MATCH threshold ({MATCH_SCORE_THRESHOLD})')
    ax.axhline(WEAK_MATCH_SCORE_THRESHOLD, color='orange', linestyle='--', alpha=0.7,
              label=f'WEAK_MATCH threshold ({WEAK_MATCH_SCORE_THRESHOLD})')

    ax.set_xlabel('Color Similarity (Bhattacharyya Coefficient)', fontsize=12)
    ax.set_ylabel('Geometric Confidence Score', fontsize=12)
    ax.set_title('Color vs Geometric Similarity: Cross-Source Pairs', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'color_vs_geometric_scatter.png'), dpi=150)
    plt.close()
    logger.info("Saved color_vs_geometric_scatter.png")

    # 5. Verdict distribution
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))

    verdict_counts = defaultdict(int)
    for result in summary.all_results:
        verdict_counts[result.verdict] += 1

    verdicts = list(verdict_counts.keys())
    counts = [verdict_counts[v] for v in verdicts]
    colors_map = {
        'NO_MATCH': '#2ecc71',
        'WEAK_MATCH': '#f39c12',
        'MATCH': '#e74c3c',
    }
    bar_colors = [colors_map.get(v, '#95a5a6') for v in verdicts]

    bars = ax.bar(verdicts, counts, color=bar_colors, edgecolor='black', linewidth=1.5)
    ax.set_ylabel('Count', fontsize=12)
    ax.set_title('Verdict Distribution: Cross-Source Pairs', fontsize=14, fontweight='bold')

    for bar, count in zip(bars, counts):
        height = bar.get_height()
        percentage = (count / summary.n_negative_pairs_tested) * 100
        ax.text(
            bar.get_x() + bar.get_width()/2., height + 0.5,
            f'{count}\n({percentage:.1f}%)',
            ha='center', va='bottom', fontsize=10, fontweight='bold'
        )

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'verdict_distribution.png'), dpi=150)
    plt.close()
    logger.info("Saved verdict_distribution.png")


def generate_markdown_report(
    summary: NegativeTestSummary,
    output_path: str,
    logger: logging.Logger,
) -> None:
    """Generate a comprehensive human-readable markdown report."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Negative Case Analysis Report\n\n")
        f.write("## Cross-Source Fragment Rejection Testing\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("---\n\n")

        f.write("## Executive Summary\n\n")
        f.write(f"- **Mission:** Test cross-source fragment rejection (negative cases)\n")
        f.write(f"- **Sources Tested:** {summary.n_sources}\n")
        f.write(f"- **Fragments Collected:** {summary.n_fragments_total}\n")
        f.write(f"- **Fragments Successfully Preprocessed:** {summary.n_fragments_processed}\n")
        f.write(f"- **Negative Pairs Tested:** {summary.n_negative_pairs_tested}\n\n")

        f.write("### Key Results\n\n")
        f.write(f"- **True Negative Rate (Correctly Rejected):** {summary.true_negative_rate*100:.2f}%\n")
        f.write(f"- **False Positive Rate (Incorrectly Matched):** {summary.false_positive_rate*100:.2f}%\n")
        f.write(f"- **False Positives:** {summary.n_false_positives}/{summary.n_negative_pairs_tested}\n")
        f.write(f"- **True Negatives:** {summary.n_true_negatives}/{summary.n_negative_pairs_tested}\n\n")

        # Performance assessment
        if summary.false_positive_rate == 0.0:
            f.write("**EXCELLENT:** 0% false positive rate - perfect cross-source rejection!\n\n")
        elif summary.false_positive_rate < 0.05:
            f.write("**VERY GOOD:** <5% false positive rate - highly reliable rejection.\n\n")
        elif summary.false_positive_rate < 0.10:
            f.write("**GOOD:** <10% false positive rate - acceptable rejection performance.\n\n")
        elif summary.false_positive_rate < 0.20:
            f.write("**MODERATE:** 10-20% false positive rate - needs threshold tuning.\n\n")
        else:
            f.write("**NEEDS IMPROVEMENT:** >20% false positive rate - significant issues with rejection.\n\n")

        f.write("---\n\n")

        f.write("## Data Collection\n\n")
        f.write("### Fragments by Source\n\n")
        f.write("| Source | Total Fragments | Preprocessed | Failed |\n")
        f.write("|--------|-----------------|--------------|--------|\n")
        for source, frags in sorted(summary.fragments_by_source.items()):
            n_total = len(frags)
            n_success = sum(1 for f in frags if f.preprocessing_success)
            n_failed = n_total - n_success
            f.write(f"| {source} | {n_total} | {n_success} | {n_failed} |\n")
        f.write("\n")

        f.write("### Test Design\n\n")
        f.write("All pairs are **negative cases** (cross-source) and should be rejected:\n")
        f.write(f"- Total cross-source pairs generated: {summary.n_negative_pairs_tested}\n")
        f.write("- Expected result: NO_MATCH verdict for all pairs\n")
        f.write("- Success metric: High true negative rate (>95%)\n\n")

        f.write("---\n\n")

        f.write("## Performance Results\n\n")
        f.write("### Overall Metrics\n\n")
        f.write(f"- **True Negative Rate:** {summary.true_negative_rate*100:.2f}% ({summary.n_true_negatives}/{summary.n_negative_pairs_tested})\n")
        f.write(f"- **False Positive Rate:** {summary.false_positive_rate*100:.2f}% ({summary.n_false_positives}/{summary.n_negative_pairs_tested})\n\n")

        f.write("### Confidence Statistics\n\n")
        f.write(f"- **Average Confidence:** {summary.avg_confidence:.4f}\n")
        f.write(f"- **Median Confidence:** {summary.median_confidence:.4f}\n")
        f.write(f"- **Average Color BC:** {summary.avg_color_bc:.4f}\n")
        f.write(f"- **Median Color BC:** {summary.median_color_bc:.4f}\n\n")

        f.write("### Comparison to Benchmark\n\n")
        f.write("**Benchmark (Expected):**\n")
        f.write("- Negative accuracy: 100% (0/36 false positives)\n")
        f.write("- False positive rate: 0%\n\n")
        f.write("**Current System:**\n")
        f.write(f"- Negative accuracy: {summary.true_negative_rate*100:.2f}%\n")
        f.write(f"- False positive rate: {summary.false_positive_rate*100:.2f}%\n\n")

        if summary.false_positive_rate > 0:
            improvement = (1.0 - summary.true_negative_rate) * 100
            f.write(f"**Gap from benchmark:** {improvement:.2f} percentage points\n\n")

        f.write("---\n\n")

        f.write("## False Positive Analysis\n\n")

        if summary.n_false_positives == 0:
            f.write("**NO FALSE POSITIVES DETECTED!**\n\n")
            f.write("The system correctly rejected all cross-source pairs. Excellent performance!\n\n")
        else:
            f.write(f"**{summary.n_false_positives} false positives detected** (pairs incorrectly matched):\n\n")

            f.write("### False Positive Details\n\n")
            f.write("| Fragment A | Fragment B | Source A | Source B | Verdict | Confidence | Color BC |\n")
            f.write("|------------|------------|----------|----------|---------|------------|----------|\n")

            # Sort false positives by confidence (highest first)
            sorted_fps = sorted(summary.false_positive_results, key=lambda r: r.confidence, reverse=True)
            for result in sorted_fps:
                f.write(
                    f"| {result.frag_a_name} | {result.frag_b_name} | "
                    f"{result.source_a} | {result.source_b} | "
                    f"{result.verdict} | {result.confidence:.4f} | {result.color_bc:.4f} |\n"
                )
            f.write("\n")

            f.write("### False Positive Patterns\n\n")

            # Analyze confidence distribution of false positives
            fp_confidences = [r.confidence for r in summary.false_positive_results]
            fp_color_bcs = [r.color_bc for r in summary.false_positive_results]

            f.write(f"- **Highest false positive confidence:** {max(fp_confidences):.4f}\n")
            f.write(f"- **Lowest false positive confidence:** {min(fp_confidences):.4f}\n")
            f.write(f"- **Average false positive confidence:** {np.mean(fp_confidences):.4f}\n")
            f.write(f"- **Average false positive color BC:** {np.mean(fp_color_bcs):.4f}\n\n")

            # Analyze by verdict type
            fp_by_verdict = defaultdict(int)
            for result in summary.false_positive_results:
                fp_by_verdict[result.verdict] += 1

            f.write("**False positives by verdict:**\n")
            for verdict, count in sorted(fp_by_verdict.items()):
                f.write(f"- {verdict}: {count}\n")
            f.write("\n")

            # Analyze by source combination
            fp_by_source_pair = defaultdict(int)
            for result in summary.false_positive_results:
                pair = tuple(sorted([result.source_a, result.source_b]))
                fp_by_source_pair[pair] += 1

            f.write("**False positives by source combination:**\n")
            for (src_a, src_b), count in sorted(fp_by_source_pair.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- {src_a} vs {src_b}: {count}\n")
            f.write("\n")

        f.write("---\n\n")

        f.write("## True Negative Analysis\n\n")
        f.write(f"**{summary.n_true_negatives} pairs correctly rejected.**\n\n")

        tn_results = [r for r in summary.all_results if not r.is_false_positive]
        if tn_results:
            tn_confidences = [r.confidence for r in tn_results]
            tn_color_bcs = [r.color_bc for r in tn_results]

            f.write("### True Negative Statistics\n\n")
            f.write(f"- **Average confidence:** {np.mean(tn_confidences):.4f}\n")
            f.write(f"- **Median confidence:** {np.median(tn_confidences):.4f}\n")
            f.write(f"- **Max confidence:** {max(tn_confidences):.4f}\n")
            f.write(f"- **Average color BC:** {np.mean(tn_color_bcs):.4f}\n")
            f.write(f"- **Median color BC:** {np.median(tn_color_bcs):.4f}\n\n")

            # Check how close true negatives came to false positive threshold
            near_misses = [r for r in tn_results if r.confidence >= 0.30]
            if near_misses:
                f.write(f"### Near Misses\n\n")
                f.write(f"**{len(near_misses)} true negatives** had confidence >= 0.30 (close to WEAK_MATCH threshold 0.35):\n\n")

                # Show top 10 closest
                sorted_near_misses = sorted(near_misses, key=lambda r: r.confidence, reverse=True)[:10]
                f.write("| Fragment A | Fragment B | Source A | Source B | Confidence | Color BC |\n")
                f.write("|------------|------------|----------|----------|------------|----------|\n")
                for result in sorted_near_misses:
                    f.write(
                        f"| {result.frag_a_name} | {result.frag_b_name} | "
                        f"{result.source_a} | {result.source_b} | "
                        f"{result.confidence:.4f} | {result.color_bc:.4f} |\n"
                    )
                f.write("\n")

        f.write("---\n\n")

        f.write("## Color Similarity Analysis\n\n")

        all_color_bcs = [r.color_bc for r in summary.all_results]
        f.write(f"- **Average Color BC (all pairs):** {np.mean(all_color_bcs):.4f}\n")
        f.write(f"- **Median Color BC (all pairs):** {np.median(all_color_bcs):.4f}\n")
        f.write(f"- **Min Color BC:** {min(all_color_bcs):.4f}\n")
        f.write(f"- **Max Color BC:** {max(all_color_bcs):.4f}\n\n")

        f.write("**Insight:** Cross-source pairs should have LOW color BC (different appearance). ")
        f.write("If color BC is high but pairs are correctly rejected, the geometric features are ")
        f.write("working well to distinguish different sources.\n\n")

        f.write("---\n\n")

        f.write("## Recommendations\n\n")

        if summary.false_positive_rate == 0.0:
            f.write("### Current System Performance: EXCELLENT\n\n")
            f.write("The system achieves 0% false positive rate on cross-source pairs. ")
            f.write("No threshold adjustments needed.\n\n")
            f.write("**Strengths:**\n")
            f.write("- Perfect rejection of cross-source pairs\n")
            f.write("- Color and geometric features working well together\n")
            f.write("- Threshold settings are appropriate\n\n")

        elif summary.false_positive_rate < 0.05:
            f.write("### Current System Performance: VERY GOOD\n\n")
            f.write("The system achieves <5% false positive rate. Minor improvements possible.\n\n")
            f.write("**Suggestions:**\n")
            f.write("- Analyze the few false positives for common patterns\n")
            f.write("- Consider minor threshold adjustments if needed\n")
            f.write("- Current performance is production-ready\n\n")

        elif summary.false_positive_rate < 0.20:
            f.write("### Current System Performance: MODERATE\n\n")
            f.write("The system shows some false positives. Threshold tuning recommended.\n\n")
            f.write("**Recommendations:**\n")
            f.write("1. **Increase MATCH_SCORE_THRESHOLD** from 0.55 to 0.60 or 0.65\n")
            f.write("2. **Increase WEAK_MATCH_SCORE_THRESHOLD** from 0.35 to 0.40\n")
            f.write("3. **Increase COLOR_PENALTY_WEIGHT** to penalize dissimilar colors more heavily\n")
            f.write("4. Analyze false positives to identify if certain source combinations are problematic\n\n")

        else:
            f.write("### Current System Performance: NEEDS IMPROVEMENT\n\n")
            f.write("The system shows significant false positive rate. Major adjustments needed.\n\n")
            f.write("**Recommendations:**\n")
            f.write("1. **Significantly increase matching thresholds:**\n")
            f.write("   - MATCH_SCORE_THRESHOLD: 0.55 → 0.70\n")
            f.write("   - WEAK_MATCH_SCORE_THRESHOLD: 0.35 → 0.50\n")
            f.write("2. **Strengthen color filtering:**\n")
            f.write("   - Increase COLOR_PENALTY_WEIGHT from 0.80 to 0.90\n")
            f.write("   - Consider adding stricter color pre-filtering\n")
            f.write("3. **Review geometric features:**\n")
            f.write("   - Check if curvature profiles are too permissive\n")
            f.write("   - Consider adding additional discriminative features\n")
            f.write("4. **Analyze false positive patterns:**\n")
            f.write("   - Identify which source combinations are problematic\n")
            f.write("   - Check if certain fragment types are causing issues\n\n")

        f.write("### General Recommendations\n\n")
        f.write("1. **Rerun with adjusted thresholds** and compare false positive rates\n")
        f.write("2. **Test on positive cases** to ensure changes don't hurt true positive rate\n")
        f.write("3. **Balance false positive vs false negative rates** for optimal performance\n")
        f.write("4. **Consider source-specific features** if certain combinations are problematic\n\n")

        f.write("---\n\n")

        f.write("## Visualizations\n\n")
        f.write("Generated plots (see `outputs/testing/` directory):\n\n")
        f.write("- `negative_case_performance.png` - True negative vs false positive rates\n")
        f.write("- `confidence_distribution.png` - Confidence score histogram\n")
        f.write("- `color_bc_distribution.png` - Color similarity histogram\n")
        f.write("- `color_vs_geometric_scatter.png` - Color BC vs confidence scatter plot\n")
        f.write("- `verdict_distribution.png` - Verdict type breakdown\n\n")

        f.write("---\n\n")
        f.write("*End of Report*\n")

    logger.info("Saved markdown report: %s", output_path)


def generate_json_report(
    summary: NegativeTestSummary,
    output_path: str,
    logger: logging.Logger,
) -> None:
    """Generate a machine-readable JSON report."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'test_type': 'negative_case_cross_source_rejection',
        'summary': {
            'n_sources': summary.n_sources,
            'n_fragments_total': summary.n_fragments_total,
            'n_fragments_processed': summary.n_fragments_processed,
            'n_preprocessing_failed': summary.n_preprocessing_failed,
            'n_negative_pairs_tested': summary.n_negative_pairs_tested,
            'n_true_negatives': summary.n_true_negatives,
            'n_false_positives': summary.n_false_positives,
            'true_negative_rate': summary.true_negative_rate,
            'false_positive_rate': summary.false_positive_rate,
            'avg_confidence': summary.avg_confidence,
            'median_confidence': summary.median_confidence,
            'avg_color_bc': summary.avg_color_bc,
            'median_color_bc': summary.median_color_bc,
        },
        'fragments_by_source': {
            source: {
                'n_total': len(frags),
                'n_preprocessed': sum(1 for f in frags if f.preprocessing_success),
                'fragments': [f.name for f in frags],
            }
            for source, frags in summary.fragments_by_source.items()
        },
        'false_positives': [
            {
                'frag_a': r.frag_a_name,
                'frag_b': r.frag_b_name,
                'source_a': r.source_a,
                'source_b': r.source_b,
                'verdict': r.verdict,
                'confidence': r.confidence,
                'color_bc': r.color_bc,
                'execution_time_ms': r.execution_time_ms,
            }
            for r in summary.false_positive_results
        ],
        'all_results': [
            {
                'frag_a': r.frag_a_name,
                'frag_b': r.frag_b_name,
                'source_a': r.source_a,
                'source_b': r.source_b,
                'verdict': r.verdict,
                'confidence': r.confidence,
                'color_bc': r.color_bc,
                'is_false_positive': r.is_false_positive,
                'execution_time_ms': r.execution_time_ms,
            }
            for r in summary.all_results
        ],
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info("Saved JSON report: %s", output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive negative case testing for cross-source fragment rejection",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--input', default='data/raw/real_fragments_validated',
        help='Base directory containing fragment sources',
    )
    parser.add_argument(
        '--output', default='outputs/testing',
        help='Output directory for reports and visualizations',
    )
    parser.add_argument(
        '--max-pairs', type=int, default=None,
        help='Maximum number of pairs to test (default: all)',
    )
    parser.add_argument(
        '--verbose', action='store_true',
        help='Enable verbose debug logging',
    )

    args = parser.parse_args()

    logger = setup_logging(args.output, verbose=args.verbose)
    logger.info("=" * 70)
    logger.info("Negative Case Testing: Cross-Source Fragment Rejection")
    logger.info("=" * 70)
    logger.info("Input directory: %s", args.input)
    logger.info("Output directory: %s", args.output)

    # Collect fragments by source
    logger.info("=" * 70)
    logger.info("Phase 1: Collecting Fragments by Source")
    logger.info("=" * 70)

    fragments_by_source_paths = collect_fragments_by_source(args.input, logger)

    if len(fragments_by_source_paths) < 2:
        logger.error("Need at least 2 different sources for negative testing")
        print(f"\n[ERROR] Found only {len(fragments_by_source_paths)} source(s). Need at least 2.")
        sys.exit(1)

    # Preprocess all fragments
    logger.info("=" * 70)
    logger.info("Phase 2: Preprocessing All Fragments")
    logger.info("=" * 70)

    fragments_by_source = {}
    for source, paths in fragments_by_source_paths.items():
        logger.info("Preprocessing source '%s' (%d fragments)...", source, len(paths))
        fragments_by_source[source] = [
            preprocess_fragment_safe(path, source, logger)
            for path in paths
        ]

    # Generate cross-source pairs
    logger.info("=" * 70)
    logger.info("Phase 3: Generating Cross-Source Pairs")
    logger.info("=" * 70)

    negative_pairs = generate_cross_source_pairs(fragments_by_source, args.max_pairs, logger)

    # Test all pairs
    logger.info("=" * 70)
    logger.info("Phase 4: Testing Negative Pairs")
    logger.info("=" * 70)

    pair_results = []
    for i, (frag_a, frag_b) in enumerate(negative_pairs, 1):
        if i % 10 == 0:
            logger.info("Progress: %d/%d pairs tested...", i, len(negative_pairs))

        result = test_negative_pair(frag_a, frag_b, logger)
        if result:
            pair_results.append(result)

    # Compute summary
    logger.info("=" * 70)
    logger.info("Phase 5: Computing Summary Statistics")
    logger.info("=" * 70)

    summary = compute_summary_statistics(fragments_by_source, pair_results)

    logger.info("True Negative Rate: %.2f%% (%d/%d)",
               summary.true_negative_rate * 100,
               summary.n_true_negatives, summary.n_negative_pairs_tested)
    logger.info("False Positive Rate: %.2f%% (%d/%d)",
               summary.false_positive_rate * 100,
               summary.n_false_positives, summary.n_negative_pairs_tested)

    # Generate outputs
    logger.info("=" * 70)
    logger.info("Phase 6: Generating Reports and Visualizations")
    logger.info("=" * 70)

    os.makedirs(args.output, exist_ok=True)

    generate_visualizations(summary, args.output, logger)

    md_report_path = os.path.join(args.output, 'negative_case_analysis.md')
    generate_markdown_report(summary, md_report_path, logger)

    json_report_path = os.path.join(args.output, 'negative_case_analysis.json')
    generate_json_report(summary, json_report_path, logger)

    # Final summary
    logger.info("=" * 70)
    logger.info("Negative Case Testing Complete")
    logger.info("=" * 70)
    logger.info("Reports saved to: %s", args.output)

    print("\n" + "=" * 70)
    print("NEGATIVE CASE TEST SUMMARY")
    print("=" * 70)
    print(f"Sources tested:             {summary.n_sources}")
    print(f"Fragments:                  {summary.n_fragments_processed}/{summary.n_fragments_total}")
    print(f"Cross-source pairs:         {summary.n_negative_pairs_tested}")
    print(f"True Negative Rate:         {summary.true_negative_rate*100:.2f}%")
    print(f"False Positive Rate:        {summary.false_positive_rate*100:.2f}%")
    print(f"False Positives:            {summary.n_false_positives}")
    print(f"Average Confidence:         {summary.avg_confidence:.4f}")
    print(f"Average Color BC:           {summary.avg_color_bc:.4f}")
    print("=" * 70)
    print(f"\nFull report: {md_report_path}")
    print(f"Visualizations: {args.output}/")
    print()


if __name__ == '__main__':
    main()
