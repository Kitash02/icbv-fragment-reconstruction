"""
Variant Manager Architecture Visualization

This script generates a text-based architectural diagram of the variant
management system to help understand component relationships.
"""


def print_architecture_diagram():
    """Print a comprehensive architecture diagram."""

    diagram = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                    VARIANT MANAGER ARCHITECTURE                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────┐
│ USER INTERFACES                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────────┐   │
│  │   CLI Scripts   │  │   GUI Components │  │  Python API        │   │
│  │   (examples/)   │  │   (future)       │  │  (direct import)   │   │
│  └────────┬────────┘  └────────┬─────────┘  └──────────┬─────────┘   │
│           │                    │                       │              │
└───────────┼────────────────────┼───────────────────────┼──────────────┘
            │                    │                       │
            ▼                    ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ VARIANT MANAGER API (src/variant_manager.py)                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Public API:                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ • apply_variant(variant_name: str) → None                        │ │
│  │ • restore_baseline() → None                                      │ │
│  │ • get_available_variants() → List[str]                           │ │
│  │ • get_variant_description(variant_name: str) → str               │ │
│  │ • get_variant_config(variant_name: str) → Dict                   │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  Internal Components:                                                  │
│  ┌────────────────┐  ┌─────────────────┐  ┌────────────────────────┐ │
│  │ VARIANT_CONFIG │  │ VARIANT_APPLIERS│  │ _original_functions   │ │
│  │ (6 variants)   │  │ (dispatchers)   │  │ (storage)             │ │
│  └────────┬───────┘  └────────┬────────┘  └──────────┬─────────────┘ │
│           │                   │                       │               │
└───────────┼───────────────────┼───────────────────────┼───────────────┘
            │                   │                       │
            ▼                   ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ VARIANT APPLIERS (monkey-patching logic)                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ apply_variant_0_iter2()  →  hard_discriminators                  │ │
│  │ apply_variant_1()        →  ensemble_postprocess                 │ │
│  │ apply_variant_5()        →  compatibility + hard_discriminators  │ │
│  │ apply_variant_8()        →  compatibility                        │ │
│  │ apply_variant_9()        →  ensemble_postprocess                 │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└───────────────────────┬─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ PATCHING MECHANISM                                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Step 1: Store Original Functions                                     │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ if 'module_name' not in _original_functions:                     │ │
│  │     _original_functions['module_name'] = {                       │ │
│  │         'func_name': module.func_name                            │ │
│  │     }                                                             │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  Step 2: Import Variant Module                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ variant_module = importlib.import_module('module_variant_X')    │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  Step 3: Replace Functions                                            │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ base_module.func_name = variant_module.func_name                │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  Step 4: Restoration Available                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ module.func_name = _original_functions['module']['func']        │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└───────────────────────┬─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ TARGET MODULES (base implementations)                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────┐  ┌────────────────────┐  ┌────────────────┐ │
│  │ hard_discriminators  │  │ ensemble_postprocess│ │ compatibility  │ │
│  │                      │  │                     │ │                │ │
│  │ • hard_reject_check()│  │ • reclassify_      │ │ • build_compat │ │
│  │ • compute_edge_     │  │   borderline_cases()│ │   _matrix()    │ │
│  │   density()         │  │                     │ │ • profile_     │ │
│  │ • compute_texture_  │  │                     │ │   similarity() │ │
│  │   entropy()         │  │                     │ │                │ │
│  └──────────────────────┘  └────────────────────┘  └────────────────┘ │
│                                                                         │
└───────────────────────┬─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ VARIANT IMPLEMENTATIONS (patched modules)                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  hard_discriminators_variant0_iter2.py  (thresholds: 0.74 / 0.69)     │
│  hard_discriminators_variant5.py        (additional checks)            │
│                                                                         │
│  ensemble_postprocess_variant1.py       (weighted ensemble)            │
│  ensemble_postprocess_variant9_FINAL.py (4-layer defense)              │
│                                                                         │
│  compatibility_variant5.py              (color^8 penalty)              │
│  compatibility_variant8.py              (adaptive Gabor)               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘


╔═══════════════════════════════════════════════════════════════════════════╗
║                           DATA FLOW EXAMPLE                               ║
╚═══════════════════════════════════════════════════════════════════════════╝

User selects "Variant 0 Iter 2 (85.1%) ⭐ BEST"
    │
    ▼
apply_variant("Variant 0 Iter 2 (85.1%) ⭐ BEST")
    │
    ▼
VARIANT_APPLIERS["Variant 0 Iter 2..."] → apply_variant_0_iter2()
    │
    ├─► Store original: hard_discriminators.hard_reject_check
    │
    ├─► Import: hard_discriminators_variant0_iter2
    │
    └─► Replace: hard_discriminators.hard_reject_check = variant.hard_reject_check
    │
    ▼
Pipeline runs with patched functions (thresholds: 0.74 / 0.69)
    │
    ▼
restore_baseline()
    │
    └─► Restore: hard_discriminators.hard_reject_check = <original>


╔═══════════════════════════════════════════════════════════════════════════╗
║                         MODULE DEPENDENCIES                               ║
╚═══════════════════════════════════════════════════════════════════════════╝

variant_manager.py
    │
    ├─► importlib (dynamic imports)
    ├─► logging (operation logging)
    └─► sys (module management)

variant_quick_reference.py
    │
    └─► (no dependencies - standalone)

Examples:
    variant_selection_example.py
        └─► variant_manager

    run_with_variant.py
        ├─► variant_manager
        ├─► main (pipeline)
        └─► argparse


╔═══════════════════════════════════════════════════════════════════════════╗
║                          VARIANT MAPPING                                  ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌────────────────────┬──────────────────────────┬─────────────────────────┐
│ Variant            │ Patches                  │ Implementation File     │
├────────────────────┼──────────────────────────┼─────────────────────────┤
│ Baseline           │ (none)                   │ (original modules)      │
├────────────────────┼──────────────────────────┼─────────────────────────┤
│ Variant 0 Iter 2 ⭐│ hard_discriminators      │ hard_discriminators_    │
│                    │                          │   variant0_iter2.py     │
├────────────────────┼──────────────────────────┼─────────────────────────┤
│ Variant 1          │ ensemble_postprocess     │ ensemble_postprocess_   │
│                    │                          │   variant1.py           │
├────────────────────┼──────────────────────────┼─────────────────────────┤
│ Variant 5          │ compatibility            │ compatibility_variant5  │
│                    │ hard_discriminators      │ hard_discriminators_    │
│                    │                          │   variant5.py           │
├────────────────────┼──────────────────────────┼─────────────────────────┤
│ Variant 8          │ compatibility            │ compatibility_variant8  │
│                    │                          │   .py                   │
├────────────────────┼──────────────────────────┼─────────────────────────┤
│ Variant 9          │ ensemble_postprocess     │ ensemble_postprocess_   │
│                    │                          │   variant9_FINAL.py     │
└────────────────────┴──────────────────────────┴─────────────────────────┘


╔═══════════════════════════════════════════════════════════════════════════╗
║                       USAGE FLOW DIAGRAM                                  ║
╚═══════════════════════════════════════════════════════════════════════════╝

START
  │
  ├──► List variants: get_available_variants()
  │         │
  │         └─► Display 6 variants to user
  │
  ├──► Get details: get_variant_description(name)
  │         │
  │         └─► Show accuracy, parameters, notes
  │
  ├──► Apply variant: apply_variant(name)
  │         │
  │         ├─► Validate name
  │         ├─► Call applier function
  │         ├─► Store originals
  │         ├─► Import variant module
  │         ├─► Patch functions
  │         └─► Log success
  │
  ├──► Run pipeline with patched modules
  │         │
  │         └─► Pipeline uses variant implementations
  │
  └──► Restore: restore_baseline()
            │
            ├─► Restore all original functions
            ├─► Clear storage
            └─► Log restoration
END

"""

    print(diagram)


if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print_architecture_diagram()
