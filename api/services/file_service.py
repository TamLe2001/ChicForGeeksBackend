"""File service for handling file operations, uploads, and default files management."""

import os
import requests
import zipfile
from io import BytesIO
from datetime import datetime
from typing import Optional


class FileService:
    """Service for managing file operations including default file downloads."""

    def __init__(self, db, config):
        """
        Initialize FileService.
        
        Args:
            db: MongoDB database instance
            config: Flask configuration object
        """
        self.db = db
        self.config = config
        self.nextcloud_url = self._normalize_base_url(config.get('NEXTCLOUD_URL'))
        self.nextcloud_user = config.get('NEXTCLOUD_USER')
        self.nextcloud_pass = config.get('NEXTCLOUD_PASS')

    @staticmethod
    def _normalize_base_url(url: Optional[str]) -> Optional[str]:
        """Ensure base URL ends with a slash for safe joining."""
        if not url:
            return None
			
        return url if url.endswith('/') else f"{url}/"

    def download_default_files(self, uploads_base_path: str) -> None:
        """
        Download default files from NextCloud storage on startup.
        
        Args:
            uploads_base_path: Base path for uploads directory
        """
        if not self.nextcloud_url:
            print("NEXTCLOUD_URL not configured, skipping default files download")
            return

        # Check if default files already exist in database
        if self._default_files_exist():
            print("Default files already loaded")
            return

        default_files_url = f"{self.nextcloud_url}default/?accept=zip"
        default_dir = os.path.join(uploads_base_path, 'default')

        try:
            self._ensure_directory(default_dir)
            self._download_and_extract_files(default_files_url, default_dir)
            self._register_files_in_database(default_dir)
            print("Successfully downloaded and registered default files")
        except Exception as e:
            print(f"Error downloading default files: {e}")

    def _default_files_exist(self) -> bool:
        """Check if default files are already registered in database."""
        count = self.db.files.count_documents({"category": "default"})
        if count > 0:
            print(f"Default files already loaded ({count} files)")
            return True
        return False

    def _ensure_directory(self, directory_path: str) -> None:
        """Create directory if it doesn't exist."""
        os.makedirs(directory_path, exist_ok=True)

    def _download_and_extract_files(self, url: str, target_dir: str) -> None:
        """
        Download and extract zip file from URL.
        
        Args:
            url: URL to download zip file from
            target_dir: Directory to extract files to
        """
        auth = None
        if self.nextcloud_user and self.nextcloud_pass:
            auth = (self.nextcloud_user, self.nextcloud_pass)

        response = requests.get(url, timeout=30, auth=auth)
        response.raise_for_status()

        with zipfile.ZipFile(BytesIO(response.content)) as zip_file:
            zip_file.extractall(target_dir)

    def _register_files_in_database(self, default_dir: str) -> None:
        """
        Register extracted files in MongoDB database.
        
        Args:
            default_dir: Directory containing extracted files
        """
        model_extensions = {'.glb', '.gltf'}

        for root, _, filenames in os.walk(default_dir):
            for filename in filenames:
                if any(filename.endswith(ext) for ext in model_extensions):
                    filepath = os.path.join(root, filename)
                    relative_path = os.path.relpath(filepath, default_dir)

                    file_doc = {
                        "filename": filename,
                        "filepath": os.path.join('default', relative_path),
                        "user_id": "system",
                        "category": "default",
                        "upload_date": datetime.now(),
                        "file_size": os.path.getsize(filepath)
                    }
                    self.db.files.insert_one(file_doc)
