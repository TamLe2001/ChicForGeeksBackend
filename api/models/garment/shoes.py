"""Shoes garment model."""

from typing import Optional, Dict, Any
from datetime import datetime

from .garment import Garment


class Shoes(Garment):
    """Shoes garment class."""

    def get_type(self) -> str:
        return "shoes"

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Shoes":
        return Shoes(
            name=data.get("name"),
            created_by=data.get("created_by"),
            gender=data.get("gender"),
            style=data.get("style"),
            reference=data.get("reference"),
            created_at=data.get("created_at"),
        )
