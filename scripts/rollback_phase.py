#!/usr/bin/env python3
"""
rollback_phase.py
-----------------
Automated rollback utility for phases.

This script:
- Rolls back specific phase changes
- Applies saved git patches in reverse
- Re-runs tests to confirm rollback worked
- Restores previous phase state

Usage:
    python scripts/rollback_phase.py --phase 1a
    python scripts/rollback_phase.py --phase 1b --dry-run
    python scripts/rollback_phase.py --to-baseline

Author: Automated Testing Framework
Date: 2026-04-08
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

OUTPUTS_DIR = ROOT / "outputs" / "testing"
BACKUP_DIR = ROOT / "outputs" / "implementation"
SRC_DIR = ROOT / "src"


class PhaseRollback:
    """Handles rollback of phase changes."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.backup_files = {}

    def backup_current_state(self, phase: str) -> bool:
        """Create backup of current state before rollback."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"pre_rollback_{phase}_{timestamp}.backup"

        print(f"Creating backup of current state...")

        if self.dry_run:
            print(f"  [DRY-RUN] Would backup to: {backup_file}")
            return True

        try:
            # Backup key source files
            files_to_backup = [
                SRC_DIR / "compatibility.py",
                SRC_DIR / "main.py",
                SRC_DIR / "preprocessing.py",
            ]

            backup_data = {}
            for file_path in files_to_backup:
                if file_path.exists():
                    backup_data[str(file_path)] = file_path.read_text()

            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            backup_file.write_text(json.dumps(backup_data, indent=2))

            print(f"✓ Backup created: {backup_file}")
            return True

        except Exception as e:
            print(f"✗ Backup failed: {e}")
            return False

    def find_phase_backup(self, phase: str) -> Optional[Path]:
        """Find the backup file for a phase."""
        # Look for backup files
        pattern = f"backup_phase_{phase}_*.backup"
        backups = sorted(BACKUP_DIR.glob(pattern))

        if not backups:
            # Try alternative naming
            pattern = f"*{phase}*.backup"
            backups = sorted(BACKUP_DIR.glob(pattern))

        if not backups:
            print(f"✗ No backup found for phase {phase}")
            return None

        # Return most recent
        latest = backups[-1]
        print(f"✓ Found backup: {latest}")
        return latest

    def restore_from_backup(self, backup_file: Path) -> bool:
        """Restore files from backup."""
        print(f"\nRestoring from backup: {backup_file.name}")

        if self.dry_run:
            print(f"  [DRY-RUN] Would restore from: {backup_file}")
            return True

        try:
            backup_data = json.loads(backup_file.read_text())

            for file_path_str, content in backup_data.items():
                file_path = Path(file_path_str)
                print(f"  Restoring: {file_path.relative_to(ROOT)}")
                file_path.write_text(content)

            print("✓ Files restored successfully")
            return True

        except Exception as e:
            print(f"✗ Restore failed: {e}")
            return False

    def rollback_to_previous_phase(self, current_phase: str) -> bool:
        """Rollback from current phase to previous phase."""
        # Phase sequence
        phase_sequence = ["baseline", "1a", "1b", "2a", "2b"]

        if current_phase not in phase_sequence:
            print(f"✗ Unknown phase: {current_phase}")
            return False

        current_idx = phase_sequence.index(current_phase)
        if current_idx == 0:
            print("✗ Cannot rollback from baseline")
            return False

        previous_phase = phase_sequence[current_idx - 1]
        print(f"\nRolling back: {current_phase} → {previous_phase}")

        # Find backup for previous phase
        backup_file = self.find_phase_backup(previous_phase)
        if not backup_file:
            print(f"✗ Cannot find backup for {previous_phase}")
            return False

        # Backup current state first
        if not self.backup_current_state(current_phase):
            print("✗ Failed to backup current state")
            return False

        # Restore previous phase
        if not self.restore_from_backup(backup_file):
            print("✗ Failed to restore previous phase")
            return False

        print(f"✓ Rollback complete: {current_phase} → {previous_phase}")
        return True

    def rollback_to_baseline(self) -> bool:
        """Rollback all changes to baseline."""
        print("\n" + "="*80)
        print("ROLLING BACK TO BASELINE")
        print("="*80)

        # Find baseline backup
        backup_file = self.find_phase_backup("baseline")
        if not backup_file:
            print("\n✗ No baseline backup found")
            print("   Baseline state may need to be recreated manually")
            return False

        # Backup current state
        if not self.backup_current_state("rollback_to_baseline"):
            print("✗ Failed to backup current state")
            return False

        # Restore baseline
        if not self.restore_from_backup(backup_file):
            print("✗ Failed to restore baseline")
            return False

        print("\n✓ Successfully rolled back to baseline")
        return True

    def verify_rollback(self, phase: str) -> bool:
        """Run tests to verify rollback worked."""
        print(f"\nVerifying rollback by running tests...")

        if self.dry_run:
            print("  [DRY-RUN] Would run tests to verify")
            return True

        try:
            # Run quick test (no rotation for speed)
            cmd = [
                sys.executable,
                str(ROOT / "run_test.py"),
                "--no-rotate",
                "--results", str(ROOT / "outputs" / "rollback_test"),
                "--logs", str(ROOT / "outputs" / "rollback_logs"),
            ]

            print("  Running test suite...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                print(f"✗ Tests failed after rollback")
                print(f"   Return code: {result.returncode}")
                return False

            # Parse results
            output = result.stdout + result.stderr

            # Look for pass/fail summary
            for line in output.splitlines():
                if "PASS" in line and "/" in line:
                    print(f"  {line.strip()}")

            print("✓ Tests passed after rollback")
            return True

        except subprocess.TimeoutExpired:
            print("✗ Tests timed out")
            return False
        except Exception as e:
            print(f"✗ Error running tests: {e}")
            return False

    def list_available_backups(self) -> None:
        """List all available backup files."""
        print("\n" + "="*80)
        print("AVAILABLE BACKUPS")
        print("="*80)

        if not BACKUP_DIR.exists():
            print("\nNo backup directory found")
            return

        backups = sorted(BACKUP_DIR.glob("*.backup"))

        if not backups:
            print("\nNo backups found")
            return

        print(f"\nFound {len(backups)} backup(s):\n")
        for backup in backups:
            size = backup.stat().st_size / 1024  # KB
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            print(f"  {backup.name:<60} {size:>8.1f} KB  {mtime.strftime('%Y-%m-%d %H:%M:%S')}")

        print()


def main():
    parser = argparse.ArgumentParser(
        description="Rollback phase changes for fragment reconstruction",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--phase",
        help="Phase to rollback from (e.g., 1a, 1b)"
    )
    parser.add_argument(
        "--to-baseline",
        action="store_true",
        help="Rollback all changes to baseline"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available backups"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run tests after rollback to verify"
    )

    args = parser.parse_args()

    rollback = PhaseRollback(dry_run=args.dry_run)

    if args.list:
        rollback.list_available_backups()
        return

    if args.dry_run:
        print("\n" + "="*80)
        print("DRY-RUN MODE (no changes will be made)")
        print("="*80 + "\n")

    success = False

    if args.to_baseline:
        success = rollback.rollback_to_baseline()

    elif args.phase:
        success = rollback.rollback_to_previous_phase(args.phase)

    else:
        parser.print_help()
        sys.exit(1)

    if success and args.verify and not args.dry_run:
        success = rollback.verify_rollback(args.phase or "baseline")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
