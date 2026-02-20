"""Shirt garment model."""

from typing import Optional, Dict, Any
from datetime import datetime

from .garment import Garment


class Shirt(Garment):
    """Shirt garment class."""

    def get_type(self) -> str:
        return "shirt"

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Shirt":
        return Shirt(
            name=data.get("name"),
            created_by=data.get("created_by"),
            gender=data.get("gender"),
            reference=data.get("reference"),
            style=data.get("style"),
            created_at=data.get("created_at"),
        )
