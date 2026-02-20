"""Pants garment model."""

from typing import Optional, Dict, Any
from datetime import datetime

from .garment import Garment


class Pants(Garment):
    """Pants garment class."""

    def get_type(self) -> str:
        return "pants"

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Pants":
        return Pants(
            name=data.get("name"),
            user_id=data.get("user_id"),
            gender=data.get("gender"),
            style=data.get("style"),
            reference=data.get("reference"),
            created_at=data.get("created_at"),
        )
