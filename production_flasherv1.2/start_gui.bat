@echo off
REM Change directory to the script's location to ensure all paths are correct
cd /d "%~dp0"

REM Auto-Updater Launcher and Logging Wrapper for DinoCore Production Flasher
REM This script handles the complete startup sequence with automatic updates

REM Run the auto-updater launcher (checks and applies updates, then starts logging)
python auto_updater_launcher.py

echo.
echo If no update was needed, starting logging wrapper manually...
echo.

REM If we reach here, no update was needed or update failed - start logging manually
python flasher_logger.py

REM If logging wrapper fails or isn't available, fallback to direct GUI
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Logging wrapper not available, starting standard GUI...
    echo.
    python gui_flasher.py
)
