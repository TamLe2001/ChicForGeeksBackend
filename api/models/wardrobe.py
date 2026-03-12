from datetime import datetime, timezone
from typing import Optional, Dict, Any, List


class Wardrobe:
    """Wardrobe model class."""

    def __init__(
        self,
        user_id: str,
        outfit_ids: Optional[List[str]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.user_id = user_id
        self.outfit_ids = outfit_ids or []
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or self.created_at
        self._id = None

    @staticmethod
    def from_payload(payload: Optional[Dict[str, Any]]) -> 'Wardrobe':
        """Create Wardrobe instance from API payload."""
        if payload is None:
            payload = {}

        return Wardrobe(
            user_id=payload.get('user_id'),
            outfit_ids=payload.get('outfit_ids') or [],
            created_at=payload.get('created_at'),
            updated_at=payload.get('updated_at'),
        )

    @staticmethod
    def from_doc(wardrobe_doc: Optional[Dict[str, Any]]) -> Optional['Wardrobe']:
        """Create Wardrobe instance from database document."""
        if not wardrobe_doc:
            return None

        wardrobe = Wardrobe(
            user_id=str(wardrobe_doc.get('user_id')),
            outfit_ids=[str(oid) for oid in (wardrobe_doc.get('outfit_ids') or [])],
            created_at=wardrobe_doc.get('created_at'),
            updated_at=wardrobe_doc.get('updated_at'),
        )
        wardrobe._id = wardrobe_doc.get('_id')
        return wardrobe

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': str(self._id) if self._id else None,
            'user_id': self.user_id,
            'outfit_ids': self.outfit_ids,
            'outfit_count': len(self.outfit_ids),
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }
