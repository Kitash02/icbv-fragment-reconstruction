"""
Variant Manager - Algorithm Variant Selection and Monkey-Patching Infrastructure

This module provides a centralized system for managing and applying different
algorithm variants to the fragment reconstruction pipeline. It enables dynamic
switching between baseline and experimental configurations through selective
monkey-patching of core modules.

Supported Variants:
- Baseline: Original algorithm (77.8% accuracy)
- Variant 0 Iter 2: Tightened hard discriminator thresholds (85.1% accuracy) ⭐ BEST
- Variant 1: Weighted ensemble post-processing (77.8% accuracy)
- Variant 5: Aggressive color^6 penalty (66.7% positive / 77.8% negative)
- Variant 8: Adaptive Gabor weighting (Ready - fixes BC=1.0 issue)
- Variant 9: Full research stack optimization (Ready - 92%+ target)

Course Mapping: Variant selection supports experimental evaluation methodology
from research practice - testing multiple algorithmic configurations against
ground truth to identify optimal parameters (Lecture 71: Object Recognition).
"""

import logging
import importlib
import sys
from typing import Dict, Optional, Callable, Any

logger = logging.getLogger(__name__)


# =============================================================================
# VARIANT CONFIGURATION DATABASE
# =============================================================================

VARIANT_CONFIG = {
    "Baseline (77.8%)": {
        "description": "Original algorithm with curvature cross-correlation, "
                      "Fourier descriptors, and appearance penalties",
        "accuracy_positive": 77.8,
        "accuracy_negative": 77.8,
        "accuracy_overall": 77.8,
        "modules_to_patch": [],
        "performance_notes": "Balanced performance, good baseline for comparison",
        "parameters": {}
    },

    "Variant 0 Iter 2 (85.1%) ⭐ BEST": {
        "description": "Tightened hard discriminator thresholds (color 0.74, texture 0.69). "
                      "Evolutionary optimization: moderate tightening for better negative accuracy",
        "accuracy_positive": 77.8,
        "accuracy_negative": 91.7,
        "accuracy_overall": 85.1,
        "modules_to_patch": ["hard_discriminators"],
        "performance_notes": "Best overall accuracy. Excellent at rejecting false matches. "
                           "Strategy: Raise appearance similarity thresholds to +2.8%/+3.0%",
        "parameters": {
            "color_threshold": 0.74,
            "texture_threshold": 0.69,
            "edge_density_max_diff": 0.15,
            "entropy_max_diff": 0.50
        }
    },

    "Variant 1 (77.8%)": {
        "description": "Weighted ensemble post-processing. Uses learned weights: "
                      "Color(0.35), Raw(0.25), Texture(0.20), Morph(0.15), Gabor(0.05)",
        "accuracy_positive": 77.8,
        "accuracy_negative": 77.8,
        "accuracy_overall": 77.8,
        "modules_to_patch": ["ensemble_postprocess"],
        "performance_notes": "Research-backed weight distribution (arXiv:2510.17145 - 97.49%). "
                           "Replaces five-way voting with weighted ensemble",
        "parameters": {
            "weight_color": 0.35,
            "weight_raw_compat": 0.25,
            "weight_texture": 0.20,
            "weight_morphological": 0.15,
            "weight_gabor": 0.05
        }
    },

    "Variant 5 (66.7%)": {
        "description": "Aggressive color^6 penalty for better cross-source discrimination. "
                      "More aggressive color penalty in appearance similarity computation",
        "accuracy_positive": 66.7,
        "accuracy_negative": 77.8,
        "accuracy_overall": 72.6,
        "modules_to_patch": ["compatibility", "hard_discriminators"],
        "performance_notes": "Strong negative discrimination but reduces positive accuracy. "
                           "POWER_COLOR = 8.0 (vs 4.0 baseline). Trade-off: -11.1% positive for same negative",
        "parameters": {
            "power_color": 8.0,
            "power_texture": 2.0,
            "power_gabor": 2.0,
            "power_haralick": 2.0
        }
    },

    "Variant 8 (Ready)": {
        "description": "Adaptive Gabor weighting - fixes BC=1.0 uninformative issue. "
                      "Detects homogeneous textures and reduces Gabor weight adaptively",
        "accuracy_positive": None,  # Ready for testing
        "accuracy_negative": None,
        "accuracy_overall": None,
        "modules_to_patch": ["compatibility"],
        "performance_notes": "Fixes critical Gabor BC=1.0 issue for brown/beige artifacts. "
                           "Adaptive: color^5 × texture^3 × gabor^0.5 × haralick^3 when uninformative. "
                           "Expected: 85-90% negative accuracy (eliminate 4-5 of 7 false positives)",
        "parameters": {
            "power_color_normal": 4.0,
            "power_gabor_normal": 2.0,
            "power_color_adaptive": 5.0,
            "power_gabor_adaptive": 0.5,
            "spectral_diversity_threshold": 0.15,
            "uninformative_gabor_threshold": 0.95
        }
    },

    "Variant 9 (Ready)": {
        "description": "Full research-optimized stack. Multi-layer defense: "
                      "hard discriminators + weighted ensemble + gating + stricter thresholds",
        "accuracy_positive": None,  # Ready for testing
        "accuracy_negative": None,
        "accuracy_overall": None,
        "modules_to_patch": ["ensemble_postprocess"],
        "performance_notes": "Culmination of all optimizations. Target: 92%+ both metrics (stretch: 95%+). "
                           "4-layer defense system combining best techniques from Variant 0D (89%/86%)",
        "parameters": {
            "weight_color": 0.45,
            "weight_raw_compat": 0.25,
            "weight_texture": 0.15,
            "weight_morphological": 0.10,
            "weight_gabor": 0.05,
            "hard_edge_density_max_diff": 0.15,
            "hard_entropy_max_diff": 0.50,
            "hard_min_color_similarity": 0.60,
            "hard_min_texture_similarity": 0.55,
            "gate_upgrade_min_color": 0.75,
            "gate_upgrade_min_texture": 0.70
        }
    }
}


# =============================================================================
# ORIGINAL FUNCTION STORAGE (for restoration)
# =============================================================================

_original_functions: Dict[str, Dict[str, Callable]] = {}


# =============================================================================
# VARIANT APPLICATION FUNCTIONS
# =============================================================================

def apply_variant_baseline() -> None:
    """
    Apply Baseline variant (no changes needed).

    This is the default configuration - all modules use their original
    implementations without any monkey-patching.
    """
    logger.info("Applying Baseline variant (77.8%% accuracy)")
    logger.info("  - No patches required - using original implementations")
    restore_all_originals()


def apply_variant_0_iter2() -> None:
    """
    Apply Variant 0 Iteration 2: Tightened hard discriminator thresholds.

    Patches: hard_discriminators module
    - Changes hard_reject_check() to use 0.74/0.69 thresholds
    - Evolutionary optimization: +2.8% color, +3.0% texture

    Expected Results:
    - Positive accuracy: 77.8% (maintained)
    - Negative accuracy: 91.7% (improved from 77.8%)
    - Overall accuracy: 85.1% ⭐ BEST
    """
    logger.info("Applying Variant 0 Iter 2 (85.1%% accuracy) ⭐ BEST")
    logger.info("  - Patching hard_discriminators module")
    logger.info("  - Thresholds: color=0.74 (+2.8%%), texture=0.69 (+3.0%%)")

    try:
        # Import variant module
        variant_module = importlib.import_module('hard_discriminators_variant0_iter2')

        # Import base module to patch
        import hard_discriminators

        # Store original functions if not already stored
        if 'hard_discriminators' not in _original_functions:
            _original_functions['hard_discriminators'] = {
                'hard_reject_check': hard_discriminators.hard_reject_check,
                'compute_edge_density': hard_discriminators.compute_edge_density,
                'compute_texture_entropy': hard_discriminators.compute_texture_entropy
            }

        # Apply monkey patches
        hard_discriminators.hard_reject_check = variant_module.hard_reject_check
        hard_discriminators.compute_edge_density = variant_module.compute_edge_density
        hard_discriminators.compute_texture_entropy = variant_module.compute_texture_entropy

        logger.info("  ✓ Successfully patched hard_discriminators module")

    except ImportError as e:
        logger.error(f"  ✗ Failed to import variant module: {e}")
        raise
    except Exception as e:
        logger.error(f"  ✗ Failed to apply variant: {e}")
        raise


def apply_variant_1() -> None:
    """
    Apply Variant 1: Weighted ensemble post-processing.

    Patches: ensemble_postprocess module
    - Replaces ensemble_verdict_five_way with ensemble_verdict_weighted
    - Uses learned weights: Color(0.35), Raw(0.25), Texture(0.20), Morph(0.15), Gabor(0.05)

    Expected Results:
    - Positive accuracy: 77.8%
    - Negative accuracy: 77.8%
    - Overall accuracy: 77.8%
    - Research-backed weight distribution (arXiv:2510.17145 - 97.49%)
    """
    logger.info("Applying Variant 1 (77.8%% accuracy)")
    logger.info("  - Patching ensemble_postprocess module")
    logger.info("  - Weights: Color(0.35), Raw(0.25), Texture(0.20), Morph(0.15), Gabor(0.05)")

    try:
        # Import variant module
        variant_module = importlib.import_module('ensemble_postprocess_variant1')

        # Import base module to patch
        import ensemble_postprocess

        # Store original functions if not already stored
        if 'ensemble_postprocess' not in _original_functions:
            _original_functions['ensemble_postprocess'] = {
                'reclassify_borderline_cases': ensemble_postprocess.reclassify_borderline_cases
            }

        # Apply monkey patch
        ensemble_postprocess.reclassify_borderline_cases = variant_module.reclassify_borderline_cases

        logger.info("  ✓ Successfully patched ensemble_postprocess module")

    except ImportError as e:
        logger.error(f"  ✗ Failed to import variant module: {e}")
        raise
    except Exception as e:
        logger.error(f"  ✗ Failed to apply variant: {e}")
        raise


def apply_variant_5() -> None:
    """
    Apply Variant 5: Aggressive color^6 penalty.

    Patches: compatibility module, hard_discriminators module
    - Changes POWER_COLOR from 4.0 to 8.0 (more aggressive)
    - Better cross-source discrimination at cost of positive accuracy

    Expected Results:
    - Positive accuracy: 66.7% (reduced from 77.8%)
    - Negative accuracy: 77.8% (maintained)
    - Overall accuracy: 72.6%
    - Trade-off: Stronger negative discrimination, weaker positive matching
    """
    logger.info("Applying Variant 5 (66.7%% positive / 77.8%% negative)")
    logger.info("  - Patching compatibility module")
    logger.info("  - POWER_COLOR: 4.0 → 8.0 (aggressive penalty)")

    try:
        # Import variant module
        variant_module = importlib.import_module('compatibility_variant5')

        # Import base module to patch
        import compatibility

        # Store original functions if not already stored
        if 'compatibility' not in _original_functions:
            _original_functions['compatibility'] = {
                'build_compatibility_matrix': compatibility.build_compatibility_matrix,
                'profile_similarity': compatibility.profile_similarity,
                'good_continuation_bonus': compatibility.good_continuation_bonus,
                'compute_color_signature': compatibility.compute_color_signature,
                'color_bhattacharyya': compatibility.color_bhattacharyya
            }

        # Apply monkey patches
        compatibility.build_compatibility_matrix = variant_module.build_compatibility_matrix
        compatibility.profile_similarity = variant_module.profile_similarity
        compatibility.good_continuation_bonus = variant_module.good_continuation_bonus
        compatibility.compute_color_signature = variant_module.compute_color_signature
        compatibility.color_bhattacharyya = variant_module.color_bhattacharyya

        # Also patch hard_discriminators if variant provides it
        try:
            import hard_discriminators
            variant_hard_disc = importlib.import_module('hard_discriminators_variant5')

            if 'hard_discriminators' not in _original_functions:
                _original_functions['hard_discriminators'] = {
                    'hard_reject_check': hard_discriminators.hard_reject_check
                }

            hard_discriminators.hard_reject_check = variant_hard_disc.hard_reject_check
            logger.info("  ✓ Successfully patched compatibility + hard_discriminators modules")

        except ImportError:
            logger.info("  ✓ Successfully patched compatibility module (hard_discriminators unchanged)")

    except ImportError as e:
        logger.error(f"  ✗ Failed to import variant module: {e}")
        raise
    except Exception as e:
        logger.error(f"  ✗ Failed to apply variant: {e}")
        raise


def apply_variant_8() -> None:
    """
    Apply Variant 8: Adaptive Gabor weighting.

    Patches: compatibility module
    - Fixes Gabor BC=1.0 uninformative issue
    - Adaptive weighting: reduces Gabor weight when homogeneous textures detected
    - Normal mode: color^4 × texture^2 × gabor^2 × haralick^2
    - Adaptive mode: color^5 × texture^3 × gabor^0.5 × haralick^3

    Expected Results:
    - Positive accuracy: 75-80% (minimal impact)
    - Negative accuracy: 85-90% (improved from 77.8%)
    - Overall accuracy: 85-88%
    - Fixes: Eliminates 4-5 of 7 false positives from brown artifact BC=1.0 issue
    """
    logger.info("Applying Variant 8 (Ready - Adaptive Gabor)")
    logger.info("  - Patching compatibility module")
    logger.info("  - Adaptive weighting: Gabor 2.0 → 0.5 when uninformative")
    logger.info("  - Fixes: BC=1.0 issue for homogeneous textures")

    try:
        # Import variant module
        variant_module = importlib.import_module('compatibility_variant8')

        # Import base module to patch
        import compatibility

        # Store original functions if not already stored
        if 'compatibility' not in _original_functions:
            _original_functions['compatibility'] = {
                'build_compatibility_matrix': compatibility.build_compatibility_matrix,
                '_build_appearance_similarity_matrices': compatibility._build_appearance_similarity_matrices
            }

        # Apply monkey patches
        compatibility.build_compatibility_matrix = variant_module.compute_compatibility_matrix

        # Check if variant has the appearance matrix builder
        if hasattr(variant_module, 'build_appearance_matrices'):
            compatibility._build_appearance_similarity_matrices = variant_module.build_appearance_matrices

        logger.info("  ✓ Successfully patched compatibility module with adaptive Gabor")

    except ImportError as e:
        logger.error(f"  ✗ Failed to import variant module: {e}")
        raise
    except Exception as e:
        logger.error(f"  ✗ Failed to apply variant: {e}")
        raise


def apply_variant_9() -> None:
    """
    Apply Variant 9: Full research-optimized stack (FINAL).

    Patches: ensemble_postprocess module
    - Multi-layer defense system
    - Layer 1: Hard discriminator pre-filter (fast rejection)
    - Layer 2: Weighted ensemble voting (discrimination)
    - Layer 3: Ensemble gating (prevent bad upgrades)
    - Layer 4: Stricter thresholds (final classification)

    Expected Results:
    - Positive accuracy: 92%+ (target)
    - Negative accuracy: 92%+ (target)
    - Overall accuracy: 92%+ (stretch: 95%+)
    - Combines best techniques from Variant 0D (89%/86%) with research ensemble
    """
    logger.info("Applying Variant 9 (Ready - Full Research Stack)")
    logger.info("  - Patching ensemble_postprocess module")
    logger.info("  - Multi-layer defense: hard disc + weighted + gating + thresholds")
    logger.info("  - Target: 92%%+ both metrics (stretch: 95%%+)")

    try:
        # Import variant module
        variant_module = importlib.import_module('ensemble_postprocess_variant9_FINAL')

        # Import base module to patch
        import ensemble_postprocess

        # Store original functions if not already stored
        if 'ensemble_postprocess' not in _original_functions:
            _original_functions['ensemble_postprocess'] = {
                'reclassify_borderline_cases': ensemble_postprocess.reclassify_borderline_cases
            }

        # Apply monkey patch
        ensemble_postprocess.reclassify_borderline_cases = variant_module.reclassify_borderline_cases

        logger.info("  ✓ Successfully patched ensemble_postprocess module with full stack")

    except ImportError as e:
        logger.error(f"  ✗ Failed to import variant module: {e}")
        raise
    except Exception as e:
        logger.error(f"  ✗ Failed to apply variant: {e}")
        raise


# =============================================================================
# VARIANT APPLICATION DISPATCHER
# =============================================================================

VARIANT_APPLIERS = {
    "Baseline (77.8%)": apply_variant_baseline,
    "Variant 0 Iter 2 (85.1%) ⭐ BEST": apply_variant_0_iter2,
    "Variant 1 (77.8%)": apply_variant_1,
    "Variant 5 (66.7%)": apply_variant_5,
    "Variant 8 (Ready)": apply_variant_8,
    "Variant 9 (Ready)": apply_variant_9
}


# =============================================================================
# PUBLIC API
# =============================================================================

def get_available_variants() -> list:
    """
    Get list of all available variant names.

    Returns:
        List of variant names (strings) that can be passed to apply_variant()
    """
    return list(VARIANT_CONFIG.keys())


def get_variant_description(variant_name: str) -> str:
    """
    Get detailed description of a variant.

    Args:
        variant_name: Name of the variant (from get_available_variants())

    Returns:
        Human-readable description string

    Raises:
        ValueError: If variant_name is not recognized
    """
    if variant_name not in VARIANT_CONFIG:
        raise ValueError(f"Unknown variant: {variant_name}")

    config = VARIANT_CONFIG[variant_name]

    desc_parts = [
        f"Variant: {variant_name}",
        f"Description: {config['description']}",
        "",
        "Accuracy Metrics:"
    ]

    if config['accuracy_positive'] is not None:
        desc_parts.append(f"  - Positive: {config['accuracy_positive']:.1f}%")
    else:
        desc_parts.append(f"  - Positive: Not yet tested")

    if config['accuracy_negative'] is not None:
        desc_parts.append(f"  - Negative: {config['accuracy_negative']:.1f}%")
    else:
        desc_parts.append(f"  - Negative: Not yet tested")

    if config['accuracy_overall'] is not None:
        desc_parts.append(f"  - Overall: {config['accuracy_overall']:.1f}%")
    else:
        desc_parts.append(f"  - Overall: Not yet tested")

    desc_parts.extend([
        "",
        f"Performance Notes: {config['performance_notes']}"
    ])

    if config['parameters']:
        desc_parts.append("")
        desc_parts.append("Parameters:")
        for param_name, param_value in config['parameters'].items():
            desc_parts.append(f"  - {param_name}: {param_value}")

    return "\n".join(desc_parts)


def get_variant_config(variant_name: str) -> Dict[str, Any]:
    """
    Get full configuration dictionary for a variant.

    Args:
        variant_name: Name of the variant

    Returns:
        Dictionary with configuration details

    Raises:
        ValueError: If variant_name is not recognized
    """
    if variant_name not in VARIANT_CONFIG:
        raise ValueError(f"Unknown variant: {variant_name}")

    return VARIANT_CONFIG[variant_name].copy()


def apply_variant(variant_name: str) -> None:
    """
    Apply a specific algorithm variant by monkey-patching relevant modules.

    This function dynamically imports the variant's implementation modules
    and patches the corresponding functions in the main pipeline. Original
    functions are stored for restoration via restore_baseline().

    Args:
        variant_name: Name of the variant to apply (from get_available_variants())

    Raises:
        ValueError: If variant_name is not recognized
        ImportError: If variant module cannot be imported
        Exception: If patching fails

    Example:
        >>> apply_variant("Variant 0 Iter 2 (85.1%) ⭐ BEST")
        >>> # Run reconstruction pipeline with tightened thresholds
        >>> restore_baseline()  # Restore original implementation
    """
    if variant_name not in VARIANT_CONFIG:
        available = ", ".join(get_available_variants())
        raise ValueError(f"Unknown variant: {variant_name}\nAvailable: {available}")

    logger.info("=" * 70)
    logger.info(f"APPLYING ALGORITHM VARIANT: {variant_name}")
    logger.info("=" * 70)

    # Get the appropriate applier function
    applier = VARIANT_APPLIERS[variant_name]

    # Apply the variant
    applier()

    logger.info("=" * 70)
    logger.info(f"Variant '{variant_name}' applied successfully")
    logger.info("=" * 70)


def restore_baseline() -> None:
    """
    Restore all original (baseline) function implementations.

    This function undoes all monkey-patches applied by apply_variant(),
    returning the system to its original baseline configuration.
    """
    restore_all_originals()


def restore_all_originals() -> None:
    """
    Internal function to restore all patched modules to their original state.
    """
    if not _original_functions:
        logger.debug("No patches to restore")
        return

    logger.info("Restoring original (baseline) implementations...")

    for module_name, functions in _original_functions.items():
        try:
            # Import the module
            module = sys.modules.get(module_name)
            if module is None:
                module = importlib.import_module(module_name)

            # Restore each function
            for func_name, original_func in functions.items():
                setattr(module, func_name, original_func)
                logger.debug(f"  ✓ Restored {module_name}.{func_name}")

        except Exception as e:
            logger.warning(f"  ✗ Failed to restore {module_name}: {e}")

    logger.info("  ✓ All original implementations restored")


def get_current_variant() -> str:
    """
    Determine which variant is currently active.

    Returns:
        Name of the currently active variant, or "Baseline" if none applied

    Note: This is a best-effort detection based on whether functions have been
    patched. It may not be 100% accurate if modules were patched externally.
    """
    if not _original_functions:
        return "Baseline (77.8%)"

    # Check which modules are patched
    patched_modules = list(_original_functions.keys())

    # Try to match against known variant signatures
    if 'hard_discriminators' in patched_modules and len(patched_modules) == 1:
        # Could be Variant 0 Iter 2
        return "Variant 0 Iter 2 (85.1%) ⭐ BEST [or similar]"
    elif 'ensemble_postprocess' in patched_modules and len(patched_modules) == 1:
        # Could be Variant 1 or Variant 9
        return "Variant 1 or 9 [ensemble_postprocess patched]"
    elif 'compatibility' in patched_modules:
        # Could be Variant 5 or Variant 8
        return "Variant 5 or 8 [compatibility patched]"

    return f"Unknown variant [patched: {', '.join(patched_modules)}]"


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def list_variants(verbose: bool = False) -> None:
    """
    Print a formatted list of all available variants to stdout.

    Args:
        verbose: If True, print detailed descriptions. If False, print summary only.
    """
    print("\n" + "=" * 70)
    print("AVAILABLE ALGORITHM VARIANTS")
    print("=" * 70)

    for variant_name in get_available_variants():
        config = VARIANT_CONFIG[variant_name]

        # Print header
        print(f"\n{variant_name}")
        print("-" * len(variant_name))

        if verbose:
            print(get_variant_description(variant_name))
        else:
            # Print summary
            print(f"Description: {config['description'][:100]}...")

            acc_parts = []
            if config['accuracy_positive'] is not None:
                acc_parts.append(f"Pos: {config['accuracy_positive']:.1f}%")
            if config['accuracy_negative'] is not None:
                acc_parts.append(f"Neg: {config['accuracy_negative']:.1f}%")
            if config['accuracy_overall'] is not None:
                acc_parts.append(f"Overall: {config['accuracy_overall']:.1f}%")

            if acc_parts:
                print(f"Accuracy: {', '.join(acc_parts)}")
            else:
                print("Accuracy: Ready for testing")

    print("\n" + "=" * 70)


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    # Configure UTF-8 encoding for Windows console
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    # Configure logging for standalone testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    print("\n" + "=" * 70)
    print("VARIANT MANAGER - STANDALONE TEST")
    print("=" * 70)

    # List all variants
    list_variants(verbose=True)

    # Test variant application (dry run - modules may not be available)
    print("\n" + "=" * 70)
    print("TESTING VARIANT APPLICATION")
    print("=" * 70)

    print("\nNote: This is a dry run. Actual patching requires module availability.")
    print("\nCurrent variant:", get_current_variant())

    print("\n" + "=" * 70)
