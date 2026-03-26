from typing import Optional

from api.models.garment.garment import Garment

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
     

    def upload_image(self, file, filename):
        """Upload image to NextCloud and save metadata in database."""
        ok, err, code = self._nextcloud_configured()
        if not ok:
            return err, code
        
    def upload_fbx(self, file, filename):
        """Upload FBX file to NextCloud and save metadata in database."""
        ok, err, code = self._nextcloud_configured()
        if not ok:
            return err, code
        
    def upload_garment(self, file, filename):
        """Upload garment file to NextCloud and save metadata in database."""
        ok, err, code = self._nextcloud_configured()
        if not ok:
            return err, code
        
    def upload_outfit(self, file, filename):
        """Upload outfit file to NextCloud and save metadata in database."""
        ok, err, code = self._nextcloud_configured()
        if not ok:
            return err, code
        
    def get_url_image(self, filename):
        """Get public URL for an image stored in NextCloud."""
        ok, err, code = self._nextcloud_configured()
        if not ok:
            return err, code
    
    def get_url_fbx(self, filename):
        """Get public URL for an FBX file stored in NextCloud."""
        ok, err, code = self._nextcloud_configured()
        if not ok:
            return err, code
        
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
      

    def get_url_outfit(self, filename):
        """Get public URL for an outfit file stored in NextCloud."""
        ok, err, code = self._nextcloud_configured()
        if not ok:
            return err, code