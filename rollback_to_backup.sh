#!/bin/bash
# Automated Rollback Script for ICBV Fragment Reconstruction
# Usage: ./rollback_to_backup.sh [backup_timestamp]
# Example: ./rollback_to_backup.sh 20260411_020401
#          ./rollback_to_backup.sh (uses latest backup)

set -e  # Exit on error

PROJECT_DIR="/c/Users/I763940/icbv-fragment-reconstruction"
cd "$PROJECT_DIR"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   ICBV Fragment Reconstruction - ROLLBACK${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Function to find backups
find_backups() {
    ls -td src_backup* 2>/dev/null | grep -E "_[0-9]{8}_[0-9]{6}" || true
}

# Check if backups exist
AVAILABLE_BACKUPS=$(find_backups)
if [ -z "$AVAILABLE_BACKUPS" ]; then
    echo -e "${RED}✗ ERROR: No backup directories found!${NC}"
    echo "  Expected format: src_backup*_YYYYMMDD_HHMMSS"
    exit 1
fi

# Determine which backup to use
if [ -n "$1" ]; then
    # User specified a timestamp
    BACKUP_DIR=$(find_backups | grep "$1" | head -1)
    if [ -z "$BACKUP_DIR" ]; then
        echo -e "${RED}✗ ERROR: No backup found matching timestamp: $1${NC}"
        echo ""
        echo "Available backups:"
        find_backups | while read backup; do
            timestamp=$(echo "$backup" | grep -oE "[0-9]{8}_[0-9]{6}")
            echo "  - $timestamp (from $backup)"
        done
        exit 1
    fi
else
    # Use latest backup
    BACKUP_DIR=$(find_backups | head -1)
fi

echo -e "${YELLOW}Selected backup: ${NC}$BACKUP_DIR"
BACKUP_TIMESTAMP=$(echo "$BACKUP_DIR" | grep -oE "[0-9]{8}_[0-9]{6}")
echo -e "${YELLOW}Timestamp: ${NC}$BACKUP_TIMESTAMP"
echo ""

# Verify backup directory exists and is not empty
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}✗ ERROR: Backup directory does not exist: $BACKUP_DIR${NC}"
    exit 1
fi

if [ -z "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ]; then
    echo -e "${RED}✗ ERROR: Backup directory is empty: $BACKUP_DIR${NC}"
    exit 1
fi

echo "Backup contents:"
ls -lh "$BACKUP_DIR" | head -10
BACKUP_FILE_COUNT=$(find "$BACKUP_DIR" -type f | wc -l)
echo "Total files in backup: $BACKUP_FILE_COUNT"
echo ""

# Safety check: backup current state before rollback
echo -e "${YELLOW}SAFETY: Creating rollback safety backup...${NC}"
SAFETY_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SAFETY_BACKUP="src_rollback_safety_${SAFETY_TIMESTAMP}"

if [ -d "src" ]; then
    echo "  Backing up current src/ to: $SAFETY_BACKUP"
    cp -r src "$SAFETY_BACKUP"
    echo -e "  ${GREEN}✓${NC} Safety backup created"
else
    echo "  Note: No existing src/ directory to backup"
fi
echo ""

# Perform rollback
echo -e "${YELLOW}ROLLBACK: Restoring from backup...${NC}"
echo "  Removing current src/ directory..."
if [ -d "src" ]; then
    rm -rf src
fi

echo "  Copying backup to src/..."
cp -r "$BACKUP_DIR" src

# Verify restoration
echo ""
echo -e "${YELLOW}VERIFICATION: Checking restoration...${NC}"

if [ ! -d "src" ]; then
    echo -e "${RED}✗ CRITICAL ERROR: src/ directory was not created!${NC}"
    echo "  Attempting to restore from safety backup..."
    if [ -d "$SAFETY_BACKUP" ]; then
        cp -r "$SAFETY_BACKUP" src
        echo "  Safety backup restored. Please investigate the issue."
    fi
    exit 1
fi

# Count files restored
FILE_COUNT=$(find src -type f | wc -l)
echo "  Files restored: $FILE_COUNT"

if [ "$FILE_COUNT" -eq 0 ]; then
    echo -e "${RED}✗ WARNING: No files found in restored src/ directory!${NC}"
    exit 1
fi

# Verify file count matches
if [ "$FILE_COUNT" -eq "$BACKUP_FILE_COUNT" ]; then
    echo -e "  ${GREEN}✓${NC} File count matches backup"
else
    echo -e "  ${YELLOW}!${NC} File count differs from backup ($BACKUP_FILE_COUNT)"
fi

# Check for key directories/files
echo ""
echo "Key components check:"
[ -f "src/main.py" ] && echo -e "  ${GREEN}✓${NC} src/main.py" || echo -e "  ${RED}✗${NC} src/main.py (missing)"
[ -f "src/score_variant.py" ] && echo -e "  ${GREEN}✓${NC} src/score_variant.py" || echo "  - src/score_variant.py (not present)"
[ -f "src/compatibility.py" ] && echo -e "  ${GREEN}✓${NC} src/compatibility.py" || echo "  - src/compatibility.py (not present)"
[ -d "src/__pycache__" ] && echo "  - src/__pycache__/ (present)" || echo "  - src/__pycache__/ (not present)"

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✓ ROLLBACK SUCCESSFUL${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Summary:"
echo "  - Restored from: $BACKUP_DIR"
echo "  - Backup timestamp: $BACKUP_TIMESTAMP"
echo "  - Files restored: $FILE_COUNT"
echo "  - Safety backup: $SAFETY_BACKUP"
echo ""
echo "You can now test the restored code:"
echo "  python src/main.py"
echo ""
echo "If issues occur, you can restore the pre-rollback state:"
echo "  rm -rf src && cp -r $SAFETY_BACKUP src"
echo ""
