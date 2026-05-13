from datetime import datetime, timezone
from typing import Optional, Dict, Any


class Comment:
    """Comment model class."""

    def __init__(
        self,
        content: str,
        outfit_id: str,
        user_id: str,
        created_at: Optional[datetime] = None,
    ):
        self.content = content
        self.outfit_id = outfit_id
        self.user_id = user_id
        self.created_at = created_at or datetime.now(timezone.utc)
        self._id = None

    def update_content(self, new_content: str) -> None:
        self.content = new_content

    @staticmethod
    def from_doc(comment_doc: Optional[Dict[str, Any]]) -> Optional['Comment']:
        if not comment_doc:
            return None

        comment = Comment(
            content=comment_doc.get('content', ''),
            outfit_id=str(comment_doc.get('outfit_id')),
            user_id=str(comment_doc.get('user_id')),
            created_at=comment_doc.get('created_at'),
        )
        comment._id = comment_doc.get('_id')
        return comment

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self._id) if self._id else None,
            'content': self.content,
            'outfit_id': self.outfit_id,
            'user_id': self.user_id,
            'created_at': self.created_at,
        }

    def __repr__(self) -> str:
        preview = (self.content or '')[:50]
        return f"Comment(id={self._id}, user_id={self.user_id}, content={preview}..., outfit_id={self.outfit_id})"