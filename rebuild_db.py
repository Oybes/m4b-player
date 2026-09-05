#!/usr/bin/env python3
"""
M4B Player Database Rebuilder & Reset Tool
-----------------------------------------
Clears all indexed audiobooks, listening progress, and cached cover art,
giving you a completely fresh start while keeping user accounts and server
configurations intact.

Usage:
    python rebuild_db.py            # Rebuilds and rescans configured audiobooks folder
    python rebuild_db.py --no-rescan # Clears database only without rescanning
"""

import os
import sys
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import database
import scanner
import config

def main():
    parser = argparse.ArgumentParser(description="Rebuild M4B Player Audiobook Database")
    parser.add_argument(
        "--no-rescan",
        action="store_true",
        help="Clear database and cover caches without rescanning audiobooks"
    )
    args = parser.parse_args()

    print("[Rebuild DB] Initializing database connection...")
    database.init_db()

    print("[Rebuild DB] Clearing audiobooks and listening progress...")
    database.rebuild_audiobooks_database()

    print("[Rebuild DB] Cleaning cached cover images...")
    removed_covers = scanner.clean_covers()
    print(f"[Rebuild DB] Purged {removed_covers} cached cover files.")

    if not args.no_rescan:
        cfg = config.load_config()
        audiobooks_dir = os.getenv("AUDIOBOOKS_DIR") or cfg.get("audiobooks_dir", "audiobooks")
        books_path = Path(audiobooks_dir)
        if not books_path.is_absolute():
            books_path = BASE_DIR / books_path
            
        print(f"[Rebuild DB] Rescanning audiobooks from: {books_path}")
        indexed = scanner.scan_directory(books_path)
        print(f"[Rebuild DB] Rescan complete! Indexed {indexed} audiobooks.")
    else:
        print("[Rebuild DB] Skipped rescan (--no-rescan specified).")

    print("[Rebuild DB] Database rebuild finished successfully!")

if __name__ == "__main__":
    main()
