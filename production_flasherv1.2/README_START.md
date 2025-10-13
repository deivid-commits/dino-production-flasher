# 🦕 DinoCore Production Flasher - Quick Start

## 🚀 Getting Started

### 1. First Time Setup
Double-click `install_everything.bat` to:
- Install all Python dependencies
- Install ESP32 drivers
- Set up Firebase logging

### 2. Starting the Application
**For logging-enabled operation (RECOMMENDED):**
- Double-click `start_with_logging.bat`

**For standard operation:**
- Double-click `start_gui.bat`

## 🔍 How Logging Works

### Automatic Logging
When you run `start_with_logging.bat`, the application:
1. Initializes Firebase logging
2. Captures all console output
3. Saves session logs to Firebase automatically
4. Stores operation results (flash results, QC tests, errors)

### Manual Logging Check
Run `python debug_firebase_logs.py` to view recent logs from Firebase.

## 📊 What Gets Logged

### Session Logs
- Application startup and initialization
- System information (OS, Python version, etc.)
- User actions and operations
- Success/failure messages
- Error messages and stack traces

### Structured Logs
- Flash operation results
- Bluetooth QC test results
- Device information
- Firmware versions

## 🛠️ Troubleshooting

### If Logging Doesn't Work
1. Check `firebase-credentials.json` exists in the directory
2. Verify Firebase credentials are correct
3. Check internet connection
4. Run `python debug_firebase_logs.py` to test connection

### If Application Won't Start
1. Make sure Python is installed
2. Run `install_everything.bat` as Administrator
3. Check that all dependencies are installed

### For Remote Teams
- All team members should use `start_with_logging.bat`
- Logs are automatically uploaded to Firebase
- Check Firebase console for remote debugging

## 📝 File Descriptions

- `start_with_logging.bat` - Recommended startup with logging
- `start_gui.bat` - Standard startup (updates but limited logging)
- `install_everything.bat` - Complete setup script
- `start_gui.sh` / `install_dependencies.sh` - Linux versions
- `flasher_logger.py` - Logging wrapper
- `debug_firebase_logs.py` - Firebase log viewer

## 🎯 Best Practices

1. **Always use `start_with_logging.bat`** for consistent logging
2. **Keep `firebase-credentials.json`** secure and don't share it
3. **Check Firebase regularly** for remote debugging
4. **Run `install_everything.bat`** after any updates

---
🦕 **Happy Flashing!** ⚡
