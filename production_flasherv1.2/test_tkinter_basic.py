#!/usr/bin/env python3
"""
Test basic Tkinter functionality to diagnose startup issues
"""

import os
import sys
import traceback

def test_tkinter():
    """Test basic Tkinter functionality"""
    print("=== Testing Basic Tkinter Functionality ===")
    print(f"Python version: {sys.version}")
    print(f"OS: {os.name}")

    try:
        print("Testing Tkinter import...")
        import tkinter as tk
        print("✅ Tkinter imported successfully")

        print("Testing PIL import...")
        from PIL import Image, ImageDraw, ImageFont
        from PIL import ImageTk
        print("✅ PIL imported successfully")

        print("Testing Firebase import...")
        try:
            from firebase_db import init_firebase_with_credentials
            print("✅ Firebase module imported")
        except Exception as e:
            print(f"❌ Firebase import error: {e}")

        print("Testing main app imports...")
        try:
            import requests
            import threading
            import queue
            print("✅ Main imports successful")
        except Exception as e:
            print(f"❌ Main import error: {e}")

        print("Testing basic Tkinter window...")
        test_root = tk.Tk()
        test_root.title("TEST WINDOW - Ignore this")

        # Basic geometry
        test_root.geometry("200x100")

        # Add minimal widget
        label = tk.Label(test_root, text="TESTING...")
        label.pack()

        # Make sure it doesn't show (withdraw)
        test_root.withdraw()

        print("✅ Tkinter window created successfully")

        # Clean up
        test_root.destroy()
        print("✅ Tkinter cleaned up successfully")

        return True

    except Exception as e:
        print(f"❌ Tkinter test failed: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_tkinter()
    if success:
        print("\n🎉 All basic tests passed - Tkinter should work")
        print("If gui_flasher.py still fails, the issue is in our application logic")
    else:
        print("\n💥 Basic Tkinter tests failed - this explains why the app exits immediately")
        print("Fix environment before trying gui_flasher.py")
