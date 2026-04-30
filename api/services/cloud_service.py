from datetime import datetime
from io import BytesIO
from typing import Optional, Tuple, Dict, Any

import requests
from PIL import Image
from requests.auth import HTTPBasicAuth
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId

from api.models.garment.garment import Garment
from api.models.image import Image as ImageType


DEFAULT_UPLOAD_TIMEOUT = 30
DEFAULT_FOLDER_TIMEOUT = 10
DEFAULT_MAX_FILE_SIZE = 100 * 1024 * 1024
VALID_GARMENT_CATEGORIES = {'shirt', 'pants', 'skirt', 'accessory'}


class CloudService:
    """Service for managing file in cloud storage."""

    def __init__(self, db, config):
        """
        Initialize CloudService.
        
        Args:
            db: MongoDB database instance
            config: Flask configuration object
        """
        self.db = db
        self.config = config
        self.nextcloud_url = self._normalize_base_url(config.get('NEXTCLOUD_URL'))
        self.nextcloud_user = config.get('NEXTCLOUD_USER')
        self.nextcloud_pass = config.get('NEXTCLOUD_PASS')
        self.max_file_size = config.get('MAX_FILE_SIZE', DEFAULT_MAX_FILE_SIZE)

    @staticmethod
    def _normalize_base_url(url: Optional[str]) -> Optional[str]:
        """Ensure base URL ends with a slash for safe joining."""
        if not url:
            return None

        return url if url.endswith('/') else f"{url}/"

    @staticmethod
    def _get_file_stream(file):
        """Normalize supported file payloads to a stream-like object."""
        if isinstance(file, dict):
            return file.get("stream")
        return getattr(file, "stream", file)

    @staticmethod
    def _get_content_type(file):
        """Normalize supported file payloads to a content type string."""
        if isinstance(file, dict):
            return file.get("content_type") or "application/octet-stream"
        return getattr(file, "content_type", None) or "application/octet-stream"

    @staticmethod
    def _get_content_length(file):
        """Normalize supported file payloads to a content length integer."""
        if isinstance(file, dict):
            return file.get("content_length") or 0
        return getattr(file, "content_length", None) or 0

    def _build_upload_url(self, folder: str, filename: str) -> str:
        """Build a safe NextCloud upload URL for a folder and filename."""
        return f"{self.nextcloud_url}{folder.strip('/')}/{secure_filename(filename or '')}"
    
    def _nextcloud_configured(self) -> tuple[bool, Optional[dict], Optional[int]]:
        """Check if NextCloud is properly configured.
        Returns (True, None, None) if configured, else (False, error_dict, status_code)
        """
        missing = []
        if not self.nextcloud_url:
            missing.append("NEXTCLOUD_URL")
        if not self.nextcloud_user:
            missing.append("NEXTCLOUD_USER") 
        if not self.nextcloud_pass:
            missing.append("NEXTCLOUD_PASS")
        if missing:
            return False, {"error": f"NextCloud not configured: missing {', '.join(missing)}"}, 500
        return True, None, None

    def _ensure_remote_folder(self, folder: str) -> tuple[bool, Optional[dict], Optional[int]]:
        """Create NextCloud folder tree if it does not exist."""
        folder = folder.strip("/")
        if not folder:
            return True, None, None

        current_path = ""
        for part in folder.split("/"):
            current_path = f"{current_path}/{part}" if current_path else part
            folder_url = f"{self.nextcloud_url}{current_path}/"
            response = requests.request(
                "MKCOL",
                folder_url,
                auth=HTTPBasicAuth(self.nextcloud_user, self.nextcloud_pass),
                timeout=DEFAULT_FOLDER_TIMEOUT,
            )

            if response.status_code not in (201, 405):
                return (
                    False,
                    {"error": f"Failed to create cloud folder '{current_path}': {response.status_code}"},
                    500,
                )

        return True, None, None

    def _upload_to_folder(self, file, filename: str, folder: str, file_type: str):
        """Upload a file object to a specific NextCloud folder and persist metadata."""
        ok, err, code = self._nextcloud_configured()
        if not ok:
            return err, code

        safe_filename = secure_filename(filename or "")
        if not safe_filename:
            return {"error": "Invalid filename"}, 400

        ok, err, code = self._ensure_remote_folder(folder)
        if not ok:
            return err, code

        upload_url = self._build_upload_url(folder, safe_filename)
        content_type = self._get_content_type(file)
        stream = self._get_file_stream(file)
        content_length = self._get_content_length(file)

        if stream is None:
            return {"error": "Invalid file payload"}, 400

        if hasattr(stream, "seek"):
            stream.seek(0)

        response = requests.put(
            upload_url,
            data=stream,
            auth=HTTPBasicAuth(self.nextcloud_user, self.nextcloud_pass),
            headers={"Content-Type": content_type},
            timeout=DEFAULT_UPLOAD_TIMEOUT,
        )

        if response.status_code not in (201, 204):
            return {
                "error": f"NextCloud error: {response.status_code}",
                "details": response.text,
            }, 500

        file_doc = {
            "filename": safe_filename,
            "url": upload_url,
            "size": content_length,
            "content_type": content_type,
            "uploaded_at": datetime.utcnow(),
            "file_type": file_type,
            "folder": folder.strip("/"),
        }
        result = self.db.files.insert_one(file_doc)

        return {
            "status": "success",
            "message": f"{file_type.capitalize()} uploaded successfully",
            "file_id": str(result.inserted_id),
            "filename": safe_filename,
            "cloud_url": upload_url,
            "file_type": file_type,
        }, 201
    
    def _image_handler(self, file, filename: str):
        """Convert any supported image file to JPG and return a stream payload."""
        safe_base = secure_filename((filename or "image").rsplit(".", 1)[0]) or "image"
        output_filename = f"{safe_base}.jpg"

        stream = self._get_file_stream(file)
        if hasattr(stream, "seek"):
            stream.seek(0)

        original_filename = (getattr(file, "filename", "") or "").lower()
        original_mime = (getattr(file, "content_type", "") or "").lower()
        is_jpeg = original_filename.endswith((".jpg", ".jpeg")) or original_mime == "image/jpeg"

        if is_jpeg:
            payload = {
                "stream": stream,
                "content_type": "image/jpeg",
                "content_length": self._get_content_length(file),
            }
            return payload, output_filename, None, None

        try:
            with Image.open(stream) as image:
                rgb_image = image.convert("RGB")
                out_buffer = BytesIO()
                rgb_image.save(out_buffer, format="JPEG", quality=90, optimize=True)
                out_buffer.seek(0)
        except Exception:
            return None, None, {"error": "Invalid or unsupported image file"}, 400

        payload = {
            "stream": out_buffer,
            "content_type": "image/jpeg",
            "content_length": len(out_buffer.getvalue()),
        }
        return payload, output_filename, None, None
     

    def upload_image_profile(self, file, user_id):
        """Upload image to NextCloud and save metadata in database."""
        payload, jpg_filename, err, code = self._image_handler(file, f"{user_id}.jpg")
        if err:
            return err, code
        return self._upload_to_folder(payload, jpg_filename, "profile_pictures", ImageType.PROFILE.value)
        
    def upload_image_custom(self, file, filename):
        """Upload image to NextCloud and save metadata in database."""
        payload, jpg_filename, err, code = self._image_handler(file, filename)
        if err:
            return err, code
        return self._upload_to_folder(payload, jpg_filename, "images", ImageType.CUSTOM.value)
        
    def upload_glb(self, file, filename):
        """Upload GLB file to NextCloud and save metadata in database."""
        return self._upload_to_folder(file, filename, "customs", "glb")
    
    def upload_model(self, file, filename: str, user_id: str, category: str) -> Tuple[Dict[str, Any], int]:
        """Upload model file with category validation for garments.
        
        Args:
            file: File object to upload
            filename: Name of the file
            user_id: User ID for folder organization
            category: Garment category (shirt, pants, skirt, accessory)
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        # Validate file extension
        safe_filename = secure_filename(filename or "")
        if not safe_filename:
            return {"error": "Invalid filename"}, 400
        
        if not safe_filename.lower().endswith(('.glb', '.gltf')):
            return {"error": "Only GLB/GLTF files allowed"}, 400
        
        # Validate file size
        content_length = self._get_content_length(file)
        if content_length > self.max_file_size:
            return {"error": f"File too large (max {self.max_file_size // (1024*1024)}MB)"}, 413
        
        # Validate category
        if category.lower() not in VALID_GARMENT_CATEGORIES:
            valid = ', '.join(sorted(VALID_GARMENT_CATEGORIES))
            return {"error": f"Invalid category. Must be one of: {valid}"}, 400
        
        # Upload to folder: garments/{user_id}/{category}/
        folder = f"garments/{user_id}/{category.lower()}"
        return self._upload_to_folder(file, safe_filename, folder, "model")
    
    def delete_file(self, file_id: str) -> Tuple[Dict[str, Any], int]:
        """Delete a file from cloud storage and database.
        
        Args:
            file_id: MongoDB file document ID
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            file_doc = self.db.files.find_one({'_id': ObjectId(file_id)})
            if not file_doc:
                return {"error": "File not found"}, 404
            
            ok, err, code = self._nextcloud_configured()
            if not ok:
                return err, code
            
            # Delete from NextCloud
            response = requests.delete(
                file_doc['url'],
                auth=HTTPBasicAuth(self.nextcloud_user, self.nextcloud_pass),
                timeout=DEFAULT_UPLOAD_TIMEOUT
            )
            
            if response.status_code not in (204, 200):
                return {"error": f"Failed to delete from NextCloud: {response.status_code}"}, 500
            
            # Delete from MongoDB
            self.db.files.delete_one({'_id': ObjectId(file_id)})
            return {"status": "success", "message": "File deleted successfully"}, 200
        except Exception as e:
            return {"error": f"Failed to delete file: {str(e)}"}, 500
        
    def get_url_image_profile(self, user_id):
        """Get public URL for an image stored in NextCloud."""
        ok, err, code = self._nextcloud_configured()
        if not ok:
            return err, code
        return f"{self.nextcloud_url}profile_pictures/{user_id}.jpg"
    
    def get_url_custom(self, user_id, filename):
        """Get public URL for an image stored in NextCloud."""
        ok, err, code = self._nextcloud_configured()
        if not ok:
            return err, code
        return f"{self.nextcloud_url}images/{user_id}/{filename}"
    
    def get_url_garment_default(self, garment_name):
        """Get public URL for a garment file stored in NextCloud."""
        ok, err, code = self._nextcloud_configured()
        if not ok:
            return err, code
        
        return f"{self.nextcloud_url}default/{garment_name}"
    
    def get_url_garment_user(self, garment: Garment):
        """Get public URL for a garment file stored in NextCloud."""
        ok, err, code = self._nextcloud_configured()
        if not ok:
            return err, code
        
        return f"{self.nextcloud_url}garments/{garment.get_type()}/{garment.id}"
      
