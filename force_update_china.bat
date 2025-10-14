@echo off
echo ===========================================
echo 🦕 FORCE UPDATE - DinoCore Production Flasher
echo ===========================================
echo.
echo 🔥 This script will completely fix your installation
echo.

REM Change to the directory where this batch file is located
cd /d "%~dp0"

echo 🔧 Step 1: Installing required dependencies...
echo.

REM Install all required packages
pip install --user requests paho-mqtt bleak firebase-admin esptool

if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    echo Please run: pip install --user requests paho-mqtt bleak firebase-admin esptool
    pause
    exit /b 1
)

echo ✅ Dependencies installed!
echo.

echo 🔄 Step 2: Downloading latest version from GitHub...
echo.

REM Try to download the latest release ZIP
curl -L -o dino_flasher_latest.zip "https://github.com/deivid-commits/dino-production-flasher/releases/latest/download/dino-production-flasher.zip" 2>nul

if not exist dino_flasher_latest.zip (
    echo ❌ Download failed - trying alternative URL...
    REM Try with version-specific URL
    curl -L -o dino_flasher_latest.zip "https://github.com/deivid-commits/dino-production-flasher/releases/download/v1.2.37/dino-production-flasher-v1.2.37.zip" 2>nul

    if not exist dino_flasher_latest.zip (
        echo ❌ Both download attempts failed
        echo Please download manually from:
        echo https://github.com/deivid-commits/dino-production-flasher/releases
        pause
        exit /b 1
    )
)

echo ✅ Download successful!
echo.

echo 📂 Step 3: Extracting update...
echo.

REM Extract the ZIP file
powershell -command "Expand-Archive -Path 'dino_flasher_latest.zip' -DestinationPath 'temp_update' -Force"

if not exist temp_update (
    echo ❌ Extraction failed
    pause
    exit /b 1
)

if exist temp_update\dino-production-flasher-v* (
    REM Find the extracted directory (might have version suffix)
    for /d %%i in (temp_update\dino-production-flasher-v*) do set "UPDATE_DIR=%%~ni"
)

set "SOURCE_DIR=temp_update\%UPDATE_DIR%\production_flasherv1.2"

if not exist "%SOURCE_DIR%" (
    echo ❌ Source directory not found in update
    pause
    exit /b 1
)

echo ✅ Extracted successfully!
echo.

echo 🔄 Step 4: Updating all files...
echo.

REM Copy all files from the update directory
xcopy "%SOURCE_DIR%\*.*" . /Y /S /I

echo ✅ Files updated!
echo.

echo 🧹 Step 5: Cleaning up...
echo.

REM Clean up temporary files
rmdir /s /q temp_update 2>nul
del dino_flasher_latest.zip 2>nul

echo ✅ Cleanup completed!
echo.

echo ===========================================
echo 🎉 UPDATE COMPLETE!
echo ===========================================
echo.
echo ✅ Your installation is now fully updated!
echo.
echo 🚀 You can now:
echo - Run start_with_logging.bat for guaranteed logging
echo - Run install_everything.bat for future updates
echo - All dependencies are installed
echo.
echo Read README_START.md for complete instructions
echo.
echo 🦕 Happy Flashing!
echo.

pause
