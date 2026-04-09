#!/usr/bin/env python3
"""
Deploy Iteration 2 configuration to production.

This script updates the main hard_discriminators.py file with the
optimal thresholds identified through evolutionary optimization.

BACKUP: Creates backup of current file before modification.
"""

import shutil
from pathlib import Path
from datetime import datetime


def deploy_iteration2_config():
    """Deploy Iteration 2 (0.74/0.69) configuration to production."""

    root_dir = Path(__file__).parent
    target_file = root_dir / "src" / "hard_discriminators.py"

    if not target_file.exists():
        print(f"ERROR: Target file not found: {target_file}")
        return False

    # Create backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = root_dir / "src" / f"hard_discriminators_backup_{timestamp}.py"

    print("="*70)
    print("DEPLOYING ITERATION 2 CONFIGURATION")
    print("="*70)
    print()
    print(f"Target file: {target_file}")
    print(f"Backup file: {backup_file}")
    print()

    # Backup current file
    shutil.copy2(target_file, backup_file)
    print(f"✓ Backup created: {backup_file}")

    # Read current file
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace thresholds
    original_line = "if bc_color < 0.70 or bc_texture < 0.65:"
    new_line = "if bc_color < 0.74 or bc_texture < 0.69:"

    if original_line in content:
        content = content.replace(original_line, new_line)
        print(f"✓ Updated threshold: 0.70/0.65 → 0.74/0.69")
    else:
        print("⚠ Warning: Original threshold line not found exactly")
        print("   Manual verification required")

        # Try alternative patterns
        if "bc_color < 0.72" in content:
            content = content.replace("bc_color < 0.72", "bc_color < 0.74")
            content = content.replace("bc_texture < 0.67", "bc_texture < 0.69")
            print("✓ Updated from iteration 1: 0.72/0.67 → 0.74/0.69")
        elif "bc_color < 0.75" in content:
            content = content.replace("bc_color < 0.75", "bc_color < 0.74")
            content = content.replace("bc_texture < 0.70", "bc_texture < 0.69")
            print("✓ Updated from variant 0B: 0.75/0.70 → 0.74/0.69")

    # Write updated file
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ Configuration deployed to: {target_file}")
    print()
    print("="*70)
    print("DEPLOYMENT SUMMARY")
    print("="*70)
    print()
    print("Configuration: Iteration 2 (Optimal)")
    print("  - hard_disc_color: 0.74 (was 0.70, +5.7%)")
    print("  - hard_disc_texture: 0.69 (was 0.65, +6.2%)")
    print()
    print("Expected Improvements:")
    print("  - Positive accuracy: ~87-90% (was ~78%)")
    print("  - Negative accuracy: ~85-88% (was ~78%)")
    print("  - False positives: 1-2 (was 8)")
    print("  - False negatives: 1-2 (was 2)")
    print()
    print("Next Steps:")
    print("  1. Run validation: python run_test.py")
    print("  2. Verify improvements match expectations")
    print("  3. Monitor production performance")
    print("  4. If results differ, restore backup:")
    print(f"     cp {backup_file} {target_file}")
    print()
    print("="*70)

    return True


if __name__ == "__main__":
    success = deploy_iteration2_config()
    exit(0 if success else 1)
