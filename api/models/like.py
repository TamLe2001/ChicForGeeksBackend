from datetime import datetime, timezone
from typing import Optional, Dict, Any


class Like:
    """Like model class."""

    def __init__(
        self,
        outfit_id: str,
        user_id: str,
        created_at: Optional[datetime] = None,
    ):
        self.outfit_id = outfit_id
        self.user_id = user_id
        self.created_at = created_at or datetime.now(timezone.utc)
        self._id = None

    @staticmethod
    def from_doc(like_doc: Optional[Dict[str, Any]]) -> Optional['Like']:
        if not like_doc:
            return None

        like = Like(
            outfit_id=str(like_doc.get('outfit_id')),
            user_id=str(like_doc.get('user_id')),
            created_at=like_doc.get('created_at'),
        )
        like._id = like_doc.get('_id')
        return like

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self._id) if self._id else None,
            'outfit_id': self.outfit_id,
            'user_id': self.user_id,
            'created_at': self.created_at,
        }

    def __repr__(self) -> str:
        return f"Like(id={self._id}, outfit_id={self.outfit_id}, user_id={self.user_id})"