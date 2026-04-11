#!/usr/bin/env python3
"""
visualize_improvement.py
------------------------
Auto-generates comparison plots after each phase.

Creates:
1. Improvement trajectory: positive/negative accuracy across phases
2. Confusion matrices: evolution from baseline through phases
3. BC distributions: separation between positive and negative pairs
4. Performance metrics: time per fragment across phases

Usage:
    python scripts/visualize_improvement.py
    python scripts/visualize_improvement.py --phase 1a
    python scripts/visualize_improvement.py --output outputs/testing/plots

Author: Automated Testing Framework
Date: 2026-04-08
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("✗ matplotlib or numpy not installed")
    print("  Install with: pip install matplotlib numpy")
    sys.exit(1)

ROOT = Path(__file__).parent.parent.resolve()
OUTPUTS_DIR = ROOT / "outputs" / "testing"
PLOTS_DIR = OUTPUTS_DIR / "plots"


class ImprovementVisualizer:
    """Visualizes improvement across phases."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or PLOTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_all_metrics(self) -> Dict[str, Dict]:
        """Load metrics for all phases."""
        phases = ["baseline", "1a", "1b", "2a", "2b"]
        metrics = {}

        for phase in phases:
            metrics_file = OUTPUTS_DIR / f"metrics_{phase}.json"
            if metrics_file.exists():
                metrics[phase] = json.loads(metrics_file.read_text())

        return metrics

    def plot_improvement_trajectory(self, metrics: Dict[str, Dict]) -> Path:
        """
        Line plot showing positive/negative accuracy across phases.
        """
        print("Generating improvement trajectory plot...")

        phases = []
        positive_acc = []
        negative_acc = []
        balanced_acc = []

        phase_order = ["baseline", "1a", "1b", "2a", "2b"]
        phase_labels = {
            "baseline": "Baseline",
            "1a": "1A: Lab",
            "1b": "1B: Exponential",
            "2a": "2A: LBP",
            "2b": "2B: Fractal"
        }

        for phase in phase_order:
            if phase in metrics:
                phases.append(phase_labels[phase])
                positive_acc.append(metrics[phase]["positive_accuracy"] * 100)
                negative_acc.append(metrics[phase]["negative_accuracy"] * 100)
                balanced_acc.append(metrics[phase]["balanced_accuracy"] * 100)

        if not phases:
            print("  No metrics to plot")
            return None

        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))

        x = np.arange(len(phases))

        ax.plot(x, positive_acc, 'o-', color='#2ecc71', linewidth=2, markersize=8, label='Positive Accuracy')
        ax.plot(x, negative_acc, 'o-', color='#e74c3c', linewidth=2, markersize=8, label='Negative Accuracy')
        ax.plot(x, balanced_acc, 'o-', color='#3498db', linewidth=2, markersize=8, label='Balanced Accuracy')

        ax.set_xlabel('Phase', fontsize=12, fontweight='bold')
        ax.set_ylabel('Accuracy (%)', fontsize=12, fontweight='bold')
        ax.set_title('Fragment Reconstruction Improvement Trajectory', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(phases, rotation=45, ha='right')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=10)
        ax.set_ylim(0, 105)

        # Add value labels
        for i, (pos, neg, bal) in enumerate(zip(positive_acc, negative_acc, balanced_acc)):
            ax.text(i, pos + 2, f'{pos:.0f}%', ha='center', va='bottom', fontsize=8, color='#2ecc71')
            ax.text(i, neg + 2, f'{neg:.0f}%', ha='center', va='bottom', fontsize=8, color='#e74c3c')

        plt.tight_layout()

        output_file = self.output_dir / "improvement_trajectory.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  ✓ Saved: {output_file}")
        return output_file

    def plot_confusion_matrices(self, metrics: Dict[str, Dict]) -> Path:
        """
        Grid of confusion matrices (baseline + phases).
        """
        print("Generating confusion matrix evolution plot...")

        phase_order = ["baseline", "1a", "1b", "2a", "2b"]
        phase_labels = {
            "baseline": "Baseline",
            "1a": "Phase 1A\nLab Color",
            "1b": "Phase 1B\nExponential",
            "2a": "Phase 2A\nLBP Texture",
            "2b": "Phase 2B\nFractal"
        }

        available_phases = [p for p in phase_order if p in metrics]

        if not available_phases:
            print("  No metrics to plot")
            return None

        # Create figure
        n_phases = len(available_phases)
        cols = min(3, n_phases)
        rows = (n_phases + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(4*cols, 4*rows))
        if n_phases == 1:
            axes = [axes]
        else:
            axes = axes.flatten() if n_phases > 1 else [axes]

        for idx, phase in enumerate(available_phases):
            ax = axes[idx]
            m = metrics[phase]

            # Confusion matrix: [[TP, FP], [FN, TN]]
            tp = m["true_positives"]
            fp = m["false_positives"]
            fn = m["false_negatives"]
            tn = m["true_negatives"]

            confusion = np.array([[tp, fp], [fn, tn]])

            # Plot heatmap
            im = ax.imshow(confusion, cmap='Blues', aspect='auto', vmin=0)

            # Add text annotations
            for i in range(2):
                for j in range(2):
                    text = ax.text(j, i, confusion[i, j],
                                 ha="center", va="center", color="black",
                                 fontsize=16, fontweight='bold')

            ax.set_xticks([0, 1])
            ax.set_yticks([0, 1])
            ax.set_xticklabels(['Predicted +', 'Predicted -'])
            ax.set_yticklabels(['Actual +', 'Actual -'])
            ax.set_title(phase_labels[phase], fontsize=11, fontweight='bold')

            # Add metrics below
            pos_acc = m["positive_accuracy"] * 100
            neg_acc = m["negative_accuracy"] * 100
            ax.text(0.5, -0.15, f'Pos: {pos_acc:.0f}%  Neg: {neg_acc:.0f}%',
                   transform=ax.transAxes, ha='center', fontsize=9)

        # Hide unused subplots
        for idx in range(len(available_phases), len(axes)):
            axes[idx].axis('off')

        plt.suptitle('Confusion Matrix Evolution', fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()

        output_file = self.output_dir / "confusion_evolution.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  ✓ Saved: {output_file}")
        return output_file

    def plot_performance_metrics(self, metrics: Dict[str, Dict]) -> Path:
        """
        Bar chart showing time per fragment across phases.
        """
        print("Generating performance metrics plot...")

        phase_order = ["baseline", "1a", "1b", "2a", "2b"]
        phase_labels = {
            "baseline": "Baseline",
            "1a": "1A: Lab",
            "1b": "1B: Exp",
            "2a": "2A: LBP",
            "2b": "2B: Fractal"
        }

        phases = []
        times = []

        for phase in phase_order:
            if phase in metrics:
                phases.append(phase_labels[phase])
                times.append(metrics[phase]["time_per_fragment"])

        if not phases:
            print("  No metrics to plot")
            return None

        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))

        x = np.arange(len(phases))
        bars = ax.bar(x, times, color='#3498db', alpha=0.7, edgecolor='black')

        # Color bars based on performance
        baseline_time = times[0] if len(times) > 0 else 0
        for i, (bar, time) in enumerate(zip(bars, times)):
            if i == 0:
                bar.set_color('#95a5a6')  # Baseline gray
            elif time <= baseline_time * 1.2:
                bar.set_color('#2ecc71')  # Good (< 20% slower)
            elif time <= baseline_time * 1.5:
                bar.set_color('#f39c12')  # Warning (20-50% slower)
            else:
                bar.set_color('#e74c3c')  # Bad (> 50% slower)

        ax.set_xlabel('Phase', fontsize=12, fontweight='bold')
        ax.set_ylabel('Time per Fragment (seconds)', fontsize=12, fontweight='bold')
        ax.set_title('Processing Time per Fragment Across Phases', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(phases, rotation=45, ha='right')
        ax.grid(True, alpha=0.3, axis='y')

        # Add value labels on bars
        for i, (bar, time) in enumerate(zip(bars, times)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{time:.2f}s',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')

            # Add percent change from baseline
            if i > 0 and baseline_time > 0:
                pct_change = ((time - baseline_time) / baseline_time) * 100
                ax.text(bar.get_x() + bar.get_width()/2., height * 0.5,
                       f'{pct_change:+.0f}%',
                       ha='center', va='center', fontsize=8, color='white', fontweight='bold')

        plt.tight_layout()

        output_file = self.output_dir / "performance_metrics.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  ✓ Saved: {output_file}")
        return output_file

    def plot_f1_scores(self, metrics: Dict[str, Dict]) -> Path:
        """
        Plot F1 scores and related metrics across phases.
        """
        print("Generating F1 score comparison plot...")

        phase_order = ["baseline", "1a", "1b", "2a", "2b"]
        phase_labels = {
            "baseline": "Baseline",
            "1a": "1A: Lab",
            "1b": "1B: Exp",
            "2a": "2A: LBP",
            "2b": "2B: Fractal"
        }

        phases = []
        precision_vals = []
        recall_vals = []
        f1_vals = []

        for phase in phase_order:
            if phase in metrics:
                phases.append(phase_labels[phase])
                precision_vals.append(metrics[phase]["precision"] * 100)
                recall_vals.append(metrics[phase]["recall"] * 100)
                f1_vals.append(metrics[phase]["f1_score"] * 100)

        if not phases:
            print("  No metrics to plot")
            return None

        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))

        x = np.arange(len(phases))
        width = 0.25

        bars1 = ax.bar(x - width, precision_vals, width, label='Precision', color='#3498db', alpha=0.8)
        bars2 = ax.bar(x, recall_vals, width, label='Recall', color='#2ecc71', alpha=0.8)
        bars3 = ax.bar(x + width, f1_vals, width, label='F1 Score', color='#9b59b6', alpha=0.8)

        ax.set_xlabel('Phase', fontsize=12, fontweight='bold')
        ax.set_ylabel('Score (%)', fontsize=12, fontweight='bold')
        ax.set_title('Precision, Recall, and F1 Score Across Phases', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(phases, rotation=45, ha='right')
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim(0, 105)

        plt.tight_layout()

        output_file = self.output_dir / "f1_comparison.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  ✓ Saved: {output_file}")
        return output_file

    def generate_all_plots(self, metrics: Optional[Dict[str, Dict]] = None) -> List[Path]:
        """Generate all visualization plots."""
        if metrics is None:
            metrics = self.load_all_metrics()

        if not metrics:
            print("✗ No metrics found. Run tests first.")
            return []

        print(f"\n{'='*80}")
        print(f"GENERATING VISUALIZATION PLOTS")
        print(f"{'='*80}\n")
        print(f"Phases available: {', '.join(metrics.keys())}")
        print(f"Output directory: {self.output_dir}\n")

        plots = []

        plot_funcs = [
            self.plot_improvement_trajectory,
            self.plot_confusion_matrices,
            self.plot_performance_metrics,
            self.plot_f1_scores,
        ]

        for plot_func in plot_funcs:
            try:
                plot_file = plot_func(metrics)
                if plot_file:
                    plots.append(plot_file)
            except Exception as e:
                print(f"  ✗ Error in {plot_func.__name__}: {e}")

        print(f"\n{'='*80}")
        print(f"VISUALIZATION COMPLETE")
        print(f"{'='*80}")
        print(f"Generated {len(plots)} plot(s)")
        for plot in plots:
            print(f"  - {plot.name}")
        print(f"{'='*80}\n")

        return plots


def main():
    parser = argparse.ArgumentParser(
        description="Visualize improvement across phases",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--phase",
        help="Generate plots up to this phase only"
    )
    parser.add_argument(
        "--output",
        help="Output directory for plots"
    )

    args = parser.parse_args()

    output_dir = Path(args.output) if args.output else PLOTS_DIR

    visualizer = ImprovementVisualizer(output_dir=output_dir)

    # Load metrics
    metrics = visualizer.load_all_metrics()

    # Filter to specified phase if requested
    if args.phase:
        phase_order = ["baseline", "1a", "1b", "2a", "2b"]
        if args.phase in phase_order:
            cutoff_idx = phase_order.index(args.phase) + 1
            metrics = {p: metrics[p] for p in phase_order[:cutoff_idx] if p in metrics}
        else:
            print(f"✗ Unknown phase: {args.phase}")
            sys.exit(1)

    # Generate plots
    plots = visualizer.generate_all_plots(metrics)

    sys.exit(0 if plots else 1)


if __name__ == "__main__":
    main()
