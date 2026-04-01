from datetime import datetime
from io import BytesIO
from typing import Optional

import requests
from PIL import Image
from requests.auth import HTTPBasicAuth
from werkzeug.utils import secure_filename

from api.models.garment.garment import Garment
from api.models.image import Image as ImageType

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


    @staticmethod
    def _normalize_base_url(url: Optional[str]) -> Optional[str]:
        """Ensure base URL ends with a slash for safe joining."""
        if not url:
            return None
			
        return url if url.endswith('/') else f"{url}/"
    
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
                timeout=10,
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

        upload_url = f"{self.nextcloud_url}{folder.strip('/')}/{safe_filename}"

        # Support both Werkzeug FileStorage objects and normalized dict payloads.
        if isinstance(file, dict):
            content_type = file.get("content_type") or "application/octet-stream"
            stream = file.get("stream")
            content_length = file.get("content_length") or 0
        else:
            content_type = getattr(file, "content_type", None) or "application/octet-stream"
            stream = getattr(file, "stream", file)
            content_length = getattr(file, "content_length", None) or 0

        if stream is None:
            return {"error": "Invalid file payload"}, 400

        if hasattr(stream, "seek"):
            stream.seek(0)

        response = requests.put(
            upload_url,
            data=stream,
            auth=HTTPBasicAuth(self.nextcloud_user, self.nextcloud_pass),
            headers={"Content-Type": content_type},
            timeout=30,
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

        stream = getattr(file, "stream", file)
        if hasattr(stream, "seek"):
            stream.seek(0)

        original_filename = (getattr(file, "filename", "") or "").lower()
        original_mime = (getattr(file, "content_type", "") or "").lower()
        is_jpeg = original_filename.endswith((".jpg", ".jpeg")) or original_mime == "image/jpeg"

        if is_jpeg:
            payload = {
                "stream": stream,
                "content_type": "image/jpeg",
                "content_length": getattr(file, "content_length", None) or 0,
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
        
    def upload_fbx(self, file, filename):
        """Upload FBX file to NextCloud and save metadata in database."""
        return self._upload_to_folder(file, filename, "fbx", "fbx")
        
    def upload_garment(self, file, filename):
        """Upload garment file to NextCloud and save metadata in database."""
        return self._upload_to_folder(file, filename, "garments", "garment")
        
    def upload_outfit(self, file, filename):
        """Upload outfit file to NextCloud and save metadata in database."""
        return self._upload_to_folder(file, filename, "outfits", "outfit")
        
    def get_url_image_profile(self, user_id):
        """Get public URL for an image stored in NextCloud."""
        ok, err, code = self._nextcloud_configured()
        if not ok:
            return err, code
        return f"{self.nextcloud_url}profile_pictures/{user_id}/profile.jpg"

    def get_url_fbx(self, filename):
        """Get public URL for an FBX file stored in NextCloud."""
        ok, err, code = self._nextcloud_configured()
        if not ok:
            return err, code
        return f"{self.nextcloud_url}fbx/{filename}"
    
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
      
