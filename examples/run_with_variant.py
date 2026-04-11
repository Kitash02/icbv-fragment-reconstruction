"""
Integration Example: Running Main Pipeline with Variant Selection

This script demonstrates how to integrate variant selection with the main
fragment reconstruction pipeline. It shows the complete workflow:

1. List available variants
2. Select and apply a variant
3. Run the reconstruction pipeline
4. Restore baseline for next run

Usage:
    python examples/run_with_variant.py --input data/sample --variant "Variant 0 Iter 2 (85.1%) ⭐ BEST"
    python examples/run_with_variant.py --input data/sample --variant Baseline
    python examples/run_with_variant.py --input data/sample --list-variants
"""

import sys
import os
import argparse
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from variant_manager import (
    apply_variant,
    restore_baseline,
    get_available_variants,
    list_variants
)


def setup_logging():
    """Configure logging for the example."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )


def main():
    # Configure UTF-8 for Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(
        description="Run fragment reconstruction with variant selection"
    )
    parser.add_argument(
        '--input',
        type=str,
        help='Input directory containing fragment images'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='outputs/results',
        help='Output directory for results'
    )
    parser.add_argument(
        '--log',
        type=str,
        default='outputs/logs',
        help='Log directory'
    )
    parser.add_argument(
        '--variant',
        type=str,
        default='Baseline (77.8%)',
        help='Variant name to apply'
    )
    parser.add_argument(
        '--list-variants',
        action='store_true',
        help='List all available variants and exit'
    )
    parser.add_argument(
        '--no-restore',
        action='store_true',
        help='Do not restore baseline after run (keep variant active)'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()
    logger = logging.getLogger('run_with_variant')

    # List variants and exit
    if args.list_variants:
        list_variants(verbose=True)
        return 0

    # Validate input directory
    if not args.input:
        logger.error("--input directory is required")
        parser.print_help()
        return 1

    if not os.path.isdir(args.input):
        logger.error(f"Input directory not found: {args.input}")
        return 1

    # Create output directories
    os.makedirs(args.output, exist_ok=True)
    os.makedirs(args.log, exist_ok=True)

    logger.info("=" * 70)
    logger.info("FRAGMENT RECONSTRUCTION WITH VARIANT SELECTION")
    logger.info("=" * 70)
    logger.info(f"Input directory: {args.input}")
    logger.info(f"Output directory: {args.output}")
    logger.info(f"Log directory: {args.log}")
    logger.info(f"Selected variant: {args.variant}")
    logger.info("=" * 70)

    try:
        # Apply the selected variant
        logger.info("\nStep 1: Applying algorithm variant...")
        apply_variant(args.variant)

        # Import and run the main pipeline
        logger.info("\nStep 2: Running reconstruction pipeline...")
        logger.info("=" * 70)

        # Import main after variant is applied so patches take effect
        from main import main as run_pipeline

        # Prepare arguments for main pipeline
        sys.argv = [
            'main.py',
            '--input', args.input,
            '--output', args.output,
            '--log', args.log
        ]

        # Run the pipeline
        run_pipeline()

        logger.info("=" * 70)
        logger.info("Pipeline completed successfully!")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1

    finally:
        # Restore baseline unless --no-restore flag is set
        if not args.no_restore:
            logger.info("\nStep 3: Restoring baseline configuration...")
            restore_baseline()
            logger.info("Baseline restored")
        else:
            logger.info("\nVariant kept active (--no-restore flag)")

    logger.info("=" * 70)
    logger.info("All done!")
    logger.info("=" * 70)

    return 0


if __name__ == '__main__':
    sys.exit(main())
