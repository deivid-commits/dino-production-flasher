#!/usr/bin/env python3
"""
DinoCore Production Flasher Auto-Updater Launcher
Automatically checks and applies updates before launching the GUI
"""

import os
import sys
import subprocess

def main():
    """Main auto-updater launcher function"""
    print("🦕 DinoCore Production Flasher")
    print("🔄 Checking for updates...")

    try:
        # Check for updates
        result = subprocess.run([
            sys.executable, 'updater.py', 'check'
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))

        if result.returncode == 0:
            # No updates available, continue to launch app
            print("✅ You are up to date!")
            print("🚀 Starting application...")
        else:
            # Updates found - apply them automatically
            print("📦 Updates found! Installing automatically...")
            print("This may take a moment...")

            update_result = subprocess.run([
                sys.executable, 'updater.py', 'update', '--yes'
            ], cwd=os.path.dirname(__file__))

            if update_result.returncode != 0:
                print("⚠️  Update failed, but continuing to launch application...")
                print("   You can manually update later with: python updater.py update")
            else:
                print("✅ Updates installed successfully!")
                print("🔄 Application updated! restarting with logging wrapper...")

                # Restart the application with the new logging wrapper
                import time
                print("⏳ Waiting 2 seconds for files to settle...")
                time.sleep(2)

                print("🔄 Starting updated application with logging...")
                try:
                    # Launch the new logging wrapper
                    subprocess.run([sys.executable, 'flasher_logger.py'], cwd=os.path.dirname(__file__))
                    print("✅ Application restarted successfully with logging wrapper!")
                except Exception as e:
                    print(f"⚠️  Could not restart with logging wrapper: {e}")
                    print("🚀 Starting standard application...")
                return  # Exit after successful update + restart

            print("🚀 Starting application...")

    except Exception as e:
        print(f"⚠️  Could not check for updates: {e}")
        print("🚀 Starting application (update check skipped)...")

    # Always launch the logging wrapper (unified execution path)
    print("✅ Update process completed!")
    print("🚀 Starting application with logging...")

    try:
        subprocess.run([sys.executable, 'flasher_logger.py'], cwd=os.path.dirname(__file__))
    except Exception as e:
        print(f"❌ Could not start application: {e}")
        print("🚀 Please run manually: python flasher_logger.py")

if __name__ == "__main__":
    main()
