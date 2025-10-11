@echo off
REM DinoCore Production Flasher - Dependencies Installation Script
REM This script installs all required Python packages and verifies installations
REM Run this before using the application for the first time

echo ========================================
echo DinoCore Production Flasher
echo Dependencies Installation Script
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is installed
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python is not installed!
    echo.
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo Make sure to add Python to PATH during installation!
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo ✅ %%i found
)

REM Check Python version (must be 3.8 or higher)
echo.
echo [2/6] Verifying Python version...
python -c "import sys; v=sys.version_info; exit(1 if (v.major<3 or (v.major==3 and v.minor<8)) else 0)" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python version too old (minimum Python 3.8 required)
    echo.
    echo Please upgrade Python to version 3.8 or higher!
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
    echo ✅ Python version %PYTHON_VER% is compatible
)

echo.
echo [3/6] Upgrading pip to latest version...
python -m pip install --upgrade pip --quiet
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️ Failed to upgrade pip, but continuing...
) else (
    echo ✅ Pip upgraded successfully
)

echo.
echo [4/6] Installing Python dependencies...
echo This may take several minutes depending on your internet connection...
echo.

REM Install core dependencies first
echo Installing core dependencies (esptool, pyserial, requests)...
python -m pip install --upgrade "esptool>=4.0.0" "pyserial>=3.5" "requests>=2.25.0" --quiet
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to install core dependencies!
    echo.
    pause
    exit /b 1
) else (
    echo ✅ Core dependencies installed successfully
)

REM Install optional dependencies
echo.
echo Installing optional dependencies (Bluetooth and Firebase)...
python -m pip install --upgrade "bleak>=0.19.0" "firebase-admin>=6.0.0" --quiet
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️ Optional dependencies installation failed
    echo The application will work without Bluetooth QC and Firebase logging.
) else (
    echo ✅ Optional dependencies installed successfully
)

REM Alternative: Install from requirements.txt if available
if exist requirements.txt (
    echo.
    echo Installing from requirements.txt...
    python -m pip install --upgrade -r requirements.txt --quiet
    if %ERRORLEVEL% NEQ 0 (
        echo ⚠️ requirements.txt installation had issues, but continuing...
    ) else (
        echo ✅ requirements.txt dependencies installed
    )
)

echo.
echo [5/6] Verifying installations...
python -c "import sys; import esptool, serial, requests; print('✅ Core modules imported successfully')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Core dependency verification failed!
    pause
    exit /b 1
)

REM Test optional dependencies
python -c "import bleak, firebase_admin; print('✅ Optional modules imported successfully')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️ Optional dependency verification failed - Bluetooth/Firestore features will not be available.
) else (
    echo ✅ All dependencies (including optional) verified
)

echo.
echo [6/6] Setup complete!

echo.
echo ========================================
echo ✅ DEPENDENCIES INSTALLATION COMPLETE!
echo ========================================
echo.
echo 🎉 All required dependencies have been installed successfully!
echo.
echo Next steps:
echo 1. Make sure you have a firebase-credentials.json file in this folder
echo 2. Double-click start_gui.bat to launch the application
echo.
pause
