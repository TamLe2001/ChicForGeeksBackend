"""Pants garment model."""

from typing import Optional, Dict, Any
from datetime import datetime

from .garment import Garment


class Pants(Garment):
    """Pants garment class."""

    def __init__(
        self,
        name: str,
        created_by: str,
        gender: str,
        type: str,
        reference: Optional[str] = None,
        created_at: Optional[datetime] = None,
        **kwargs
    ):
        """
        Initialize Pants.

        Args:
            name: Name of the pants
            created_by: User ID who created these pants
            gender: Target gender ('male', 'female', 'unisex')
            type: Genre or category (e.g., 'streetwear', 'formal', 'casual', etc.)
            reference: Reference URL or path to the pants model
            created_at: Creation timestamp
        """
        super().__init__(name, created_by, gender, type, reference, created_at)
        self.type = type

    def get_type(self) -> str:
        return "pants"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.get_type(),
            "name": self.name,
            "created_by": self.created_by,
            "gender": self.gender,
            "type": self.type,
            "reference": self.reference,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Pants":
        return Pants(
            name=data.get("name"),
            created_by=data.get("created_by"),
            gender=data.get("gender"),
            type=data.get("type"),
            reference=data.get("reference"),
            created_at=data.get("created_at"),
        )
