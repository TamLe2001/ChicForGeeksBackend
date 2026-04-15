"""Accessory garment model."""

from typing import Dict, Any
from .garment import Garment

class Accessory(Garment):
    """Accessory garment class."""

    def get_type(self) -> str:
        return "accessory"

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Accessory":
        accessory = Accessory(
            name=data.get("name"),
            user_id=data.get("user_id"),
            gender=data.get("gender"),
            created_at=data.get("created_at"),
            id=data.get("id") or data.get("_id"),
            display_name=data.get("display_name"),
            is_custom=data.get("is_custom", False),
        )
        accessory._id = data.get("_id")
        return accessory
