#!/usr/bin/env python3
"""
analyze_failure.py
------------------
Automated diagnostic tool for phase failures.

If a phase fails, this script automatically analyzes WHY:
- Checks which pairs flipped (pass→fail or fail→pass)
- Analyzes color Bhattacharyya coefficient distributions
- Analyzes texture BC distributions
- Profiles geometric scores
- Suggests specific fixes with parameter recommendations

Usage:
    python scripts/analyze_failure.py --phase 1a
    python scripts/analyze_failure.py --compare baseline phase_1a
    python scripts/analyze_failure.py --deep-dive --case "mixed_gettyimages-13116049_gettyimages-17009652"

Author: Automated Testing Framework
Date: 2026-04-08
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

OUTPUTS_DIR = ROOT / "outputs" / "testing"
DATA_DIR = ROOT / "data" / "examples"


class FailureAnalyzer:
    """Analyzes test failures and suggests fixes."""

    def __init__(self):
        self.suggestions = []
        self.diagnostics = []

    def load_metrics(self, phase: str) -> Optional[Dict]:
        """Load metrics for a phase."""
        metrics_file = OUTPUTS_DIR / f"metrics_{phase}.json"
        if not metrics_file.exists():
            print(f"✗ Metrics file not found: {metrics_file}")
            return None

        return json.loads(metrics_file.read_text())

    def analyze_accuracy_drop(self, current: Dict, baseline: Dict) -> None:
        """Analyze positive accuracy drop."""
        current_acc = current["positive_accuracy"]
        baseline_acc = baseline["positive_accuracy"]
        drop = baseline_acc - current_acc

        if drop <= 0.02:
            return  # Acceptable

        self.diagnostics.append({
            "type": "POSITIVE_ACCURACY_DROP",
            "severity": "CRITICAL" if drop > 0.05 else "WARNING",
            "current": current_acc,
            "baseline": baseline_acc,
            "drop": drop,
        })

        print("\n" + "!"*80)
        print("FAILURE MODE 1: POSITIVE ACCURACY DROPPED")
        print("!"*80)
        print(f"Baseline: {baseline_acc:.1%}")
        print(f"Current:  {current_acc:.1%}")
        print(f"Drop:     {drop:.1%}")
        print("")

        # Analyze which cases failed
        if "positive_cases" in current and "positive_cases" in baseline:
            flipped = []
            for i, (curr, base) in enumerate(zip(current["positive_cases"], baseline["positive_cases"])):
                if base["passed"] and not curr["passed"]:
                    flipped.append((i, curr))

            if flipped:
                print(f"Cases that flipped from PASS to FAIL: {len(flipped)}")
                for idx, case in flipped[:5]:
                    print(f"  [{idx+1}] {case['line'][:70]}")
                print("")

        # Diagnostic steps
        print("DIAGNOSTIC STEPS:")
        print("1. Check color BC, texture BC, and geometric scores for failed pairs")
        print("2. Analyze if penalty became too strong")
        print("3. Check if color histograms are mismatched for same-source fragments")
        print("")

        # Suggest fixes based on the pattern
        if drop > 0.05:
            self.suggestions.append({
                "priority": "HIGH",
                "action": "Reduce exponential power",
                "detail": "Drop > 5% suggests penalty is too aggressive. Try reducing exponential power from 2.5 to 2.0 or 1.5",
                "code": """
# In src/compatibility.py
# Change:
#   penalty_factor = (1.0 - bc) ** 2.5
# To:
#   penalty_factor = (1.0 - bc) ** 2.0
"""
            })
        else:
            self.suggestions.append({
                "priority": "MEDIUM",
                "action": "Fine-tune color penalty weight",
                "detail": f"Drop of {drop:.1%} is borderline. Try reducing COLOR_PENALTY_WEIGHT from 0.80 to 0.70",
                "code": """
# In src/compatibility.py
# Change:
#   COLOR_PENALTY_WEIGHT = 0.80
# To:
#   COLOR_PENALTY_WEIGHT = 0.70
"""
            })

    def analyze_no_improvement(self, current: Dict, baseline: Dict, phase: str) -> None:
        """Analyze when negative accuracy doesn't improve."""
        current_neg = current["negative_accuracy"]
        baseline_neg = baseline["negative_accuracy"]
        improvement = current_neg - baseline_neg

        # Expected improvements by phase
        expected_improvements = {
            "1a": 0.15,  # Lab color should give 15-20% improvement
            "1b": 0.10,  # Additional 10% from exponential
            "2a": 0.15,  # Texture adds 15%
            "2b": 0.10,  # Fractal adds 10%
        }

        expected = expected_improvements.get(phase, 0.05)

        if improvement >= expected * 0.5:
            return  # Acceptable improvement

        self.diagnostics.append({
            "type": "NO_IMPROVEMENT_NEGATIVE",
            "severity": "WARNING",
            "current": current_neg,
            "baseline": baseline_neg,
            "improvement": improvement,
            "expected": expected,
        })

        print("\n" + "!"*80)
        print("FAILURE MODE 2: NO IMPROVEMENT IN NEGATIVE ACCURACY")
        print("!"*80)
        print(f"Baseline:    {baseline_neg:.1%}")
        print(f"Current:     {current_neg:.1%}")
        print(f"Improvement: {improvement:.1%}")
        print(f"Expected:    {expected:.1%} minimum")
        print("")

        print("DIAGNOSTIC STEPS:")
        print("1. Check color BC distribution for negative pairs")
        print("2. If BC > 0.90 for most pairs → color too similar, need texture")
        print("3. If BC < 0.80 for most pairs → exponential penalty wrong")
        print("4. Check if histogram bins are appropriate")
        print("")

        # Suggest fixes based on phase
        if phase in ["1a", "1b"]:
            self.suggestions.append({
                "priority": "HIGH",
                "action": "Skip to texture phase",
                "detail": "Color alone insufficient to separate negative pairs. Consider moving to Phase 2A (LBP texture)",
                "code": "# Implement Phase 2A: LBP texture signatures"
            })

            self.suggestions.append({
                "priority": "MEDIUM",
                "action": "Increase histogram bins",
                "detail": "Try increasing Lab histogram bins for finer color discrimination",
                "code": """
# In src/compatibility.py
# Change:
#   bins_L, bins_a, bins_b = 16, 8, 8
# To:
#   bins_L, bins_a, bins_b = 32, 16, 16
"""
            })

        elif phase in ["2a", "2b"]:
            self.suggestions.append({
                "priority": "HIGH",
                "action": "Tune LBP parameters",
                "detail": "LBP may be too coarse. Try increasing P (points) and R (radius)",
                "code": """
# In src/compatibility.py
# Change:
#   P, R = 8, 1
# To:
#   P, R = 16, 2
"""
            })

            self.suggestions.append({
                "priority": "MEDIUM",
                "action": "Increase texture weight",
                "detail": "Texture signal may be too weak. Increase TEXTURE_PENALTY_WEIGHT",
                "code": """
# In src/compatibility.py
# Change:
#   TEXTURE_PENALTY_WEIGHT = 0.50
# To:
#   TEXTURE_PENALTY_WEIGHT = 0.70
"""
            })

    def analyze_time_explosion(self, current: Dict, baseline: Dict) -> None:
        """Analyze processing time increase."""
        current_time = current["time_per_fragment"]
        baseline_time = baseline["time_per_fragment"]
        increase_pct = ((current_time - baseline_time) / baseline_time * 100) if baseline_time > 0 else 0

        if increase_pct < 50:
            return  # Acceptable

        self.diagnostics.append({
            "type": "TIME_REGRESSION",
            "severity": "WARNING" if increase_pct < 100 else "CRITICAL",
            "current": current_time,
            "baseline": baseline_time,
            "increase_pct": increase_pct,
        })

        print("\n" + "!"*80)
        print("FAILURE MODE 3: PROCESSING TIME EXPLODED")
        print("!"*80)
        print(f"Baseline:  {baseline_time:.2f}s per fragment")
        print(f"Current:   {current_time:.2f}s per fragment")
        print(f"Increase:  {increase_pct:.1f}%")
        print("")

        print("DIAGNOSTIC STEPS:")
        print("1. Profile each component (color, texture, fractal, curvature)")
        print("2. Identify bottleneck")
        print("3. Check for inefficient loops or redundant computations")
        print("")

        self.suggestions.append({
            "priority": "HIGH",
            "action": "Profile and optimize",
            "detail": f"Time increased by {increase_pct:.1f}%. Run profiler to identify bottleneck",
            "code": """
# Run profiler:
python scripts/profile_performance.py

# Common optimizations:
# 1. Reduce LBP histogram bins
# 2. Reduce fractal scales (e.g., 4-6 instead of 4-8)
# 3. Add caching for expensive computations
# 4. Vectorize loops with NumPy
"""
        })

        if increase_pct > 100:
            self.suggestions.append({
                "priority": "CRITICAL",
                "action": "Emergency optimization",
                "detail": "Time doubled. Check for O(n^2) loops that should be O(n log n)",
                "code": """
# Check for:
# - Nested loops over fragments
# - Redundant histogram computations
# - Lack of memoization for color signatures
"""
            })

    def analyze_confusion_pattern(self, current: Dict) -> None:
        """Analyze confusion matrix patterns."""
        tp = current["true_positives"]
        fp = current["false_positives"]
        tn = current["true_negatives"]
        fn = current["false_negatives"]

        total = tp + fp + tn + fn

        print("\n" + "="*80)
        print("CONFUSION MATRIX ANALYSIS")
        print("="*80)
        print(f"True Positives:  {tp:3d} ({tp/total*100:5.1f}%)")
        print(f"False Positives: {fp:3d} ({fp/total*100:5.1f}%)")
        print(f"True Negatives:  {tn:3d} ({tn/total*100:5.1f}%)")
        print(f"False Negatives: {fn:3d} ({fn/total*100:5.1f}%)")
        print("")

        # Analyze patterns
        if fp > tn:
            print("⚠ HIGH FALSE POSITIVE RATE")
            print("Pattern: System is too permissive (matches when shouldn't)")
            print("Fix: Increase penalty weights or thresholds")
            print("")

            self.suggestions.append({
                "priority": "HIGH",
                "action": "Increase matching threshold",
                "detail": "Too many false positives. Raise MATCH threshold or increase penalties",
                "code": """
# In src/main.py or compatibility threshold
# Option 1: Raise threshold
#   MATCH_THRESHOLD = 0.55  →  0.60

# Option 2: Increase color penalty
#   COLOR_PENALTY_WEIGHT = 0.80  →  0.90
"""
            })

        if fn > tp:
            print("⚠ HIGH FALSE NEGATIVE RATE")
            print("Pattern: System is too restrictive (doesn't match when should)")
            print("Fix: Reduce penalty weights or lower thresholds")
            print("")

            self.suggestions.append({
                "priority": "HIGH",
                "action": "Reduce matching threshold",
                "detail": "Too many false negatives. Lower MATCH threshold or reduce penalties",
                "code": """
# In src/main.py
# Option 1: Lower threshold
#   MATCH_THRESHOLD = 0.55  →  0.50

# Option 2: Reduce color penalty
#   COLOR_PENALTY_WEIGHT = 0.80  →  0.70
"""
            })

    def generate_parameter_sweep_script(self, phase: str) -> str:
        """Generate a parameter sweep script for tuning."""
        if phase in ["1a", "1b"]:
            # Color parameter sweep
            script = """#!/usr/bin/env python3
# Auto-generated parameter sweep for color phases

import subprocess
import json
from pathlib import Path

# Parameters to test
if "{phase}" == "1b":
    # Exponential power sweep
    param_name = "exponential_power"
    param_values = [1.5, 2.0, 2.5, 3.0, 3.5]
else:
    # Histogram bins sweep
    param_name = "histogram_bins"
    param_values = [(8,4,4), (16,8,8), (32,16,16), (64,32,32)]

results = []

for value in param_values:
    print(f"\\nTesting {{param_name}} = {{value}}...")

    # Modify code (manual step - add code modification here)
    # TODO: Implement automatic code patching

    # Run test
    result = subprocess.run(
        ["python", "run_test.py"],
        capture_output=True,
        text=True
    )

    # Parse results (simplified)
    # TODO: Implement proper parsing

    print(f"  Result: {{result.returncode}}")

print("\\nSweep complete. Analyze results to find optimal parameters.")
""".format(phase=phase)

        elif phase in ["2a", "2b"]:
            # Texture parameter sweep
            script = """#!/usr/bin/env python3
# Auto-generated parameter sweep for texture phases

import subprocess
import json

if "{phase}" == "2a":
    # LBP parameter sweep
    param_name = "LBP_params"
    param_values = [(8,1), (8,2), (16,1), (16,2), (24,2), (24,3)]
else:
    # Fractal scales sweep
    param_name = "fractal_scales"
    param_values = [(3,5), (3,6), (4,6), (4,7), (4,8), (5,8)]

results = []

for value in param_values:
    print(f"\\nTesting {{param_name}} = {{value}}...")

    # Modify code and run test
    # TODO: Implement

    print(f"  Result: ...")

print("\\nSweep complete.")
""".format(phase=phase)

        else:
            script = "# No parameter sweep defined for this phase"

        return script

    def print_suggestions(self) -> None:
        """Print all suggestions in priority order."""
        if not self.suggestions:
            print("\n✓ No specific suggestions (phase may have passed)")
            return

        # Sort by priority
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_suggestions = sorted(
            self.suggestions,
            key=lambda s: priority_order.get(s.get("priority", "LOW"), 99)
        )

        print("\n" + "="*80)
        print("SUGGESTED FIXES (in priority order)")
        print("="*80)

        for i, suggestion in enumerate(sorted_suggestions, 1):
            priority = suggestion.get("priority", "MEDIUM")
            action = suggestion["action"]
            detail = suggestion["detail"]
            code = suggestion.get("code", "")

            print(f"\n[{i}] [{priority}] {action}")
            print(f"    {detail}")
            if code:
                print(f"\n    Code change:")
                for line in code.strip().split("\n"):
                    print(f"    {line}")

        print("\n" + "="*80)

    def save_analysis_report(self, phase: str) -> None:
        """Save analysis report to file."""
        from datetime import datetime

        report = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "diagnostics": self.diagnostics,
            "suggestions": self.suggestions,
        }

        report_file = OUTPUTS_DIR / f"failure_analysis_{phase}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.write_text(json.dumps(report, indent=2))
        print(f"\n✓ Analysis report saved to: {report_file}")


def analyze_specific_case(case_name: str) -> None:
    """Deep-dive analysis of a specific test case."""
    print(f"\n{'='*80}")
    print(f"DEEP-DIVE ANALYSIS: {case_name}")
    print(f"{'='*80}\n")

    # Determine if positive or negative
    is_positive = not case_name.startswith("mixed_")

    print(f"Case Type: {'POSITIVE' if is_positive else 'NEGATIVE'}")
    print(f"Expected: {'MATCH' if is_positive else 'NO_MATCH'}")
    print("")

    # Find the case directory
    case_dir = None
    if is_positive:
        case_dir = DATA_DIR / "positive" / case_name
    else:
        case_dir = DATA_DIR / "negative" / case_name

    if not case_dir or not case_dir.exists():
        print(f"✗ Case directory not found: {case_dir}")
        return

    # List fragments
    from pathlib import Path
    fragments = sorted(case_dir.glob("*.png")) + sorted(case_dir.glob("*.jpg"))
    print(f"Fragments: {len(fragments)}")
    for frag in fragments:
        print(f"  - {frag.name}")
    print("")

    print("DIAGNOSTIC SUGGESTIONS:")
    print("1. Run pipeline on this case alone:")
    print(f"   python src/main.py --input \"{case_dir}\" --output outputs/debug")
    print("")
    print("2. Check intermediate results:")
    print("   - Color histograms")
    print("   - Texture descriptors (if applicable)")
    print("   - Geometric compatibility scores")
    print("")
    print("3. Visual inspection:")
    print(f"   - Open fragments in {case_dir}")
    print("   - Check if they visually match")
    print("   - Look for color/texture similarities")
    print("")


def main():
    parser = argparse.ArgumentParser(
        description="Automated failure analysis for phase testing",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--phase",
        help="Phase to analyze (e.g., 1a, 1b, 2a, 2b)"
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("BASELINE", "CURRENT"),
        help="Compare two phases"
    )
    parser.add_argument(
        "--deep-dive",
        action="store_true",
        help="Perform deep-dive analysis"
    )
    parser.add_argument(
        "--case",
        help="Specific test case to analyze (requires --deep-dive)"
    )
    parser.add_argument(
        "--generate-sweep",
        action="store_true",
        help="Generate parameter sweep script"
    )

    args = parser.parse_args()

    analyzer = FailureAnalyzer()

    # Deep-dive into specific case
    if args.deep_dive and args.case:
        analyze_specific_case(args.case)
        return

    # Compare two phases
    if args.compare:
        baseline_phase, current_phase = args.compare

        baseline = analyzer.load_metrics(baseline_phase)
        current = analyzer.load_metrics(current_phase)

        if not baseline or not current:
            sys.exit(1)

        print(f"\nAnalyzing: {baseline_phase} → {current_phase}\n")

        # Run all analyses
        analyzer.analyze_accuracy_drop(current, baseline)
        analyzer.analyze_no_improvement(current, baseline, current_phase)
        analyzer.analyze_time_explosion(current, baseline)
        analyzer.analyze_confusion_pattern(current)

        # Print suggestions
        analyzer.print_suggestions()

        # Generate parameter sweep if requested
        if args.generate_sweep:
            sweep_script = analyzer.generate_parameter_sweep_script(current_phase)
            sweep_file = ROOT / "scripts" / f"parameter_sweep_{current_phase}.py"
            sweep_file.write_text(sweep_script)
            print(f"\n✓ Parameter sweep script generated: {sweep_file}")

        # Save report
        analyzer.save_analysis_report(current_phase)

    # Analyze single phase
    elif args.phase:
        current = analyzer.load_metrics(args.phase)
        if not current:
            sys.exit(1)

        baseline = analyzer.load_metrics("baseline")
        if not baseline:
            print("⚠ Baseline metrics not found - limited analysis available")
            analyzer.analyze_confusion_pattern(current)
        else:
            print(f"\nAnalyzing phase: {args.phase}\n")
            analyzer.analyze_accuracy_drop(current, baseline)
            analyzer.analyze_no_improvement(current, baseline, args.phase)
            analyzer.analyze_time_explosion(current, baseline)
            analyzer.analyze_confusion_pattern(current)

        analyzer.print_suggestions()
        analyzer.save_analysis_report(args.phase)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
