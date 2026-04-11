#!/usr/bin/env python3
"""
Quick Evolutionary Weight Test for Variant 1

Tests 3 key configurations to demonstrate the optimization strategy:
1. Baseline (current weights)
2. Color-optimized (increase color weight for pottery)
3. Balanced (optimize all weights for pottery)

This is a quick test to validate the approach before running full evolution.
"""

import sys
import subprocess
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Tuple

ROOT = Path(__file__).parent


def test_weight_configuration(weights: Dict[str, float], name: str) -> Tuple[float, float, float]:
    """
    Test a weight configuration by temporarily modifying ensemble_voting.py.

    Returns: (positive_acc, negative_acc, overall_acc)
    """
    # Validate weights sum to 1.0
    total = sum(weights.values())
    assert abs(total - 1.0) < 0.001, f"Weights must sum to 1.0, got {total}"

    # Path to ensemble_voting.py
    voting_file = ROOT / "src" / "ensemble_voting.py"
    backup_file = ROOT / "src" / "ensemble_voting.py.backup"

    # Backup original
    shutil.copy(voting_file, backup_file)

    try:
        # Read original file
        with open(voting_file, 'r') as f:
            content = f.read()

        # Replace default weights in ensemble_verdict_weighted
        new_weights_block = f"""    if weights is None:
        weights = {{
            'color': {weights['color']},
            'raw_compat': {weights['raw_compat']},
            'texture': {weights['texture']},
            'morphological': {weights['morphological']},
            'gabor': {weights['gabor']}
        }}"""

        # Find and replace
        start_marker = "    if weights is None:"
        end_marker = "        }"

        start_idx = content.find(start_marker)
        if start_idx == -1:
            raise ValueError("Could not find weights block in ensemble_voting.py")

        end_idx = content.find(end_marker, start_idx)
        if end_idx == -1:
            raise ValueError("Could not find end of weights block")

        end_idx += len(end_marker)

        # Replace
        modified_content = content[:start_idx] + new_weights_block + content[end_idx:]

        # Write modified file
        with open(voting_file, 'w') as f:
            f.write(modified_content)

        # Run test
        print(f"\nTesting: {name}")
        print(f"Weights: Color={weights['color']:.2f}, Raw={weights['raw_compat']:.2f}, "
              f"Texture={weights['texture']:.2f}, Morph={weights['morphological']:.2f}, "
              f"Gabor={weights['gabor']:.2f}")
        print("Running test (this takes ~10 minutes)...")

        start = time.time()
        result = subprocess.run(
            [sys.executable, str(ROOT / "test_variant1_quick.py")],
            capture_output=True,
            text=True,
            timeout=900  # 15 minute timeout
        )
        elapsed = time.time() - start

        output = result.stdout + result.stderr

        # Parse results - look for accuracy summary
        lines = output.split('\n')

        # Try to find the accuracy metrics
        pos_acc = neg_acc = overall = 0.0

        for i, line in enumerate(lines):
            if 'Positive Cases:' in line and '=' in line:
                # Format: "Positive Cases: X/Y = Z.Z%"
                try:
                    parts = line.split('=')
                    if len(parts) >= 2:
                        pos_acc = float(parts[-1].strip().rstrip('%'))
                except:
                    pass
            elif 'Negative Cases:' in line and '=' in line:
                try:
                    parts = line.split('=')
                    if len(parts) >= 2:
                        neg_acc = float(parts[-1].strip().rstrip('%'))
                except:
                    pass
            elif 'Overall:' in line and '=' in line:
                try:
                    parts = line.split('=')
                    if len(parts) >= 2:
                        overall = float(parts[-1].strip().rstrip('%'))
                except:
                    pass

        if pos_acc == 0 and neg_acc == 0:
            # Try alternate parsing for [P] and [N] lines
            positive_pass = positive_total = 0
            negative_pass = negative_total = 0

            for line in lines:
                if '[P]' in line:
                    positive_total += 1
                    if 'PASS' in line:
                        positive_pass += 1
                elif '[N]' in line:
                    negative_total += 1
                    if 'PASS' in line:
                        negative_pass += 1

            if positive_total > 0:
                pos_acc = (positive_pass / positive_total) * 100
            if negative_total > 0:
                neg_acc = (negative_pass / negative_total) * 100
            if positive_total + negative_total > 0:
                overall = ((positive_pass + negative_pass) / (positive_total + negative_total)) * 100

        print(f"Results: Pos={pos_acc:.1f}%, Neg={neg_acc:.1f}%, Overall={overall:.1f}% (Time: {elapsed:.1f}s)")

        return (pos_acc, neg_acc, overall)

    finally:
        # Restore original file
        shutil.copy(backup_file, voting_file)
        backup_file.unlink()


def main():
    """Run quick weight optimization test."""
    print("="*100)
    print("QUICK EVOLUTIONARY WEIGHT TEST FOR VARIANT 1")
    print("="*100)
    print("Testing 3 key configurations:")
    print("  1. Baseline (current weights from paper)")
    print("  2. Color-optimized (increase color weight for pottery)")
    print("  3. Balanced (optimize all weights for pottery)")
    print()
    print("Each test takes ~10 minutes. Total time: ~30 minutes")
    print("="*100)

    # Define 3 key configurations
    configurations = [
        {
            'name': 'Baseline',
            'weights': {
                'color': 0.35,
                'raw_compat': 0.25,
                'texture': 0.20,
                'morphological': 0.15,
                'gabor': 0.05
            },
            'description': 'Current weights (from paper on general objects)'
        },
        {
            'name': 'Color-Optimized',
            'weights': {
                'color': 0.50,
                'raw_compat': 0.25,
                'texture': 0.15,
                'morphological': 0.10,
                'gabor': 0.00
            },
            'description': 'Increased color to 0.50 (pigment is artifact-specific for pottery)'
        },
        {
            'name': 'Balanced',
            'weights': {
                'color': 0.45,
                'raw_compat': 0.30,
                'texture': 0.15,
                'morphological': 0.10,
                'gabor': 0.00
            },
            'description': 'Balance color (0.45) + geometry (0.30), remove gabor'
        },
    ]

    results = []

    for i, config in enumerate(configurations, 1):
        print(f"\n{'='*100}")
        print(f"TEST {i}/3: {config['name']}")
        print(f"Description: {config['description']}")
        print("="*100)

        try:
            pos_acc, neg_acc, overall = test_weight_configuration(
                config['weights'],
                config['name']
            )

            results.append({
                'name': config['name'],
                'weights': config['weights'],
                'pos_acc': pos_acc,
                'neg_acc': neg_acc,
                'overall': overall,
                'description': config['description']
            })

            # Early stopping if target reached
            if pos_acc >= 95.0 and neg_acc >= 95.0:
                print(f"\n✓✓✓ TARGET REACHED with {config['name']}!")
                break

        except Exception as e:
            print(f"\nERROR testing {config['name']}: {e}")
            import traceback
            traceback.print_exc()
            continue

        # Give system a moment
        time.sleep(2)

    # Print final summary
    print("\n" + "="*100)
    print("QUICK TEST SUMMARY")
    print("="*100)
    print(f"{'Configuration':<20} {'Color':<8} {'Raw':<8} {'Texture':<8} {'Morph':<8} {'Gabor':<8} {'Pos%':<8} {'Neg%':<8} {'Overall%':<10}")
    print("-"*100)

    for r in results:
        print(f"{r['name']:<20} {r['weights']['color']:<8.2f} {r['weights']['raw_compat']:<8.2f} "
              f"{r['weights']['texture']:<8.2f} {r['weights']['morphological']:<8.2f} "
              f"{r['weights']['gabor']:<8.2f} {r['pos_acc']:<8.1f} {r['neg_acc']:<8.1f} {r['overall']:<10.1f}")

    print("="*100)

    if results:
        best = max(results, key=lambda r: r['overall'])
        print(f"\nBEST CONFIGURATION: {best['name']}")
        print(f"  Weights: Color={best['weights']['color']:.2f}, Raw={best['weights']['raw_compat']:.2f}, "
              f"Texture={best['weights']['texture']:.2f}, Morph={best['weights']['morphological']:.2f}, "
              f"Gabor={best['weights']['gabor']:.2f}")
        print(f"  Accuracy: Pos={best['pos_acc']:.1f}%, Neg={best['neg_acc']:.1f}%, Overall={best['overall']:.1f}%")

        # Check if target reached
        if best['pos_acc'] >= 95.0 and best['neg_acc'] >= 95.0:
            print("\n✓✓✓ TARGET REACHED! 95%+ on both positive and negative cases!")
        else:
            gap_pos = max(0, 95.0 - best['pos_acc'])
            gap_neg = max(0, 95.0 - best['neg_acc'])
            print(f"\n✗ Target not reached. Gaps: Pos={gap_pos:.1f}%, Neg={gap_neg:.1f}%")

        print("\nRECOMMENDATION:")
        if best['name'] == 'Baseline':
            print("  The baseline weights are already optimal. No changes needed.")
        else:
            print(f"  Update ensemble_voting.py to use {best['name']} weights:")
            print(f"    'color': {best['weights']['color']},")
            print(f"    'raw_compat': {best['weights']['raw_compat']},")
            print(f"    'texture': {best['weights']['texture']},")
            print(f"    'morphological': {best['weights']['morphological']},")
            print(f"    'gabor': {best['weights']['gabor']}")

        # Save results
        results_file = ROOT / "evolution_quick_results.txt"
        with open(results_file, 'w') as f:
            f.write("QUICK EVOLUTIONARY WEIGHT TEST RESULTS\n")
            f.write("="*100 + "\n\n")

            for r in results:
                f.write(f"Configuration: {r['name']}\n")
                f.write(f"  Description: {r['description']}\n")
                f.write(f"  Weights: {r['weights']}\n")
                f.write(f"  Accuracy: Pos={r['pos_acc']:.1f}%, Neg={r['neg_acc']:.1f}%, Overall={r['overall']:.1f}%\n")
                f.write("\n")

            f.write(f"BEST: {best['name']}\n")
            f.write(f"  Weights: {best['weights']}\n")
            f.write(f"  Accuracy: Pos={best['pos_acc']:.1f}%, Neg={best['neg_acc']:.1f}%, Overall={best['overall']:.1f}%\n")

        print(f"\nResults saved to: {results_file}")

    print("="*100)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
