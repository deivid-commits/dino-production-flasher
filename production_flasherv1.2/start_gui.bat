@echo off
REM Production Startup Script with Guaranteed Firebase Logging
cd /d "%~dp0"

echo Starting DinoCore Production Flasher v1.2.25...
echo.

REM Always start with guaranteed logging first
echo Initializing logging system...
python flasher_logger.py

REM If logging fails, fallback to GUI with error message
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Logging system failed to initialize.
    echo Starting GUI without logging...
    echo.
    python gui_flasher.py
) else (
    echo Logging system initialized successfully.
    echo GUI will be launched by logging system automatically.
)
