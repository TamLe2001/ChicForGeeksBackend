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
            id= data.get("id"),    
            name=data.get("name"),
            user_id=data.get("user_id"),
            gender=data.get("gender"),
            reference=data.get("reference"),
            style=data.get("style"),
            created_at=data.get("created_at"),
        )
        # Preserve MongoDB _id field
        shirt._id = data.get("_id")
        return shirt
