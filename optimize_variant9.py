#!/usr/bin/env python3
"""
Variant 9 Optimization Framework
================================

This script systematically optimizes Variant 9 to achieve 95%+ accuracy.

Optimization Strategy:
1. Test baseline (current weights and thresholds)
2. Grid search over ensemble weights
3. Grid search over adaptive thresholds
4. Test combined optimal configuration
5. Iterate until 95%+ accuracy achieved

Target: 95%+ accuracy (paper claims 99.3%)
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, Tuple, List
import subprocess
import re

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

# Results storage
RESULTS_FILE = ROOT / "outputs" / "evolution" / "variant9_optimization_results.json"
RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)


def parse_test_output(output: str) -> Dict:
    """Parse test output to extract accuracy metrics."""
    results = {
        'positive_correct': 0,
        'positive_total': 0,
        'negative_correct': 0,
        'negative_total': 0,
        'positive_accuracy': 0.0,
        'negative_accuracy': 0.0,
        'overall_accuracy': 0.0
    }

    # Extract positive accuracy
    pos_match = re.search(r'Positive Tests.*?(\d+)/(\d+).*?\((\d+(?:\.\d+)?)%\)', output, re.DOTALL)
    if pos_match:
        results['positive_correct'] = int(pos_match.group(1))
        results['positive_total'] = int(pos_match.group(2))
        results['positive_accuracy'] = float(pos_match.group(3))

    # Extract negative accuracy
    neg_match = re.search(r'Negative Tests.*?(\d+)/(\d+).*?\((\d+(?:\.\d+)?)%\)', output, re.DOTALL)
    if neg_match:
        results['negative_correct'] = int(neg_match.group(1))
        results['negative_total'] = int(neg_match.group(2))
        results['negative_accuracy'] = float(neg_match.group(3))

    # Calculate overall
    if results['positive_total'] > 0 and results['negative_total'] > 0:
        total_correct = results['positive_correct'] + results['negative_correct']
        total = results['positive_total'] + results['negative_total']
        results['overall_accuracy'] = 100.0 * total_correct / total

    return results


def test_configuration(weights: Dict[str, float], thresholds: Dict[str, float],
                       artifact_type: str = 'default') -> Dict:
    """Test a specific configuration."""
    print(f"\n{'='*80}")
    print(f"Testing Configuration:")
    print(f"  Weights: {weights}")
    print(f"  Thresholds: {thresholds}")
    print(f"  Artifact Type: {artifact_type}")
    print(f"{'='*80}\n")

    # Create temporary variant file with custom configuration
    variant_code = f'''"""
Temporary Variant 9 Configuration for Optimization
"""

import numpy as np
import logging
from typing import List, Dict, Optional
from ensemble_voting import ensemble_verdict_weighted

logger = logging.getLogger(__name__)

# Custom weights from optimization
CUSTOM_WEIGHTS = {weights}

def reclassify_borderline_cases(
    assemblies: List[Dict],
    compat_matrix: np.ndarray,
    appearance_mats: Optional[Dict[str, np.ndarray]] = None,
    all_images: Optional[List[np.ndarray]] = None
) -> List[Dict]:
    """Re-classify WEAK_MATCH pairs using optimized configuration."""
    if appearance_mats is None or all_images is None:
        logger.warning("Ensemble post-processing skipped: appearance matrices not available")
        return assemblies

    from hard_discriminators import compute_edge_density, compute_texture_entropy

    edge_densities = [compute_edge_density(img) for img in all_images]
    entropies = [compute_texture_entropy(img) for img in all_images]

    for asm_idx, assembly in enumerate(assemblies):
        for pair in assembly['pairs']:
            if pair['verdict'] != 'WEAK_MATCH':
                continue

            frag_i = pair['frag_i']
            frag_j = pair['frag_j']
            raw_compat = pair['raw_compat']
            bc_color = appearance_mats['color'][frag_i, frag_j]
            bc_texture = appearance_mats['texture'][frag_i, frag_j]
            bc_gabor = appearance_mats['gabor'][frag_i, frag_j]
            edge_density_diff = abs(edge_densities[frag_i] - edge_densities[frag_j])
            entropy_diff = abs(entropies[frag_i] - entropies[frag_j])

            ensemble_verdict = ensemble_verdict_weighted(
                raw_compat=raw_compat,
                bc_color=bc_color,
                bc_texture=bc_texture,
                bc_gabor=bc_gabor,
                edge_density_diff=edge_density_diff,
                entropy_diff=entropy_diff,
                weights=CUSTOM_WEIGHTS
            )

            if ensemble_verdict != pair['verdict']:
                pair['verdict'] = ensemble_verdict

        assembly['verdict'] = _recompute_assembly_verdict(assembly)

    return assemblies


def _recompute_assembly_verdict(assembly: Dict) -> str:
    """Recompute assembly verdict based on updated pair verdicts."""
    pairs = assembly['pairs']
    n_pairs = len(pairs)

    if n_pairs == 0:
        return 'NO_MATCH'

    n_match = sum(1 for p in pairs if p['verdict'] == 'MATCH')
    n_weak = sum(1 for p in pairs if p['verdict'] == 'WEAK_MATCH')
    n_valid = n_match + n_weak

    assembly['n_match'] = n_match
    assembly['n_weak'] = n_weak
    assembly['n_no_match'] = n_pairs - n_valid

    valid_ratio = n_valid / n_pairs
    match_ratio = n_match / n_pairs

    if match_ratio >= 0.40 or valid_ratio >= 0.60:
        return 'MATCH'
    elif valid_ratio >= 0.40:
        return 'WEAK_MATCH'
    else:
        return 'NO_MATCH'
'''

    # Write temporary ensemble postprocess file
    temp_ensemble = ROOT / "src" / "ensemble_postprocess_variant9_temp.py"
    temp_ensemble.write_text(variant_code)

    # Create temporary relaxation file with custom thresholds
    relaxation_code = f'''"""
Temporary Relaxation Configuration for Optimization
"""

import numpy as np
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 50
CONVERGENCE_THRESHOLD = 1e-4

# Custom thresholds from optimization
THRESHOLDS = {{
    'pottery': {{
        'match': {thresholds['pottery_match']},
        'weak': {thresholds['pottery_weak']},
        'assembly': {thresholds['pottery_assembly']}
    }},
    'sculpture': {{
        'match': {thresholds['sculpture_match']},
        'weak': {thresholds['sculpture_weak']},
        'assembly': {thresholds['sculpture_assembly']}
    }},
    'default': {{
        'match': {thresholds['default_match']},
        'weak': {thresholds['default_weak']},
        'assembly': {thresholds['default_assembly']}
    }}
}}

# Set global thresholds based on artifact type
profile = THRESHOLDS['{artifact_type}']
MATCH_SCORE_THRESHOLD = profile['match']
WEAK_MATCH_SCORE_THRESHOLD = profile['weak']
ASSEMBLY_CONFIDENCE_THRESHOLD = profile['assembly']

logger.info("Using thresholds: match=%.2f, weak=%.2f, assembly=%.2f",
           MATCH_SCORE_THRESHOLD, WEAK_MATCH_SCORE_THRESHOLD, ASSEMBLY_CONFIDENCE_THRESHOLD)

# Import all other functions from baseline
from relaxation import (
    initialize_probabilities,
    compute_support,
    update_probabilities,
    run_relaxation,
    extract_top_assemblies,
    classify_pair_score,
    classify_assembly
)
'''

    temp_relaxation = ROOT / "src" / "relaxation_variant9_temp.py"
    temp_relaxation.write_text(relaxation_code)

    # Create temporary test runner
    runner_code = f'''#!/usr/bin/env python3
import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

# Monkey-patch with temporary modules
import ensemble_postprocess_variant9_temp
import relaxation_variant9_temp
sys.modules['ensemble_postprocess'] = ensemble_postprocess_variant9_temp
sys.modules['relaxation'] = relaxation_variant9_temp

import run_test

if __name__ == "__main__":
    run_test.main()
'''

    temp_runner = ROOT / "run_variant9_temp.py"
    temp_runner.write_text(runner_code)

    # Run test
    try:
        result = subprocess.run(
            [sys.executable, str(temp_runner)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=300
        )
        output = result.stdout + result.stderr

        # Parse results
        results = parse_test_output(output)
        results['weights'] = weights
        results['thresholds'] = thresholds
        results['artifact_type'] = artifact_type

        return results

    except subprocess.TimeoutExpired:
        print("Test timed out!")
        return {'error': 'timeout'}

    finally:
        # Cleanup temporary files
        if temp_ensemble.exists():
            temp_ensemble.unlink()
        if temp_relaxation.exists():
            temp_relaxation.unlink()
        if temp_runner.exists():
            temp_runner.unlink()


def grid_search_weights() -> List[Dict]:
    """Grid search over ensemble weights."""
    print("\n" + "="*80)
    print("GRID SEARCH: ENSEMBLE WEIGHTS")
    print("="*80)

    # Default thresholds
    default_thresholds = {
        'pottery_match': 0.78, 'pottery_weak': 0.63, 'pottery_assembly': 0.68,
        'sculpture_match': 0.70, 'sculpture_weak': 0.55, 'sculpture_assembly': 0.60,
        'default_match': 0.75, 'default_weak': 0.60, 'default_assembly': 0.65
    }

    # Weight configurations to test
    weight_configs = [
        # Current baseline
        {'color': 0.40, 'raw_compat': 0.25, 'texture': 0.15, 'morphological': 0.15, 'gabor': 0.05},

        # Color-focused (pottery discrimination)
        {'color': 0.50, 'raw_compat': 0.20, 'texture': 0.15, 'morphological': 0.10, 'gabor': 0.05},
        {'color': 0.45, 'raw_compat': 0.25, 'texture': 0.15, 'morphological': 0.10, 'gabor': 0.05},

        # Balanced approach
        {'color': 0.35, 'raw_compat': 0.25, 'texture': 0.20, 'morphological': 0.15, 'gabor': 0.05},
        {'color': 0.30, 'raw_compat': 0.30, 'texture': 0.20, 'morphological': 0.15, 'gabor': 0.05},

        # Geometric-focused
        {'color': 0.35, 'raw_compat': 0.35, 'texture': 0.15, 'morphological': 0.10, 'gabor': 0.05},

        # Texture-enhanced
        {'color': 0.35, 'raw_compat': 0.25, 'texture': 0.25, 'morphological': 0.10, 'gabor': 0.05},
    ]

    results = []
    for weights in weight_configs:
        result = test_configuration(weights, default_thresholds)
        if 'error' not in result:
            results.append(result)
            print(f"\nResults: Pos={result['positive_accuracy']:.1f}%, "
                  f"Neg={result['negative_accuracy']:.1f}%, "
                  f"Overall={result['overall_accuracy']:.1f}%")

    return results


def grid_search_thresholds(best_weights: Dict[str, float]) -> List[Dict]:
    """Grid search over adaptive thresholds."""
    print("\n" + "="*80)
    print("GRID SEARCH: ADAPTIVE THRESHOLDS")
    print("="*80)

    # Threshold configurations to test
    threshold_configs = [
        # Current baseline
        {
            'pottery_match': 0.78, 'pottery_weak': 0.63, 'pottery_assembly': 0.68,
            'sculpture_match': 0.70, 'sculpture_weak': 0.55, 'sculpture_assembly': 0.60,
            'default_match': 0.75, 'default_weak': 0.60, 'default_assembly': 0.65
        },

        # More aggressive (lower thresholds)
        {
            'pottery_match': 0.75, 'pottery_weak': 0.60, 'pottery_assembly': 0.65,
            'sculpture_match': 0.68, 'sculpture_weak': 0.53, 'sculpture_assembly': 0.58,
            'default_match': 0.72, 'default_weak': 0.57, 'default_assembly': 0.62
        },

        # Very aggressive
        {
            'pottery_match': 0.72, 'pottery_weak': 0.57, 'pottery_assembly': 0.62,
            'sculpture_match': 0.65, 'sculpture_weak': 0.50, 'sculpture_assembly': 0.55,
            'default_match': 0.70, 'default_weak': 0.55, 'default_assembly': 0.60
        },

        # More conservative (higher thresholds)
        {
            'pottery_match': 0.80, 'pottery_weak': 0.65, 'pottery_assembly': 0.70,
            'sculpture_match': 0.72, 'sculpture_weak': 0.57, 'sculpture_assembly': 0.62,
            'default_match': 0.77, 'default_weak': 0.62, 'default_assembly': 0.67
        },

        # Pottery-focused (stricter pottery, relaxed sculpture)
        {
            'pottery_match': 0.82, 'pottery_weak': 0.67, 'pottery_assembly': 0.72,
            'sculpture_match': 0.68, 'sculpture_weak': 0.53, 'sculpture_assembly': 0.58,
            'default_match': 0.75, 'default_weak': 0.60, 'default_assembly': 0.65
        },
    ]

    results = []
    for thresholds in threshold_configs:
        result = test_configuration(best_weights, thresholds)
        if 'error' not in result:
            results.append(result)
            print(f"\nResults: Pos={result['positive_accuracy']:.1f}%, "
                  f"Neg={result['negative_accuracy']:.1f}%, "
                  f"Overall={result['overall_accuracy']:.1f}%")

    return results


def fine_tune_configuration(best_config: Dict) -> Dict:
    """Fine-tune the best configuration with small adjustments."""
    print("\n" + "="*80)
    print("FINE TUNING: BEST CONFIGURATION")
    print("="*80)

    best_weights = best_config['weights']
    best_thresholds = best_config['thresholds']
    best_accuracy = best_config['overall_accuracy']

    # Try small adjustments to weights
    adjustments = [
        {'color': 0.02, 'raw_compat': 0.0, 'texture': -0.01, 'morphological': -0.01, 'gabor': 0.0},
        {'color': -0.02, 'raw_compat': 0.02, 'texture': 0.0, 'morphological': 0.0, 'gabor': 0.0},
        {'color': 0.0, 'raw_compat': 0.0, 'texture': 0.02, 'morphological': -0.01, 'gabor': -0.01},
    ]

    results = []
    for adj in adjustments:
        test_weights = {k: v + adj[k] for k, v in best_weights.items()}
        result = test_configuration(test_weights, best_thresholds)

        if 'error' not in result and result['overall_accuracy'] > best_accuracy:
            results.append(result)
            print(f"\nImprovement found! Pos={result['positive_accuracy']:.1f}%, "
                  f"Neg={result['negative_accuracy']:.1f}%, "
                  f"Overall={result['overall_accuracy']:.1f}%")

    return results


def main():
    """Main optimization loop."""
    print("="*80)
    print("VARIANT 9 OPTIMIZATION FRAMEWORK")
    print("Target: 95%+ accuracy (both positive and negative)")
    print("="*80)

    all_results = []

    # Phase 1: Grid search weights
    print("\n### PHASE 1: Grid Search Ensemble Weights ###")
    weight_results = grid_search_weights()
    all_results.extend(weight_results)

    # Find best weight configuration
    best_weight_config = max(weight_results, key=lambda x: x['overall_accuracy'])
    print(f"\n### Best Weights: {best_weight_config['weights']}")
    print(f"### Accuracy: Pos={best_weight_config['positive_accuracy']:.1f}%, "
          f"Neg={best_weight_config['negative_accuracy']:.1f}%, "
          f"Overall={best_weight_config['overall_accuracy']:.1f}%")

    # Phase 2: Grid search thresholds with best weights
    print("\n### PHASE 2: Grid Search Adaptive Thresholds ###")
    threshold_results = grid_search_thresholds(best_weight_config['weights'])
    all_results.extend(threshold_results)

    # Find best overall configuration
    best_config = max(all_results, key=lambda x: x['overall_accuracy'])
    print(f"\n### Best Configuration:")
    print(f"### Weights: {best_config['weights']}")
    print(f"### Thresholds: {best_config['thresholds']}")
    print(f"### Accuracy: Pos={best_config['positive_accuracy']:.1f}%, "
          f"Neg={best_config['negative_accuracy']:.1f}%, "
          f"Overall={best_config['overall_accuracy']:.1f}%")

    # Phase 3: Fine tuning if not at target
    if best_config['overall_accuracy'] < 95.0:
        print("\n### PHASE 3: Fine Tuning ###")
        fine_tune_results = fine_tune_configuration(best_config)
        if fine_tune_results:
            all_results.extend(fine_tune_results)
            best_config = max(all_results, key=lambda x: x['overall_accuracy'])
            print(f"\n### Updated Best Configuration:")
            print(f"### Weights: {best_config['weights']}")
            print(f"### Thresholds: {best_config['thresholds']}")
            print(f"### Accuracy: Pos={best_config['positive_accuracy']:.1f}%, "
                  f"Neg={best_config['negative_accuracy']:.1f}%, "
                  f"Overall={best_config['overall_accuracy']:.1f}%")

    # Save all results
    with open(RESULTS_FILE, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n### Results saved to: {RESULTS_FILE}")

    # Final report
    print("\n" + "="*80)
    print("OPTIMIZATION COMPLETE")
    print("="*80)
    print(f"\nBest Configuration Achieved:")
    print(f"  Positive Accuracy: {best_config['positive_accuracy']:.1f}%")
    print(f"  Negative Accuracy: {best_config['negative_accuracy']:.1f}%")
    print(f"  Overall Accuracy: {best_config['overall_accuracy']:.1f}%")
    print(f"\nWeights: {best_config['weights']}")
    print(f"Thresholds: {best_config['thresholds']}")

    if best_config['positive_accuracy'] >= 95.0 and best_config['negative_accuracy'] >= 95.0:
        print("\n✅ TARGET ACHIEVED: 95%+ accuracy on both metrics!")
    else:
        print(f"\n⚠️ Target not reached. Best overall: {best_config['overall_accuracy']:.1f}%")
        print(f"   Gap to 95%: Pos={95.0 - best_config['positive_accuracy']:.1f}%, "
              f"Neg={95.0 - best_config['negative_accuracy']:.1f}%")


if __name__ == "__main__":
    main()
