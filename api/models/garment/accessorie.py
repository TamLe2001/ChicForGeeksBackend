"""Accessories garment model."""

from typing import Dict, Any
from .garment import Garment

class Accessorie(Garment):
    """Accessories garment class."""

    def get_type(self) -> str:
        return "accessories"

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Accessorie":
        return Accessorie(
            name=data.get("name"),
            user_id=data.get("user_id"),
            gender=data.get("gender"),
            style=data.get("style"),
            reference=data.get("reference"),
            created_at=data.get("created_at"),
        )
