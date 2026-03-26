



from typing import Optional


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
    
    def upload_image(self, file, filename):
        """Upload image to NextCloud and save metadata in database."""
        if not self.nextcloud_url or not self.nextcloud_user or not self.nextcloud_pass:
            return {"error": "NextCloud not configured"}, 500
        
    def upload_fbx(self, file, filename):
        """Upload FBX file to NextCloud and save metadata in database."""
        if not self.nextcloud_url or not self.nextcloud_user or not self.nextcloud_pass:
            return {"error": "NextCloud not configured"}, 500
        
    def upload_garment(self, file, filename):
        """Upload garment file to NextCloud and save metadata in database."""
        if not self.nextcloud_url or not self.nextcloud_user or not self.nextcloud_pass:
            return {"error": "NextCloud not configured"}, 500
        
    def upload_outfit(self, file, filename):
        """Upload outfit file to NextCloud and save metadata in database."""
        if not self.nextcloud_url or not self.nextcloud_user or not self.nextcloud_pass:
            return {"error": "NextCloud not configured"}, 500
        
    def get_url_image(self, filename):
        """Get public URL for an image stored in NextCloud."""
        if not self.nextcloud_url or not self.nextcloud_user or not self.nextcloud_pass:
            return {"error": "NextCloud not configured"}, 500
    
    def get_url_fbx(self, filename):
        """Get public URL for an FBX file stored in NextCloud."""
        if not self.nextcloud_url or not self.nextcloud_user or not self.nextcloud_pass:
            return {"error": "NextCloud not configured"}, 500
        
    def get_url_garment(self, filename):
        """Get public URL for a garment file stored in NextCloud."""
        if not self.nextcloud_url or not self.nextcloud_user or not self.nextcloud_pass:
            return {"error": "NextCloud not configured"}, 500
    
    def get_url_outfit(self, filename):
        """Get public URL for an outfit file stored in NextCloud."""
        if not self.nextcloud_url or not self.nextcloud_user or not self.nextcloud_pass:
            return {"error": "NextCloud not configured"}, 500