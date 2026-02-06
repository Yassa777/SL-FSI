"""
Configuration for Google Docs to Obsidian importer.

Instructions:
1. Go to https://console.cloud.google.com
2. Create a new project (or select existing)
3. Enable "Google Drive API" and "Google Docs API"
4. Go to Credentials > Create Credentials > OAuth 2.0 Client ID
5. Choose "Desktop app" as application type
6. Download the JSON file and save it as 'credentials.json' in the scripts/ folder
7. Add your folder IDs below
"""

import os
from pathlib import Path

# Base paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Google OAuth credentials file (download from Google Cloud Console)
CREDENTIALS_FILE = SCRIPT_DIR / "credentials.json"

# Token file (auto-generated after first auth)
TOKEN_FILE = SCRIPT_DIR / "token.json"

# Output directories
OUTPUT_DIR = PROJECT_ROOT / "Google"
ATTACHMENTS_DIR = PROJECT_ROOT / "attachments"

# =============================================================================
# ADD YOUR GOOGLE DRIVE FOLDER IDs HERE
# =============================================================================
# To find a folder ID:
# 1. Open the folder in Google Drive
# 2. Look at the URL: https://drive.google.com/drive/folders/{FOLDER_ID}
# 3. Copy the {FOLDER_ID} part

FOLDER_IDS = [
    # "1ABC123xyz...",  # Example: My Notes folder
    # "2DEF456abc...",  # Example: Work Documents folder
]

# =============================================================================
# Optional Settings
# =============================================================================

# Whether to preserve folder hierarchy from Google Drive
PRESERVE_FOLDER_STRUCTURE = True

# File extensions to include (Google Docs are always included)
# Set to None to only import Google Docs
INCLUDE_FILE_TYPES = None  # or ["pdf", "docx", "txt"]

# OAuth scopes (don't change unless you know what you're doing)
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/documents.readonly",
]
