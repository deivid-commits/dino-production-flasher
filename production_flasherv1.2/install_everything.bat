@echo off
echo ===========================================
echo DinoCore Production Flasher - Complete Setup
echo ===========================================

REM Change to the directory where this batch file is located
cd /d "%~dp0"

echo.
echo Installing Python dependencies...
echo.

REM Install required Python packages
pip install requests paho-mqtt bleak firebase-admin esptool

if %errorlevel% neq 0 (
    echo.
    echo ❌ Error installing Python dependencies
    echo Please run this as Administrator or install manually:
    echo pip install requests paho-mqtt bleak firebase-admin esptool
    pause
    exit /b 1
)

echo.
echo ✅ Python dependencies installed successfully!
echo.
echo Installing ESP32 drivers...
echo.

REM ESP32 driver installation - download and install
curl -L -o esp32_drivers.exe "https://www.silabs.com/documents/public/software/CP210x_Windows_Drivers.zip" 2>nul

if exist esp32_drivers.exe (
    echo Running ESP32 driver installer...
    esp32_drivers.exe /S /v/qn
    del esp32_drivers.exe
    echo ✅ ESP32 drivers installed
) else (
    echo ⚠️ ESP32 drivers download failed - you may need to install them manually
)

echo.
echo Setting up Firebase credentials...
echo.

if not exist firebase-credentials.json (
    echo ⚠️ firebase-credentials.json not found
    echo Please place your Firebase service account credentials in firebase-credentials.json
    echo You can download them from:
    echo https://console.firebase.google.com/project/[your-project]/settings/serviceaccounts/adminsdk
)

echo.
echo ===========================================
echo Setup Complete!
echo ===========================================
echo.
echo Next steps:
echo 1. Place your firebase-credentials.json file in this directory
echo 2. Run start_with_logging.bat to start the application
echo 3. Check Firebase logs at: https://console.firebase.google.com/
echo.
echo Have fun flashing! 🦕⚡
echo.

pause
