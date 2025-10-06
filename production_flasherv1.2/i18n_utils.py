#!/usr/bin/env python3
"""
DinoCore Production Flasher Internationalization System
Support for English and Chinese languages
"""

import os
import locale
import gettext
from pathlib import Path

class TranslationManager:
    """Manages application translations"""

    def __init__(self, domain='dino_flasher', locale_dir=None):
        self.domain = domain
        self.supported_languages = ['en', 'zh_CN', 'zh_TW']
        self.current_language = 'en'

        # Built-in translations (fallback when .mo files not available)
        self.translations = self.load_builtin_translations()

        # Try to detect system language
        self.detect_system_language()

        # Install translation function
        self.update_translation_function()

    def detect_system_language(self):
        """Detect system language preference"""
        try:
            # Get system locale
            system_locale, encoding = locale.getdefaultlocale()

            if system_locale:
                lang_code = system_locale.split('_')[0]
                if lang_code in ['zh']:
                    # Check if it's Traditional or Simplified
                    if 'TW' in system_locale or 'HK' in system_locale:
                        self.current_language = 'zh_TW'
                    else:
                        self.current_language = 'zh_CN'
                elif lang_code == 'en':
                    self.current_language = 'en'
                else:
                    self.current_language = 'en'  # Default to English
            else:
                self.current_language = 'en'
        except:
            self.current_language = 'en'

    def update_translation_function(self):
        """Update the global _ function"""
        def translation_func(message):
            if self.current_language == 'en':
                return message
            return self.translations.get(self.current_language, {}).get(message, message)

        self._ = translation_func

    def load_builtin_translations(self):
        """Load built-in translations"""
        return {
            'zh_CN': {  # Chinese Simplified
                # Window titles and headers
                "🦕 DinoCore Production Flasher v1.2.0": "🦕 DinoCore 生产闪存器 v1.2.0",
                " ⚙️ Configuration ": " ⚙️ 配置 ",
                " 🎮 Control Panel ": " 🎮 控制面板 ",
                " 📋 Activity Log ": " 📋 活动日志 ",

                # Labels and buttons
                "🎯 Target HW Version:": "🎯 目标硬件版本:",
                "💾 Save Version": "💾 保存版本",
                "▶️  SELECT A MODE": "▶️  选择模式",
                "🏭 PRODUCTION MODE": "🏭 生产模式",
                "🧪 TESTING MODE": "🧪 测试模式",
                "⏹️  STOP & CHANGE MODE": "⏹️  停止并更改模式",

                # Status messages
                "ACTIVE MODE: PRODUCTION": "激活模式：生产",
                "ACTIVE MODE: TESTING": "激活模式：测试",
                "--- SCANNING STOPPED ---": "--- 扫描停止 ---",
                "Please select a new mode.": "请选择新模式。",

                # Connection status
                "🔗 SERVER ONLINE": "🔗 服务器在线",
                "⚠️ SERVER ISSUES": "⚠️ 服务器问题",
                "❌ OFFLINE": "❌ 离线",

                # Common UI elements
                "Success": "成功",
                "Error": "错误",
                "Warning": "警告",
                "Notice": "注意",

                # Update messages
                "✅ You're up to date! (version {version})": "✅ 您已是最新版本！（版本 {version}）",
                "\n📦 Update available: {version}": "\n📦 可用更新：{version}",
                "\n🔄 Starting update to version {version}...": "\n🔄 开始更新到版本 {version}...",
                "\n✅ Successfully updated to version {version}!": "\n✅ 成功更新到版本 {version}！",

                # Validation messages
                "Hardware version saved: {version}": "硬件版本已保存：{version}",
                "Invalid version format. Please use format X.Y.Z (e.g., 1.9.1)": "无效的版本格式。请使用格式 X.Y.Z（例如：1.9.1）",

                # Warnings
                "Production mode will NOT burn eFuses and requires devices to be tested first. Continue?": "生产模式不会烧录 eFuses，需要先测试设备。继续？",
                "Testing mode will attempt to burn HW version {version} to eFuses. This is irreversible. Continue?": "测试模式将尝试将硬件版本 {version} 烧录到 eFuses。这是不可逆转的。继续？",

                # Operation messages (simplified for UI)
                "Using Target HW Version:": "使用目标硬件版本：",
                "Waiting for new devices...": "等待新设备...",
                "[OK] Flash successful!\n": "[成功] 烧录成功！\n",
                "[X] Flash failed with exit code {code}.\n": "[失败] 烧录失败，退出代码 {code}。\n",
            },
            'zh_TW': {  # Chinese Traditional
                # Window titles and headers
                "🦕 DinoCore Production Flasher v1.2.0": "🦕 DinoCore 生產燒錄器 v1.2.0",
                " ⚙️ Configuration ": " ⚙️ 設定 ",
                " 🎮 Control Panel ": " 🎮 控制面板 ",
                " 📋 Activity Log ": " 📋 活動日誌 ",

                # Labels and buttons
                "🎯 Target HW Version:": "🎯 目標硬體版本:",
                "💾 Save Version": "💾 儲存版本",
                "▶️  SELECT A MODE": "▶️  選擇模式",
                "🏭 PRODUCTION MODE": "🏭 生產模式",
                "🧪 TESTING MODE": "🧪 測試模式",
                "⏹️  STOP & CHANGE MODE": "⏹️  停止並更改模式",

                # Status messages
                "ACTIVE MODE: PRODUCTION": "啟動模式：生產",
                "ACTIVE MODE: TESTING": "啟動模式：測試",
                "--- SCANNING STOPPED ---": "--- 掃描停止 ---",
                "Please select a new mode.": "請選擇新模式。",

                # Connection status
                "🔗 SERVER ONLINE": "🔗 伺服器線上",
                "⚠️ SERVER ISSUES": "⚠️ 伺服器問題",
                "❌ OFFLINE": "❌ 離線",

                # Common UI elements
                "Success": "成功",
                "Error": "錯誤",
                "Warning": "警告",
                "Notice": "注意",

                # Update messages
                "✅ You're up to date! (version {version})": "✅ 您已是最新版本！（版本 {version}）",
                "\n📦 Update available: {version}": "\n📦 可用更新：{version}",
                "\n🔄 Starting update to version {version}...": "\n🔄 開始更新到版本 {version}...",
                "\n✅ Successfully updated to version {version}!": "\n✅ 成功更新到版本 {version}！",

                # Validation messages
                "Hardware version saved: {version}": "硬體版本已儲存：{version}",
                "Invalid version format. Please use format X.Y.Z (e.g., 1.9.1)": "無效的版本格式。請使用格式 X.Y.Z（例如：1.9.1）",

                # Warnings
                "Production mode will NOT burn eFuses and requires devices to be tested first. Continue?": "生產模式不會燒錄 eFuses，需要先測試設備。繼續？",
                "Testing mode will attempt to burn HW version {version} to eFuses. This is irreversible. Continue?": "測試模式將嘗試將硬體版本 {version} 燒錄到 eFuses。這是不可逆轉的。繼續？",

                # Operation messages (simplified for UI)
                "Using Target HW Version:": "使用目標硬體版本：",
                "Waiting for new devices...": "等待新設備...",
                "[OK] Flash successful!\n": "[成功] 燒錄成功！\n",
                "[X] Flash failed with exit code {code}.\n": "[失敗] 燒錄失敗，退出程式碼 {code}。\n",
            }
        }

    def set_language(self, language):
        """Change application language"""
        if language in self.supported_languages:
            self.current_language = language
            self.update_translation_function()
            return True
        return False

    def get_current_language(self):
        """Get current language code"""
        return self.current_language

    def get_available_languages(self):
        """Get list of available languages with names"""
        return {
            'en': 'English',
            'zh_CN': '简体中文',
            'zh_TW': '繁體中文'
        }

    def get_language_display_name(self, lang_code):
        """Get display name for language code"""
        names = self.get_available_languages()
        return names.get(lang_code, lang_code)

# Global translation manager instance
translation_manager = TranslationManager()

# Global translation function
def _(message):
    """Global translation function"""
    return translation_manager._(message)

def N_(message):
    """Translation function for non-contextual strings"""
    return message

# Translations for static strings (to be extracted)
# Window titles and headers
WINDOW_TITLE = N_("🦕 DinoCore Production Flasher v1.2.0")
CONFIG_SECTION_TITLE = N_(" ⚙️ Configuration ")
CONTROL_PANEL_TITLE = N_(" 🎮 Control Panel ")
ACTIVITY_LOG_TITLE = N_(" 📋 Activity Log ")

# Labels and buttons
TARGET_HW_VERSION_LABEL = N_("🎯 Target HW Version:")
SAVE_VERSION_BUTTON = N_("💾 Save Version")
SELECT_MODE_LABEL = N_("▶️  SELECT A MODE")
PRODUCTION_MODE_BUTTON = N_("🏭 PRODUCTION MODE")
TESTING_MODE_BUTTON = N_("🧪 TESTING MODE")
STOP_BUTTON = N_("⏹️  STOP & CHANGE MODE")

# Status messages
ACTIVATING_PRODUCTION = N_("ACTIVE MODE: PRODUCTION")
ACTIVATING_TESTING = N_("ACTIVE MODE: TESTING")
SCANNING_STOPPED = N_("--- SCANNING STOPPED ---")
SELECT_NEW_MODE = N_("Please select a new mode.")

# Connection status
CONNECTION_ONLINE = N_("🔗 SERVER ONLINE")
CONNECTION_ISSUES = N_("⚠️ SERVER ISSUES")
CONNECTION_OFFLINE = N_("❌ OFFLINE")

# Log messages
USING_HW_VERSION = N_("Using Target HW Version:")
IGNORING_PORTS = N_("Ignoring existing ports:")
WAITING_DEVICES = N_("Waiting for new devices...")
PORTS_DISCONNECTED = N_("Ports disconnected:")

# Firmware operations
DOWNLOADING_FIRMWARE = N_("Downloading {mode} firmware for HW {hardware_version}...")
NO_COMPATIBLE_FIRMWARE = N_("[X] No compatible {mode} firmware found for HW {hardware_version}.")
FOUND_BUILD = N_("Found compatible build: {name}")
DOWNLOADING_FILE = N_("Downloading {filename}...")
DOWNLOAD_SUCCESS = N_("[OK] {mode} firmware for {hardware_version} downloaded successfully.")
NETWORK_ERROR = N_("[X] Network error while downloading: {error}")

# eFuse operations
BURNING_EFUSE = N_("Attempting to burn eFuse with version {version}...")
BURNING_RESET = N_("Attempting to reset device into download mode...")
BURNING_SUCCESS = N_("Device reset successful, proceeding with eFuse burning...")
BURNING_FAIL = N_("Device reset failed, but continuing with eFuse burning...")
BURNING_ERROR = N_("[X] Invalid version format: {version}")
EFUSE_BURN_SUCCESS = N_("[OK] eFuse burned successfully.")
EFUSE_VERIFY_SUCCESS = N_("[OK] Verification successful. Version {version} is burned.")
EFUSE_VERIFY_FAILED = N_("[X] VERIFICATION FAILED. Burned version ({burned}) does not match target ({target}). Stopping.")
EFUSE_BURN_FAILED = N_("Could not burn eFuse. It might be already written.")
EFUSE_BURN_ERROR = N_("eFuse burn error: {error}")

# Reading eFuse
READING_EFUSE = N_("Attempting to read eFuse from {port}...")
EFUSE_READ_FAILED = N_("[X] Failed to read eFuse. Maybe locked?")
FOUND_EFUSE_VERSION = N_("[OK] Found raw eFuse version: {version}")
EFUSE_EMPTY = N_("[!] eFuse block is empty (version 0.0.0). Treating as no version found.")
EFUSE_VERSION_NONE = N_("[!] No version found on eFuse.")

# Flashing operations
FLASHER_UPDATE_AVAILABLE = N_("\n📦 Update available: {version}")
FLASHER_UPDATE_CHANGES = N_("\n📋 Changelog:")
FLASHER_ALL_UP_TO_DATE = N_("✅ You're up to date! (version {version})")
FLASHER_UPDATE_CANCELLED = N_("❌ Update cancelled by user")
FLASHER_NO_DOWNLOAD_URL = N_("❌ No download URL found for update")
FLASHER_STARTING_UPDATE = N_("\n🔄 Starting update to version {version}...")
FLASHER_BACKUP_SUCCESS = N_("✅ Backup created in: {backup_dir}")
FLASHER_BACKUP_FAILED = N_("❌ Failed to create backup: {error}")
FLASHER_DOWNLOADING = N_("📥 Downloading update...")
FLASHER_DOWNLOAD_SUCCESS = N_("✅ Update downloaded to: {zip_path}")
FLASHER_DOWNLOAD_FAILED = N_("❌ Failed to download update: {error}")
FLASHER_EXTRACTING = N_("📂 Extracting update...")
FLASHER_INSTALLING_FILES = N_("🔄 Installing update files...")
FLASHER_FILE_UPDATED = N_("   📄 Updated: {file}")
FLASHER_UPDATE_SUCCESS = N_("\n✅ Successfully updated to version {version}!")
FLASHER_UPDATE_COMPLETE = N_("🔄 It's recommended to restart the application")
FLASHER_UPDATE_FAILED = N_("❌ Failed to extract/install update: {error}")
FLASHER_ROLLBACK = N_("🔄 Attempting rollback to previous version...")
FLASHER_ROLLBACK_FAILED = N_("❌ Rollback failed: {error}")
FLASHER_NO_BACKUP_DIR = N_("❌ No backup directory found")
FLASHER_NO_BACKUPS = N_("❌ No backups found")

# Main flashing process
START_FLASHING = N_("-- Starting {mode} flash for HW {hardware_version} on {port} --")
FLASH_FINISHED = N_("FINISHED FLASHING {port} --")
DOWNLOAD_FAILED_ABORT = N_("[X] Download for {hardware_version} failed. Aborting flash.")
FLASH_SUCCESS = N_("\n[OK] Flash successful!\n")
FLASH_FAILED = N_("\n[X] Flash failed with exit code {code}.\n")
FLASH_UNEXPECTED_ERROR = N_("\n[X] An unexpected error occurred during flash: {error}\n")
FLASH_FINAL_FINISHED = N_("FINISHED FLASHING {port} --")

# Serial monitor
SERIAL_MONITOR_START = N_("--- Serial monitor started for {port} ---")
SERIAL_MONITOR_STOP = N_("--- Serial monitor for {port} stopped. ---")
SERIAL_MONITOR_ERROR = N_("\n[X] Error opening serial monitor on {port}: {error}")
DEVICE_DISCONNECTED_CLOSE = N_("\n--- Device {port} disconnected. Closing monitor. ---")
DEVICE_DISCONNECTED_OPEN = N_("\n--- Device {port} disconnected. Closing monitor. ---")

# Device processing
PROCESSING_NEW_DEVICE = N_("--- Processing new device on {port} ---")
PRODUCTION_MODE_READING = N_("Production mode: Reading eFuse...")
PRODUCTION_FAILED = N_("[X] PRODUCTION FAILED: No eFuse version found. Please run device through Testing Mode first.")
VERSION_FROM_EXISTING = N_("Proceeding with existing version: {version}")
BURN_PENDING_VERIFICATION = N_("Burn command succeeded. Verifying by reading back eFuse...")
BURN_SUCCESS = N_("[OK] Burn command succeeded.")
BURN_FAILED_READ_EXISTING = N_("Burn command failed. Attempting to read existing version...")
BURN_FAILED_NO_VERSION = N_("[X] Could not read existing version after burn failure. Stopping.")

# Thread errors
UNEXPECTED_ERROR = N_("!!!!!!!!!! UNEXPECTED ERROR in device processing thread !!!!!!!!!!!")

# Success confirmation
SUCCESS_DIALOG_TITLE = N_("Success")
SUCCESS_DIALOG_MESSAGE = N_("Hardware version saved: {version}")

# Error dialogs
ERROR_DIALOG_TITLE = N_("Error")
INVALID_VERSION_FORMAT = N_("Invalid version format. Please use format X.Y.Z (e.g., 1.9.1)")
EFUSE_READ_ERROR = N_("[X] Error reading eFuse: {error}")

# Progress indicators
EFUSE_READING_ERROR = N_("[X] Error reading eFuse: {error}")

# Warnings
PRODUCTION_WARNING_TITLE = N_("Warning")
PRODUCTION_WARNING_MESSAGE = N_("Production mode will NOT burn eFuses and requires devices to be tested first. Continue?")
TESTING_NOTICE_TITLE = N_("Notice")
TESTING_NOTICE_MESSAGE = N_("Testing mode will attempt to burn HW version {version} to eFuses. This is irreversible. Continue?")
