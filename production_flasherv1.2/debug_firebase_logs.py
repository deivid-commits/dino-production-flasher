#!/usr/bin/env python3
"""
DinoCore Production Flasher - Firebase Logs Debugger
Downloads and displays recent logs from Firebase for remote debugging
"""

import os
import sys
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

# Add the current directory to the path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Firebase imports with fallback
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, initialize_app
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("❌ Firebase not available - install firebase-admin: pip install firebase-admin")
    firebase_admin = None

class FirebaseLogsDebugger:
    """Firebase logs debugger for remote troubleshooting"""

    def __init__(self):
        self.db = None
        self.initialized = False

    def initialize_firebase(self) -> bool:
        """Initialize Firebase connection"""
        if not FIREBASE_AVAILABLE:
            return False

        try:
            # Try common Firebase credentials locations
            possible_paths = [
                'firebase-credentials.json',
                'credentials.json',
                'firebase-adminsdk.json',
                os.path.expanduser('~/.firebase/credentials.json'),
                os.path.expanduser('~/firebase-credentials.json')
            ]

            cred = None
            for path in possible_paths:
                if os.path.exists(path):
                    cred = credentials.Certificate(path)
                    print(f"✅ Found Firebase credentials at: {path}")
                    break

            if not cred:
                print("❌ Firebase credentials not found. Please provide credentials file.")
                return False

            # Initialize Firebase app (use default app)
            try:
                initialize_app(cred)
            except ValueError as e:
                if "already exists" in str(e):
                    # App already exists, that's fine
                    pass
                else:
                    raise

            # Get Firestore client
            self.db = firestore.client()
            self.initialized = True

            print("✅ Firebase initialized successfully")
            return True

        except Exception as e:
            print(f"❌ Firebase initialization error: {e}")
            return False

    def get_recent_logs(self, hours: int = 24, limit: int = 100) -> Dict[str, List[Dict[str, Any]]]:
        """Get recent logs from all collections"""
        if not self.initialized or not self.db:
            return {}

        try:
            # Calculate time threshold
            time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours)

            all_logs = {
                'session_logs': [],
                'flash_logs': [],
                'qc_results': []
            }

            # Get session logs
            try:
                print(f"📥 Downloading session logs (last {hours}h)...")
                logs_ref = self.db.collection('logs')
                query = logs_ref.where('timestamp', '>=', time_threshold).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
                docs = query.stream()

                for doc in docs:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    data['collection'] = 'logs'
                    all_logs['session_logs'].append(data)

                print(f"   ✅ Found {len(all_logs['session_logs'])} session logs")

            except Exception as e:
                print(f"   ⚠️ Error getting session logs: {e}")

            # Get flash logs
            try:
                print(f"📥 Downloading flash logs (last {hours}h)...")
                flash_ref = self.db.collection('flash_logs')
                query = flash_ref.where('timestamp', '>=', time_threshold).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
                docs = query.stream()

                for doc in docs:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    data['collection'] = 'flash_logs'
                    all_logs['flash_logs'].append(data)

                print(f"   ✅ Found {len(all_logs['flash_logs'])} flash logs")

            except Exception as e:
                print(f"   ⚠️ Error getting flash logs: {e}")

            # Get QC results
            try:
                print(f"📥 Downloading QC results (last {hours}h)...")
                qc_ref = self.db.collection('qc_results')
                query = qc_ref.where('timestamp', '>=', time_threshold).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
                docs = query.stream()

                for doc in docs:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    data['collection'] = 'qc_results'
                    all_logs['qc_results'].append(data)

                print(f"   ✅ Found {len(all_logs['qc_results'])} QC results")

            except Exception as e:
                print(f"   ⚠️ Error getting QC results: {e}")

            return all_logs

        except Exception as e:
            print(f"❌ Error getting logs: {e}")
            return {}

    def display_logs(self, logs_data: Dict[str, List[Dict[str, Any]]], show_details: bool = True):
        """Display logs in a formatted way"""
        print("\n" + "="*80)
        print("🔍 DINOCORE FIREBASE LOGS DEBUGGER")
        print("="*80)

        total_logs = sum(len(logs) for logs in logs_data.values())
        print(f"📊 Total logs found: {total_logs}")

        for collection, logs in logs_data.items():
            if not logs:
                continue

            print(f"\n📁 Collection: {collection.upper()}")
            print("-" * 50)

            for log in logs:
                self.display_single_log(log, show_details)

    def display_single_log(self, log: Dict[str, Any], show_details: bool = True):
        """Display a single log entry"""
        log_id = log.get('id', 'unknown')
        timestamp = log.get('timestamp')

        if isinstance(timestamp, datetime):
            timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')
        else:
            timestamp_str = str(timestamp)

        print(f"🆔 {log_id}")
        print(f"⏰ {timestamp_str}")

        if log.get('collection') == 'logs':
            log_content = log.get('log_content', 'No content')
            print(f"📝 Content: {log_content[:200]}..." if len(log_content) > 200 else f"📝 Content: {log_content}")

        elif log.get('collection') == 'flash_logs':
            success = log.get('success', False)
            mode = log.get('mode', 'unknown')
            hardware_version = log.get('hardware_version', 'unknown')
            error = log.get('error_message', 'None')
            duration = log.get('duration', 0)

            status_icon = "✅" if success else "❌"
            print(f"🔧 Operation: {mode} flash")
            print(f"📱 Hardware Version: {hardware_version}")
            print(f"⏱️ Duration: {duration}s")
            print(f"📊 Status: {status_icon} {'Success' if success else 'Failed'}")
            if error:
                print(f"🚨 Error: {error}")

        elif log.get('collection') == 'qc_results':
            device_name = log.get('device_name', 'Unknown')
            device_address = log.get('device_address', 'Unknown')
            total_tests = log.get('total_tests', 0)
            passed_tests = log.get('passed_tests', 0)
            failed_tests = log.get('failed_tests', 0)

            print(f"📱 Device: {device_name} ({device_address})")
            print(f"🧪 Tests: {passed_tests}/{total_tests} passed")

            if show_details and 'test_results' in log:
                for test in log['test_results']:
                    status_icon = "✅" if test.get('status') == 'pass' else "❌"
                    print(f"   {status_icon} {test.get('name', 'Unknown')}: {test.get('status', 'unknown')}")

        print("-" * 30)

    def export_logs_to_file(self, logs_data: Dict[str, List[Dict[str, Any]]], filename: str = None):
        """Export logs to a JSON file for further analysis"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"firebase_logs_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(logs_data, f, indent=2, default=str, ensure_ascii=False)

            print(f"💾 Logs exported to: {filename}")
            return True

        except Exception as e:
            print(f"❌ Error exporting logs: {e}")
            return False

def main():
    """Main debugging function"""
    print("🔧 DinoCore Firebase Logs Debugger")
    print("=================================")

    debugger = FirebaseLogsDebugger()

    # Initialize Firebase
    if not debugger.initialize_firebase():
        print("❌ Cannot proceed without Firebase connection")
        return 1

    # Get recent logs (last 24 hours by default)
    print("\n📥 Downloading recent logs from Firebase...")
    logs_data = debugger.get_recent_logs(hours=24, limit=50)

    # Display logs
    debugger.display_logs(logs_data)

    print("\n✅ Debugging session completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
