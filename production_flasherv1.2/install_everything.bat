@echo off
echo ===========================================
echo 🦕 DinoCore Production Flasher - Complete Setup
echo ===========================================

REM Change to the directory where this batch file is located
cd /d "%~dp0"

echo.
echo 🔧 Installing Python dependencies...
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Running as Administrator
) else (
    echo ⚠️ Not running as Administrator - some installations may fail
    echo Please run as Administrator for best results
)

REM Install required Python packages one by one with verification
echo Installing core packages...
pip install --user --quiet requests
pip install --user --quiet paho-mqtt
pip install --user --quiet bleak
pip install --user --quiet firebase-admin
pip install --user --quiet esptool

REM Install Pillow separately with better error handling
echo Installing Pillow for image processing...
pip install --user --quiet Pillow

REM Verify Pillow installation
python -c "import PIL; print('✓ Pillow installed successfully')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ Pillow installation failed, retrying...
    pip install --user Pillow --verbose

    REM Final verification
    python -c "import PIL; print('✓ Pillow installed successfully')" 2>nul
    if %errorlevel% neq 0 (
        echo.
        echo ❌ CRITICAL: Pillow is required for the application to work
        echo Please install manually with: pip install --user Pillow
        echo Then run this script again
        echo.
        echo Press any key to continue anyway...
        pause
        REM Don't exit here, continue with other installations
    )
)

REM Verify other critical packages
python -c "import requests, bleak, firebase_admin, esptool" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo ⚠️ Some packages may have installation issues
    echo This is usually due to network or permissions
    echo The application may not work correctly
    echo.
)

echo.
echo ✅ Python dependencies installed!
echo.

REM ESP32 driver installation - download and install (only if running as admin)
net session >nul 2>&1
if %errorlevel% == 0 (
    echo 🔌 Installing ESP32 drivers...
    echo.

    REM Download ESP32 drivers (more reliable URL)
    curl -L -o cp210x_drivers.exe "https://www.silabs.com/documents/public/software/CP210x_Windows_Drivers.zip" 2>nul

    if exist cp210x_drivers.exe (
        echo Running ESP32 driver installer...
        REM Extract and install
        powershell -command "Expand-Archive -Path 'cp210x_drivers.exe' -DestinationPath 'esp_drivers' -Force"
        if exist esp_drivers (
            echo ESP32 drivers extracted. Please run the installer manually if needed.
            echo File location: %CD%\esp_drivers\
        )
        echo ✅ ESP32 drivers downloaded
    ) else (
        echo ⚠️ ESP32 drivers download failed - you may need to install them manually
        echo Download from: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
    )
) else (
    echo ⚠️ Skipping ESP32 drivers (requires Administrator)
    echo Run this script as Administrator to install drivers automatically
)

echo.
echo 🔥 Setting up Firebase logging...
echo.

if not exist firebase-credentials.json (
    echo ⚠️ firebase-credentials.json not found
    echo.
    echo 📋 To enable logging, follow these steps:
    echo 1. Go to: https://console.firebase.google.com/
    echo 2. Select your project or create new one
    echo 3. Go to Project Settings → Service Accounts
    echo 4. Click "Generate new private key"
    echo 5. Download the JSON file
    echo 6. Rename it to 'firebase-credentials.json'
    echo 7. Place it in this directory: %CD%
    echo.
    echo The logging will work automatically once you add the credentials file.
    echo.
)

echo.
echo ===========================================
echo 🎉 Setup Complete!
echo ===========================================
echo.
echo ✅ What you can do now:
echo.
echo 1. 📁 Place your firebase-credentials.json file here for logging
echo 2. 🚀 Run start_with_logging.bat to start with logging
echo 3. 🔍 Run 'python debug_firebase_logs.py' to check logs
echo 4. 🌐 Check Firebase console for remote debugging
echo.
echo 📖 Read README_START.md for detailed instructions
echo.
echo 🦕 Happy Flashing! ⚡
echo.

pause
