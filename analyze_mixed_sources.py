#!/usr/bin/env python3
"""
Extended Analysis on Mixed-Source Fragments

This script tests algorithm components on mixed-source data to better
demonstrate discriminative power of each feature.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import cv2
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt

from preprocessing import preprocess_fragment
from chain_code import (
    encode_fragment,
    contour_to_pixel_segments,
    compute_curvature_profile
)
from compatibility import (
    profile_similarity,
    compute_color_signature,
    color_bhattacharyya,
    segment_fourier_score
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_mixed_fragments(data_dir: str):
    """Load fragments from mixed-source directory and parse source labels."""
    data_path = Path(data_dir)
    fragments = []

    image_files = sorted(list(data_path.glob('*.png')) + list(data_path.glob('*.jpg')))

    for img_file in image_files:
        try:
            # Parse source from filename (A_xx or B_xx prefix)
            source = 'A' if img_file.name.startswith('A_') else 'B'

            img_bgr, contour = preprocess_fragment(str(img_file))
            if contour is not None and len(contour) > 10:
                normalized_chain, segs = encode_fragment(contour, n_segments=4)
                pixel_segs = contour_to_pixel_segments(contour, n_segments=4)

                fragments.append({
                    'name': img_file.name,
                    'source': source,
                    'image': img_bgr,
                    'contour': contour,
                    'chain': normalized_chain,
                    'segments': segs,
                    'pixel_segments': pixel_segs
                })

                logger.info(f"Loaded: {img_file.name} (source {source})")
        except Exception as e:
            logger.warning(f"Failed to load {img_file.name}: {e}")

    return fragments


def analyze_mixed_source_discrimination(fragments: List[Dict]) -> Dict:
    """Analyze how well each component discriminates between same vs different sources."""

    results = {
        'curvature': {'same_source': [], 'cross_source': []},
        'fourier': {'same_source': [], 'cross_source': []},
        'color': {'same_source': [], 'cross_source': []}
    }

    n = len(fragments)

    # Curvature profile similarities
    logger.info("\nAnalyzing curvature discrimination...")
    for i in range(n):
        for seg_a in range(len(fragments[i]['pixel_segments'])):
            profile_a = compute_curvature_profile(fragments[i]['pixel_segments'][seg_a])

            for j in range(i+1, n):
                same_source = (fragments[i]['source'] == fragments[j]['source'])

                for seg_b in range(len(fragments[j]['pixel_segments'])):
                    profile_b = compute_curvature_profile(fragments[j]['pixel_segments'][seg_b])
                    score = profile_similarity(profile_a, profile_b)

                    if same_source:
                        results['curvature']['same_source'].append(score)
                    else:
                        results['curvature']['cross_source'].append(score)

    # Fourier descriptor similarities
    logger.info("Analyzing Fourier discrimination...")
    for i in range(n):
        for seg_a in range(len(fragments[i]['pixel_segments'])):
            for j in range(i+1, n):
                same_source = (fragments[i]['source'] == fragments[j]['source'])

                for seg_b in range(len(fragments[j]['pixel_segments'])):
                    score = segment_fourier_score(
                        fragments[i]['pixel_segments'][seg_a],
                        fragments[j]['pixel_segments'][seg_b]
                    )

                    if same_source:
                        results['fourier']['same_source'].append(score)
                    else:
                        results['fourier']['cross_source'].append(score)

    # Color histogram BC
    logger.info("Analyzing color discrimination...")
    color_sigs = [compute_color_signature(f['image']) for f in fragments]

    for i in range(n):
        for j in range(i+1, n):
            same_source = (fragments[i]['source'] == fragments[j]['source'])
            bc = color_bhattacharyya(color_sigs[i], color_sigs[j])

            if same_source:
                results['color']['same_source'].append(bc)
            else:
                results['color']['cross_source'].append(bc)

    # Compute statistics
    for component in ['curvature', 'fourier', 'color']:
        same = np.array(results[component]['same_source'])
        cross = np.array(results[component]['cross_source'])

        results[component]['stats'] = {
            'same_mean': float(np.mean(same)) if len(same) > 0 else 0.0,
            'same_std': float(np.std(same)) if len(same) > 0 else 0.0,
            'cross_mean': float(np.mean(cross)) if len(cross) > 0 else 0.0,
            'cross_std': float(np.std(cross)) if len(cross) > 0 else 0.0,
            'separation': 0.0
        }

        # Separation metric: distance between means in units of pooled std
        if len(same) > 0 and len(cross) > 0:
            pooled_std = np.sqrt((np.var(same) + np.var(cross)) / 2)
            if pooled_std > 0:
                results[component]['stats']['separation'] = abs(
                    np.mean(same) - np.mean(cross)
                ) / pooled_std

    return results


def generate_discrimination_plots(results: Dict, output_dir: Path):
    """Generate comparison plots showing discriminative power."""

    # Plot 1: Curvature discrimination
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    components = ['curvature', 'fourier', 'color']
    titles = ['Curvature Profile Similarity', 'Fourier Descriptor Similarity', 'Color Histogram BC']

    for idx, (comp, title) in enumerate(zip(components, titles)):
        ax = axes[idx]

        same = results[comp]['same_source']
        cross = results[comp]['cross_source']

        ax.hist(same, bins=30, alpha=0.6, label='Same Source', color='green', edgecolor='black')
        ax.hist(cross, bins=30, alpha=0.6, label='Cross Source', color='red', edgecolor='black')

        ax.axvline(results[comp]['stats']['same_mean'], color='green',
                   linestyle='--', linewidth=2, label=f"Same μ={results[comp]['stats']['same_mean']:.3f}")
        ax.axvline(results[comp]['stats']['cross_mean'], color='red',
                   linestyle='--', linewidth=2, label=f"Cross μ={results[comp]['stats']['cross_mean']:.3f}")

        ax.set_xlabel('Similarity Score')
        ax.set_ylabel('Frequency')
        ax.set_title(f"{title}\nSeparation: {results[comp]['stats']['separation']:.2f}σ")
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / 'mixed_source_discrimination.png', dpi=150, bbox_inches='tight')
    plt.close()

    logger.info(f"Discrimination plot saved to {output_dir}")


def generate_discrimination_report(results: Dict, fragments: List[Dict], output_path: Path):
    """Generate markdown report on discrimination analysis."""

    report = [
        "# Mixed-Source Discrimination Analysis",
        "",
        f"**Fragments analyzed:** {len(fragments)}",
        f"**Source A count:** {sum(1 for f in fragments if f['source'] == 'A')}",
        f"**Source B count:** {sum(1 for f in fragments if f['source'] == 'B')}",
        "",
        "## Discriminative Power Analysis",
        "",
        "This analysis tests how well each algorithm component can distinguish fragments "
        "from the same source vs. fragments from different sources.",
        "",
        "### Separation Metric",
        "",
        "Separation is measured as the distance between means in units of pooled standard deviation:",
        "",
        "```",
        "separation = |μ_same - μ_cross| / σ_pooled",
        "```",
        "",
        "- **< 1.0σ:** Poor discrimination (distributions overlap heavily)",
        "- **1.0-2.0σ:** Moderate discrimination",
        "- **> 2.0σ:** Strong discrimination (clear separation)",
        "",
        "---",
        "",
        "## 1. Curvature Profile Cross-Correlation",
        "",
        f"- **Same source mean:** {results['curvature']['stats']['same_mean']:.3f} ± {results['curvature']['stats']['same_std']:.3f}",
        f"- **Cross source mean:** {results['curvature']['stats']['cross_mean']:.3f} ± {results['curvature']['stats']['cross_std']:.3f}",
        f"- **Separation:** {results['curvature']['stats']['separation']:.2f}σ",
        "",
        "### Verdict",
        ""
    ]

    curv_sep = results['curvature']['stats']['separation']
    if curv_sep > 2.0:
        report.append("✓ **Strong discriminative power** - Clear separation between same/cross source")
    elif curv_sep > 1.0:
        report.append("⚠ **Moderate discriminative power** - Some overlap but useful signal")
    else:
        report.append("✗ **Weak discriminative power** - Heavy overlap, limited utility")

    report.extend([
        "",
        "---",
        "",
        "## 2. Fourier Descriptors",
        "",
        f"- **Same source mean:** {results['fourier']['stats']['same_mean']:.3f} ± {results['fourier']['stats']['same_std']:.3f}",
        f"- **Cross source mean:** {results['fourier']['stats']['cross_mean']:.3f} ± {results['fourier']['stats']['cross_std']:.3f}",
        f"- **Separation:** {results['fourier']['stats']['separation']:.2f}σ",
        "",
        "### Verdict",
        ""
    ])

    fourier_sep = results['fourier']['stats']['separation']
    if fourier_sep > 2.0:
        report.append("✓ **Strong discriminative power**")
    elif fourier_sep > 1.0:
        report.append("⚠ **Moderate discriminative power**")
    else:
        report.append("✗ **Weak discriminative power**")

    report.extend([
        "",
        "---",
        "",
        "## 3. Color Histogram (Bhattacharyya Coefficient)",
        "",
        f"- **Same source mean:** {results['color']['stats']['same_mean']:.3f} ± {results['color']['stats']['same_std']:.3f}",
        f"- **Cross source mean:** {results['color']['stats']['cross_mean']:.3f} ± {results['color']['stats']['cross_std']:.3f}",
        f"- **Separation:** {results['color']['stats']['separation']:.2f}σ",
        "",
        "### Verdict",
        ""
    ])

    color_sep = results['color']['stats']['separation']
    if color_sep > 2.0:
        report.append("✓ **Strong discriminative power** - Excellent cross-source filter")
    elif color_sep > 1.0:
        report.append("⚠ **Moderate discriminative power**")
    else:
        report.append("✗ **Weak discriminative power**")

    report.extend([
        "",
        "---",
        "",
        "## Summary Comparison",
        "",
        "| Component | Separation (σ) | Discriminative Power |",
        "|-----------|----------------|---------------------|",
        f"| Curvature | {results['curvature']['stats']['separation']:.2f} | {'Strong' if curv_sep > 2.0 else 'Moderate' if curv_sep > 1.0 else 'Weak'} |",
        f"| Fourier | {results['fourier']['stats']['separation']:.2f} | {'Strong' if fourier_sep > 2.0 else 'Moderate' if fourier_sep > 1.0 else 'Weak'} |",
        f"| Color | {results['color']['stats']['separation']:.2f} | {'Strong' if color_sep > 2.0 else 'Moderate' if color_sep > 1.0 else 'Weak'} |",
        "",
        "### Recommendations",
        "",
        "1. **Primary feature:** " + (
            "Color" if color_sep == max(curv_sep, fourier_sep, color_sep) else
            "Curvature" if curv_sep == max(curv_sep, fourier_sep, color_sep) else
            "Fourier"
        ),
        "2. **Secondary features:** Combine all three for robust matching",
        "3. **Color histogram weight:** Should be high given strong discrimination",
        "",
        "![Discrimination Comparison](mixed_source_discrimination.png)",
        ""
    ])

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    logger.info(f"Report saved to {output_path}")


def main():
    """Main execution."""
    logger.info("="*80)
    logger.info("MIXED-SOURCE DISCRIMINATION ANALYSIS")
    logger.info("="*80)

    # Load mixed-source fragments
    data_dir = 'data/examples/negative/mixed_gettyimages-13116049_gettyimages-17009652'

    if not os.path.exists(data_dir):
        logger.error(f"Data directory not found: {data_dir}")
        return

    logger.info(f"\nLoading mixed-source fragments from: {data_dir}")
    fragments = load_mixed_fragments(data_dir)

    if len(fragments) < 2:
        logger.error("Need at least 2 fragments for discrimination analysis")
        return

    logger.info(f"Loaded {len(fragments)} fragments")

    # Analyze discrimination
    results = analyze_mixed_source_discrimination(fragments)

    # Generate outputs
    output_dir = Path('outputs/testing')
    output_dir.mkdir(parents=True, exist_ok=True)

    generate_discrimination_plots(results, output_dir)
    generate_discrimination_report(results, fragments, output_dir / 'mixed_source_analysis.md')

    logger.info("\n" + "="*80)
    logger.info("ANALYSIS COMPLETE")
    logger.info("="*80)
    logger.info(f"Results: {output_dir}")


if __name__ == '__main__':
    main()
