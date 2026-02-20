from datetime import datetime, timezone
from typing import Optional, Dict, Any

class Follow:
    def __init__(self, follower_id: str, followed_id: str, created_at: Optional[datetime] = None):
        self.follower_id = follower_id
        self.followed_id = followed_id
        self.created_at = created_at or datetime.now(timezone.utc)
        self._id = None  # Set by database

    @staticmethod
    def from_payload(payload: Optional[Dict[str, Any]]) -> 'Follow':
        """Create Follow instance from API payload."""
        if payload is None:
            payload = {}
        
        return Follow(
            follower_id=payload.get('follower_id'),
            followed_id=payload.get('followed_id'),
            created_at=payload.get('created_at'),
        )

    @staticmethod
    def from_doc(follow_doc: Optional[Dict[str, Any]]) -> Optional['Follow']:
        """Create Follow instance from database document."""
        if not follow_doc:
            return None
        
        follow = Follow(
            follower_id=follow_doc.get('follower_id'),
            followed_id=follow_doc.get('followed_id'),
            created_at=follow_doc.get('created_at'),
        )
        follow._id = follow_doc.get('_id')
        return follow

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': str(self._id) if self._id else None,
            'follower_id': self.follower_id,
            'followed_id': self.followed_id,
            'created_at': self.created_at,
        }