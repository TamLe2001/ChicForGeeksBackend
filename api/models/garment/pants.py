"""Pants garment model."""

from typing import Dict, Any
from .garment import Garment

class Pants(Garment):
    """Pants garment class."""

    def get_type(self) -> str:
        return "pants"

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Pants":
        pants = Pants(
            name=data.get("name"),
            user_id=data.get("user_id"),
            gender=data.get("gender"),
            created_at=data.get("created_at"),
            id=data.get("id") or data.get("_id"),
            display_name=data.get("display_name"),
            is_custom=data.get("is_custom", False),
        )
        # Preserve MongoDB _id field
        pants._id = data.get("_id")
        return pants
