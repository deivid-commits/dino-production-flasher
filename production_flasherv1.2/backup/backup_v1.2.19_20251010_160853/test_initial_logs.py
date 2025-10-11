#!/usr/bin/env python3
"""
Test script to manually save initial startup logs to Firebase
"""

import datetime
from firebase_db import init_firebase_with_credentials, store_session_log

def test_initial_logging():
    """Test saving initial logs to Firebase"""
    print("=== Testing Initial Logging to Firebase ===")
    print(f"Current time: {datetime.datetime.now()}")

    # Initialize Firebase
    print("Initializing Firebase...")
    if init_firebase_with_credentials():
        print("✅ Firebase initialized successfully")

        # Create test initial logs
        initial_logs = [
            "🚀 Starting DinoCore Production Flasher v1.2.14",
            f"📍 Working directory: C:\\Users\\deivi\\OneDrive\\Documents\\Dino\\Production Flasher2.1\\production_flasherv1.2",
            "🐍 Python version: 3.12.x",
            "Attempting to initialize Firebase...",
            "✅ Firebase connection successful.",
            f"🎯 Using hardware version for this session: 1.9.1",
            f"Started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]

        print(f"Saving {len(initial_logs)} initial log entries to Firebase...")

        # Save logs
        if store_session_log(initial_logs):
            print("✅ Initial logs saved successfully!")
            print("Log entries:")
            for i, log in enumerate(initial_logs):
                print(f"  {i+1}. {log}")
        else:
            print("❌ Failed to save initial logs")
    else:
        print("❌ Firebase initialization failed")

if __name__ == "__main__":
    test_initial_logging()
