#!/usr/bin/env python3
"""
validate_metrics.py
-------------------
Reads test outputs and computes detailed metrics with comparison tables.

This script:
- Reads test output files
- Computes: positive accuracy, negative accuracy, balanced accuracy, F1, precision, recall
- Generates comparison tables (baseline vs current)
- Flags regressions automatically
- Outputs formatted reports

Usage:
    python scripts/validate_metrics.py --output outputs/testing/test_results_20260408.txt
    python scripts/validate_metrics.py --compare baseline phase_1a
    python scripts/validate_metrics.py --all

Author: Automated Testing Framework
Date: 2026-04-08
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).parent.parent.resolve()
OUTPUTS_DIR = ROOT / "outputs" / "testing"
BASELINE_FILE = OUTPUTS_DIR / "baseline_metrics.json"


class MetricsValidator:
    """Validates and compares test metrics."""

    def __init__(self):
        self.regression_threshold = 0.02  # 2% drop
        self.time_regression_threshold = 0.50  # 50% increase

    def parse_output_file(self, filepath: str) -> Optional[Dict]:
        """
        Parse a test output file and extract all metrics.

        Returns:
            Dictionary with comprehensive metrics or None if parsing failed
        """
        try:
            content = Path(filepath).read_text()
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            return None

        # Initialize counters
        positive_cases = []
        negative_cases = []
        total_time = 0.0

        in_results = False
        for line in content.splitlines():
            if "RECONSTRUCTION TEST RESULTS" in line:
                in_results = True
                continue

            if not in_results or not line.strip():
                continue

            # Parse positive cases
            if " positive " in line:
                parts = line.split()
                passed = "PASS" in line
                time_val = None

                # Extract time
                for i, part in enumerate(parts):
                    try:
                        if '.' in part and part.replace('.', '').isdigit():
                            time_val = float(part)
                            break
                    except ValueError:
                        pass

                positive_cases.append({
                    "passed": passed,
                    "time": time_val or 0.0,
                    "line": line.strip()
                })

                if time_val:
                    total_time += time_val

            # Parse negative cases
            elif " negative " in line:
                parts = line.split()
                passed = "PASS" in line
                time_val = None

                # Extract time
                for i, part in enumerate(parts):
                    try:
                        if '.' in part and part.replace('.', '').isdigit():
                            time_val = float(part)
                            break
                    except ValueError:
                        pass

                negative_cases.append({
                    "passed": passed,
                    "time": time_val or 0.0,
                    "line": line.strip()
                })

                if time_val:
                    total_time += time_val

        if not positive_cases and not negative_cases:
            print(f"Warning: No test cases found in {filepath}")
            return None

        # Compute metrics
        positive_total = len(positive_cases)
        positive_pass = sum(1 for c in positive_cases if c["passed"])
        positive_fail = positive_total - positive_pass

        negative_total = len(negative_cases)
        negative_pass = sum(1 for c in negative_cases if c["passed"])
        negative_fail = negative_total - negative_pass

        # True Positives: positive cases that passed
        # False Positives: negative cases that failed (matched when shouldn't)
        # True Negatives: negative cases that passed
        # False Negatives: positive cases that failed (didn't match when should)
        tp = positive_pass
        fp = negative_fail
        tn = negative_pass
        fn = positive_fail

        # Metrics
        positive_accuracy = positive_pass / positive_total if positive_total > 0 else 0.0
        negative_accuracy = negative_pass / negative_total if negative_total > 0 else 0.0
        balanced_accuracy = (positive_accuracy + negative_accuracy) / 2.0

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

        total_cases = positive_total + negative_total
        time_per_fragment = total_time / total_cases if total_cases > 0 else 0.0

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "filepath": filepath,
            "total_cases": total_cases,
            "positive_total": positive_total,
            "positive_pass": positive_pass,
            "positive_fail": positive_fail,
            "positive_accuracy": positive_accuracy,
            "negative_total": negative_total,
            "negative_pass": negative_pass,
            "negative_fail": negative_fail,
            "negative_accuracy": negative_accuracy,
            "balanced_accuracy": balanced_accuracy,
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "specificity": specificity,
            "total_time": total_time,
            "time_per_fragment": time_per_fragment,
            "positive_cases": positive_cases,
            "negative_cases": negative_cases,
        }

        return metrics

    def compare_metrics(self, current: Dict, baseline: Dict) -> Dict:
        """
        Compare current metrics to baseline.

        Returns:
            Dictionary with comparison results and flags
        """
        comparison = {
            "timestamp": datetime.now().isoformat(),
            "deltas": {},
            "regressions": [],
            "improvements": [],
            "warnings": [],
        }

        # Compare each metric
        metrics_to_compare = [
            ("positive_accuracy", "higher_better", True),  # critical
            ("negative_accuracy", "higher_better", False),
            ("balanced_accuracy", "higher_better", False),
            ("precision", "higher_better", False),
            ("recall", "higher_better", True),  # critical
            ("f1_score", "higher_better", False),
            ("specificity", "higher_better", False),
            ("time_per_fragment", "lower_better", False),
        ]

        for metric_name, direction, critical in metrics_to_compare:
            current_val = current.get(metric_name, 0)
            baseline_val = baseline.get(metric_name, 0)
            delta = current_val - baseline_val
            delta_pct = (delta / baseline_val * 100) if baseline_val != 0 else 0

            comparison["deltas"][metric_name] = {
                "current": current_val,
                "baseline": baseline_val,
                "delta": delta,
                "delta_pct": delta_pct,
            }

            # Check for regressions
            if direction == "higher_better" and delta < -self.regression_threshold:
                severity = "CRITICAL" if critical else "WARNING"
                comparison["regressions"].append({
                    "metric": metric_name,
                    "severity": severity,
                    "delta": delta,
                    "delta_pct": delta_pct,
                    "message": f"{metric_name}: {current_val:.3f} vs {baseline_val:.3f} ({delta:+.3f}, {delta_pct:+.1f}%)"
                })
            elif direction == "lower_better" and delta_pct > (self.time_regression_threshold * 100):
                comparison["regressions"].append({
                    "metric": metric_name,
                    "severity": "WARNING",
                    "delta": delta,
                    "delta_pct": delta_pct,
                    "message": f"{metric_name}: {current_val:.3f}s vs {baseline_val:.3f}s ({delta:+.3f}s, {delta_pct:+.1f}%)"
                })

            # Check for improvements
            if direction == "higher_better" and delta > 0.01:
                comparison["improvements"].append({
                    "metric": metric_name,
                    "delta": delta,
                    "delta_pct": delta_pct,
                    "message": f"{metric_name}: {current_val:.3f} vs {baseline_val:.3f} ({delta:+.3f}, {delta_pct:+.1f}%)"
                })
            elif direction == "lower_better" and delta < -0.1:
                comparison["improvements"].append({
                    "metric": metric_name,
                    "delta": delta,
                    "delta_pct": delta_pct,
                    "message": f"{metric_name}: {current_val:.3f}s vs {baseline_val:.3f}s ({delta:+.3f}s, {delta_pct:+.1f}%)"
                })

        return comparison

    def generate_comparison_table(self, current: Dict, baseline: Dict) -> str:
        """Generate a formatted comparison table."""
        lines = []
        lines.append("\n" + "="*100)
        lines.append("METRICS COMPARISON TABLE")
        lines.append("="*100)

        # Header
        lines.append(f"{'Metric':<25} {'Baseline':>12} {'Current':>12} {'Delta':>12} {'Delta %':>12} {'Status':>10}")
        lines.append("-"*100)

        metrics = [
            ("Positive Accuracy", "positive_accuracy", True),
            ("Negative Accuracy", "negative_accuracy", True),
            ("Balanced Accuracy", "balanced_accuracy", True),
            ("Precision", "precision", True),
            ("Recall", "recall", True),
            ("F1 Score", "f1_score", True),
            ("Specificity", "specificity", True),
            ("Time per Fragment", "time_per_fragment", False),
        ]

        for display_name, metric_key, higher_better in metrics:
            current_val = current.get(metric_key, 0)
            baseline_val = baseline.get(metric_key, 0)
            delta = current_val - baseline_val
            delta_pct = (delta / baseline_val * 100) if baseline_val != 0 else 0

            # Determine status
            if higher_better:
                if delta > 0.01:
                    status = "✓ BETTER"
                elif delta < -self.regression_threshold:
                    status = "✗ WORSE"
                else:
                    status = "= SAME"
            else:
                if delta < -0.1:
                    status = "✓ BETTER"
                elif delta_pct > (self.time_regression_threshold * 100):
                    status = "✗ WORSE"
                else:
                    status = "= SAME"

            # Format values
            if metric_key == "time_per_fragment":
                baseline_str = f"{baseline_val:.3f}s"
                current_str = f"{current_val:.3f}s"
                delta_str = f"{delta:+.3f}s"
            else:
                baseline_str = f"{baseline_val:.3f}"
                current_str = f"{current_val:.3f}"
                delta_str = f"{delta:+.3f}"

            delta_pct_str = f"{delta_pct:+.1f}%"

            lines.append(f"{display_name:<25} {baseline_str:>12} {current_str:>12} {delta_str:>12} {delta_pct_str:>12} {status:>10}")

        lines.append("="*100)

        # Summary statistics
        lines.append("\nSUMMARY:")
        lines.append(f"  Total Test Cases: {current['total_cases']} (baseline: {baseline['total_cases']})")
        lines.append(f"  True Positives:   {current['true_positives']} (baseline: {baseline['true_positives']})")
        lines.append(f"  False Positives:  {current['false_positives']} (baseline: {baseline['false_positives']})")
        lines.append(f"  True Negatives:   {current['true_negatives']} (baseline: {baseline['true_negatives']})")
        lines.append(f"  False Negatives:  {current['false_negatives']} (baseline: {baseline['false_negatives']})")
        lines.append("")

        return "\n".join(lines)

    def flag_regressions(self, comparison: Dict) -> str:
        """Generate a report of regressions and warnings."""
        lines = []

        if comparison["regressions"]:
            lines.append("\n" + "!"*80)
            lines.append("REGRESSIONS DETECTED")
            lines.append("!"*80)

            for reg in comparison["regressions"]:
                severity_icon = "✗✗" if reg["severity"] == "CRITICAL" else "⚠"
                lines.append(f"  {severity_icon} [{reg['severity']}] {reg['message']}")

            lines.append("!"*80 + "\n")
        else:
            lines.append("\n✓ No regressions detected\n")

        if comparison["improvements"]:
            lines.append("\n" + "+"*80)
            lines.append("IMPROVEMENTS DETECTED")
            lines.append("+"*80)

            for imp in comparison["improvements"]:
                lines.append(f"  ✓ {imp['message']}")

            lines.append("+"*80 + "\n")

        return "\n".join(lines)

    def analyze_flipped_cases(self, current: Dict, baseline: Dict) -> str:
        """Analyze which cases changed from pass to fail or vice versa."""
        lines = []
        lines.append("\n" + "="*80)
        lines.append("CASE-BY-CASE ANALYSIS")
        lines.append("="*80)

        # Track flips
        positive_flips_to_fail = []
        positive_flips_to_pass = []
        negative_flips_to_fail = []
        negative_flips_to_pass = []

        # Compare positive cases (if we have the same number)
        if len(current.get("positive_cases", [])) == len(baseline.get("positive_cases", [])):
            for i, (curr_case, base_case) in enumerate(zip(
                current["positive_cases"], baseline["positive_cases"]
            )):
                if curr_case["passed"] != base_case["passed"]:
                    if curr_case["passed"]:
                        positive_flips_to_pass.append((i, curr_case))
                    else:
                        positive_flips_to_fail.append((i, curr_case))

        # Compare negative cases
        if len(current.get("negative_cases", [])) == len(baseline.get("negative_cases", [])):
            for i, (curr_case, base_case) in enumerate(zip(
                current["negative_cases"], baseline["negative_cases"]
            )):
                if curr_case["passed"] != base_case["passed"]:
                    if curr_case["passed"]:
                        negative_flips_to_pass.append((i, curr_case))
                    else:
                        negative_flips_to_fail.append((i, curr_case))

        # Report positive flips to fail (BAD)
        if positive_flips_to_fail:
            lines.append(f"\n✗ POSITIVE CASES THAT NOW FAIL: {len(positive_flips_to_fail)}")
            for idx, case in positive_flips_to_fail[:10]:  # Show first 10
                lines.append(f"  [{idx+1}] {case['line'][:70]}")

        # Report positive flips to pass (GOOD but unexpected)
        if positive_flips_to_pass:
            lines.append(f"\n✓ POSITIVE CASES THAT NOW PASS: {len(positive_flips_to_pass)}")
            for idx, case in positive_flips_to_pass[:10]:
                lines.append(f"  [{idx+1}] {case['line'][:70]}")

        # Report negative flips to pass (GOOD)
        if negative_flips_to_pass:
            lines.append(f"\n✓ NEGATIVE CASES THAT NOW PASS: {len(negative_flips_to_pass)}")
            for idx, case in negative_flips_to_pass[:10]:
                lines.append(f"  [{idx+1}] {case['line'][:70]}")

        # Report negative flips to fail (BAD)
        if negative_flips_to_fail:
            lines.append(f"\n✗ NEGATIVE CASES THAT NOW FAIL: {len(negative_flips_to_fail)}")
            for idx, case in negative_flips_to_fail[:10]:
                lines.append(f"  [{idx+1}] {case['line'][:70]}")

        if not any([positive_flips_to_fail, positive_flips_to_pass,
                    negative_flips_to_pass, negative_flips_to_fail]):
            lines.append("\n= No case flips detected (all cases maintained same pass/fail status)")

        lines.append("\n" + "="*80)
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Validate and compare test metrics",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output",
        help="Path to test output file to validate"
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("BASELINE", "CURRENT"),
        help="Compare two phases (e.g., baseline phase_1a)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all metrics files in outputs/testing/"
    )
    parser.add_argument(
        "--save",
        help="Save metrics to JSON file"
    )

    args = parser.parse_args()

    validator = MetricsValidator()
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    # Single file validation
    if args.output:
        print(f"\nValidating: {args.output}")
        metrics = validator.parse_output_file(args.output)

        if not metrics:
            print("✗ Failed to parse metrics")
            sys.exit(1)

        # Print metrics
        print("\n" + "="*80)
        print("METRICS SUMMARY")
        print("="*80)
        print(f"Total Cases:          {metrics['total_cases']}")
        print(f"Positive Accuracy:    {metrics['positive_accuracy']:.1%} ({metrics['positive_pass']}/{metrics['positive_total']})")
        print(f"Negative Accuracy:    {metrics['negative_accuracy']:.1%} ({metrics['negative_pass']}/{metrics['negative_total']})")
        print(f"Balanced Accuracy:    {metrics['balanced_accuracy']:.1%}")
        print(f"Precision:            {metrics['precision']:.3f}")
        print(f"Recall:               {metrics['recall']:.3f}")
        print(f"F1 Score:             {metrics['f1_score']:.3f}")
        print(f"Specificity:          {metrics['specificity']:.3f}")
        print(f"Time per Fragment:    {metrics['time_per_fragment']:.3f}s")
        print("="*80 + "\n")

        if args.save:
            Path(args.save).write_text(json.dumps(metrics, indent=2))
            print(f"✓ Metrics saved to: {args.save}\n")

    # Compare two phases
    elif args.compare:
        baseline_phase, current_phase = args.compare

        # Load metrics files
        baseline_file = OUTPUTS_DIR / f"metrics_{baseline_phase}.json"
        current_file = OUTPUTS_DIR / f"metrics_{current_phase}.json"

        if not baseline_file.exists():
            print(f"✗ Baseline metrics not found: {baseline_file}")
            sys.exit(1)

        if not current_file.exists():
            print(f"✗ Current metrics not found: {current_file}")
            sys.exit(1)

        baseline_metrics = json.loads(baseline_file.read_text())
        current_metrics = json.loads(current_file.read_text())

        # Generate comparison
        comparison = validator.compare_metrics(current_metrics, baseline_metrics)

        # Print comparison table
        print(validator.generate_comparison_table(current_metrics, baseline_metrics))

        # Print regression analysis
        print(validator.flag_regressions(comparison))

        # Print case flips
        print(validator.analyze_flipped_cases(current_metrics, baseline_metrics))

        # Overall verdict
        has_critical = any(r["severity"] == "CRITICAL" for r in comparison["regressions"])
        has_warnings = any(r["severity"] == "WARNING" for r in comparison["regressions"])

        print("\n" + "="*80)
        print("OVERALL VERDICT")
        print("="*80)
        if has_critical:
            print("✗ CRITICAL REGRESSIONS DETECTED - DO NOT PROCEED")
        elif has_warnings:
            print("⚠ WARNINGS DETECTED - REVIEW BEFORE PROCEEDING")
        else:
            print("✓ NO REGRESSIONS - SAFE TO PROCEED")
        print("="*80 + "\n")

        sys.exit(1 if has_critical else 0)

    # Validate all files
    elif args.all:
        metrics_files = sorted(OUTPUTS_DIR.glob("metrics_*.json"))

        if not metrics_files:
            print("✗ No metrics files found in outputs/testing/")
            sys.exit(1)

        print(f"\nFound {len(metrics_files)} metrics files:")
        for f in metrics_files:
            print(f"  - {f.name}")

        print("\n" + "="*80)
        print("METRICS ACROSS ALL PHASES")
        print("="*80)
        print(f"{'Phase':<15} {'Pos Acc':>10} {'Neg Acc':>10} {'Bal Acc':>10} {'F1':>8} {'Time/Frag':>12}")
        print("-"*80)

        for metrics_file in metrics_files:
            phase_name = metrics_file.stem.replace("metrics_", "")
            metrics = json.loads(metrics_file.read_text())

            print(f"{phase_name:<15} {metrics['positive_accuracy']:>9.1%} {metrics['negative_accuracy']:>9.1%} "
                  f"{metrics['balanced_accuracy']:>9.1%} {metrics['f1_score']:>7.3f} {metrics['time_per_fragment']:>10.2f}s")

        print("="*80 + "\n")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
