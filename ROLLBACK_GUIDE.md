# Rollback Scripts - User Guide

## Overview
Automated rollback scripts for instant recovery of the ICBV Fragment Reconstruction project if anything goes wrong.

## Files Created
1. `rollback_to_backup.sh` - Bash script (Linux/Mac/Git Bash)
2. `rollback_to_backup.bat` - Windows batch script

## Features
- **Automatic backup discovery**: Finds all backups matching pattern `src_backup*_YYYYMMDD_HHMMSS`
- **Latest backup auto-selection**: Run without parameters to use most recent backup
- **Manual backup selection**: Specify timestamp to restore from specific backup
- **Safety first**: Creates safety backup of current state before rolling back
- **Verification**: Confirms file counts match and key files are present
- **Color-coded output**: Clear visual feedback of progress and status
- **Error handling**: Automatic recovery if rollback fails

## Usage

### Bash Script (Linux/Mac/Git Bash)

**Restore from latest backup:**
```bash
./rollback_to_backup.sh
```

**Restore from specific backup:**
```bash
./rollback_to_backup.sh 20260411_020401
```

**List available backups:**
```bash
ls -td src_backup* | grep -E "_[0-9]{8}_[0-9]{6}"
```

### Windows Batch Script

**Restore from latest backup:**
```cmd
rollback_to_backup.bat
```

**Restore from specific backup:**
```cmd
rollback_to_backup.bat 20260411_020401
```

**List available backups:**
```cmd
dir /b /ad /o-d src_backup*
```

## What Happens During Rollback

1. **Backup Discovery**: Script finds all available backups
2. **Backup Selection**: Uses latest or user-specified backup
3. **Verification**: Confirms backup exists and contains files
4. **Safety Backup**: Current `src/` directory backed up to `src_rollback_safety_TIMESTAMP`
5. **Restoration**: Old `src/` removed, backup copied to `src/`
6. **Verification**: File counts checked, key files verified
7. **Summary**: Clear success/failure message with details

## Example Output

```
================================================
   ICBV Fragment Reconstruction - ROLLBACK
================================================

Selected backup: src_backup_unicode_20260411_020401
Timestamp: 20260411_020401

Backup contents:
Total files in backup: 88

SAFETY: Creating rollback safety backup...
  Backing up current src/ to: src_rollback_safety_20260411_023541
  ✓ Safety backup created

ROLLBACK: Restoring from backup...
  Removing current src/ directory...
  Copying backup to src/...

VERIFICATION: Checking restoration...
  Files restored: 88
  ✓ File count matches backup

Key components check:
  ✓ src/main.py
  ✓ src/compatibility.py

================================================
✓ ROLLBACK SUCCESSFUL
================================================

Summary:
  - Restored from: src_backup_unicode_20260411_020401
  - Backup timestamp: 20260411_020401
  - Files restored: 88
  - Safety backup: src_rollback_safety_20260411_023541
```

## Safety Features

### Double Backup Protection
Before any rollback, the current state is backed up to `src_rollback_safety_TIMESTAMP`. This means:
- You can rollback a rollback if needed
- No risk of losing current work
- Multiple safety nets in place

### Recovery Commands

**If rollback goes wrong, restore pre-rollback state:**
```bash
# Bash
rm -rf src && cp -r src_rollback_safety_TIMESTAMP src

# Windows
rd /s /q src && xcopy src_rollback_safety_TIMESTAMP src\ /E /I /Q /H /Y
```

**If everything is broken, manually restore from backup:**
```bash
# Bash
rm -rf src && cp -r src_backup_TIMESTAMP src

# Windows
rd /s /q src && xcopy src_backup_TIMESTAMP src\ /E /I /Q /H /Y
```

## Testing Results

### Test 1: Specific Timestamp Rollback
- Command: `./rollback_to_backup.sh 20260411_020401`
- Result: ✓ SUCCESS
- Files restored: 88
- Time: <10 seconds
- Safety backup created: src_rollback_safety_20260411_023541

### Test 2: Latest Backup Auto-Selection
- Command: `./rollback_to_backup.sh`
- Result: ✓ SUCCESS
- Files restored: 96
- Time: <10 seconds
- Automatically selected: src_backup_before_exe_20260411_023343

### Test 3: Invalid Timestamp
- Command: `./rollback_to_backup.sh 99999999_999999`
- Result: ✓ CORRECT ERROR HANDLING
- Output: Lists available backups for user selection

## Performance

- **Execution time**: <30 seconds (typically 10-15 seconds)
- **File operations**: Copy-on-write where possible
- **Disk space**: Minimal (safety backup only)
- **Network**: None required

## Success Criteria

✓ One command restores to working state
✓ Takes <30 seconds
✓ Cannot accidentally destroy data (safety backup always created)
✓ Clear success/failure feedback with color coding
✓ Handles multiple backup formats
✓ Works with both absolute and relative timestamps
✓ Verifies restoration completeness

## Troubleshooting

**No backups found:**
- Check backup naming convention: `src_backup*_YYYYMMDD_HHMMSS`
- Ensure you're in the project root directory
- Verify backups haven't been deleted

**Rollback fails:**
- Script automatically attempts recovery from safety backup
- Check disk space
- Verify file permissions
- Review error messages for specific issues

**Wrong backup restored:**
- Use safety backup to restore previous state
- Specify exact timestamp for next rollback
- Check backup contents before rolling back

## Integration with Backup Scripts

These rollback scripts work with backup scripts that create directories matching:
- `src_backup*_YYYYMMDD_HHMMSS`

Examples:
- `src_backup_unicode_20260411_020401`
- `src_backup_before_exe_20260411_023343`
- `src_backup_manual_20260411_120000`

## Best Practices

1. **Test before production**: Run rollback in test environment first
2. **Verify restoration**: Always run tests after rollback
3. **Keep backups**: Don't delete old backups immediately
4. **Document changes**: Note why rollback was needed
5. **Clean up safety backups**: Remove old safety backups after confirming success

## Files Location

All scripts and backups in project root:
```
C:\Users\I763940\icbv-fragment-reconstruction\
├── rollback_to_backup.sh          # Bash rollback script
├── rollback_to_backup.bat         # Windows rollback script
├── src/                            # Current source code
├── src_backup_*/                   # Backup directories
└── src_rollback_safety_*/          # Safety backups from rollback operations
```
