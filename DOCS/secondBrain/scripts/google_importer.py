"""
Google Docs Importer - Downloads Google Docs and converts them to Obsidian-compatible Markdown.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse, parse_qs

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from markdownify import markdownify as md

from config import (
    CREDENTIALS_FILE,
    TOKEN_FILE,
    OUTPUT_DIR,
    ATTACHMENTS_DIR,
    FOLDER_IDS,
    SCOPES,
    PRESERVE_FOLDER_STRUCTURE,
)


class GoogleDocsImporter:
    """Imports Google Docs from specified folders and converts to Markdown."""

    def __init__(self):
        self.creds = None
        self.drive_service = None
        self.docs_service = None
        self.imported_count = 0
        self.error_count = 0

    def authenticate(self) -> bool:
        """Authenticate with Google APIs using OAuth 2.0."""
        print("🔐 Authenticating with Google...")

        # Check for existing token
        if TOKEN_FILE.exists():
            self.creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

        # If no valid credentials, authenticate
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                print("   Refreshing expired token...")
                self.creds.refresh(Request())
            else:
                if not CREDENTIALS_FILE.exists():
                    print(f"❌ Error: credentials.json not found at {CREDENTIALS_FILE}")
                    print("   Please download OAuth credentials from Google Cloud Console")
                    return False

                print("   Opening browser for authentication...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_FILE), SCOPES
                )
                self.creds = flow.run_local_server(port=0)

            # Save token for future use
            with open(TOKEN_FILE, "w") as token:
                token.write(self.creds.to_json())
            print("   Token saved for future use")

        # Build services
        self.drive_service = build("drive", "v3", credentials=self.creds)
        self.docs_service = build("docs", "v1", credentials=self.creds)

        print("✅ Authentication successful!")
        return True

    def get_folder_name(self, folder_id: str) -> str:
        """Get the name of a folder by ID."""
        try:
            folder = self.drive_service.files().get(
                fileId=folder_id, fields="name"
            ).execute()
            return folder.get("name", folder_id)
        except Exception:
            return folder_id

    def list_docs_in_folder(
        self, folder_id: str, path_prefix: str = ""
    ) -> list[dict]:
        """Recursively list all Google Docs in a folder."""
        docs = []

        # Query for items in this folder
        query = f"'{folder_id}' in parents and trashed = false"
        page_token = None

        while True:
            response = self.drive_service.files().list(
                q=query,
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink)",
                pageToken=page_token,
                pageSize=100,
            ).execute()

            for item in response.get("files", []):
                item_path = f"{path_prefix}/{item['name']}" if path_prefix else item["name"]

                if item["mimeType"] == "application/vnd.google-apps.folder":
                    # Recurse into subfolders
                    docs.extend(self.list_docs_in_folder(item["id"], item_path))
                elif item["mimeType"] == "application/vnd.google-apps.document":
                    # It's a Google Doc
                    docs.append({
                        "id": item["id"],
                        "name": item["name"],
                        "path": item_path,
                        "modified": item.get("modifiedTime", ""),
                        "url": item.get("webViewLink", ""),
                    })

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return docs

    def export_doc_as_html(self, doc_id: str) -> str:
        """Export a Google Doc as HTML."""
        # Export as HTML to preserve formatting
        request = self.drive_service.files().export_media(
            fileId=doc_id, mimeType="text/html"
        )
        
        import io
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            _, done = downloader.next_chunk()
        
        return fh.getvalue().decode("utf-8")

    def extract_and_download_images(self, html_content: str, doc_name: str) -> str:
        """Extract images from HTML and download them locally."""
        # Find all image URLs in the HTML
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
        images = re.findall(img_pattern, html_content)

        for img_url in images:
            if not img_url.startswith("http"):
                continue

            try:
                # Generate a unique filename based on URL hash
                url_hash = hashlib.md5(img_url.encode()).hexdigest()[:12]
                ext = self._get_image_extension(img_url)
                local_filename = f"{self._sanitize_filename(doc_name)}_{url_hash}{ext}"
                local_path = ATTACHMENTS_DIR / local_filename

                # Download image if not already cached
                if not local_path.exists():
                    self._download_image(img_url, local_path)

                # Replace URL with local path (Obsidian-style)
                relative_path = f"../attachments/{local_filename}"
                html_content = html_content.replace(img_url, relative_path)

            except Exception as e:
                print(f"      Warning: Could not download image: {e}")

        return html_content

    def _get_image_extension(self, url: str) -> str:
        """Get image extension from URL."""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"]:
            if ext in path:
                return ext
        return ".png"  # Default

    def _download_image(self, url: str, local_path: Path):
        """Download an image from URL."""
        import urllib.request
        urllib.request.urlretrieve(url, str(local_path))

    def html_to_markdown(self, html_content: str) -> str:
        """Convert HTML to clean Obsidian-compatible Markdown."""
        # Use markdownify for conversion
        markdown = md(
            html_content,
            heading_style="ATX",
            bullets="-",
            strip=["script", "style", "meta", "link"],
        )

        # Clean up the markdown
        markdown = self._clean_markdown(markdown)

        return markdown

    def _clean_markdown(self, content: str) -> str:
        """Clean up converted markdown."""
        # Remove excessive blank lines
        content = re.sub(r"\n{3,}", "\n\n", content)

        # Fix heading spacing
        content = re.sub(r"(#{1,6})\s*\n+", r"\1 ", content)

        # Remove Google Docs specific cruft
        content = re.sub(r'<span[^>]*>', '', content)
        content = re.sub(r'</span>', '', content)

        # Clean up whitespace
        content = content.strip()

        return content

    def _sanitize_filename(self, name: str) -> str:
        """Convert a document name to a valid filename."""
        # Remove/replace invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(invalid_chars, "-", name)
        
        # Remove multiple dashes
        sanitized = re.sub(r"-+", "-", sanitized)
        
        # Trim and limit length
        sanitized = sanitized.strip("-").strip()[:100]
        
        return sanitized

    def create_frontmatter(self, doc: dict) -> str:
        """Create YAML frontmatter for the markdown file."""
        modified = doc.get("modified", "")
        if modified:
            # Parse ISO format and convert to date only
            try:
                dt = datetime.fromisoformat(modified.replace("Z", "+00:00"))
                modified = dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        frontmatter = [
            "---",
            f'title: "{doc["name"]}"',
            "source: google",
            f'url: "{doc.get("url", "")}"',
            f"modified: {modified}",
            "---",
            "",
        ]
        return "\n".join(frontmatter)

    def import_document(self, doc: dict, base_output_dir: Path) -> bool:
        """Import a single document."""
        try:
            print(f"   📄 {doc['name']}")

            # Determine output path
            if PRESERVE_FOLDER_STRUCTURE:
                # Use folder path from doc
                path_parts = doc["path"].split("/")
                if len(path_parts) > 1:
                    output_subdir = base_output_dir / "/".join(path_parts[:-1])
                else:
                    output_subdir = base_output_dir
            else:
                output_subdir = base_output_dir

            output_subdir.mkdir(parents=True, exist_ok=True)

            # Export as HTML
            html_content = self.export_doc_as_html(doc["id"])

            # Download images
            html_content = self.extract_and_download_images(html_content, doc["name"])

            # Convert to markdown
            markdown_content = self.html_to_markdown(html_content)

            # Add frontmatter
            frontmatter = self.create_frontmatter(doc)
            full_content = frontmatter + "\n" + markdown_content

            # Write file
            filename = self._sanitize_filename(doc["name"]) + ".md"
            output_path = output_subdir / filename

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(full_content)

            self.imported_count += 1
            return True

        except Exception as e:
            print(f"      ❌ Error: {e}")
            self.error_count += 1
            return False

    def run(self):
        """Run the full import process."""
        print("\n" + "=" * 60)
        print("Google Docs → Obsidian Importer")
        print("=" * 60 + "\n")

        # Check configuration
        if not FOLDER_IDS:
            print("❌ No folder IDs configured!")
            print("   Edit scripts/config.py and add your Google Drive folder IDs")
            return

        # Authenticate
        if not self.authenticate():
            return

        # Ensure output directories exist
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)

        # Process each folder
        for folder_id in FOLDER_IDS:
            print(f"\n📁 Processing folder: {folder_id}")
            
            try:
                folder_name = self.get_folder_name(folder_id)
                print(f"   Folder name: {folder_name}")

                # List all docs
                print("   Scanning for documents...")
                docs = self.list_docs_in_folder(folder_id)
                print(f"   Found {len(docs)} document(s)")

                if not docs:
                    continue

                # Determine output directory for this folder
                folder_output_dir = OUTPUT_DIR / self._sanitize_filename(folder_name)

                # Import each document
                print("   Importing...")
                for doc in docs:
                    self.import_document(doc, folder_output_dir)

            except Exception as e:
                print(f"   ❌ Error processing folder: {e}")
                self.error_count += 1

        # Summary
        print("\n" + "=" * 60)
        print("Import Complete!")
        print(f"   ✅ Imported: {self.imported_count} document(s)")
        if self.error_count:
            print(f"   ❌ Errors: {self.error_count}")
        print(f"   📂 Output: {OUTPUT_DIR}")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    importer = GoogleDocsImporter()
    importer.run()
