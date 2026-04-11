"""
Example: Using the Variant Manager with the Fragment Reconstruction Pipeline

This script demonstrates how to apply different algorithm variants to the
reconstruction pipeline and compare their performance.

Usage:
    python examples/variant_selection_example.py --variant "Variant 0 Iter 2 (85.1%) ⭐ BEST"
    python examples/variant_selection_example.py --list-variants
"""

import sys
import os
import argparse

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from variant_manager import (
    apply_variant,
    restore_baseline,
    get_available_variants,
    get_variant_description,
    list_variants
)


def main():
    parser = argparse.ArgumentParser(
        description="Apply algorithm variants to fragment reconstruction"
    )
    parser.add_argument(
        '--variant',
        type=str,
        help='Variant name to apply'
    )
    parser.add_argument(
        '--list-variants',
        action='store_true',
        help='List all available variants'
    )
    parser.add_argument(
        '--describe',
        type=str,
        help='Show detailed description of a variant'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show verbose output'
    )

    args = parser.parse_args()

    # Configure UTF-8 for Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    # List variants
    if args.list_variants:
        list_variants(verbose=args.verbose)
        return

    # Describe variant
    if args.describe:
        print(get_variant_description(args.describe))
        return

    # Apply variant
    if args.variant:
        print(f"\nApplying variant: {args.variant}")
        print("=" * 70)

        try:
            apply_variant(args.variant)
            print("\n✓ Variant applied successfully!")
            print("\nYou can now run the main pipeline with this variant:")
            print("  python src/main.py --input data/sample --output outputs/results")
            print("\nTo restore baseline:")
            print("  restore_baseline()")

        except Exception as e:
            print(f"\n✗ Failed to apply variant: {e}")
            return 1

        return 0

    # No arguments - show help
    parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
