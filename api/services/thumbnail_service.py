"""Service for generating and managing outfit thumbnails."""

import os
import base64
from datetime import datetime, timezone
from typing import Optional


class ThumbnailService:
    """Service for managing outfit thumbnails."""

    def __init__(self, db, uploads_base_path: str):
        """
        Initialize ThumbnailService.
        
        Args:
            db: MongoDB database instance
            uploads_base_path: Base path for uploads directory
        """
        self.db = db
        self.uploads_base_path = uploads_base_path
        self.thumbnails_dir = os.path.join(uploads_base_path, 'thumbnails')
        self._ensure_directory(self.thumbnails_dir)

    @staticmethod
    def _ensure_directory(directory_path: str) -> None:
        """Create directory if it doesn't exist."""
        os.makedirs(directory_path, exist_ok=True)

    def generate_thumbnail(
        self,
        outfit_id: str,
        thumbnail_data: str,
        outfit_name: str
    ) -> str:
        """
        Save outfit thumbnail received from frontend and store in database.
        
        Args:
            outfit_id: ID of the outfit
            thumbnail_data: Base64 encoded thumbnail image from frontend PNG/data URL
            outfit_name: Name of the outfit for file naming
            
        Returns:
            Thumbnail URL path for the outfit
        """
        try:
            # Extract base64 data if it comes with data URI prefix
            if isinstance(thumbnail_data, str) and thumbnail_data.startswith('data:'):
                # Extract the base64 part after the comma
                thumbnail_data = thumbnail_data.split(',')[1]
            
            # Generate filename
            thumbnail_filename = f"{outfit_id}_thumbnail.png"
            thumbnail_path = os.path.join(self.thumbnails_dir, thumbnail_filename)
            
            # Decode and save thumbnail file
            thumbnail_bytes = base64.b64decode(thumbnail_data)
            with open(thumbnail_path, 'wb') as f:
                f.write(thumbnail_bytes)
            
            # Save thumbnail reference in database
            self.db.outfit_thumbnails.update_one(
                {'outfit_id': outfit_id},
                {
                    '$set': {
                        'outfit_id': outfit_id,
                        'filename': thumbnail_filename,
                        'outfit_name': outfit_name,
                        'updated_at': datetime.now(timezone.utc),
                    },
                    '$setOnInsert': {
                        'created_at': datetime.now(timezone.utc),
                    }
                },
                upsert=True
            )
            
            # Return the URL path to access the thumbnail
            return f"/api/outfits/{outfit_id}/thumbnail"
            
        except Exception as e:
            raise Exception(f"Failed to generate thumbnail: {str(e)}")

    def get_thumbnail(self, outfit_id: str) -> Optional[bytes]:
        """
        Retrieve thumbnail image bytes for an outfit.
        
        Args:
            outfit_id: ID of the outfit
            
        Returns:
            Image bytes or None if not found
        """
        try:
            # Find thumbnail reference in database
            thumb_doc = self.db.outfit_thumbnails.find_one({'outfit_id': outfit_id})
            if not thumb_doc:
                return None
            
            filename = thumb_doc.get('filename')
            thumbnail_path = os.path.join(self.thumbnails_dir, filename)
            
            # Read and return thumbnail file
            if os.path.exists(thumbnail_path):
                with open(thumbnail_path, 'rb') as f:
                    return f.read()
            
            return None
            
        except Exception as e:
            print(f"Error retrieving thumbnail: {str(e)}")
            return None

    def delete_thumbnail(self, outfit_id: str) -> bool:
        """
        Delete thumbnail for an outfit.
        
        Args:
            outfit_id: ID of the outfit
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            thumb_doc = self.db.outfit_thumbnails.find_one({'outfit_id': outfit_id})
            if not thumb_doc:
                return False
            
            filename = thumb_doc.get('filename')
            thumbnail_path = os.path.join(self.thumbnails_dir, filename)
            
            # Delete file
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
            
            # Delete database reference
            self.db.outfit_thumbnails.delete_one({'outfit_id': outfit_id})
            
            return True
            
        except Exception as e:
            print(f"Error deleting thumbnail: {str(e)}")
            return False

    def thumbnail_exists(self, outfit_id: str) -> bool:
        """Check if thumbnail exists for an outfit."""
        return self.db.outfit_thumbnails.count_documents({'outfit_id': outfit_id}) > 0
