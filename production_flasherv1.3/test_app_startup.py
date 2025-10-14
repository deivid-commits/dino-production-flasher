#!/usr/bin/env python3
"""
Detailed test of gui_flasher.py startup process
"""

import os
import sys
import traceback
import threading
import queue

def test_app_startup():
    """Test gui_flasher.py startup step by step"""
    print("=== Testing DinoCore GUI Application Startup ===")

    try:
        print("\n1. Testing Tkinter root creation...")
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide it for now
        print("✅ Root Tkinter window created")

        print("\n2. Testing imports from gui_flasher.py...")
        # Import necessary modules
        import configparser
        print("✅ configparser imported")

        # Test translation manager
        try:
            from i18n_utils import _
            print("✅ i18n_utils imported")
        except ImportError:
            print("❌ i18n_utils import failed")

        print("\n3. Testing Firebase initialization in thread...")
        # Test Firebase init (should not block)
        firebase_available = False
        try:
            from firebase_db import get_firebase_db, store_qc_results, store_flash_log, store_session_log, init_firebase_with_credentials
            print("✅ Firebase modules imported")

            # Try to init Firebase
            firebase_available = True
            firebase_thread = threading.Thread(target=lambda: init_firebase_with_credentials(), daemon=True)
            firebase_thread.start()
            print("✅ Firebase initialization thread started")

        except ImportError as e:
            firebase_available = False
            print(f"⚠️ Firebase not available: {e}")

        print("\n4. Testing Bluetooth modules...")
        bt_available = False
        try:
            from bluetooth_qc import get_bluetooth_qc_tester, BLEAK_AVAILABLE
            bt_available = True
            print("✅ Bluetooth QC modules imported")
        except ImportError as e:
            print(f"⚠️ Bluetooth QC not available: {e}")

        print("\n5. Testing main app class import...")
        try:
            # Import the main classes from gui_flasher.py at the module level
            from gui_flasher import VersionDialog, LogViewer, FlasherApp
            print("✅ FlasherApp class imported")

            print("\n6. Testing FlasherApp initialization...")
            # Try to create the app - this is where it might fail
            app = FlasherApp(root)
            print("✅ FlasherApp instance created")

            print("\n7. Testing mainloop start...")
            # Start mainloop but in a controlled way
            root.after(1000, lambda: root.quit())  # Exit after 1 second
            root.mainloop()
            print("✅ Mainloop ran successfully")

            return True

        except Exception as e:
            print(f"❌ FlasherApp creation/initialization failed: {e}")
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"❌ General startup test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_app_startup()
    if success:
        print("\n🎉 Application startup test PASSED")
        print("The app should start normally")
    else:
        print("\n💥 Application startup test FAILED")
        print("This explains why gui_flasher.py exits immediately")
        print("Need to fix the initialization error in gui_flasher.py")
