#!/usr/bin/env python3
"""
test_phase_validation.py
------------------------
Automated test runner for each phase of the fragment reconstruction improvement roadmap.

This script validates EVERY phase autonomously:
- Runs benchmarks
- Extracts metrics
- Compares to baseline
- Returns PASS/FAIL with detailed diagnostics
- No human interaction required

Usage:
    python scripts/test_phase_validation.py --phase baseline
    python scripts/test_phase_validation.py --phase 1a --compare-to baseline
    python scripts/test_phase_validation.py --phase 1b --compare-to phase_1a
    python scripts/test_phase_validation.py --all

Author: Automated Testing Framework
Date: 2026-04-08
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

OUTPUTS_DIR = ROOT / "outputs" / "testing"
RESULTS_DIR = ROOT / "outputs" / "test_results"
LOGS_DIR = ROOT / "outputs" / "test_logs"
BASELINE_FILE = OUTPUTS_DIR / "baseline_metrics.json"
METRICS_CSV = OUTPUTS_DIR / "metrics_tracking.csv"

# Phase definitions
PHASES = {
    "baseline": {
        "name": "Baseline (Current Implementation)",
        "description": "Original BGR color space with standard compatibility scoring",
        "files_to_check": ["src/compatibility.py", "src/main.py"],
        "git_branch": None,
    },
    "1a": {
        "name": "Phase 1A: Lab Color Space",
        "description": "Replace BGR with Lab color space for perceptually uniform color comparison",
        "files_to_check": ["src/compatibility.py"],
        "expected_improvements": {
            "negative_accuracy": {"min": 0.15, "max": 0.25},
            "positive_accuracy": {"min": 0.95, "max": 1.00},
        },
        "acceptable_regressions": {
            "positive_accuracy": {"max_drop": 0.02},  # 2% drop acceptable
            "time_per_fragment": {"max_increase_pct": 20},  # 20% slower acceptable
        },
    },
    "1b": {
        "name": "Phase 1B: Exponential Color Penalty",
        "description": "Apply exponential penalty to color dissimilarity (power=2.5)",
        "files_to_check": ["src/compatibility.py"],
        "expected_improvements": {
            "negative_accuracy": {"min": 0.25, "max": 0.40},
            "positive_accuracy": {"min": 0.95, "max": 1.00},
        },
        "acceptable_regressions": {
            "positive_accuracy": {"max_drop": 0.03},
            "time_per_fragment": {"max_increase_pct": 20},
        },
    },
    "2a": {
        "name": "Phase 2A: LBP Texture Signatures",
        "description": "Add Local Binary Pattern texture descriptors",
        "files_to_check": ["src/compatibility.py"],
        "expected_improvements": {
            "negative_accuracy": {"min": 0.40, "max": 0.60},
            "positive_accuracy": {"min": 0.95, "max": 1.00},
        },
        "acceptable_regressions": {
            "positive_accuracy": {"max_drop": 0.03},
            "time_per_fragment": {"max_increase_pct": 30},
        },
    },
    "2b": {
        "name": "Phase 2B: Fractal Dimension",
        "description": "Add box-counting fractal dimension to texture analysis",
        "files_to_check": ["src/compatibility.py"],
        "expected_improvements": {
            "negative_accuracy": {"min": 0.55, "max": 0.75},
            "positive_accuracy": {"min": 0.95, "max": 1.00},
        },
        "acceptable_regressions": {
            "positive_accuracy": {"max_drop": 0.03},
            "time_per_fragment": {"max_increase_pct": 40},
        },
    },
}

# Thresholds
POSITIVE_ACCURACY_CRITICAL = 0.93  # Below this is a critical failure
REGRESSION_ALERT_THRESHOLD = 0.02  # 2% drop triggers warning
TIME_REGRESSION_THRESHOLD = 1.50  # 50% slower triggers warning


def setup_logging(phase: str) -> logging.Logger:
    """Configure logging for test run."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"test_phase_{phase}_{timestamp}.log"

    logger = logging.getLogger("test_phase_validation")
    logger.setLevel(logging.DEBUG)

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    ))

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def run_benchmark(logger: logging.Logger) -> Tuple[bool, Optional[str]]:
    """
    Run the benchmark test suite (run_test.py).

    Returns:
        (success, output_file_path)
    """
    logger.info("Running benchmark test suite...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUTS_DIR / f"test_results_{timestamp}.txt"

    try:
        # Run test with rotation enabled
        cmd = [
            sys.executable,
            str(ROOT / "run_test.py"),
            "--examples", str(ROOT / "data" / "examples"),
            "--results", str(RESULTS_DIR),
            "--logs", str(LOGS_DIR),
            "--rotate",
        ]

        logger.debug(f"Running command: {' '.join(cmd)}")
        start_time = time.time()

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )

        elapsed = time.time() - start_time
        logger.info(f"Benchmark completed in {elapsed:.1f}s")

        # Save output
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        output_file.write_text(result.stdout + "\n" + result.stderr)
        logger.info(f"Results saved to: {output_file}")

        if result.returncode != 0:
            logger.error(f"Benchmark failed with return code {result.returncode}")
            logger.error(f"stderr: {result.stderr}")
            return False, str(output_file)

        return True, str(output_file)

    except subprocess.TimeoutExpired:
        logger.error("Benchmark timed out after 10 minutes")
        return False, None
    except Exception as e:
        logger.error(f"Error running benchmark: {e}")
        return False, None


def parse_test_results(output_file: str, logger: logging.Logger) -> Optional[Dict]:
    """
    Parse test results from run_test.py output.

    Returns:
        Dictionary with metrics or None if parsing failed
    """
    logger.info(f"Parsing results from: {output_file}")

    try:
        content = Path(output_file).read_text()

        # Extract pass/fail counts
        total_cases = 0
        positive_pass = 0
        positive_total = 0
        negative_pass = 0
        negative_total = 0
        total_time = 0.0

        in_results_section = False
        for line in content.splitlines():
            # Look for results table
            if "RECONSTRUCTION TEST RESULTS" in line:
                in_results_section = True
                continue

            if not in_results_section:
                continue

            # Parse result lines
            if " positive " in line and ("PASS" in line or "FAIL" in line):
                positive_total += 1
                if "PASS" in line:
                    positive_pass += 1
                # Extract time
                parts = line.split()
                for i, part in enumerate(parts):
                    if i > 0 and parts[i-1].replace('.', '').isdigit():
                        try:
                            total_time += float(parts[i-1])
                            break
                        except ValueError:
                            pass

            elif " negative " in line and ("PASS" in line or "FAIL" in line):
                negative_total += 1
                if "PASS" in line:
                    negative_pass += 1
                # Extract time
                parts = line.split()
                for i, part in enumerate(parts):
                    if i > 0 and parts[i-1].replace('.', '').isdigit():
                        try:
                            total_time += float(parts[i-1])
                            break
                        except ValueError:
                            pass

        if positive_total == 0 and negative_total == 0:
            logger.error("Failed to parse any test results")
            return None

        total_cases = positive_total + negative_total

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "total_cases": total_cases,
            "positive_cases": positive_total,
            "positive_pass": positive_pass,
            "positive_accuracy": positive_pass / positive_total if positive_total > 0 else 0.0,
            "negative_cases": negative_total,
            "negative_pass": negative_pass,
            "negative_accuracy": negative_pass / negative_total if negative_total > 0 else 0.0,
            "balanced_accuracy": (
                (positive_pass / positive_total if positive_total > 0 else 0.0) +
                (negative_pass / negative_total if negative_total > 0 else 0.0)
            ) / 2.0,
            "total_time": total_time,
            "time_per_fragment": total_time / total_cases if total_cases > 0 else 0.0,
            "output_file": output_file,
        }

        logger.info(f"Parsed metrics: {json.dumps(metrics, indent=2)}")
        return metrics

    except Exception as e:
        logger.error(f"Error parsing results: {e}")
        return None


def validate_phase_prerequisites(phase: str, logger: logging.Logger) -> bool:
    """
    Validate that prerequisites for a phase are met.

    Returns:
        True if prerequisites are met, False otherwise
    """
    logger.info(f"Validating prerequisites for phase {phase}...")

    phase_info = PHASES.get(phase)
    if not phase_info:
        logger.error(f"Unknown phase: {phase}")
        return False

    # Check that required files exist
    for file_path in phase_info["files_to_check"]:
        full_path = ROOT / file_path
        if not full_path.exists():
            logger.error(f"Required file not found: {file_path}")
            return False
        logger.debug(f"Found required file: {file_path}")

    # For non-baseline phases, check that baseline exists
    if phase != "baseline" and not BASELINE_FILE.exists():
        logger.error("Baseline metrics not found. Run baseline phase first.")
        return False

    logger.info("Prerequisites validated successfully")
    return True


def compare_to_baseline(
    current_metrics: Dict,
    baseline_metrics: Dict,
    phase: str,
    logger: logging.Logger
) -> Tuple[bool, List[str]]:
    """
    Compare current metrics to baseline and determine if phase passes.

    Returns:
        (passed, issues_list)
    """
    logger.info(f"Comparing phase {phase} to baseline...")

    phase_info = PHASES.get(phase, {})
    expected = phase_info.get("expected_improvements", {})
    acceptable = phase_info.get("acceptable_regressions", {})

    issues = []
    critical_failure = False

    # Check positive accuracy (critical)
    pos_acc = current_metrics["positive_accuracy"]
    baseline_pos_acc = baseline_metrics["positive_accuracy"]
    pos_acc_drop = baseline_pos_acc - pos_acc

    if pos_acc < POSITIVE_ACCURACY_CRITICAL:
        issues.append(f"CRITICAL: Positive accuracy {pos_acc:.1%} is below critical threshold {POSITIVE_ACCURACY_CRITICAL:.1%}")
        critical_failure = True
    elif pos_acc_drop > acceptable.get("positive_accuracy", {}).get("max_drop", 0.02):
        issues.append(f"WARNING: Positive accuracy dropped by {pos_acc_drop:.1%} (baseline: {baseline_pos_acc:.1%} → current: {pos_acc:.1%})")
    else:
        logger.info(f"✓ Positive accuracy: {pos_acc:.1%} (drop: {pos_acc_drop:.1%})")

    # Check negative accuracy (improvement expected)
    neg_acc = current_metrics["negative_accuracy"]
    baseline_neg_acc = baseline_metrics["negative_accuracy"]
    neg_acc_improvement = neg_acc - baseline_neg_acc

    expected_neg_range = expected.get("negative_accuracy", {})
    if expected_neg_range:
        if neg_acc < expected_neg_range.get("min", 0):
            issues.append(f"WARNING: Negative accuracy {neg_acc:.1%} is below expected minimum {expected_neg_range['min']:.1%}")
        elif neg_acc > expected_neg_range.get("max", 1.0):
            logger.info(f"✓ Negative accuracy {neg_acc:.1%} exceeds expected maximum (good!)")
        else:
            logger.info(f"✓ Negative accuracy: {neg_acc:.1%} (improvement: {neg_acc_improvement:.1%})")

    # Check balanced accuracy
    bal_acc = current_metrics["balanced_accuracy"]
    baseline_bal_acc = baseline_metrics["balanced_accuracy"]
    bal_acc_improvement = bal_acc - baseline_bal_acc

    if bal_acc_improvement <= 0:
        issues.append(f"WARNING: Balanced accuracy did not improve (baseline: {baseline_bal_acc:.1%} → current: {bal_acc:.1%})")
    else:
        logger.info(f"✓ Balanced accuracy: {bal_acc:.1%} (improvement: {bal_acc_improvement:.1%})")

    # Check processing time
    time_per_frag = current_metrics["time_per_fragment"]
    baseline_time = baseline_metrics["time_per_fragment"]
    time_increase_pct = ((time_per_frag - baseline_time) / baseline_time * 100) if baseline_time > 0 else 0

    max_time_increase = acceptable.get("time_per_fragment", {}).get("max_increase_pct", 50)
    if time_increase_pct > max_time_increase:
        issues.append(f"WARNING: Processing time increased by {time_increase_pct:.1f}% (baseline: {baseline_time:.2f}s → current: {time_per_frag:.2f}s)")
    else:
        logger.info(f"✓ Processing time: {time_per_frag:.2f}s per fragment (increase: {time_increase_pct:.1f}%)")

    # Overall verdict
    passed = not critical_failure
    if passed:
        if issues:
            logger.warning(f"Phase {phase} PASSED with warnings")
        else:
            logger.info(f"Phase {phase} PASSED all checks")
    else:
        logger.error(f"Phase {phase} FAILED")

    return passed, issues


def save_metrics(phase: str, metrics: Dict, logger: logging.Logger):
    """Save metrics to JSON file and append to CSV tracking."""
    # Save JSON
    json_file = OUTPUTS_DIR / f"metrics_{phase}.json"
    json_file.write_text(json.dumps(metrics, indent=2))
    logger.info(f"Metrics saved to: {json_file}")

    # Append to CSV tracking
    csv_exists = METRICS_CSV.exists()
    with open(METRICS_CSV, "a") as f:
        if not csv_exists:
            # Write header
            f.write("phase,timestamp,positive_accuracy,negative_accuracy,balanced_accuracy,time_per_fragment,notes\n")

        # Write data row
        f.write(f"{phase},{metrics['timestamp']},{metrics['positive_accuracy']:.4f},"
                f"{metrics['negative_accuracy']:.4f},{metrics['balanced_accuracy']:.4f},"
                f"{metrics['time_per_fragment']:.3f},\n")

    logger.info(f"Metrics appended to tracking CSV: {METRICS_CSV}")


def generate_report(
    phase: str,
    metrics: Dict,
    baseline_metrics: Optional[Dict],
    passed: bool,
    issues: List[str],
    logger: logging.Logger
):
    """Generate a detailed test report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    phase_info = PHASES.get(phase, {})

    report = []
    report.append(f"# Phase {phase.upper()} Test Report")
    report.append(f"**Timestamp:** {timestamp}")
    report.append(f"**Status:** {'✓ PASS' if passed else '✗ FAIL'}")
    report.append("")

    report.append("## Phase Information")
    report.append(f"- **Name:** {phase_info.get('name', 'Unknown')}")
    report.append(f"- **Description:** {phase_info.get('description', 'N/A')}")
    report.append("")

    report.append("## Metrics")
    if baseline_metrics:
        report.append("| Metric | Baseline | Current | Change |")
        report.append("|--------|----------|---------|--------|")

        def format_change(current, baseline, pct=True):
            delta = current - baseline
            symbol = "✓" if delta >= 0 else "✗"
            if pct:
                return f"{delta:+.1%} {symbol}"
            else:
                return f"{delta:+.2f}s {symbol}"

        report.append(f"| Positive Accuracy | {baseline_metrics['positive_accuracy']:.1%} | "
                     f"{metrics['positive_accuracy']:.1%} | "
                     f"{format_change(metrics['positive_accuracy'], baseline_metrics['positive_accuracy'])} |")
        report.append(f"| Negative Accuracy | {baseline_metrics['negative_accuracy']:.1%} | "
                     f"{metrics['negative_accuracy']:.1%} | "
                     f"{format_change(metrics['negative_accuracy'], baseline_metrics['negative_accuracy'])} |")
        report.append(f"| Balanced Accuracy | {baseline_metrics['balanced_accuracy']:.1%} | "
                     f"{metrics['balanced_accuracy']:.1%} | "
                     f"{format_change(metrics['balanced_accuracy'], baseline_metrics['balanced_accuracy'])} |")
        report.append(f"| Processing Time | {baseline_metrics['time_per_fragment']:.2f}s | "
                     f"{metrics['time_per_fragment']:.2f}s | "
                     f"{format_change(metrics['time_per_fragment'], baseline_metrics['time_per_fragment'], pct=False)} |")
    else:
        report.append("| Metric | Value |")
        report.append("|--------|-------|")
        report.append(f"| Positive Accuracy | {metrics['positive_accuracy']:.1%} |")
        report.append(f"| Negative Accuracy | {metrics['negative_accuracy']:.1%} |")
        report.append(f"| Balanced Accuracy | {metrics['balanced_accuracy']:.1%} |")
        report.append(f"| Processing Time | {metrics['time_per_fragment']:.2f}s |")

    report.append("")

    if issues:
        report.append("## Issues")
        for issue in issues:
            report.append(f"- {issue}")
        report.append("")

    report.append("## Recommendation")
    if passed:
        next_phase = {
            "baseline": "1a",
            "1a": "1b",
            "1b": "2a",
            "2a": "2b",
            "2b": None,
        }.get(phase)

        if next_phase:
            report.append(f"✓ PROCEED to Phase {next_phase.upper()} ({PHASES[next_phase]['name']})")
        else:
            report.append("✓ ALL PHASES COMPLETE")
    else:
        report.append("✗ DO NOT PROCEED - Fix issues before continuing")

    report.append("")
    report.append("## Details")
    report.append(f"- Total test cases: {metrics['total_cases']}")
    report.append(f"- Positive cases: {metrics['positive_pass']}/{metrics['positive_cases']}")
    report.append(f"- Negative cases: {metrics['negative_pass']}/{metrics['negative_cases']}")
    report.append(f"- Total time: {metrics['total_time']:.1f}s")
    report.append(f"- Output file: {metrics['output_file']}")
    report.append("")

    # Save report
    report_file = OUTPUTS_DIR / f"report_{phase}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_file.write_text("\n".join(report))
    logger.info(f"Report saved to: {report_file}")

    # Also print to console
    print("\n" + "="*80)
    print("\n".join(report))
    print("="*80 + "\n")


def validate_phase(phase: str, compare_to: Optional[str] = None) -> bool:
    """
    Main validation function for a phase.

    Returns:
        True if phase passes validation, False otherwise
    """
    logger = setup_logging(phase)

    logger.info(f"="*80)
    logger.info(f"Starting validation for phase: {phase}")
    logger.info(f"="*80)

    # Step 1: Validate prerequisites
    if not validate_phase_prerequisites(phase, logger):
        logger.error("Prerequisites not met")
        return False

    # Step 2: Run benchmark
    success, output_file = run_benchmark(logger)
    if not success:
        logger.error("Benchmark execution failed")
        return False

    # Step 3: Parse results
    metrics = parse_test_results(output_file, logger)
    if not metrics:
        logger.error("Failed to parse test results")
        return False

    # Step 4: Save metrics
    save_metrics(phase, metrics, logger)

    # Step 5: For baseline, just save and return success
    if phase == "baseline":
        json_file = BASELINE_FILE
        json_file.write_text(json.dumps(metrics, indent=2))
        logger.info(f"Baseline metrics saved to: {json_file}")
        generate_report(phase, metrics, None, True, [], logger)
        return True

    # Step 6: Load comparison metrics (baseline or previous phase)
    compare_phase = compare_to or "baseline"
    compare_file = BASELINE_FILE if compare_phase == "baseline" else OUTPUTS_DIR / f"metrics_{compare_phase}.json"

    if not compare_file.exists():
        logger.error(f"Comparison metrics not found: {compare_file}")
        logger.error(f"Run phase '{compare_phase}' first")
        return False

    baseline_metrics = json.loads(compare_file.read_text())

    # Step 7: Compare and validate
    passed, issues = compare_to_baseline(metrics, baseline_metrics, phase, logger)

    # Step 8: Generate report
    generate_report(phase, metrics, baseline_metrics, passed, issues, logger)

    return passed


def main():
    parser = argparse.ArgumentParser(
        description="Automated phase validation for fragment reconstruction improvements",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--phase",
        choices=list(PHASES.keys()),
        help="Phase to validate"
    )
    parser.add_argument(
        "--compare-to",
        help="Phase to compare against (default: baseline)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all phases in sequence"
    )

    args = parser.parse_args()

    if not args.phase and not args.all:
        parser.error("Either --phase or --all must be specified")

    # Create output directories
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    if args.all:
        # Run all phases in sequence
        phase_sequence = ["baseline", "1a", "1b", "2a", "2b"]
        all_passed = True

        for phase in phase_sequence:
            print(f"\n{'='*80}")
            print(f"VALIDATING PHASE: {phase}")
            print(f"{'='*80}\n")

            passed = validate_phase(phase)
            if not passed:
                print(f"\n✗ Phase {phase} FAILED - stopping validation sequence")
                all_passed = False
                break

            print(f"\n✓ Phase {phase} PASSED")

        if all_passed:
            print(f"\n{'='*80}")
            print("✓ ALL PHASES PASSED")
            print(f"{'='*80}\n")
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        # Run single phase
        passed = validate_phase(args.phase, args.compare_to)
        sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
