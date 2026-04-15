"""Shirt garment model."""

from typing import Dict, Any
from .garment import Garment

class Shirt(Garment):
    """Shirt garment class."""

    def get_type(self) -> str:
        return "shirt"

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Shirt":
        shirt = Shirt(
            name=data.get("name"),
            user_id=data.get("user_id"),
            gender=data.get("gender"),
            created_at=data.get("created_at"),
            id=data.get("id") or data.get("_id"),
            display_name=data.get("display_name"),
            thumbnail_url=data.get("thumbnail_url"),
            is_custom=data.get("is_custom", False),
        )
        shirt._id = data.get("_id")
        return shirt
