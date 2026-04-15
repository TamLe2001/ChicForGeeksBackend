"""Skirt garment model."""

from typing import Dict, Any

from api.models.garment.enums.gender import Gender
from .garment import Garment

class Skirt(Garment):
    """Skirt garment class."""

    def get_type(self) -> str:
        return "skirt"

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Skirt":
        skirt = Skirt(
            name=data.get("name"),
            user_id=data.get("user_id"),
            gender= Gender.FEMALE,  # Skirts are typically associated with females
            style=data.get("style"),
            created_at=data.get("created_at"),
            id=data.get("id") or data.get("_id"),
            display_name=data.get("display_name"),
            is_custom=data.get("is_custom", False),
        )
        # Preserve MongoDB _id field
        skirt._id = data.get("_id")
        return skirt
