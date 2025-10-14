import os
import sys
import time
import subprocess
import requests
import winsound
import threading
import queue
import logging
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
from serial.tools.list_ports import comports
import re
import traceback
import serial
import configparser
import asyncio
from tkinter import simpledialog
import bleak
from PIL import Image, ImageTk, ImageDraw, ImageFont

# Import internationalization system
from i18n_utils import _, translation_manager

# Import local modules
try:
    from updater import DinoUpdater
except ImportError:
    DinoUpdater = None

try:
    from bluetooth_qc import get_bluetooth_qc_tester, BLEAK_AVAILABLE
    BT_QC_AVAILABLE = True
except ImportError:
    BT_QC_AVAILABLE = False
    get_bluetooth_qc_tester = None

# Firebase database integration (optional)
try:
    from firebase_db import get_firebase_db, store_qc_results, store_flash_log, store_session_log, init_firebase_with_credentials
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    get_firebase_db = None

# --- Configuration ---
#TARGET_HW_VERSION = "1.9.0"
DINOCORE_BASE_URL = "https://dinocore-telemetry-production.up.railway.app/"
FIRMWARE_DIR = "production_firmware"
TESTING_FIRMWARE_DIR = "testing_firmware"
FLASH_BAUD = "460800"
MONITOR_BAUD = 115200
CONFIG_FILE = "config.ini"

# --- Sound Definitions ---
START_FREQ = 800
START_DUR = 150
END_FREQ = 1200
END_DUR = 400
ERROR_FREQ = 400
ERROR_DUR = 800

# --- Helper Functions ---
def play_sound(freq, duration):
    try:
        winsound.Beep(freq, duration)
    except Exception:
        pass

class RichLogView(tk.Frame):
    """A custom text widget that displays logs with icons."""
    def __init__(self, parent, colors, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.colors = colors
        self.icons = {}
        self._create_icons()

        self.text = tk.Text(
            self,
            font=("Segoe UI", 10),
            bg=self.colors['log_bg'],
            fg=self.colors['log_text'],
            insertbackground=self.colors['highlight'],
            selectbackground=self.colors['highlight'],
            relief=tk.FLAT,
            borderwidth=0,
            padx=10,
            pady=5,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.scrollbar = tk.Scrollbar(self, command=self.text.yview)
        self.text.config(yscrollcommand=self.scrollbar.set)

        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure tags for text colors
        self.text.tag_config("success", foreground=self.colors['success_btn'])
        self.text.tag_config("error", foreground=self.colors['prod_btn'])
        self.text.tag_config("warning", foreground=self.colors['warning_btn'])
        self.text.tag_config("info", foreground=self.colors['log_text'])
        self.text.tag_config("bluetooth", foreground="#89dceb") # Cyan
        self.text.tag_config("firebase", foreground="#f9e2af") # Yellow

    def _create_icons(self):
        """Generate icons using Pillow to avoid external files."""
        icon_data = {
            'success': ('✅', '#a6e3a1'),
            'error': ('❌', '#f38ba8'),
            'warning': ('⚠️', '#f9e2af'),
            'info': ('ℹ️', '#89b4fa'),
            'bluetooth': ('🔵', '#89dceb'),
            'firebase': ('🔥', '#fab387')
        }
        try:
            font = ImageFont.truetype("seguiemj.ttf", 18)
        except IOError:
            font = ImageFont.load_default()

        for name, (emoji, color) in icon_data.items():
            image = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.text((12, 12), emoji, font=font, anchor="mm", fill=color)
            self.icons[name] = ImageTk.PhotoImage(image)

    def log(self, message, level='info'):
        """Add a log entry with an icon and styled text."""
        self.text.config(state=tk.NORMAL)
        
        # Insert icon
        icon = self.icons.get(level)
        if icon:
            self.text.image_create(tk.END, image=icon, padx=5)

        # Insert message with color tag
        self.text.insert(tk.END, f" {message.strip()}\n", (level,))
        
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)

# --- Business Logic ---
def parse_version(version_string):
    try:
        parts = version_string.split('.')
        if len(parts) != 3: return None
        return tuple(map(int, parts))
    except (ValueError, IndexError):
        return None

def download_firmware(log_queue, mode, hardware_version):
    log_queue.put(f"Downloading {mode} firmware for HW {hardware_version}...")
    api_path = 'builds' if mode == 'production' else 'testing-builds'
    fw_dir = FIRMWARE_DIR if mode == 'production' else TESTING_FIRMWARE_DIR
    url = f"{DINOCORE_BASE_URL}/api/{api_path}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        builds = response.json()
        compatible = [b for b in builds if hardware_version in b.get('supported_versions', [])]
        if not compatible:
            log_queue.put(f"[X] No compatible {mode} firmware found for HW {hardware_version}.")
            return False
        latest_build = max(compatible, key=lambda x: x['created_at'])
        build_id = latest_build['id']
        log_queue.put(f"Found compatible build: {latest_build['name']}")
        os.makedirs(fw_dir, exist_ok=True)
        file_types = ['bootloader', 'app', 'partition_table', 'ota_initial']
        filenames = ["bootloader.bin", "magical-toys.bin", "partition-table.bin", "ota_data_initial.bin"]
        for f_type, f_name in zip(file_types, filenames):
            output_path = os.path.join(fw_dir, f_name)
            dl_url = f"{DINOCORE_BASE_URL}/api/{api_path}/{build_id}/files/{f_type}/download"
            log_queue.put(f"Downloading {f_name}...")
            dl_resp = requests.get(dl_url, stream=True, timeout=30)
            dl_resp.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in dl_resp.iter_content(chunk_size=8192):
                    f.write(chunk)
        log_queue.put(f"[OK] {mode.capitalize()} firmware for {hardware_version} downloaded successfully.")
        return True
    except requests.exceptions.RequestException as e:
        log_queue.put(f"[X] Network error while downloading: {e}")
        return False

def burn_efuse(log_queue, port, version):
    log_queue.put(f"Attempting to burn eFuse with version {version}...")
    version_parts = parse_version(version)
    if not version_parts:
        log_queue.put(f"[X] Invalid version format: {version}")
        return False

    log_queue.put("Attempting to reset device into download mode...")
    try:
        reset_cmd = [sys.executable, "-m", "esptool", "--chip", "esp32s3", "-p", port, "--before=default_reset", "--after=hard_reset", "chip_id"]
        result = subprocess.run(reset_cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            log_queue.put("Device reset successful, proceeding with eFuse burning...")
        else:
            log_queue.put("Device reset failed, but continuing with eFuse burning...")
    except Exception as e:
        log_queue.put(f"Device reset error: {e}, but continuing...")

    major, minor, patch = version_parts
    temp_file = f"temp_efuse_{port}.bin"
    try:
        with open(temp_file, 'wb') as f:
            buffer = bytearray(32)
            buffer[0], buffer[1], buffer[2] = major, minor, patch
            f.write(buffer)
        efuse_cmd = [sys.executable, "-m", "espefuse", "--chip", "esp32s3", "-p", port, "--do-not-confirm", "burn_block_data", "BLOCK3", temp_file]
        result = subprocess.run(efuse_cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            log_queue.put("Could not burn eFuse. It might be already written.")
            if result.stderr:
                log_queue.put(f"eFuse burn error: {result.stderr}")
            return False
        log_queue.put("[OK] eFuse burned successfully.")
        return True
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

def read_efuse_version(log_queue, port):
    log_queue.put(f"Attempting to read eFuse from {port}...")
    try:
        summary_cmd = [sys.executable, "-m", "espefuse", "--chip", "esp32s3", "-p", port, "summary"]
        result = subprocess.run(summary_cmd, capture_output=True, text=True, check=False, timeout=15)
        if result.returncode != 0:
            log_queue.put("[X] Failed to read eFuse. Maybe locked?")
            return None
        output = result.stdout
        match = re.search(r"BLOCK_USR_DATA \(BLOCK3\).*?=\s*([0-9a-f]{2})\s*([0-9a-f]{2})\s*([0-9a-f]{2})", output, re.DOTALL | re.IGNORECASE)
        if match:
            major, minor, patch = int(match.group(1), 16), int(match.group(2), 16), int(match.group(3), 16)
            if major == 0 and minor == 0 and patch == 0:
                log_queue.put("[!] eFuse block is empty (version 0.0.0). Treating as no version found.")
                return None
            version = f"{major}.{minor}.{patch}"
            log_queue.put(f"[OK] Found raw eFuse version: {version}")
            return version
        log_queue.put("[!] No version found on eFuse.")
        return None
    except Exception as e:
        log_queue.put(f"[X] Error reading eFuse: {e}")
        return None

def flash_device(log_queue, port, mode, hardware_version):
    log_queue.put(('show_progress',))
    play_sound(START_FREQ, START_DUR)
    log_queue.put(f"-- Starting {mode} flash for HW {hardware_version} on {port} --")
    fw_dir = FIRMWARE_DIR if mode == 'production' else TESTING_FIRMWARE_DIR
    if os.path.exists(fw_dir):
        for f in os.listdir(fw_dir):
            try:
                os.remove(os.path.join(fw_dir, f))
            except OSError:
                pass
    if not download_firmware(log_queue, mode, hardware_version):
        log_queue.put(f"[X] Download for {hardware_version} failed. Aborting flash.")
        play_sound(ERROR_FREQ, ERROR_DUR)
        log_queue.put(('hide_progress',))
        return False
    bootloader, app, p_table, ota_data = [os.path.join(fw_dir, f) for f in ["bootloader.bin", "magical-toys.bin", "partition-table.bin", "ota_data_initial.bin"]]
    flash_cmd = [sys.executable, "-m", "esptool", "--chip", "esp32s3", "-p", port, "-b", FLASH_BAUD, "--before=default_reset", "--after=hard_reset", "write_flash", "--flash_mode", "dio", "--flash_freq", "80m", "--flash_size", "16MB", "0x0", bootloader, "0x260000", app, "0x10000", p_table, "0x15000", ota_data]
    try:
        process = subprocess.Popen(flash_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
        is_flashing_main_app = False
        last_progress_line = ""
        for line in iter(process.stdout.readline, ''):
            if "Writing at" in line and "%" in line:
                # Clean up progress line
                progress_match = re.search(r'(\d+\.\d+)%', line)
                if progress_match:
                    clean_line = f"\rFlashing... {progress_match.group(0)}"
                    if clean_line != last_progress_line:
                        log_queue.put(clean_line)
                        last_progress_line = clean_line
            else:
                log_queue.put(line)

            if "Writing at 0x00260000" in line:
                is_flashing_main_app = True
            if is_flashing_main_app:
                match = re.search(r"([\d\.]+)\%", line)
                if match:
                    progress = int(float(match.group(1)))
                    log_queue.put(('progress', progress))
            if is_flashing_main_app and "Wrote" in line and "at 0x00260000" in line:
                is_flashing_main_app = False
        process.stdout.close()
        return_code = process.wait()
        if return_code != 0:
            log_queue.put(f"\n[X] Flash failed with exit code {return_code}.\n")
            play_sound(ERROR_FREQ, ERROR_DUR)
            return False
        else:
            log_queue.put("\n[OK] Flash successful!\n")
            play_sound(END_FREQ, END_DUR)
            return True
    except Exception as e:
        log_queue.put(f"\n[X] An unexpected error occurred during flash: {e}\n")
        play_sound(ERROR_FREQ, ERROR_DUR)
        return False
    finally:
        log_queue.put(('hide_progress',))
        log_queue.put(f"-- Finished flashing {port} --")

def serial_monitor_thread(log_queue, port, stop_event, app_instance):
    try:
        ser = serial.Serial(port, MONITOR_BAUD, timeout=1)
        log_queue.put(f"--- Serial monitor started for {port} ---")
        mac_address = None
        device_name = None
        while not stop_event.is_set():
            try:
                if ser.in_waiting > 0:
                    line_bytes = ser.readline()
                    line = line_bytes.decode('utf-8', errors='replace')
                    log_queue.put(line)

                    # Capture MAC and Name
                    if "Bluetooth MAC:" in line:
                        mac_match = re.search(r'Bluetooth MAC: ([\w:]+)', line)
                        if mac_match:
                            mac_address = mac_match.group(1).strip().upper()
                            log_queue.put(f"📱 Captured Bluetooth MAC: {mac_address}")
                    
                    if "Setting device name to:" in line:
                        name_match = re.search(r'Setting device name to: ([\w-]+)', line)
                        if name_match:
                            device_name = name_match.group(1).strip()
                            log_queue.put(f"📱 Captured Bluetooth Name: {device_name}")

                    if "The device is now discoverable and ready for connection!" in line:
                        if mac_address and device_name:
                            app_instance.set_captured_ble_details(mac_address, device_name)
                            mac_address, device_name = None, None # Reset
                else:
                    time.sleep(0.05)
                    if not any(p.device == port for p in comports()):
                        log_queue.put(f"\n--- Device {port} disconnected. Closing monitor. ---")
                        break
            except serial.SerialException:
                log_queue.put(f"\n--- Device {port} disconnected. Closing monitor. ---")
                break
        ser.close()
        log_queue.put(f"--- Serial monitor for {port} stopped. ---")
    except Exception as e:
        log_queue.put(f"\n[X] Error opening serial monitor on {port}: {e}")

def get_esp32_port(log_queue):
    """Scans COM ports and identifies the one connected to an ESP32 using VID/PID."""
    esp32_ports = [p for p in comports() if "303A:1001" in p.hwid]

    if not esp32_ports:
        return None, "NO_ESP32_FOUND"
    
    if len(esp32_ports) > 1:
        return None, "MULTIPLE_ESP32_FOUND"

    port = esp32_ports[0].device
    return port, "ESP32_FOUND"

def process_device_thread(log_queue, port, mode, stop_event, target_hw_version, app_instance):
    start_time = time.time()
    device_info = {'port': port, 'serial_number': 'unknown'}
    flash_result = {
        'success': False,
        'mode': mode,
        'hardware_version': target_hw_version,
        'error': ''
    }

    try:
        log_queue.put(f"--- Processing new device on {port} ---")
        flash_hw_version = None
        if mode == 'testing':
            log_queue.put(_("Attempting to burn eFuse with version {version}...").format(version=target_hw_version))
            burn_successful = burn_efuse(log_queue, port, target_hw_version)
            if burn_successful:
                log_queue.put(_("Burn command succeeded. Verifying by reading back eFuse..."))
                time.sleep(2)  # Increased delay for device stabilization
                read_version = read_efuse_version(log_queue, port)
                if read_version == target_hw_version:
                    log_queue.put(_("[OK] Verification successful. Version {version} is burned.").format(version=read_version))
                    flash_hw_version = target_hw_version
                    log_queue.put(_("eFuse burning completed successfully. Starting firmware flash..."))
                else:
                    log_queue.put(_("[X] VERIFICATION FAILED. Burned version ({burned}) does not match target ({target}). Stopping.").format(burned=read_version, target=target_hw_version))
                    play_sound(ERROR_FREQ, ERROR_DUR)
                    return
            else:
                log_queue.put(_("Burn command failed. Attempting to read existing version..."))
                existing_version = read_efuse_version(log_queue, port)
                if existing_version:
                    log_queue.put(_("Proceeding with existing version: {version}").format(version=existing_version))
                    flash_hw_version = existing_version
                else:
                    log_queue.put(_("[X] Could not read existing version after burn failure. Stopping."))
                    play_sound(ERROR_FREQ, ERROR_DUR)
                    return
        elif mode == 'production':
            log_queue.put(_("Production mode: Reading eFuse..."))
            existing_version = read_efuse_version(log_queue, port)
            if existing_version:
                flash_hw_version = existing_version
                log_queue.put(_("Found eFuse version: {version}. Starting firmware flash...").format(version=existing_version))
            else:
                log_queue.put(_("[X] PRODUCTION FAILED: No eFuse version found. Please run device through Testing Mode first."))
                play_sound(ERROR_FREQ, ERROR_DUR)
                return

        # If we have a firmware version to flash, proceed with flashing
        if flash_hw_version:
            log_queue.put(_("-- Starting {mode} flash for HW {hardware_version} on {port} --").format(
                mode=mode.capitalize(), hardware_version=flash_hw_version, port=port))
            flash_ok = flash_device(log_queue, port, mode, flash_hw_version)
            if flash_ok:
                log_queue.put(_("Flash completed successfully. Starting serial monitor..."))
                flash_result['success'] = True
                serial_monitor_thread(log_queue, port, stop_event, app_instance)
            else:
                log_queue.put(_("[X] Flash failed. Unable to complete device programming."))
                flash_result['error'] = "Flash process failed"
                play_sound(ERROR_FREQ, ERROR_DUR)
        else:
            log_queue.put(_("[X] No valid hardware version found. Cannot proceed with flash."))
            flash_result['error'] = "No valid hardware version found"
            play_sound(ERROR_FREQ, ERROR_DUR)

    except Exception as e:
        flash_result['error'] = str(e)
        log_queue.put("!!!!!!!!!! UNEXPECTED ERROR in device processing thread !!!!!!!!!!!")
        log_queue.put(f"ERROR: {e}")
        log_queue.put(traceback.format_exc() + "\n")
        play_sound(ERROR_FREQ, ERROR_DUR)
    finally:
        flash_result['duration'] = time.time() - start_time
        if FIREBASE_AVAILABLE:
            store_flash_log(device_info, flash_result)
            # Also store the full session log
            if app_instance.session_logs:
                store_session_log(app_instance.session_logs)

class FlasherApp:
    def __init__(self, root):
        self.root = root
        self.root.title(_("🦕 DinoCore Production Flasher v1.2.0"))
        self.root.geometry("800x700")
        self.root.resizable(True, True)

        # --- Set App Icon ---
        try:
            # Create a simple image with the emoji for the icon
            # This is a cross-platform way to set an icon without needing an .ico file
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a blank image with transparency
            icon_image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(icon_image)
            
            # Try to load a suitable font
            try:
                font = ImageFont.truetype("seguiemj.ttf", 48)
            except IOError:
                font = ImageFont.load_default()

            # Draw the emoji centered on the image
            draw.text((32, 32), "🦕", font=font, anchor="mm", fill="#89dceb")
            
            self.app_icon = ImageTk.PhotoImage(icon_image)
            self.root.iconphoto(True, self.app_icon)
        except Exception as e:
            print(f"Could not set app icon: {e}") # Non-critical error

        # Ultra-Modern Dark Theme
        self.colors = {
            'bg': '#1e1e2e',           # Deep dark blue-grey
            'log_bg': '#2a2a3a',       # Slightly lighter dark
            'text': '#cdd6f4',         # Light blue-grey text
            'log_text': '#89b4fa',     # Light blue
            'header_bg': '#181825',    # Very dark header
            'prod_btn': '#f38ba8',     # Soft red
            'test_btn': '#89dceb',     # Soft blue
            'stop_btn': '#a6e3a1',     # Soft green
            'success_btn': '#a6e3a1',  # Emerald
            'warning_btn': '#f9e2af',  # Yellow
            'status_prod': '#f38ba8',  # Red for active
            'status_test': '#89dceb',  # Blue for active
            'status_idle': '#6c7086',  # Grey for idle
            'status_success': '#a6e3a1', # Green for success
            'status_warning': '#fab387',  # Orange warning
            'frame_bg': '#313244',     # Medium grey-blue
            'entry_bg': '#1e1e2e',     # Same as bg
            'entry_fg': '#cdd6f4',     # Light text
            'border': '#f38ba8',       # Red accent
            'highlight': '#89b4fa'     # Blue accent
        }

        self.root.configure(bg=self.colors['bg'])
        self.root.attributes('-topmost', True)  # Always on top for better UX
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
        
        # --- File Logger Setup ---
        self.log_file = "session.log"
        # Clear log file on start, ensuring it's UTF-8
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write(f"--- Session Log Started: {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n\n")
        
        self.hw_version_var = tk.StringVar()
        self.captured_ble_name = None
        self.captured_mac = None
        self.session_logs = []
        self.ble_ready_event = threading.Event()
        
        self.log_queue = queue.Queue()
        self.scanner_stop_event = threading.Event()
        self.create_widgets()
        self.update_log()
        
        # Initialize Firebase
        if FIREBASE_AVAILABLE:
            init_thread = threading.Thread(target=self.initialize_firebase, daemon=True)
            init_thread.start()

        self.root.after(200, self.ask_hardware_version)

    def set_captured_ble_details(self, mac, name):
        self.captured_mac = mac
        self.captured_ble_name = name
        self.ble_ready_event.set() # Signal that BLE is ready
        self.bt_qc_button.config(state='normal')
        self.status_label.config(text="🔵 " + _("Ready for Bluetooth QC"), bg=self.colors['highlight'])

    def ask_hardware_version(self):
        dialog = VersionDialog(self.root, self.colors)
        self.root.wait_window(dialog.top)
        version = dialog.version

        if version and parse_version(version):
            self.hw_version_var.set(version)
            self.log_queue.put(f"🎯 Using hardware version for this session: {version}")
            self.scanner_stop_event.clear()
            detector_thread = threading.Thread(target=self.device_detector_worker, daemon=True)
            detector_thread.start()
        elif version is None: # User cancelled
            self.root.destroy()
        else: # Invalid format
            messagebox.showerror(_("Invalid Version"), _("Invalid version format. The application will now close."))
            self.root.destroy()

    def initialize_firebase(self):
        self.log_queue.put(("Firebase", "Attempting to initialize Firebase..."))
        if init_firebase_with_credentials():
            self.log_queue.put(("Firebase", "✅ Firebase connection successful."))
        else:
            self.log_queue.put(("Firebase", "⚠️ Firebase connection failed. Logs will not be saved."))

    def create_widgets(self):
        # Modern header with gradient and branding
        header_frame = tk.Frame(self.root, bg=self.colors['header_bg'], height=60)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)

        # Header content
        header_content = tk.Frame(header_frame, bg=self.colors['header_bg'])
        header_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Logo and title
        title_frame = tk.Frame(header_content, bg=self.colors['header_bg'])
        title_frame.pack(side=tk.LEFT)

        tk.Label(title_frame, text="🦕", font=("Segoe UI Emoji", 24), bg=self.colors['header_bg'], fg="#89dceb").pack(side=tk.LEFT, padx=(0, 10))
        self.title_label = tk.Label(title_frame, text=_("DinoCore Production Flasher"),
                                   font=("Segoe UI", 18, "bold"), bg=self.colors['header_bg'],
                                   fg=self.colors['text'])
        self.title_label.pack(side=tk.LEFT)

        tk.Label(title_frame, text="v1.2.0", font=("Segoe UI", 10), bg=self.colors['header_bg'],
                fg=self.colors['log_text']).pack(side=tk.LEFT, padx=(10, 0))

        # Language selection buttons
        lang_frame = tk.Frame(header_content, bg=self.colors['header_bg'])
        lang_frame.pack(side=tk.RIGHT, padx=(20, 0))

        self.en_button = tk.Button(lang_frame, text="English", font=("Segoe UI", 10, "bold"),
                                   bg=self.colors['frame_bg'], fg=self.colors['text'], relief=tk.FLAT,
                                   command=lambda: self.set_language('en'))
        self.en_button.pack(side=tk.LEFT, padx=(0, 5))

        self.zh_button = tk.Button(lang_frame, text="中文", font=("Segoe UI", 10, "bold"),
                                   bg=self.colors['frame_bg'], fg=self.colors['text'], relief=tk.FLAT,
                                   command=lambda: self.set_language('zh_CN'))
        self.zh_button.pack(side=tk.LEFT)

        # Connection status indicator
        self.connection_label = tk.Label(header_content, text=_("🔗 SERVER ONLINE"),
                                        font=("Segoe UI", 10), bg=self.colors['success_btn'],
                                        fg=self.colors['bg'], padx=10, pady=2, relief=tk.RAISED)
        self.connection_label.pack(side=tk.RIGHT)

        # Main content area
        content_frame = tk.Frame(self.root, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Configuration section
        config_frame = tk.LabelFrame(content_frame, text=f" ⚙️ {_('Configuration')} ", font=("Segoe UI", 11, "bold"),
                                    bg=self.colors['frame_bg'], fg=self.colors['text'],
                                    relief=tk.GROOVE, borderwidth=2)
        config_frame.pack(fill=tk.X, pady=(0, 15))

        config_inner = tk.Frame(config_frame, bg=self.colors['frame_bg'])
        config_inner.pack(fill=tk.X, padx=15, pady=10)

        tk.Label(config_inner, text=_("🎯 Target HW Version:"), font=("Segoe UI", 12, "bold"),
                bg=self.colors['frame_bg'], fg=self.colors['text']).pack(side=tk.LEFT)
        self.version_entry = tk.Entry(config_inner, textvariable=self.hw_version_var,
                                     font=("Consolas", 12), width=15, bg=self.colors['entry_bg'],
                                     fg=self.colors['entry_fg'], insertbackground=self.colors['text'],
                                     relief=tk.FLAT, borderwidth=1, state='readonly')
        self.version_entry.pack(side=tk.LEFT, padx=(15, 10))
        
        # Update button (only if updater is available)
        if DinoUpdater is not None:
            self.update_button = tk.Button(config_inner, text=_("🔄 Check Updates"), font=("Segoe UI", 10, "bold"),
                                          bg=self.colors['warning_btn'], fg=self.colors['bg'],
                                          command=self.check_for_updates, relief=tk.FLAT, padx=15)
            self.update_button.pack(side=tk.LEFT)
        else:
            tk.Label(config_inner, text=_("🔄 Auto-update system not available"), font=("Segoe UI", 9),
                    bg=self.colors['frame_bg'], fg=self.colors['log_text']).pack(side=tk.LEFT, padx=(10, 0))

        # --- Main Control Area ---
        control_area = tk.Frame(content_frame, bg=self.colors['bg'])
        control_area.pack(fill=tk.X, pady=(0, 15))

        # --- Status Display ---
        self.status_label = tk.Label(control_area, text="🔌 " + _("Connect ESP32 Device"), font=("Segoe UI", 16, "bold"),
                                    bg=self.colors['status_idle'], fg="white", pady=8, padx=15,
                                    relief=tk.FLAT)
        self.status_label.pack(fill=tk.X, pady=(0, 10))
        
        # --- Progress Bar ---
        self.progress_bar = ttk.Progressbar(control_area, orient='horizontal', length=100, mode='determinate', style="TProgressbar")
        self.progress_visible = False # Will be packed/unpacked as needed

        # --- Button Configuration ---
        button_config = {
            'font': ("Segoe UI", 12, "bold"),
            'relief': tk.FLAT,
            'borderwidth': 0,
            'pady': 12
        }

        # --- Flashing Section ---
        flash_frame = tk.LabelFrame(control_area, text=f" ⚡ {_('Firmware Flashing')} ", font=("Segoe UI", 11, "bold"),
                                    bg=self.colors['frame_bg'], fg=self.colors['text'], relief=tk.GROOVE, borderwidth=2)
        flash_frame.pack(fill=tk.X, pady=(10, 5))

        flash_inner = tk.Frame(flash_frame, bg=self.colors['frame_bg'])
        flash_inner.pack(fill=tk.X, padx=15, pady=10)

        self.prod_button = tk.Button(flash_inner, text=_("🏭 Flash Production"),
                                    bg=self.colors['prod_btn'], fg=self.colors['bg'],
                                    command=lambda: self.start_flashing('production'), state='disabled', **button_config)
        self.prod_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.test_button = tk.Button(flash_inner, text=_("🧪 Flash Testing & eFuse"),
                                    bg=self.colors['test_btn'], fg=self.colors['bg'],
                                    command=lambda: self.start_flashing('testing'), state='disabled', **button_config)
        self.test_button.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

        # --- Quality Control Section ---
        qc_frame = tk.LabelFrame(control_area, text=f" 🔵 {_('Bluetooth Quality Control (QC)')} ", font=("Segoe UI", 11, "bold"),
                                    bg=self.colors['frame_bg'], fg=self.colors['text'], relief=tk.GROOVE, borderwidth=2)
        qc_frame.pack(fill=tk.X, pady=(5, 0))

        qc_inner = tk.Frame(qc_frame, bg=self.colors['frame_bg'])
        qc_inner.pack(fill=tk.X, padx=15, pady=10)

        if BT_QC_AVAILABLE and BLEAK_AVAILABLE:
            self.bt_select_button = tk.Button(qc_inner, text=_("📡 Scan & Test Device"),
                                            bg='#f9e2af', fg=self.colors['bg'], # Yellow
                                            command=self.start_manual_bt_selection, state='normal', **button_config)
            self.bt_select_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

            self.bt_qc_button = tk.Button(qc_inner, text=_("▶️ Run QC (After Flash)"),
                                        bg='#7b68ee', fg=self.colors['bg'],  # Medium slate blue
                                        command=self.start_bluetooth_qc, state='disabled', **button_config)
            self.bt_qc_button.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        else:
            # Show disabled buttons if Bluetooth not available
            self.bt_select_button = tk.Button(qc_inner, text=_("📡 BT UNAVAILABLE"),
                                        bg='#6c7086', fg=self.colors['bg'],
                                        state='disabled', **button_config)
            self.bt_select_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
            
            self.bt_qc_button = tk.Button(qc_inner, text=_("🔵 BT UNAVAILABLE"),
                                        bg='#6c7086', fg=self.colors['bg'],
                                        state='disabled', **button_config)
            self.bt_qc_button.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

        self.show_mode_buttons()

        # Log Tabs
        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[10, 5])
        style.configure("TNotebook", background=self.colors['bg'], borderwidth=0)
        
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.log_views = {}
        for tab_name in ["USB/Serial", "Bluetooth", "Firebase"]:
            frame = tk.Frame(self.notebook, bg=self.colors['frame_bg'])
            self.notebook.add(frame, text=tab_name)
            log_view = RichLogView(frame, self.colors, bg=self.colors['log_bg'])
            log_view.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.log_views[tab_name] = log_view

        # Start connection monitoring
        self.update_connection_status()

    def is_font_available(self, font_name):
        """Check if a font is available on the system"""
        try:
            test_label = tk.Label(self.root, font=(font_name, 10))
            return True
        except:
            return False

    def update_connection_status(self):
        """Monitor and update connection status"""
        try:
            # Check if we can reach the DinoCore API
            response = requests.get("https://dinocore-telemetry-production.up.railway.app/api/status",
                                  timeout=5)
            if response.status_code == 200:
                self.connection_label.config(text="🔗 SERVER ONLINE", bg=self.colors['success_btn'])
            else:
                self.connection_label.config(text="⚠️ SERVER ISSUES", bg=self.colors['warning_btn'])
        except:
            self.connection_label.config(text="❌ OFFLINE", bg=self.colors['prod_btn'])

        # Update every 30 seconds
        self.root.after(30000, self.update_connection_status)

    def show_mode_buttons(self):
        # This function is now simplified as buttons are always visible
        pass

    def show_stop_button(self):
        # This function is no longer needed
        pass

    def update_log(self):
        while not self.log_queue.empty():
            message_info = self.log_queue.get_nowait()
            
            # --- Write to file log ---
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(str(message_info).strip() + "\n")
            except Exception as e:
                print(f"Failed to write to log file: {e}") # Fallback to console
            
            # Store raw message for Firebase logging
            self.session_logs.append(str(message_info))

            # Determine target tab and message content
            tab_name = "USB/Serial" # Default tab
            message = message_info

            if isinstance(message_info, tuple):
                if message_info[0] in self.log_views:
                    tab_name, message = message_info
                # This handles progress bar updates without trying to log them as text
                elif message_info[0] in ['progress', 'show_progress', 'hide_progress']:
                    if message_info[0] == 'progress':
                        self.progress_bar['value'] = message_info[1]
                    elif message_info[0] == 'show_progress':
                        if not self.progress_visible:
                            self.progress_bar.pack(in_=self.status_frame, fill=tk.X, pady=5, before=self.button_frame)
                            self.progress_visible = True
                    elif message_info[0] == 'hide_progress':
                        if self.progress_visible:
                            self.progress_bar.pack_forget()
                            self.progress_visible = False
                    continue # Skip text logging for this message
            
            message_str = str(message).strip()
            level = 'info' # Default level

            # Determine level from message content
            if "[OK]" in message_str or "✅" in message_str or "[SUCCESS]" in message_str:
                level = 'success'
            elif "[X]" in message_str or "❌" in message_str or "[ERROR]" in message_str or "[FAILED]" in message_str:
                level = 'error'
            elif "[!]" in message_str or "⚠️" in message_str or "[WARNING]" in message_str:
                level = 'warning'
            elif "[BLE" in message_str or "Bluetooth" in message_str or "🔵" in message_str:
                level = 'bluetooth'
            elif "Firebase" in message_str or "🔥" in message_str:
                level = 'firebase'

            # Determine target tab
            if level == 'bluetooth':
                tab_name = "Bluetooth"
            elif level == 'firebase':
                tab_name = "Firebase"
            
            log_view = self.log_views[tab_name]
            
            # Handle special case for flashing progress
            if message_str.startswith('\r'):
                # This is a progress line, handle it without an icon for now
                log_view.text.config(state=tk.NORMAL)
                log_view.text.delete("end-2l", "end-1l")
                log_view.text.insert("end-1l", message_str[1:])
                log_view.text.config(state=tk.DISABLED)
            else:
                log_view.log(message_str, level)

        self.root.after(100, self.update_log)

    def start_flashing(self, operation):
        if not self.esp32_port:
            messagebox.showerror(_("Error"), _("No ESP32 device detected."))
            return

        # Reset captured details on new flash operation
        self.captured_mac = None
        self.captured_ble_name = None
        self.bt_qc_button.config(state='disabled')

        if operation == 'production':
            if not messagebox.askokcancel(_("Confirm"), _("Ready to flash PRODUCTION firmware to {port}?").format(port=self.esp32_port)):
                return
            self.status_label.config(text="🏭 " + _("Flashing Production..."), bg=self.colors['status_prod'])
        else: # testing
            if not messagebox.askokcancel(_("Confirm"), _("Ready to flash TESTING firmware and burn eFuse on {port}? This is irreversible.").format(port=self.esp32_port)):
                return
            self.status_label.config(text="🧪 " + _("Flashing Testing..."), bg=self.colors['status_test'])
        
        self.scanner_stop_event.set() # Stop the detector thread
        
        target_hw_version = self.hw_version_var.get()
        # Pass 'self' to process_device_thread
        flash_thread = threading.Thread(target=process_device_thread, args=(self.log_queue, self.esp32_port, operation, threading.Event(), target_hw_version, self), daemon=True)
        flash_thread.start()

        # Disable buttons during flash
        self.prod_button.config(state='disabled')
        self.test_button.config(state='disabled')
        self.bt_qc_button.config(state='disabled')

        # Monitor thread to re-enable buttons
        def monitor_flash_thread():
            flash_thread.join()
            self.scanner_stop_event.clear()
            detector_thread = threading.Thread(target=self.device_detector_worker, daemon=True)
            detector_thread.start()

        monitor_thread = threading.Thread(target=monitor_flash_thread, daemon=True)
        monitor_thread.start()

    def device_detector_worker(self):
        self.esp32_port = None
        last_status = None

        while not self.scanner_stop_event.is_set():
            port, status = get_esp32_port(self.log_queue)

            if status != last_status:
                if status == "ESP32_FOUND":
                    self.esp32_port = port
                    self.log_queue.put(f"✅ ESP32 detected on port {port}")
                    self.status_label.config(text="✅ " + _("ESP32 Ready on {}").format(port), bg=self.colors['status_success'])
                    self.prod_button.config(state='normal')
                    self.test_button.config(state='normal')
                    self.bt_qc_button.config(state='normal')
                elif status == "NO_ESP32_FOUND":
                    self.esp32_port = None
                    self.status_label.config(text="🔌 " + _("Connect ESP32 Device"), bg=self.colors['status_idle'])
                    self.prod_button.config(state='disabled')
                    self.test_button.config(state='disabled')
                    self.bt_qc_button.config(state='disabled')
                elif status == "MULTIPLE_ESP32_FOUND":
                    self.esp32_port = None
                    self.status_label.config(text="⚠️ " + _("Multiple ESP32s Detected"), bg=self.colors['status_warning'])
                    self.prod_button.config(state='disabled')
                    self.test_button.config(state='disabled')
                    self.bt_qc_button.config(state='disabled')
                last_status = status
            
            time.sleep(2)

    def set_language(self, lang_code):
        """Set the application language and update UI."""
        if translation_manager.set_language(lang_code):
            self.update_all_texts()
        else:
            messagebox.showerror(_("Error"), _("Failed to change language"))

    def update_language_buttons(self):
        """Update the visual state of language buttons."""
        current_lang = translation_manager.get_current_language()
        if current_lang == 'en':
            self.en_button.config(relief=tk.SUNKEN, bg=self.colors['highlight'])
            self.zh_button.config(relief=tk.FLAT, bg=self.colors['frame_bg'])
        elif current_lang.startswith('zh'):
            self.zh_button.config(relief=tk.SUNKEN, bg=self.colors['highlight'])
            self.en_button.config(relief=tk.FLAT, bg=self.colors['frame_bg'])

    def check_for_updates(self):
        """Check for updates and show results in log"""
        if DinoUpdater is None:
            messagebox.showerror(_("Error"), _("Update system is not available"))
            return

        # Disable the update button during check
        self.update_button.config(state='disabled', text=_("🔄 Checking..."))

        def update_check_thread():
            try:
                updater = DinoUpdater()
                update_info = updater.check_for_updates()

                if update_info:
                    # Show update available dialog
                    changelog = update_info['changelog'][:300] + "..." if len(update_info['changelog']) > 300 else update_info['changelog']
                    message = _(f"Update available: {update_info['version']}\n\nChanges:\n{changelog}\n\nDo you want to install this update?")

                    # Use after() to show dialog in main thread
                    def show_update_dialog():
                        if messagebox.askyesno(_("Update Available"), message):
                            self.perform_update(update_info)
                        else:
                            self.log_queue.put(_("Update cancelled by user"))
                            self.update_button.config(state='normal', text=_("🔄 Check Updates"))

                    self.root.after(0, show_update_dialog)
                else:
                    self.log_queue.put(_("✅ You are using the latest version"))
                    self.root.after(0, lambda: self.update_button.config(state='normal', text=_("🔄 Check Updates")))

            except Exception as e:
                self.log_queue.put(_(f"[X] Update check failed: {e}"))
                self.root.after(0, lambda: self.update_button.config(state='normal', text=_("🔄 Check Updates")))

        # Start update check in background thread
        thread = threading.Thread(target=update_check_thread, daemon=True)
        thread.start()

    def perform_update(self, update_info):
        """Perform the actual update"""
        # Disable button and show progress
        self.update_button.config(state='disabled', text=_("⬆️ Updating..."))

        def update_thread():
            try:
                updater = DinoUpdater()
                if updater.update(auto_confirm=True):
                    self.log_queue.put(_("✅ Update completed! Please restart the application."))
                    messagebox.showinfo(_("Success"), _("Update completed successfully!\n\nPlease restart the application to use the new version."))
                else:
                    self.log_queue.put(_("[X] Update failed or was cancelled"))
                    messagebox.showerror(_("Error"), _("Update failed. Check the log for details."))
            except Exception as e:
                self.log_queue.put(_(f"[X] Update error: {e}"))
                messagebox.showerror(_("Error"), _("Update failed. Check the log for details."))

            # Re-enable button
            self.root.after(0, lambda: self.update_button.config(state='normal', text=_("🔄 Check Updates")))

        # Start update in background thread
        thread = threading.Thread(target=update_thread, daemon=True)
        thread.start()

    def start_bluetooth_qc(self):
        """Start Bluetooth QC testing mode"""
        if not BT_QC_AVAILABLE or not BLEAK_AVAILABLE:
            self.bt_not_available()
            return

        if messagebox.askokcancel(_("Bluetooth QC"),
                                  _("Start Bluetooth LE quality control testing?\n\n"
                                    "This will scan for QA-enabled devices and run microphone\n"
                                    "balance tests via Bluetooth LE.\n\n"
                                    "Make sure devices are powered on and in range.")):
            self.start_bluetooth_qc_mode()

    def bt_not_available(self):
        """Show message when Bluetooth is not available"""
        messagebox.showerror(_("Bluetooth Not Available"),
                           _("Bluetooth QC testing is not available on this system.\n\n"
                             "Required components:\n"
                             "• bleak package for Bluetooth LE support\n"
                             "• Compatible Bluetooth adapter\n"
                             "• Python asyncio support\n\n"
                             "Please install bleak: pip install bleak"))

    def start_bluetooth_qc_mode(self):
        """Initialize and start Bluetooth QC testing"""
        self.status_label.config(text="🔵 " + _("Bluetooth QC Active..."), bg='#7b68ee')
        
        # Disable buttons during QC
        self.prod_button.config(state='disabled')
        self.test_button.config(state='disabled')
        self.bt_qc_button.config(state='disabled')

        def bt_qc_thread_wrapper():
            asyncio.run(self.run_bluetooth_qc())
            # Re-enable detector worker when done
            self.scanner_stop_event.clear()
            detector_thread = threading.Thread(target=self.device_detector_worker, daemon=True)
            detector_thread.start()

        bt_thread = threading.Thread(target=bt_qc_thread_wrapper, daemon=True)
        bt_thread.start()

    def stop_bluetooth_qc(self):
        """Stop Bluetooth QC testing"""
        if hasattr(self, 'bt_qc_stop_event'):
            self.bt_qc_stop_event.set()

        # Reset UI
        self.status_label.config(text=_("▶️  SELECT A MODE"), bg=self.colors['status_idle'])
        self.bt_qc_button.config(text=_("🔵 BLUETOOTH QC"), bg='#7b68ee',
                                command=self.start_bluetooth_qc)

    def start_manual_bt_selection(self):
        """Wrapper to run the async device selection process."""
        self.log_queue.put("Starting manual Bluetooth device selection...")
        
        def selection_thread_wrapper():
            asyncio.run(self.manual_bt_selection_async())

        selection_thread = threading.Thread(target=selection_thread_wrapper, daemon=True)
        selection_thread.start()

    async def manual_bt_selection_async(self):
        """Async function to scan, select, and immediately test a BT device."""
        try:
            bt_qc_tester = get_bluetooth_qc_tester()
            bt_qc_tester.set_log_queue(self.log_queue)
            
            devices = await bt_qc_tester.scan_devices()
            if not devices:
                self.log_queue.put("No Bluetooth devices found.")
                messagebox.showinfo(_("Scan Result"), _("No Bluetooth devices found."))
                return

            selected_device = await self.select_bluetooth_device(devices)
            
            if selected_device:
                self.log_queue.put(f"User selected: {selected_device.name} ({selected_device.address})")
                self.set_captured_ble_details(selected_device.address, selected_device.name)
                
                # Automatically start the QC test
                self.log_queue.put("Device selected. Starting QC test automatically...")
                self.start_bluetooth_qc_mode()
            else:
                self.log_queue.put("User cancelled selection.")

        except Exception as e:
            self.log_queue.put(f"Error during manual selection: {e}")
            messagebox.showerror("Error", f"An error occurred: {e}")

    async def run_bluetooth_qc(self):
        """Async function to run Bluetooth QC testing with retries and detailed logging."""
        if not self.captured_mac:
            messagebox.showerror(_("Error"), _("No Bluetooth MAC captured. Please run a 'Testing' flash first."))
            return

        try:
            bt_qc_tester = get_bluetooth_qc_tester()
            bt_qc_tester.set_log_queue(self.log_queue)

            self.log_queue.put(f"🟦 Starting Bluetooth QC for MAC: {self.captured_mac}...")
            
            self.log_queue.put("⏳ Waiting for device to signal it's ready for connection...")
            if not self.ble_ready_event.wait(timeout=15):
                self.log_queue.put("❌ Timed out waiting for BLE ready signal from device.")
                self.root.after(0, self.stop_bluetooth_qc)
                return

            found_device = None
            max_retries = 3
            for attempt in range(max_retries):
                self.log_queue.put(f"🔎 Attempt {attempt + 1}/{max_retries}: Scanning for device with MAC {self.captured_mac}...")
                try:
                    devices = await bleak.BleakScanner.discover(timeout=7.0)
                    self.log_queue.put(f"   - Found {len(devices)} BLE devices in this scan.")
                    for i, d in enumerate(devices):
                        self.log_queue.put(f"     - Device {i}: {d.name or 'Unknown'} ({d.address})")
                    
                    for device in devices:
                        # Compare MAC addresses (case-insensitive)
                        if device.address.upper() == self.captured_mac.upper():
                            found_device = device
                            self.log_queue.put(f"🎯 MAC Address match found: {device.name} at {device.address}")
                            break
                    if found_device:
                        break
                except Exception as e:
                    self.log_queue.put(f"   - Error during scan attempt {attempt + 1}: {e}")
                
                if not found_device:
                    self.log_queue.put(f"   - Device not found. Retrying in 2 seconds...")
                    await asyncio.sleep(2)

            if not found_device:
                self.log_queue.put(f"❌ CRITICAL: Device with MAC '{self.captured_mac}' not found after {max_retries} attempts.")
                self.root.after(0, self.stop_bluetooth_qc)
                return

            self.log_queue.put(f"✅ Found device. Attempting to connect to {found_device.address}...")
            connected = await bt_qc_tester.connect_device(found_device.address)
            if not connected:
                self.log_queue.put("❌ Failed to connect to device")
                self.root.after(0, self.stop_bluetooth_qc)
                return

            self.log_queue.put("✅ Connected to Bluetooth device. Waiting for services to stabilize...")
            await asyncio.sleep(1.0) # Added delay for stability

            # Run microphone balance test with retry logic
            test_result = False
            for i in range(2): # Try up to 2 times
                test_result = await bt_qc_tester.run_test(0)  # Test index 0: Mic L/R Balance
                if test_result:
                    break
                self.log_queue.put(f"⚠️ Test command failed to send on attempt {i+1}. Retrying after 1s...")
                await asyncio.sleep(1.0)

            # Get MAC address
            mac_address = found_device.address
            self.log_queue.put(f"MAC Address: {mac_address}")

            if test_result:
                # Wait for results (they come via notifications)
                await asyncio.sleep(15)  # Wait up to 15 seconds for test results

                # Get final results
                results = bt_qc_tester.get_test_results()
                if results:
                    self.display_test_results(results)

                    # Store results in Firebase if available
                    if FIREBASE_AVAILABLE:
                        try:
                            device_info = {
                                'name': found_device.name or 'Unknown',
                                'address': found_device.address
                            }
                            if store_qc_results(device_info, results):
                                self.log_queue.put("💾 QC results stored in Firebase database")
                            else:
                                self.log_queue.put("⚠️ Failed to store QC results in Firebase")
                        except Exception as e:
                            self.log_queue.put(f"⚠️ Firebase storage error: {e}")
                else:
                    self.log_queue.put("⚠️ No test results received")
            else:
                self.log_queue.put("❌ Failed to run Bluetooth test")

            # Disconnect
            await bt_qc_tester.disconnect()

        except Exception as e:
            self.log_queue.put(f"❌ Bluetooth QC error: {e}")
        finally:
            # Store the session log to Firebase
            if FIREBASE_AVAILABLE and self.session_logs:
                store_session_log(self.session_logs)
            
            self.root.after(0, self.stop_bluetooth_qc)

    async def select_bluetooth_device(self, devices):
        """Show device selection dialog and let user choose"""
        # Use asyncio to show the dialog in the main thread
        device_result = {'selected_device': None}

        def show_device_dialog():
            # Create a new window for device selection
            dialog = tk.Toplevel(self.root)
            dialog.title(_("Select Bluetooth Device"))
            dialog.geometry("500x400")
            dialog.configure(bg=self.colors['bg'])
            dialog.transient(self.root)  # Make it modal
            dialog.grab_set()  # Block interaction with main window

            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
            y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
            dialog.geometry(f"+{x}+{y}")

            # Header
            header_frame = tk.Frame(dialog, bg=self.colors['header_bg'], height=50)
            header_frame.pack(fill=tk.X, padx=0, pady=0)
            header_frame.pack_propagate(False)

            tk.Label(header_frame, text="📱 " + _("Select Bluetooth Device"),
                    font=("Segoe UI", 14, "bold"), bg=self.colors['header_bg'],
                    fg=self.colors['text']).pack(pady=10)

            # Device list frame
            list_frame = tk.Frame(dialog, bg=self.colors['bg'])
            list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

            # Create a frame for the list and scrollbar
            list_container = tk.Frame(list_frame, bg=self.colors['bg'])
            list_container.pack(fill=tk.BOTH, expand=True)

            # Canvas and scrollbar for scrolling
            canvas = tk.Canvas(list_container, bg=self.colors['bg'], highlightthickness=0)
            scrollbar = tk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            # Pack canvas and scrollbar
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # Mouse wheel scrolling
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

            # Variables for selection
            selected_device_var = tk.StringVar()
            all_device_frames = []

            def on_radio_select():
                try:
                    selected_index = int(selected_device_var.get())
                    for idx, frame in enumerate(all_device_frames):
                        if idx == selected_index:
                            frame.config(bg=self.colors['frame_bg'])
                        else:
                            frame.config(bg=self.colors['bg'])
                except (ValueError, IndexError):
                    pass

            # Create radio buttons for each device
            for i, device in enumerate(devices):
                device_frame = tk.Frame(scrollable_frame, bg=self.colors['bg'], relief=tk.SOLID, borderwidth=1, highlightbackground=self.colors['frame_bg'])
                device_frame.pack(fill=tk.X, pady=5, padx=10)
                all_device_frames.append(device_frame)

                # Device info
                device_name = device.name or "Unknown Device"
                device_addr = device.address

                # Radio button for selection
                radio_btn = tk.Radiobutton(
                    device_frame,
                    text=f"{device_name} ({device_addr})",
                    variable=selected_device_var,
                    value=f"{i}",
                    font=("Segoe UI", 10),
                    bg=self.colors['bg'],
                    fg=self.colors['text'],
                    selectcolor=self.colors['bg'], # Make radio circle blend in
                    activebackground=self.colors['bg'],
                    activeforeground=self.colors['highlight'],
                    highlightthickness=0,
                    command=on_radio_select,
                    anchor="w"
                )
                radio_btn.pack(anchor="w", fill=tk.X, padx=5, pady=5)

                # Add some styling
                if 'dino' in device_name.lower():
                    radio_btn.config(font=("Segoe UI", 10, "bold"), fg=self.colors['success_btn'])
                elif 'qa' in device_name.lower():
                    radio_btn.config(font=("Segoe UI", 10, "italic"), fg=self.colors['warning_btn'])

            # Pre-select first device
            if devices:
                selected_device_var.set("0")

            # Button frame
            button_frame = tk.Frame(dialog, bg=self.colors['bg'])
            button_frame.pack(fill=tk.X, padx=20, pady=10)

            def on_select():
                try:
                    selected_index = int(selected_device_var.get())
                    device_result['selected_device'] = devices[selected_index]
                    dialog.destroy()
                except (ValueError, IndexError):
                    pass

            def on_cancel():
                device_result['selected_device'] = None
                dialog.destroy()

            # Buttons
            select_btn = tk.Button(
                button_frame,
                text=_("✅ Select Device"),
                command=on_select,
                font=("Segoe UI", 11, "bold"),
                bg=self.colors['success_btn'],
                fg=self.colors['bg'],
                relief=tk.FLAT,
                padx=20,
                pady=8
            )
            select_btn.pack(side=tk.RIGHT, padx=(10, 0))

            cancel_btn = tk.Button(
                button_frame,
                text=_("❌ Cancel"),
                command=on_cancel,
                font=("Segoe UI", 11),
                bg=self.colors['prod_btn'],
                fg=self.colors['bg'],
                relief=tk.FLAT,
                padx=20,
                pady=8
            )
            cancel_btn.pack(side=tk.RIGHT)

            # Wait for dialog to close
            self.root.wait_window(dialog)

        # Show dialog in main thread
        self.root.after(0, show_device_dialog)

        # Wait for user selection (with timeout)
        timeout = 30  # 30 seconds timeout
        start_time = time.time()

        while device_result['selected_device'] is None and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.1)

        selected_device = device_result['selected_device']

        if selected_device:
            self.log_queue.put(f"📱 User selected device: {selected_device.name or 'Unknown'} ({selected_device.address})")
        else:
            self.log_queue.put("❌ User cancelled device selection or timed out")

        return selected_device

    def display_test_results(self, results):
        """Display QC test results in a formatted way"""
        self.log_queue.put("\n🎯 QA TEST RESULTS:")
        self.log_queue.put("=" * 50)

        for result in results:
            status_icon = "✅" if result['status'] == 'pass' else "❌"
            self.log_queue.put(f"Test: {result['name']}")
            self.log_queue.put(f"Result: {status_icon} {result['status'].upper()}")

            if 'details' in result:
                self.log_queue.put(f"Details: {result['details']}")

            if 'evaluation_data' in result:
                eval_data = result['evaluation_data']
                if 'rms_L' in eval_data and 'rms_R' in eval_data:
                    balance = eval_data['rms_L'] / max(eval_data['rms_R'], 0.001)
                    if balance > 0.9 and balance < 1.1:
                        balance_status = "Balanced 🎵"
                    else:
                        balance_status = "Unbalanced ⚠️"
                    self.log_queue.put(f"Audio Balance: {balance_status}")
                    self.log_queue.put(".1f")
                    self.log_queue.put(".1f")

            self.log_queue.put("-" * 30)

        # Summary
        pass_count = sum(1 for r in results if r['status'] == 'pass')
        total_count = len(results)
        self.log_queue.put(f"Summary: {pass_count}/{total_count} tests passed")

        if pass_count == total_count:
            self.log_queue.put("🎉 ALL TESTS PASSED - Device approved!")
        else:
            self.log_queue.put("⚠️ Some tests failed - Device requires attention")

        self.log_queue.put("=" * 50)

    def update_all_texts(self):
        """Update all interface texts after language change."""
        self.root.title(_("🦕 DinoCore Production Flasher v1.2.0"))
        self.title_label.config(text=_("DinoCore Production Flasher"))
        self.connection_label.config(text=_("🔗 SERVER ONLINE")) # This will be updated by status check
        
        # Config Frame
        self.notebook.tab(0, text=_("USB/Serial"))
        self.notebook.tab(1, text=_("Bluetooth"))
        self.notebook.tab(2, text=_("Firebase"))

        # Buttons and Labels
        if DinoUpdater is not None:
            self.update_button.config(text=_("🔄 Check Updates"))
        self.prod_button.config(text=_("🏭 Flash Production"))
        self.test_button.config(text=_("🧪 Flash Testing & eFuse"))
        self.bt_select_button.config(text=_("📡 Scan & Test Device"))
        self.bt_qc_button.config(text=_("▶️ Run QC (After Flash)"))

        # Update status label text if it's in a default state
        current_status = self.status_label.cget("text")
        if "Connect ESP32 Device" in current_status or "连接ESP32设备" in current_status:
             self.status_label.config(text="🔌 " + _("Connect ESP32 Device"))
        
        # Update language button states
        self.update_language_buttons()



class VersionDialog:
    def __init__(self, parent, colors):
        self.top = tk.Toplevel(parent)
        self.top.title(_("Enter Hardware Version"))
        self.top.configure(bg=colors['bg'])
        self.top.resizable(False, False)
        self.colors = colors
        self.version = ""

        # Load and display image
        try:
            img_path = "pcb_example.png"
            img = Image.open(img_path)
            img.thumbnail((400, 400))
            self.photo = ImageTk.PhotoImage(img)
            img_label = tk.Label(self.top, image=self.photo, bg=colors['bg'])
            img_label.pack(pady=10, padx=20)
        except FileNotFoundError:
            tk.Label(self.top, text=_("Image not found."), bg=colors['bg'], fg=colors['text']).pack(pady=10)

        # Label
        label = tk.Label(self.top, text=_("Please enter the version number printed on the PCB:"), font=("Segoe UI", 12), bg=colors['bg'], fg=colors['text'])
        label.pack(pady=(10, 5), padx=20)

        # Entry
        self.entry = tk.Entry(self.top, font=("Consolas", 14), width=15, bg=colors['entry_bg'], fg=colors['entry_fg'], insertbackground=colors['text'])
        self.entry.pack(pady=10)
        self.entry.focus_set()

        # Button
        button = tk.Button(self.top, text=_("OK"), font=("Segoe UI", 12, "bold"), bg=colors['success_btn'], fg=colors['bg'], command=self.ok)
        button.pack(pady=10, padx=20, fill=tk.X)

        self.top.transient(parent)
        self.top.grab_set()
        self.top.protocol("WM_DELETE_WINDOW", self.cancel)
        self.entry.bind("<Return>", self.ok)

    def ok(self, event=None):
        self.version = self.entry.get()
        self.top.destroy()

    def cancel(self):
        self.version = ""
        self.top.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FlasherApp(root)
    root.mainloop()
