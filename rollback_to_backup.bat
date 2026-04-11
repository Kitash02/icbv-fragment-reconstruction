@echo off
REM Automated Rollback Script for ICBV Fragment Reconstruction (Windows)
REM Usage: rollback_to_backup.bat [backup_timestamp]
REM Example: rollback_to_backup.bat 20260411_020401
REM          rollback_to_backup.bat (uses latest backup)

setlocal enabledelayedexpansion

set "PROJECT_DIR=C:\Users\I763940\icbv-fragment-reconstruction"
cd /d "%PROJECT_DIR%"

echo ================================================
echo    ICBV Fragment Reconstruction - ROLLBACK
echo ================================================
echo.

REM Find available backups
set BACKUP_FOUND=0
set LATEST_BACKUP=
for /f "tokens=*" %%a in ('dir /b /ad /o-d src_backup_* 2^>nul') do (
    set BACKUP_FOUND=1
    if "!LATEST_BACKUP!"=="" set "LATEST_BACKUP=%%a"
)

if %BACKUP_FOUND%==0 (
    echo X ERROR: No backup directories found!
    echo   Expected format: src_backup_*_YYYYMMDD_HHMMSS
    exit /b 1
)

REM Determine which backup to use
if "%~1"=="" (
    REM Use latest backup
    set "BACKUP_DIR=!LATEST_BACKUP!"
    echo Using latest backup: !BACKUP_DIR!
) else (
    REM User specified a timestamp
    set BACKUP_DIR=
    for /f "tokens=*" %%a in ('dir /b /ad src_backup_*%~1* 2^>nul') do (
        set "BACKUP_DIR=%%a"
        goto :found_backup
    )
    :found_backup
    if "!BACKUP_DIR!"=="" (
        echo X ERROR: No backup found matching timestamp: %~1
        echo.
        echo Available backups:
        for /f "tokens=*" %%a in ('dir /b /ad /o-d src_backup_* 2^>nul') do (
            echo   - %%a
        )
        exit /b 1
    )
    echo Selected backup: !BACKUP_DIR!
)

REM Extract timestamp from backup name
for /f "tokens=3,4 delims=_" %%a in ("!BACKUP_DIR!") do (
    set "BACKUP_TIMESTAMP=%%a_%%b"
)
echo Timestamp: !BACKUP_TIMESTAMP!
echo.

REM Verify backup directory exists
if not exist "!BACKUP_DIR!" (
    echo X ERROR: Backup directory does not exist: !BACKUP_DIR!
    exit /b 1
)

REM Check if backup is empty
dir /b "!BACKUP_DIR!" | findstr "^" >nul
if errorlevel 1 (
    echo X ERROR: Backup directory is empty: !BACKUP_DIR!
    exit /b 1
)

echo Backup directory verified.
echo.

REM Safety check: backup current state before rollback
echo SAFETY: Creating rollback safety backup...
for /f "tokens=1-6 delims=:/., " %%a in ("%date% %time%") do (
    set "SAFETY_TIMESTAMP=%%c%%a%%b_%%d%%e%%f"
)
set "SAFETY_TIMESTAMP=!SAFETY_TIMESTAMP: =0!"
set "SAFETY_BACKUP=src_rollback_safety_!SAFETY_TIMESTAMP!"

if exist "src" (
    echo   Backing up current src\ to: !SAFETY_BACKUP!
    xcopy "src" "!SAFETY_BACKUP!\" /E /I /Q /H /Y >nul 2>&1
    if errorlevel 1 (
        echo   X Warning: Safety backup may have failed
    ) else (
        echo   - Safety backup created
    )
) else (
    echo   Note: No existing src\ directory to backup
)
echo.

REM Perform rollback
echo ROLLBACK: Restoring from backup...
echo   Removing current src\ directory...
if exist "src" (
    rd /s /q "src" 2>nul
)

echo   Copying backup to src\...
xcopy "!BACKUP_DIR!" "src\" /E /I /Q /H /Y >nul
if errorlevel 1 (
    echo X CRITICAL ERROR: Failed to copy backup!
    if exist "!SAFETY_BACKUP!" (
        echo   Attempting to restore from safety backup...
        xcopy "!SAFETY_BACKUP!" "src\" /E /I /Q /H /Y >nul
        echo   Safety backup restored. Please investigate the issue.
    )
    exit /b 1
)

REM Verify restoration
echo.
echo VERIFICATION: Checking restoration...

if not exist "src" (
    echo X CRITICAL ERROR: src\ directory was not created!
    if exist "!SAFETY_BACKUP!" (
        echo   Attempting to restore from safety backup...
        xcopy "!SAFETY_BACKUP!" "src\" /E /I /Q /H /Y >nul
        echo   Safety backup restored. Please investigate the issue.
    )
    exit /b 1
)

REM Count files restored
set FILE_COUNT=0
for /r "src" %%f in (*) do set /a FILE_COUNT+=1
echo   Files restored: !FILE_COUNT!

if !FILE_COUNT!==0 (
    echo X WARNING: No files found in restored src\ directory!
    exit /b 1
)

REM Check for key files
echo.
echo Key components check:
if exist "src\main.py" (
    echo   - src\main.py [OK]
) else (
    echo   X src\main.py [MISSING]
)

if exist "src\score_variant.py" (
    echo   - src\score_variant.py [OK]
) else (
    echo   X src\score_variant.py [MISSING]
)

if exist "src\__pycache__" (
    echo   - src\__pycache__\ [OK]
) else (
    echo   Note: src\__pycache__\ [not present]
)

echo.
echo ================================================
echo - ROLLBACK SUCCESSFUL
echo ================================================
echo.
echo Summary:
echo   - Restored from: !BACKUP_DIR!
echo   - Backup timestamp: !BACKUP_TIMESTAMP!
echo   - Files restored: !FILE_COUNT!
echo   - Safety backup: !SAFETY_BACKUP!
echo.
echo You can now test the restored code:
echo   python src\main.py
echo.
echo If issues occur, you can restore the pre-rollback state:
echo   rd /s /q src ^&^& xcopy !SAFETY_BACKUP! src\ /E /I /Q /H /Y
echo.

endlocal
