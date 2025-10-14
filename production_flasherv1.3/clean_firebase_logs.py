#!/usr/bin/env python3
"""
Script to clean all test logs from Firebase
"""

from firebase_db import get_firebase_db, init_firebase_with_credentials

def clean_firebase_logs():
    """Clean all test logs from Firebase collections"""
    print("🧹 Cleaning ALL Firebase logs...")

    if not init_firebase_with_credentials():
        print("❌ Failed to initialize Firebase")
        return False

    firebase_db = get_firebase_db()

    try:
        # Clean session logs (only ones containing test indicators)
        session_docs = firebase_db.db.collection('logs').stream()
        session_deleted = 0
        for doc in session_docs:
            data = doc.to_dict()
            if ('session_logs' in data and
                any('test' in str(log).lower() or 'production flasher v1' in str(log).lower()
                    for log in data.get('session_logs', []))):
                doc.reference.delete()
                session_deleted += 1
                print(f"🗑️ Deleted test session log: {doc.id}")

        # Clean flash logs (on-site)
        flash_docs = firebase_db.db.collection('flash_logs').stream()
        flash_deleted = 0
        for doc in flash_docs:
            doc.reference.delete()
            flash_deleted += 1
            print(f"🗑️ Deleted flash log: {doc.id}")

        # Keep QC results as they seem to be real (no test indicators)

        print("\n✅ Firebase cleanup completed!")
        print(f"   🗂️ Session logs deleted: {session_deleted}")
        print(f"   ⚡ Flash logs deleted: {flash_deleted}")
        print("   🔵 QC results preserved")
        return True

    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False

if __name__ == "__main__":
    clean_firebase_logs()
