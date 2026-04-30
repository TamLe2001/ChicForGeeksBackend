"""File service for handling file operations, uploads, and default files management."""

import os
from datetime import datetime
from typing import Optional
from flask import current_app


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

    @property
    def cloud(self):
        """Resolve cloud service from the active app context when needed."""
        return getattr(current_app, 'cloud_service', None)

    @staticmethod
    def _normalize_base_url(url: Optional[str]) -> Optional[str]:
        """Ensure base URL ends with a slash for safe joining."""
        if not url:
            return None
			
        return url if url.endswith('/') else f"{url}/"

    def download_default_files(self, uploads_base_path: str) -> None:
        """
        Register default files in MongoDB if not already present. 
        Args:
            uploads_base_path: Base path for uploads directory
        """
        if not self.cloud:
            print("Cloud service not configured, skipping default files registration")
            return

        # Check if default files already exist in database
        if self._default_files_exist():
            print("Default files already loaded")
            return

        default_dir = os.path.join(uploads_base_path, 'default')
        try:
            self._ensure_directory(default_dir)
            self._register_files_in_database(default_dir)
            print("Successfully registered default files")
        except Exception as e:
            print(f"Error registering default files: {e}")

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

    # _download_and_extract_files removed (zip download not needed)

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
