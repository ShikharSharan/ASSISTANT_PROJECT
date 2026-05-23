"""
app/uninstall.py
-----------------
Phase 4 — Uninstall / reinstall cleanup utilities.

Called by:
  * The uninstaller script / setup.py uninstall hook
  * main.py on first-run if stale app data is detected
    (e.g. reinstalled without running the uninstaller)

Usage from CLI:
    python -m app.uninstall --wipe
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def wipe_app_data(app_data_dir: Path, *, confirm: bool = False) -> None:
    """
    Permanently delete the app data directory.
    Requires confirm=True as a safeguard against accidental calls.
    """
    if not confirm:
        raise RuntimeError("wipe_app_data called without confirm=True — aborting.")
    if app_data_dir.exists():
        shutil.rmtree(app_data_dir, ignore_errors=True)
        print(f"[uninstall] Removed app data directory: {app_data_dir}")
    else:
        print(f"[uninstall] App data directory not found (already clean): {app_data_dir}")


def is_stale_install(setup_marker: Path, credentials_file: Path) -> bool:
    """
    Returns True if there is leftover data from a previous install
    that did NOT complete its own setup (i.e. partial/corrupt state).

    Heuristic: credentials file exists but setup marker is missing,
    or vice versa — meaning a previous install was partially wiped.
    """
    marker_exists = setup_marker.exists()
    creds_exists = credentials_file.exists()
    return marker_exists != creds_exists  # XOR — one exists without the other


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AssistantApp uninstall / data wipe utility")
    parser.add_argument("--wipe", action="store_true", help="Delete all app data from this machine")
    args = parser.parse_args()

    if args.wipe:
        # Import here to avoid circular import at top-level
        from config import APP_DATA_DIR  # noqa: E402
        print(f"WARNING: This will permanently delete all data in: {APP_DATA_DIR}")
        confirm = input("Type 'yes' to confirm: ")
        if confirm.strip().lower() == "yes":
            wipe_app_data(APP_DATA_DIR, confirm=True)
            print("Wipe complete.")
        else:
            print("Aborted.")
            sys.exit(1)
    else:
        parser.print_help()
