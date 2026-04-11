#!/usr/bin/env python3
"""
Generate comprehensive final report for evolutionary optimization.
"""

import json
import sys
from pathlib import Path
from parse_results import parse_test_results


def generate_report(root_dir):
    """Generate comprehensive optimization report."""
    evolution_dir = root_dir / "outputs" / "evolution"
    progress_file = evolution_dir / "variant0_progress.json"

    # Load progress
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            progress = json.load(f)
    else:
        progress = {"iterations": []}

    # Parse all iteration results
    iterations = []
    for i in range(6):
        result_file = evolution_dir / f"variant0_iter{i}.txt"
        if not result_file.exists():
            result_file = evolution_dir / f"variant0_iter{i}_full.txt"

        if result_file.exists():
            metrics = parse_test_results(result_file)
            if metrics:
                iterations.append({
                    'iteration': i,
                    'metrics': metrics,
                    'config': get_config_for_iteration(i)
                })

    if not iterations:
        print("ERROR: No iteration results found")
        return

    # Generate report
    print("="*80)
    print("VARIANT 0 EVOLUTIONARY OPTIMIZATION - FINAL REPORT")
    print("="*80)
    print()
    print("TARGET: 95%+ positive AND 95%+ negative accuracy")
    print()
    print("="*80)
    print("ITERATION RESULTS")
    print("="*80)
    print()

    # Table header
    print(f"{'Iter':<6} {'Color':>7} {'Texture':>7} {'Pos%':>7} {'Neg%':>7} {'FP':>4} {'FN':>4} {'Status':>10}")
    print("-" * 80)

    best_config = None
    best_score = 0
    target_reached = False

    for it in iterations:
        i = it['iteration']
        m = it['metrics']
        c = it['config']

        pos_acc = m['positive_accuracy']
        neg_acc = m['negative_accuracy']
        fp_count = len(m['false_positives'])
        fn_count = len(m['false_negatives'])

        # Calculate combined score
        combined_score = (pos_acc + neg_acc) / 2

        # Determine status
        status = ""
        if pos_acc >= 95 and neg_acc >= 95:
            status = "✓ TARGET"
            target_reached = True
        elif combined_score > best_score:
            status = "BEST"
            best_score = combined_score
            best_config = it

        print(f"{i:<6} {c['color']:.2f}    {c['texture']:.2f}    "
              f"{pos_acc:6.1f}% {neg_acc:6.1f}% {fp_count:4} {fn_count:4} {status:>10}")

    print("-" * 80)
    print()

    # Summary
    if target_reached:
        print("=" * 80)
        print("SUCCESS: TARGET ACHIEVED!")
        print("=" * 80)
        print()
        for it in iterations:
            m = it['metrics']
            if m['positive_accuracy'] >= 95 and m['negative_accuracy'] >= 95:
                c = it['config']
                print(f"Optimal Configuration: Iteration {it['iteration']}")
                print(f"  - hard_disc_color: {c['color']:.2f}")
                print(f"  - hard_disc_texture: {c['texture']:.2f}")
                print(f"  - Positive accuracy: {m['positive_accuracy']:.1f}%")
                print(f"  - Negative accuracy: {m['negative_accuracy']:.1f}%")
                print()
    elif best_config:
        print("=" * 80)
        print("BEST ACHIEVABLE CONFIGURATION")
        print("=" * 80)
        print()
        m = best_config['metrics']
        c = best_config['config']
        print(f"Iteration: {best_config['iteration']}")
        print(f"Configuration:")
        print(f"  - hard_disc_color: {c['color']:.2f}")
        print(f"  - hard_disc_texture: {c['texture']:.2f}")
        print()
        print(f"Results:")
        print(f"  - Positive accuracy: {m['positive_accuracy']:.1f}%")
        print(f"  - Negative accuracy: {m['negative_accuracy']:.1f}%")
        print(f"  - Combined score: {best_score:.1f}%")
        print()
        print(f"False Positives ({len(m['false_positives'])}):")
        for fp in m['false_positives']:
            print(f"  - {fp}")
        print()
        print(f"False Negatives ({len(m['false_negatives'])}):")
        for fn in m['false_negatives']:
            print(f"  - {fn}")
        print()

    # Recommendations
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()

    if target_reached:
        print("The target of 95%+ both metrics has been achieved.")
        print("Deploy the optimal configuration shown above.")
    else:
        avg_neg = sum(it['metrics']['negative_accuracy'] for it in iterations) / len(iterations)
        avg_pos = sum(it['metrics']['positive_accuracy'] for it in iterations) / len(iterations)

        if avg_neg < 90:
            print("Negative accuracy is below target.")
            print("Recommendation: Further tighten thresholds or add ensemble gating.")
        elif avg_pos < 90:
            print("Positive accuracy is below target.")
            print("Recommendation: Relax thresholds or improve color pre-check.")
        else:
            print("Both metrics are close to target.")
            print("Recommendation: Fine-tune around best configuration.")

    print()
    print("="*80)


def get_config_for_iteration(iteration):
    """Return configuration parameters for a given iteration."""
    configs = {
        0: {'color': 0.70, 'texture': 0.65},
        1: {'color': 0.72, 'texture': 0.67},
        2: {'color': 0.74, 'texture': 0.69},
        3: {'color': 0.76, 'texture': 0.71},
        4: {'color': 0.78, 'texture': 0.73},
        5: {'color': 0.80, 'texture': 0.75},
    }
    return configs.get(iteration, {'color': 0.70, 'texture': 0.65})


if __name__ == "__main__":
    root_dir = Path(__file__).parent
    generate_report(root_dir)
