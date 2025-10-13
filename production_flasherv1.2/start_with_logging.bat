@echo off
echo Starting DinoCore Production Flasher with logging...

REM Change to the directory where this batch file is located
cd /d "%~dp0"

REM Launch the logging wrapper directly
python flasher_logger.py

pause
