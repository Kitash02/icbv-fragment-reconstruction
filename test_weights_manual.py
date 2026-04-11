#!/usr/bin/env python3
"""
Manual Weight Optimization Test

This script demonstrates how to optimize weights for Variant 1.
Run this manually to test different weight configurations.

Usage:
  python test_weights_manual.py --color 0.50 --raw 0.25 --texture 0.15 --morph 0.10 --gabor 0.00
"""

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).parent


def update_weights(color, raw, texture, morph, gabor):
    """Update the weights in ensemble_voting.py"""
    # Validate
    total = color + raw + texture + morph + gabor
    if abs(total - 1.0) > 0.001:
        raise ValueError(f"Weights must sum to 1.0, got {total}")

    voting_file = ROOT / "src" / "ensemble_voting.py"
    backup_file = ROOT / "src" / "ensemble_voting.py.original"

    # Backup if not already done
    if not backup_file.exists():
        shutil.copy(voting_file, backup_file)
        print(f"✓ Created backup: {backup_file}")

    # Read file
    with open(voting_file, 'r') as f:
        content = f.read()

    # Replace weights block
    new_weights_block = f"""    if weights is None:
        weights = {{
            'color': {color},
            'raw_compat': {raw},
            'texture': {texture},
            'morphological': {morph},
            'gabor': {gabor}
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

    # Write
    with open(voting_file, 'w') as f:
        f.write(modified_content)

    print("\n" + "="*80)
    print("WEIGHTS UPDATED SUCCESSFULLY")
    print("="*80)
    print(f"Color:         {color:.2f}")
    print(f"Raw Compat:    {raw:.2f}")
    print(f"Texture:       {texture:.2f}")
    print(f"Morphological: {morph:.2f}")
    print(f"Gabor:         {gabor:.2f}")
    print("="*80)
    print()
    print("Now run the test:")
    print("  python test_variant1_quick.py")
    print()
    print("To restore original weights:")
    print(f"  cp {backup_file} {voting_file}")
    print("="*80)


def restore_original():
    """Restore original weights"""
    voting_file = ROOT / "src" / "ensemble_voting.py"
    backup_file = ROOT / "src" / "ensemble_voting.py.original"

    if not backup_file.exists():
        print("ERROR: No backup file found. Cannot restore.")
        return

    shutil.copy(backup_file, voting_file)
    print("✓ Restored original weights from backup")


def main():
    parser = argparse.ArgumentParser(description="Manually update Variant 1 ensemble weights")
    parser.add_argument('--color', type=float, help='Color weight (default: 0.35)')
    parser.add_argument('--raw', type=float, help='Raw compatibility weight (default: 0.25)')
    parser.add_argument('--texture', type=float, help='Texture weight (default: 0.20)')
    parser.add_argument('--morph', type=float, help='Morphological weight (default: 0.15)')
    parser.add_argument('--gabor', type=float, help='Gabor weight (default: 0.05)')
    parser.add_argument('--restore', action='store_true', help='Restore original weights')
    parser.add_argument('--preset', choices=['baseline', 'color-opt', 'balanced'],
                       help='Use a preset configuration')

    args = parser.parse_args()

    if args.restore:
        restore_original()
        return

    # Presets
    if args.preset == 'baseline':
        color, raw, texture, morph, gabor = 0.35, 0.25, 0.20, 0.15, 0.05
        print("Using BASELINE preset (paper defaults)")
    elif args.preset == 'color-opt':
        color, raw, texture, morph, gabor = 0.50, 0.25, 0.15, 0.10, 0.00
        print("Using COLOR-OPTIMIZED preset (pottery-specific)")
    elif args.preset == 'balanced':
        color, raw, texture, morph, gabor = 0.45, 0.30, 0.15, 0.10, 0.00
        print("Using BALANCED preset (geometry + color)")
    else:
        # Use command line args or defaults
        color = args.color if args.color is not None else 0.35
        raw = args.raw if args.raw is not None else 0.25
        texture = args.texture if args.texture is not None else 0.20
        morph = args.morph if args.morph is not None else 0.15
        gabor = args.gabor if args.gabor is not None else 0.05

    update_weights(color, raw, texture, morph, gabor)


if __name__ == "__main__":
    main()
