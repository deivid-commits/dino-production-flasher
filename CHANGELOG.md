# DinoCore Production Flasher Changelog

## [v1.2.22] - 2025-10-13
### Fixed
- Auto-update system now properly includes critical logging files (`flasher_logger.py`, `start_gui.bat`, `auto_updater_launcher.py`)
- Fixed version detection to ensure old versions (v1.2.19+) update correctly to latest
- Enhanced start_gui.bat script to ensure logging wrapper is used
- Auto-updater now restarts with guaranteed logging after updates

### Changed
- Improved fallback sequence in auto_updater_launcher.py
- Better Firebase logging initialization to prevent duplicate app errors
- Enhanced update file inclusion for comprehensive version upgrades

### Technical
- All `update_files` in updater.py now include logging-critical files
- Version forced update to v1.2.22 to trigger auto-updates from v1.2.19

## [v1.2.21] - 2025-10-12
### Added
- Guaranteed logging system with `flasher_logger.py` wrapper
- Auto-restart after updates with proper logging initialization
- Enhanced Firebase logging for all application sessions
- Comprehensive backup system before updates

### Fixed
- Firebase logging now starts immediately before GUI initialization
- No more lost logs due to application crashes
- Better error handling in update process
- Improved Bluetooth QC module integration

### Changed
- Modified startup sequence to prioritize logging
- Enhanced auto_updater_launcher.py with better update handling
- Improved version comparison logic
- Better user feedback during update process

## [v1.2.20] - 2025-10-10
### Added
- Basic Firebase integration
- Auto-updater system foundation
- Session logging started
- Initial Bluetooth QC implementation

### Technical
- Firebase-admin SDK integration
- Google Cloud Firestore setup
- Basic ESP32 flashing automation
- PySerial communication with devices

## [v1.2.19] - 2025-10-10
### Added
- Hitachi HB2X eFuse burning support
- Bluetooth LE connectivity for QC
- Basic session logging (incomplete)

### Issues
- Logging may fail on application crashes
- No guaranteed log persistence
- Firestore initialization issues

## [v1.2.0] - 2025-09-01
### Added
- Initial production flasher GUI
- ESP32 firmware flashing functionality
- Basic device control interface
- Testing firmware support
