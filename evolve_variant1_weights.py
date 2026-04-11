#!/usr/bin/env python3
"""
Evolutionary Weight Optimization for Variant 1 (arXiv:2510.17145)

Strategy: Optimize ensemble weights for pottery fragment reconstruction.
Paper claims 97.49% accuracy with learned weights. We optimize for pottery specifically.

Current weights (from paper's general object classification):
- Color: 0.35
- Raw compatibility: 0.25
- Texture: 0.20
- Morphology: 0.15
- Gabor: 0.05

Hypothesis: For pottery, color is MORE discriminative (pigment chemistry is artifact-specific).
We'll iteratively test configurations that increase color weight.

Evolutionary iterations:
1. Baseline: Current weights (0.35, 0.25, 0.20, 0.15, 0.05)
2. Iteration 1: Color↑ 0.40 (absorb from gabor)
3. Iteration 2: Color↑ 0.45 (absorb from texture)
4. Iteration 3: Color↑ 0.50 (absorb from morphology)
5. Iteration 4: Color↑ 0.55 (absorb from raw)

Note: Each test takes ~10 minutes (45 test cases). Total evolution time: 30-60 minutes.

Target: 95%+ positive accuracy AND 95%+ negative accuracy.
"""

import sys
import subprocess
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Tuple

ROOT = Path(__file__).parent


def test_weight_configuration(weights: Dict[str, float]) -> Tuple[float, float, float, str]:
    """
    Test a weight configuration by temporarily modifying ensemble_voting.py.

    Args:
        weights: Dictionary with keys: color, raw_compat, texture, morphological, gabor

    Returns:
        (positive_acc, negative_acc, overall_acc, output_text)
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
        # Find the line: weights = {
        # Replace until the closing }

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

        # Find the closing brace after start_marker
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
        print(f"\nTesting weights: {weights}")
        print("Running full 45-case test...")

        start = time.time()
        result = subprocess.run(
            [sys.executable, str(ROOT / "run_variant1.py"), "--no-rotate"],
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout (conservative for 45 cases)
        )
        elapsed = time.time() - start

        output = result.stdout + result.stderr

        # Parse results
        positive_pass = positive_total = 0
        negative_pass = negative_total = 0

        for line in output.split('\n'):
            if '[P]' in line:
                positive_total += 1
                if 'PASS' in line:
                    positive_pass += 1
            elif '[N]' in line:
                negative_total += 1
                if 'PASS' in line:
                    negative_pass += 1

        if positive_total == 0 or negative_total == 0:
            print(f"WARNING: Could not parse results. Output tail:\n{output[-1000:]}")
            return (0.0, 0.0, 0.0, output)

        pos_acc = (positive_pass / positive_total) * 100
        neg_acc = (negative_pass / negative_total) * 100
        overall = ((positive_pass + negative_pass) / (positive_total + negative_total)) * 100

        print(f"Results: Pos={pos_acc:.1f}%, Neg={neg_acc:.1f}%, Overall={overall:.1f}% (Time: {elapsed:.1f}s)")

        return (pos_acc, neg_acc, overall, output)

    finally:
        # Restore original file
        shutil.copy(backup_file, voting_file)
        backup_file.unlink()


def print_summary_table(results: list):
    """Print a summary table of all tested configurations."""
    print("\n" + "="*100)
    print("EVOLUTIONARY WEIGHT OPTIMIZATION SUMMARY")
    print("="*100)
    print(f"{'Iteration':<12} {'Color':<8} {'Raw':<8} {'Texture':<8} {'Morph':<8} {'Gabor':<8} {'Pos%':<8} {'Neg%':<8} {'Overall%':<10}")
    print("-"*100)

    for r in results:
        print(f"{r['name']:<12} {r['weights']['color']:<8.2f} {r['weights']['raw_compat']:<8.2f} "
              f"{r['weights']['texture']:<8.2f} {r['weights']['morphological']:<8.2f} "
              f"{r['weights']['gabor']:<8.2f} {r['pos_acc']:<8.1f} {r['neg_acc']:<8.1f} {r['overall']:<10.1f}")

    print("="*100)

    # Find best configuration
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

    print("="*100)


def main():
    """Run evolutionary weight optimization."""
    print("="*100)
    print("EVOLUTIONARY WEIGHT OPTIMIZATION FOR VARIANT 1")
    print("="*100)
    print("Target: 95%+ positive accuracy AND 95%+ negative accuracy")
    print("Strategy: Optimize color weight (most discriminative for pottery)")
    print("="*100)

    # Define configurations to test
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
            'description': 'Current weights from paper (general object classification)'
        },
        {
            'name': 'Iteration 1',
            'weights': {
                'color': 0.40,
                'raw_compat': 0.25,
                'texture': 0.20,
                'morphological': 0.15,
                'gabor': 0.00
            },
            'description': 'Increase color to 0.40, remove gabor (least useful for pottery)'
        },
        {
            'name': 'Iteration 2',
            'weights': {
                'color': 0.45,
                'raw_compat': 0.25,
                'texture': 0.15,
                'morphological': 0.15,
                'gabor': 0.00
            },
            'description': 'Increase color to 0.45, reduce texture'
        },
        {
            'name': 'Iteration 3',
            'weights': {
                'color': 0.50,
                'raw_compat': 0.25,
                'texture': 0.10,
                'morphological': 0.15,
                'gabor': 0.00
            },
            'description': 'Increase color to 0.50, further reduce texture'
        },
        {
            'name': 'Iteration 4',
            'weights': {
                'color': 0.50,
                'raw_compat': 0.25,
                'texture': 0.15,
                'morphological': 0.10,
                'gabor': 0.00
            },
            'description': 'Color at 0.50, balance texture/morph (alternative config)'
        },
        {
            'name': 'Iteration 5',
            'weights': {
                'color': 0.55,
                'raw_compat': 0.20,
                'texture': 0.15,
                'morphological': 0.10,
                'gabor': 0.00
            },
            'description': 'Increase color to 0.55, reduce raw compatibility'
        },
    ]

    results = []

    for config in configurations:
        print("\n" + "="*100)
        print(f"TESTING: {config['name']}")
        print(f"Description: {config['description']}")
        print("="*100)

        pos_acc, neg_acc, overall, output = test_weight_configuration(config['weights'])

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
            print(f"\n✓✓✓ TARGET REACHED with {config['name']}! Stopping evolution.")
            break

        # Give system a moment to recover
        time.sleep(2)

    # Print final summary
    print_summary_table(results)

    # Save results to file
    results_file = ROOT / "evolution_results_variant1.txt"
    with open(results_file, 'w') as f:
        f.write("EVOLUTIONARY WEIGHT OPTIMIZATION RESULTS\n")
        f.write("="*100 + "\n\n")

        for r in results:
            f.write(f"Configuration: {r['name']}\n")
            f.write(f"  Description: {r['description']}\n")
            f.write(f"  Weights: {r['weights']}\n")
            f.write(f"  Accuracy: Pos={r['pos_acc']:.1f}%, Neg={r['neg_acc']:.1f}%, Overall={r['overall']:.1f}%\n")
            f.write("\n")

        best = max(results, key=lambda r: r['overall'])
        f.write(f"BEST CONFIGURATION: {best['name']}\n")
        f.write(f"  Weights: {best['weights']}\n")
        f.write(f"  Accuracy: Pos={best['pos_acc']:.1f}%, Neg={best['neg_acc']:.1f}%, Overall={best['overall']:.1f}%\n")

    print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nEvolution interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
