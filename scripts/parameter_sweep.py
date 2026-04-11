#!/usr/bin/env python3
"""
parameter_sweep.py
------------------
Automated parameter sweeps for phase tuning.

If a phase needs tuning, this script automatically runs parameter sweeps:
- Exponential power (Phase 1B)
- Lab histogram bins (Phase 1A)
- LBP parameters (Phase 2A)
- Fractal scales (Phase 2B)

Finds optimal parameters by maximizing balanced accuracy.

Usage:
    python scripts/parameter_sweep.py --phase 1b --param exponential_power
    python scripts/parameter_sweep.py --phase 2a --param lbp
    python scripts/parameter_sweep.py --quick  # Reduced parameter space

Author: Automated Testing Framework
Date: 2026-04-08
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

OUTPUTS_DIR = ROOT / "outputs" / "testing"
SWEEP_DIR = OUTPUTS_DIR / "parameter_sweeps"


class ParameterSweeper:
    """Runs automated parameter sweeps."""

    def __init__(self, phase: str, quick: bool = False):
        self.phase = phase
        self.quick = quick
        self.results = []
        SWEEP_DIR.mkdir(parents=True, exist_ok=True)

    def backup_file(self, filepath: Path) -> str:
        """Backup a file before modification."""
        backup_path = filepath.with_suffix(filepath.suffix + ".backup")
        content = filepath.read_text()
        backup_path.write_text(content)
        return content

    def restore_file(self, filepath: Path, content: str):
        """Restore file from backup content."""
        filepath.write_text(content)

    def modify_code(self, param_name: str, value: Any) -> bool:
        """
        Modify source code to set parameter value.

        Returns True if modification successful.
        """
        compat_file = ROOT / "src" / "compatibility.py"

        if not compat_file.exists():
            print(f"✗ File not found: {compat_file}")
            return False

        content = compat_file.read_text()
        modified = False

        # Exponential power
        if param_name == "exponential_power":
            # Look for pattern: penalty_factor = (1.0 - bc) ** X
            import re
            pattern = r'(penalty_factor\s*=\s*\(1\.0\s*-\s*\w+\)\s*\*\*\s*)([\d.]+)'
            new_line = f'\\g<1>{value}'
            content, count = re.subn(pattern, new_line, content)
            modified = count > 0

        # Lab histogram bins
        elif param_name == "lab_bins":
            import re
            # Pattern: bins_L, bins_a, bins_b = X, Y, Z
            L, a, b = value
            pattern = r'(bins_L,\s*bins_a,\s*bins_b\s*=\s*)([\d,\s]+)'
            new_line = f'\\g<1>{L}, {a}, {b}'
            content, count = re.subn(pattern, new_line, content)
            modified = count > 0

        # LBP parameters
        elif param_name == "lbp_params":
            import re
            P, R = value
            # Look for P = X, R = Y
            pattern_p = r'(P\s*=\s*)(\d+)'
            pattern_r = r'(R\s*=\s*)(\d+)'
            content, count_p = re.subn(pattern_p, f'\\g<1>{P}', content)
            content, count_r = re.subn(pattern_r, f'\\g<1>{R}', content)
            modified = (count_p > 0 and count_r > 0)

        # Color penalty weight
        elif param_name == "color_penalty_weight":
            import re
            pattern = r'(COLOR_PENALTY_WEIGHT\s*=\s*)([\d.]+)'
            new_line = f'\\g<1>{value}'
            content, count = re.subn(pattern, new_line, content)
            modified = count > 0

        else:
            print(f"✗ Unknown parameter: {param_name}")
            return False

        if modified:
            compat_file.write_text(content)
            return True
        else:
            print(f"⚠ Could not modify parameter {param_name}")
            return False

    def run_test(self) -> Dict:
        """
        Run the test suite and return metrics.

        Returns dict with metrics or None if failed.
        """
        try:
            cmd = [
                sys.executable,
                str(ROOT / "run_test.py"),
                "--no-rotate",  # Faster for parameter sweep
                "--results", str(ROOT / "outputs" / "sweep_test"),
                "--logs", str(ROOT / "outputs" / "sweep_logs"),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                return {"success": False}

            # Parse output (simplified)
            output = result.stdout + result.stderr

            # Extract pass/fail counts
            positive_pass = 0
            positive_total = 0
            negative_pass = 0
            negative_total = 0

            for line in output.splitlines():
                if " positive " in line:
                    positive_total += 1
                    if "PASS" in line:
                        positive_pass += 1
                elif " negative " in line:
                    negative_total += 1
                    if "PASS" in line:
                        negative_pass += 1

            if positive_total == 0 and negative_total == 0:
                return {"success": False}

            metrics = {
                "success": True,
                "positive_accuracy": positive_pass / positive_total if positive_total > 0 else 0,
                "negative_accuracy": negative_pass / negative_total if negative_total > 0 else 0,
                "balanced_accuracy": (
                    (positive_pass / positive_total if positive_total > 0 else 0) +
                    (negative_pass / negative_total if negative_total > 0 else 0)
                ) / 2.0,
            }

            return metrics

        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            return {"success": False}

    def sweep_exponential_power(self) -> List[Dict]:
        """Sweep exponential power values."""
        print("\nSweeping exponential power values...")

        if self.quick:
            powers = [1.5, 2.0, 2.5, 3.0]
        else:
            powers = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]

        compat_file = ROOT / "src" / "compatibility.py"
        original_content = self.backup_file(compat_file)

        results = []

        try:
            for power in powers:
                print(f"\n  Testing power = {power}...")

                # Modify code
                if not self.modify_code("exponential_power", power):
                    print(f"    ⚠ Could not modify code")
                    continue

                # Run test
                start_time = time.time()
                metrics = self.run_test()
                elapsed = time.time() - start_time

                if not metrics.get("success"):
                    print(f"    ✗ Test failed")
                    continue

                result = {
                    "power": power,
                    "positive_accuracy": metrics["positive_accuracy"],
                    "negative_accuracy": metrics["negative_accuracy"],
                    "balanced_accuracy": metrics["balanced_accuracy"],
                    "time": elapsed,
                }

                results.append(result)

                print(f"    ✓ Pos: {result['positive_accuracy']:.1%}  "
                      f"Neg: {result['negative_accuracy']:.1%}  "
                      f"Bal: {result['balanced_accuracy']:.1%}  "
                      f"Time: {elapsed:.1f}s")

        finally:
            # Restore original
            self.restore_file(compat_file, original_content)
            print(f"\n  ✓ Restored original code")

        return results

    def sweep_lab_bins(self) -> List[Dict]:
        """Sweep Lab histogram bin configurations."""
        print("\nSweeping Lab histogram bin configurations...")

        if self.quick:
            bin_configs = [(8, 4, 4), (16, 8, 8), (32, 16, 16)]
        else:
            bin_configs = [(8, 4, 4), (16, 8, 8), (24, 12, 12), (32, 16, 16), (48, 24, 24)]

        compat_file = ROOT / "src" / "compatibility.py"
        original_content = self.backup_file(compat_file)

        results = []

        try:
            for bins in bin_configs:
                L, a, b = bins
                print(f"\n  Testing bins = ({L}, {a}, {b})...")

                if not self.modify_code("lab_bins", bins):
                    print(f"    ⚠ Could not modify code")
                    continue

                start_time = time.time()
                metrics = self.run_test()
                elapsed = time.time() - start_time

                if not metrics.get("success"):
                    print(f"    ✗ Test failed")
                    continue

                result = {
                    "bins_L": L,
                    "bins_a": a,
                    "bins_b": b,
                    "positive_accuracy": metrics["positive_accuracy"],
                    "negative_accuracy": metrics["negative_accuracy"],
                    "balanced_accuracy": metrics["balanced_accuracy"],
                    "time": elapsed,
                }

                results.append(result)

                print(f"    ✓ Pos: {result['positive_accuracy']:.1%}  "
                      f"Neg: {result['negative_accuracy']:.1%}  "
                      f"Bal: {result['balanced_accuracy']:.1%}")

        finally:
            self.restore_file(compat_file, original_content)
            print(f"\n  ✓ Restored original code")

        return results

    def sweep_lbp_params(self) -> List[Dict]:
        """Sweep LBP parameter configurations."""
        print("\nSweeping LBP parameter configurations...")

        if self.quick:
            lbp_configs = [(8, 1), (16, 1), (16, 2)]
        else:
            lbp_configs = [(8, 1), (8, 2), (16, 1), (16, 2), (24, 2), (24, 3)]

        compat_file = ROOT / "src" / "compatibility.py"
        original_content = self.backup_file(compat_file)

        results = []

        try:
            for params in lbp_configs:
                P, R = params
                print(f"\n  Testing LBP (P={P}, R={R})...")

                if not self.modify_code("lbp_params", params):
                    print(f"    ⚠ Could not modify code")
                    continue

                start_time = time.time()
                metrics = self.run_test()
                elapsed = time.time() - start_time

                if not metrics.get("success"):
                    print(f"    ✗ Test failed")
                    continue

                result = {
                    "P": P,
                    "R": R,
                    "positive_accuracy": metrics["positive_accuracy"],
                    "negative_accuracy": metrics["negative_accuracy"],
                    "balanced_accuracy": metrics["balanced_accuracy"],
                    "time": elapsed,
                }

                results.append(result)

                print(f"    ✓ Pos: {result['positive_accuracy']:.1%}  "
                      f"Neg: {result['negative_accuracy']:.1%}  "
                      f"Bal: {result['balanced_accuracy']:.1%}")

        finally:
            self.restore_file(compat_file, original_content)
            print(f"\n  ✓ Restored original code")

        return results

    def analyze_results(self, results: List[Dict], param_name: str) -> Dict:
        """Analyze sweep results and find optimal configuration."""
        if not results:
            return None

        # Find best by balanced accuracy
        best = max(results, key=lambda r: r.get("balanced_accuracy", 0))

        print("\n" + "="*80)
        print("SWEEP RESULTS ANALYSIS")
        print("="*80)
        print(f"\nParameter: {param_name}")
        print(f"Configurations tested: {len(results)}")
        print("")

        # Print all results
        print(f"{'Config':<20} {'Pos Acc':>10} {'Neg Acc':>10} {'Bal Acc':>10} {'Time':>8}")
        print("-"*80)

        for r in results:
            if param_name == "exponential_power":
                config = f"Power={r['power']}"
            elif param_name == "lab_bins":
                config = f"({r['bins_L']},{r['bins_a']},{r['bins_b']})"
            elif param_name == "lbp_params":
                config = f"P={r['P']}, R={r['R']}"
            else:
                config = str(r)

            marker = " ← BEST" if r == best else ""

            print(f"{config:<20} {r['positive_accuracy']:>9.1%} {r['negative_accuracy']:>9.1%} "
                  f"{r['balanced_accuracy']:>9.1%} {r.get('time', 0):>7.1f}s{marker}")

        print("="*80)

        # Recommendation
        print("\nRECOMMENDATION:")
        if param_name == "exponential_power":
            print(f"  Use exponential power = {best['power']}")
        elif param_name == "lab_bins":
            print(f"  Use Lab bins = ({best['bins_L']}, {best['bins_a']}, {best['bins_b']})")
        elif param_name == "lbp_params":
            print(f"  Use LBP parameters: P={best['P']}, R={best['R']}")

        print(f"  Expected balanced accuracy: {best['balanced_accuracy']:.1%}")
        print("")

        return best

    def save_results(self, param_name: str, results: List[Dict], best: Dict):
        """Save sweep results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = SWEEP_DIR / f"sweep_{self.phase}_{param_name}_{timestamp}.json"

        data = {
            "timestamp": datetime.now().isoformat(),
            "phase": self.phase,
            "parameter": param_name,
            "results": results,
            "best_config": best,
        }

        output_file.write_text(json.dumps(data, indent=2))
        print(f"✓ Results saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Automated parameter sweeps for phase tuning",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--phase",
        choices=["1a", "1b", "2a", "2b"],
        required=True,
        help="Phase to sweep parameters for"
    )
    parser.add_argument(
        "--param",
        help="Specific parameter to sweep (auto-detected if not specified)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick sweep with reduced parameter space"
    )

    args = parser.parse_args()

    sweeper = ParameterSweeper(args.phase, quick=args.quick)

    # Determine which parameter to sweep
    param_name = args.param

    if not param_name:
        # Auto-detect based on phase
        param_map = {
            "1a": "lab_bins",
            "1b": "exponential_power",
            "2a": "lbp_params",
            "2b": None,  # No automated sweep for fractal yet
        }
        param_name = param_map.get(args.phase)

        if not param_name:
            print(f"✗ No default parameter sweep for phase {args.phase}")
            print("  Specify --param explicitly")
            sys.exit(1)

    print(f"\n{'='*80}")
    print(f"PARAMETER SWEEP: Phase {args.phase} - {param_name}")
    print(f"{'='*80}")

    # Run appropriate sweep
    if param_name == "exponential_power":
        results = sweeper.sweep_exponential_power()
    elif param_name == "lab_bins":
        results = sweeper.sweep_lab_bins()
    elif param_name == "lbp_params":
        results = sweeper.sweep_lbp_params()
    else:
        print(f"✗ Unknown parameter: {param_name}")
        sys.exit(1)

    if not results:
        print("\n✗ No results obtained from sweep")
        sys.exit(1)

    # Analyze and report
    best = sweeper.analyze_results(results, param_name)

    # Save results
    sweeper.save_results(param_name, results, best)

    print("\n✓ Parameter sweep complete\n")


if __name__ == "__main__":
    main()
