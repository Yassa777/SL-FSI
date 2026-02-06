#!/usr/bin/env python3
"""
Main entry point for the Google Docs to Obsidian importer.

Usage:
    python run_import.py

Before running:
1. Install dependencies: pip install -r requirements.txt
2. Add your credentials.json file to the scripts/ folder
3. Edit config.py and add your Google Drive folder IDs
"""

import sys
from pathlib import Path

# Ensure we can import from the scripts directory
sys.path.insert(0, str(Path(__file__).parent))

from google_importer import GoogleDocsImporter
from config import CREDENTIALS_FILE, FOLDER_IDS


def check_setup() -> bool:
    """Verify the setup is complete before running."""
    errors = []

    if not CREDENTIALS_FILE.exists():
        errors.append(
            f"Missing credentials.json at:\n"
            f"   {CREDENTIALS_FILE}\n"
            f"   Download OAuth credentials from Google Cloud Console"
        )

    if not FOLDER_IDS:
        errors.append(
            "No folder IDs configured!\n"
            "   Edit scripts/config.py and add your Google Drive folder IDs to FOLDER_IDS"
        )

    if errors:
        print("\n❌ Setup incomplete:\n")
        for i, error in enumerate(errors, 1):
            print(f"{i}. {error}\n")
        return False

    return True


def main():
    """Main entry point."""
    print("\n🧠 Second Brain - Google Docs Importer")
    print("─" * 40)

    # Check setup
    if not check_setup():
        print("Please complete the setup and try again.\n")
        sys.exit(1)

    # Run the importer
    importer = GoogleDocsImporter()
    importer.run()

    # Return appropriate exit code
    if importer.error_count > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
