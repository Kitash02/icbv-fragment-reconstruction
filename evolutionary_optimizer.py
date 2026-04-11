#!/usr/bin/env python3
"""
Evolutionary Optimization System
---------------------------------
Iteratively improves each variant until reaching 95%+ accuracy target.

Strategy:
1. Test current configuration
2. If < 95% both metrics, analyze failures
3. Apply targeted fixes
4. Repeat until target reached or ceiling found
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

def parse_test_results(output: str) -> Dict:
    """Extract accuracy metrics from test output."""
    lines = output.split('\n')

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

    pos_acc = (positive_pass / positive_total * 100) if positive_total > 0 else 0
    neg_acc = (negative_pass / negative_total * 100) if negative_total > 0 else 0
    overall_acc = ((positive_pass + negative_pass) / (positive_total + negative_total) * 100) \
                  if (positive_total + negative_total) > 0 else 0

    return {
        'positive_pass': positive_pass,
        'positive_total': positive_total,
        'positive_acc': pos_acc,
        'negative_pass': negative_pass,
        'negative_total': negative_total,
        'negative_acc': neg_acc,
        'overall_acc': overall_acc
    }

def identify_failure_patterns(output: str) -> Dict:
    """Analyze which cases are failing."""
    false_positives = []
    false_negatives = []

    for line in output.split('\n'):
        if '[P]' in line and 'FAIL' in line:
            # Extract case name
            parts = line.split('>')
            if len(parts) > 1:
                case_name = parts[1].split()[0]
                false_negatives.append(case_name)
        elif '[N]' in line and 'FAIL' in line:
            parts = line.split('>')
            if len(parts) > 1:
                case_name = parts[1].split()[0]
                false_positives.append(case_name)

    return {
        'false_positives': false_positives,
        'false_negatives': false_negatives,
        'fp_count': len(false_positives),
        'fn_count': len(false_negatives)
    }

def suggest_fixes(results: Dict, failures: Dict, iteration: int) -> List[str]:
    """Suggest next fixes based on failure analysis."""
    fixes = []

    neg_acc = results['negative_acc']
    pos_acc = results['positive_acc']
    fp_count = failures['fp_count']
    fn_count = failures['fn_count']

    # Priority 1: Fix false positives (low negative accuracy)
    if neg_acc < 95 and fp_count > 5:
        if iteration == 1:
            fixes.append("TIGHTEN_HARD_DISCRIMINATOR:0.75:0.70")
        elif iteration == 2:
            fixes.append("TIGHTEN_HARD_DISCRIMINATOR:0.80:0.75")
        elif iteration == 3:
            fixes.append("ADD_ENSEMBLE_GATING:0.75:0.70")
        else:
            fixes.append("RAISE_RELAXATION_THRESHOLDS:0.85:0.70")

    elif neg_acc < 95 and fp_count <= 5:
        fixes.append("FINE_TUNE_DISCRIMINATOR:0.77:0.72")

    # Priority 2: Fix false negatives (low positive accuracy)
    if pos_acc < 95 and fn_count > 2:
        if iteration == 1:
            fixes.append("RELAX_HARD_DISCRIMINATOR:0.65:0.60")
        elif iteration == 2:
            fixes.append("LOWER_RELAXATION_THRESHOLDS:0.70:0.55")
        else:
            fixes.append("DISABLE_PRECHECK_FOR_POSITIVES")

    # Priority 3: Balance trade-offs
    if neg_acc >= 85 and pos_acc < 85:
        fixes.append("REBALANCE_TRADEOFF:FAVOR_POSITIVE")
    elif pos_acc >= 85 and neg_acc < 85:
        fixes.append("REBALANCE_TRADEOFF:FAVOR_NEGATIVE")

    return fixes if fixes else ["MINOR_TUNING"]

def apply_fix(fix: str, config: Dict) -> Dict:
    """Apply suggested fix to configuration."""
    new_config = config.copy()

    if fix.startswith("TIGHTEN_HARD_DISCRIMINATOR"):
        _, color_thresh, texture_thresh = fix.split(':')
        new_config['hard_disc_color'] = float(color_thresh)
        new_config['hard_disc_texture'] = float(texture_thresh)

    elif fix.startswith("RELAX_HARD_DISCRIMINATOR"):
        _, color_thresh, texture_thresh = fix.split(':')
        new_config['hard_disc_color'] = float(color_thresh)
        new_config['hard_disc_texture'] = float(texture_thresh)

    elif fix.startswith("ADD_ENSEMBLE_GATING"):
        _, color_thresh, texture_thresh = fix.split(':')
        new_config['ensemble_gating'] = True
        new_config['ensemble_gate_color'] = float(color_thresh)
        new_config['ensemble_gate_texture'] = float(texture_thresh)

    elif fix.startswith("RAISE_RELAXATION_THRESHOLDS"):
        _, match_thresh, weak_thresh = fix.split(':')
        new_config['match_threshold'] = float(match_thresh)
        new_config['weak_match_threshold'] = float(weak_thresh)

    elif fix.startswith("LOWER_RELAXATION_THRESHOLDS"):
        _, match_thresh, weak_thresh = fix.split(':')
        new_config['match_threshold'] = float(match_thresh)
        new_config['weak_match_threshold'] = float(weak_thresh)

    return new_config

def run_test_with_config(variant_name: str, config: Dict) -> Tuple[Dict, str]:
    """Run test with specific configuration."""
    # Write config to temp file
    config_file = Path(f"outputs/evolution/{variant_name}_config.json")
    config_file.parent.mkdir(parents=True, exist_ok=True)

    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

    # TODO: Apply config and run test
    # For now, simulate
    print(f"  Testing {variant_name} with config: {config}")

    return {}, ""

def evolve_variant(variant_name: str, initial_config: Dict, max_iterations: int = 10):
    """
    Evolutionary optimization for a single variant.
    Iterates until 95%+ target reached or max iterations.
    """
    print(f"\n{'='*80}")
    print(f"EVOLVING {variant_name}")
    print(f"{'='*80}")
    print(f"Target: 95%+ positive AND 95%+ negative accuracy")
    print(f"Max iterations: {max_iterations}")

    config = initial_config.copy()
    history = []

    for iteration in range(1, max_iterations + 1):
        print(f"\n--- Iteration {iteration} ---")

        # Run test
        results, output = run_test_with_config(f"{variant_name}_iter{iteration}", config)

        if not results:
            print("  Skipping (implementation needed)")
            break

        # Analyze results
        failures = identify_failure_patterns(output)

        pos_acc = results['positive_acc']
        neg_acc = results['negative_acc']

        print(f"  Results: {pos_acc:.1f}% positive, {neg_acc:.1f}% negative")
        print(f"  Failures: {failures['fp_count']} FP, {failures['fn_count']} FN")

        # Record history
        history.append({
            'iteration': iteration,
            'config': config.copy(),
            'results': results,
            'failures': failures
        })

        # Check if target reached
        if pos_acc >= 95 and neg_acc >= 95:
            print(f"\n  *** TARGET REACHED! ***")
            print(f"  Final: {pos_acc:.1f}% pos, {neg_acc:.1f}% neg")
            break

        # Check if no improvement possible
        if iteration > 3:
            recent_pos = [h['results']['positive_acc'] for h in history[-3:]]
            recent_neg = [h['results']['negative_acc'] for h in history[-3:]]
            if max(recent_pos) - min(recent_pos) < 1 and max(recent_neg) - min(recent_neg) < 1:
                print(f"\n  *** CONVERGENCE DETECTED (no improvement) ***")
                print(f"  Best: {pos_acc:.1f}% pos, {neg_acc:.1f}% neg")
                break

        # Suggest and apply fixes
        fixes = suggest_fixes(results, failures, iteration)
        print(f"  Applying fixes: {fixes}")

        for fix in fixes:
            config = apply_fix(fix, config)

    # Save evolution history
    history_file = Path(f"outputs/evolution/{variant_name}_history.json")
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)

    print(f"\nEvolution history saved: {history_file}")

    return history

def main():
    """Run evolutionary optimization for all variants."""

    # Baseline configuration
    base_config = {
        'power_color': 4.0,
        'power_texture': 2.0,
        'power_gabor': 2.0,
        'power_haralick': 2.0,
        'match_threshold': 0.75,
        'weak_match_threshold': 0.60,
        'assembly_confidence': 0.65,
        'hard_disc_color': 0.70,
        'hard_disc_texture': 0.65,
        'color_precheck_gap': 0.15,
        'color_precheck_low_max': 0.75,
        'ensemble_gating': False
    }

    variants_to_evolve = [
        ("Variant0_Baseline", base_config),
        # Add more variants as needed
    ]

    print("="*80)
    print("EVOLUTIONARY OPTIMIZATION SYSTEM")
    print("="*80)
    print("Target: 95%+ accuracy on BOTH positive and negative metrics")
    print("Strategy: Iterative analysis → fix → test until target reached")
    print("="*80)

    all_results = {}

    for variant_name, config in variants_to_evolve:
        history = evolve_variant(variant_name, config, max_iterations=10)
        all_results[variant_name] = history

    print(f"\n{'='*80}")
    print("EVOLUTION COMPLETE")
    print(f"{'='*80}")

    for variant_name, history in all_results.items():
        if history:
            final = history[-1]['results']
            print(f"{variant_name}: {final['positive_acc']:.1f}% pos, {final['negative_acc']:.1f}% neg")

if __name__ == "__main__":
    main()
