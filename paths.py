"""
Central user-data paths for Arch-Ive.
All writable data (config, logs) goes to %APPDATA%\Arch-Ive so the app
works correctly when installed in Program Files (read-only for normal users).
"""
import os
from pathlib import Path

APP_DATA_DIR = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "Arch-Ive"
LOGS_DIR = APP_DATA_DIR / "logs"
CONFIG_FILE = APP_DATA_DIR / "config.json"
BACKUP_HISTORY_FILE = LOGS_DIR / "backup_history.json"

# Ensure directories exist on import
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
