#!/usr/bin/env python3
"""
Create visual gallery of fragment quality examples

Showcases best and worst quality fragments with annotations
"""

import cv2
import numpy as np
import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from typing import List, Dict, Any


def create_annotated_fragment(img_path: Path, result: Dict[str, Any], figsize=(4, 4)) -> np.ndarray:
    """Create annotated version of fragment image"""

    img = cv2.imread(str(img_path))
    if img is None:
        return None

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    ax.imshow(img_rgb)
    ax.axis('off')

    # Add title with score
    score = result.get('quality_score', 0)
    category = result.get('category', 'unknown')
    title = f"Score: {score:.2f}/10 ({category.capitalize()})"
    ax.set_title(title, fontsize=10, fontweight='bold')

    # Convert to image
    fig.tight_layout()
    fig.canvas.draw()
    data = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
    data = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))
    plt.close(fig)

    return data


def create_quality_gallery(json_path: Path, base_path: Path, output_path: Path):
    """Create comprehensive quality gallery"""

    # Load results
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data['results']
    all_results = results['wikimedia_processed'] + results['wikimedia'] + results['british_museum']

    # Filter valid results
    valid_results = [r for r in all_results if 'quality_score' in r]
    sorted_results = sorted(valid_results, key=lambda x: x['quality_score'], reverse=True)

    # Select examples
    excellent = sorted_results[:8]
    good = [r for r in sorted_results if r.get('category') == 'good'][:4]
    acceptable = [r for r in sorted_results if r.get('category') == 'acceptable'][:4]

    # Create figure
    fig = plt.figure(figsize=(20, 14))
    gs = gridspec.GridSpec(4, 8, figure=fig, hspace=0.3, wspace=0.2)

    # Add title
    fig.suptitle("Fragment Quality Gallery - Data Quality Audit", fontsize=20, fontweight='bold')

    # Section 1: Excellent examples
    fig.text(0.05, 0.95, "Excellent Quality (Score >= 8.5)", fontsize=14, fontweight='bold')

    for i, result in enumerate(excellent[:8]):
        ax = fig.add_subplot(gs[0, i])

        # Find image
        img_path = None
        for source_dir in ['wikimedia_processed', 'wikimedia_processed/example1_auto', 'wikimedia', 'british_museum']:
            candidate = base_path / source_dir / result['filename']
            if candidate.exists():
                img_path = candidate
                break

        if img_path and img_path.exists():
            img = cv2.imread(str(img_path))
            if img is not None:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                ax.imshow(img_rgb)
                ax.set_title(f"{result['quality_score']:.2f}", fontsize=9)
        else:
            ax.text(0.5, 0.5, 'Not Found', ha='center', va='center')

        ax.axis('off')

    # Section 2: Good examples
    fig.text(0.05, 0.70, "Good Quality (Score 7.0-8.5)", fontsize=14, fontweight='bold')

    for i, result in enumerate(good[:8]):
        ax = fig.add_subplot(gs[1, i])

        img_path = None
        for source_dir in ['wikimedia_processed', 'wikimedia_processed/example1_auto', 'wikimedia', 'british_museum']:
            candidate = base_path / source_dir / result['filename']
            if candidate.exists():
                img_path = candidate
                break

        if img_path and img_path.exists():
            img = cv2.imread(str(img_path))
            if img is not None:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                ax.imshow(img_rgb)
                ax.set_title(f"{result['quality_score']:.2f}", fontsize=9)
        else:
            ax.text(0.5, 0.5, 'Not Found', ha='center', va='center')

        ax.axis('off')

    # Section 3: Acceptable examples
    fig.text(0.05, 0.45, "Acceptable Quality (Score 5.0-7.0)", fontsize=14, fontweight='bold')

    for i, result in enumerate(acceptable[:8]):
        ax = fig.add_subplot(gs[2, i])

        img_path = None
        for source_dir in ['wikimedia_processed', 'wikimedia_processed/example1_auto', 'wikimedia', 'british_museum']:
            candidate = base_path / source_dir / result['filename']
            if candidate.exists():
                img_path = candidate
                break

        if img_path and img_path.exists():
            img = cv2.imread(str(img_path))
            if img is not None:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                ax.imshow(img_rgb)
                ax.set_title(f"{result['quality_score']:.2f}", fontsize=9)

                # Show issues
                issues = [name.replace('_', ' ') for name, check in result.get('checks', {}).items()
                         if not check.get('passed', False)]
                if issues:
                    ax.text(0.5, -0.1, f"Issues: {', '.join(issues[:2])}",
                           ha='center', va='top', transform=ax.transAxes, fontsize=7, color='red')
        else:
            ax.text(0.5, 0.5, 'Not Found', ha='center', va='center')

        ax.axis('off')

    # Section 4: Quality metrics visualization
    fig.text(0.05, 0.20, "Quality Score Distribution", fontsize=14, fontweight='bold')

    # Histogram
    ax_hist = fig.add_subplot(gs[3, :4])
    scores = [r['quality_score'] for r in valid_results]
    ax_hist.hist(scores, bins=20, edgecolor='black', alpha=0.7, color='steelblue')
    ax_hist.set_xlabel('Quality Score', fontsize=10)
    ax_hist.set_ylabel('Frequency', fontsize=10)
    ax_hist.set_title('Score Distribution', fontsize=11)
    ax_hist.grid(True, alpha=0.3)

    # Category pie chart
    ax_pie = fig.add_subplot(gs[3, 4:])
    categories = data['quality_categories']
    cat_counts = [len(categories.get(cat, [])) for cat in ['excellent', 'good', 'acceptable', 'poor']]
    colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c']
    ax_pie.pie(cat_counts, labels=['Excellent', 'Good', 'Acceptable', 'Poor'],
              autopct='%1.1f%%', startangle=90, colors=colors)
    ax_pie.set_title('Quality Categories', fontsize=11)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Gallery saved to: {output_path}")

    plt.close()


def create_same_source_comparison(json_path: Path, base_path: Path, output_path: Path):
    """Create visual comparison of same-source fragments"""

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Get wikimedia_processed fragments
    wp_results = data['results']['wikimedia_processed']
    valid_wp = [r for r in wp_results if 'quality_score' in r]

    # Take first 16 fragments
    samples = valid_wp[:16]

    fig, axes = plt.subplots(4, 4, figsize=(16, 16))
    fig.suptitle("Same-Source Fragments (Wikimedia Processed)\nAll from same original photo",
                fontsize=16, fontweight='bold')

    for i, (ax, result) in enumerate(zip(axes.flat, samples)):
        img_path = None
        for source_dir in ['wikimedia_processed', 'wikimedia_processed/example1_auto']:
            candidate = base_path / source_dir / result['filename']
            if candidate.exists():
                img_path = candidate
                break

        if img_path and img_path.exists():
            img = cv2.imread(str(img_path))
            if img is not None:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                ax.imshow(img_rgb)
                ax.set_title(f"Fragment {i+1} (Score: {result['quality_score']:.2f})", fontsize=10)
        else:
            ax.text(0.5, 0.5, 'Not Found', ha='center', va='center')

        ax.axis('off')

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Same-source comparison saved to: {output_path}")

    plt.close()


def create_different_source_comparison(json_path: Path, base_path: Path, output_path: Path):
    """Create visual comparison of different-source fragments"""

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Get wikimedia fragments
    wm_results = data['results']['wikimedia']
    valid_wm = [r for r in wm_results if 'quality_score' in r]

    # Take all available (should be around 6)
    samples = valid_wm[:12]

    rows = (len(samples) + 3) // 4
    fig, axes = plt.subplots(rows, 4, figsize=(16, rows*4))
    fig.suptitle("Different-Source Fragments (Wikimedia)\nEach from different artifact",
                fontsize=16, fontweight='bold')

    if rows == 1:
        axes = axes.reshape(1, -1)

    for i, (ax, result) in enumerate(zip(axes.flat[:len(samples)], samples)):
        img_path = base_path / 'wikimedia' / result['filename']

        if img_path.exists():
            img = cv2.imread(str(img_path))
            if img is not None:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                ax.imshow(img_rgb)
                ax.set_title(f"Artifact {i+1} (Score: {result['quality_score']:.2f})", fontsize=10)
        else:
            ax.text(0.5, 0.5, 'Not Found', ha='center', va='center')

        ax.axis('off')

    # Hide unused subplots
    for ax in axes.flat[len(samples):]:
        ax.axis('off')

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Different-source comparison saved to: {output_path}")

    plt.close()


def main():
    """Main execution"""
    base_path = Path(__file__).parent.parent / "data" / "raw" / "real_fragments_validated"
    output_dir = Path(__file__).parent.parent / "outputs" / "testing"
    json_path = output_dir / "data_quality_audit.json"

    if not json_path.exists():
        print(f"Error: JSON file not found at {json_path}")
        print("Please run data_quality_audit.py first")
        return

    print("Creating visual galleries...")

    # Main quality gallery
    gallery_path = output_dir / "fragment_quality_gallery.png"
    create_quality_gallery(json_path, base_path, gallery_path)

    # Same-source comparison
    same_source_path = output_dir / "same_source_comparison.png"
    create_same_source_comparison(json_path, base_path, same_source_path)

    # Different-source comparison
    diff_source_path = output_dir / "different_source_comparison.png"
    create_different_source_comparison(json_path, base_path, diff_source_path)

    print()
    print("=" * 80)
    print("VISUAL GALLERIES CREATED")
    print("=" * 80)
    print(f"Main gallery: {gallery_path}")
    print(f"Same-source: {same_source_path}")
    print(f"Different-source: {diff_source_path}")


if __name__ == "__main__":
    main()
