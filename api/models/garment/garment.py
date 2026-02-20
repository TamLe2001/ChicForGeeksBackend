"""Garment base model and related classes for clothing items."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional, Dict, Any


class Garment(ABC):
    """Abstract base class for all garment types."""

    def __init__(
        self,
        name: str,
        user_id: str,
        gender: str,
        style: str,
        reference: Optional[str] = None,
        created_at: Optional[datetime] = None,
        **kwargs
    ):
        """
        Initialize a Garment.

        Args:
            name: Name of the garment
            user_id: User ID who created this garment
            gender: Target gender ('male', 'female', 'unisex')
            style: Genre or category (e.g., 'streetwear', 'formal', 'casual', etc.)
            reference: Reference URL or path to the garment model
            created_at: Creation timestamp
            **kwargs: Additional attributes specific to garment type
        """
        self.name = name
        self.user_id = user_id
        self.gender = gender
        self.style = style
        self.reference = reference
        self.created_at = created_at or datetime.now(timezone.utc)
        self._id = None  # Set by database

    def to_dict(self) -> Dict[str, Any]:
        """Convert garment to dictionary for database storage."""
        return {
            "id": str(self._id) if self._id else None,
            "type": self.get_type(),
            "name": self.name,
            "user_id": self.user_id,
            "gender": self.gender,
            "style": self.style,
            "reference": self.reference,
            "created_at": self.created_at,
        }

    @abstractmethod
    def get_type(self) -> str:
        """Return the type of garment."""
        pass

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Garment":
        """Factory method to create garment from dictionary."""
        from .shirt import Shirt
        from .pants import Pants
        from .hat import Hat
        from .shoes import Shoes

        garment_type = data.get("type")

        if garment_type == "shirt":
            return Shirt.from_dict(data)
        elif garment_type == "pants":
            return Pants.from_dict(data)
        elif garment_type == "hat":
            return Hat.from_dict(data)
        elif garment_type == "shoes":
            return Shoes.from_dict(data)
        else:
            raise ValueError(f"Unknown garment type: {garment_type}")
