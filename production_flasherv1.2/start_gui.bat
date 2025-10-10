@echo off
REM Change directory to the script's location to ensure all paths are correct
cd /d "%~dp0"

REM Auto-Updater Launcher for DinoCore Production Flasher
REM This script automatically checks for updates and applies them before launching
python auto_updater_launcher.py
