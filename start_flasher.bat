@echo off
REM Start Flasher with Logging - Production Script
REM This script provides guaranteed logging for all versions

REM Change directory to the script's location to ensure all paths are correct
cd /d "%~dp0"

echo ========================================
echo 🦕 DinoCore Production Flasher v1.2.24
echo 🛡️  Startup with Guaranteed Logging
echo ========================================
echo.

REM Always use the logging wrapper for guaranteed Firebase logging
if exist "production_flasherv1.2\flasher_logger.py" (
    echo ✅ Logging wrapper found - Starting with guaranteed logging...
    python "production_flasherv1.2\flasher_logger.py"
) else (
    echo ⚠️  Logging wrapper not found - Starting standard GUI...
    python "production_flasherv1.2\gui_flasher.py"
)

echo.
echo Startup completed.
pause
