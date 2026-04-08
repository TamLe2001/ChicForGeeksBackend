"""Garment base model and related classes for clothing items."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from flask import url_for
from .enums import Gender, Style

class Garment(ABC):
    """Abstract base class for all garment types."""

    def __init__(
        self,
        name: str,
        user_id: str,
        gender: Gender,
        style: Style,
        display_name: Optional[str] = None,
        reference: Optional[str] = None,
        created_at: Optional[datetime] = None,
        is_custom: bool = False,
        id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a Garment.

        Args:
            name: Name of the garment
            user_id: User ID who created this garment
            gender: Target gender (Gender enum)
            style: Genre or category (Style enum)
            display_name: Name to display for the garment (defaults to name if not provided)
            reference: Reference URL or path to the garment model
            created_at: Creation timestamp
            is_custom: Flag indicating if the garment is custom
            id: Optional custom ID field from database
            **kwargs: Additional attributes specific to garment type
        """
        self.name = name
        self.user_id = user_id
        self.gender = gender if isinstance(gender, Gender) else Gender(str(gender).lower())
        self.style = style if isinstance(style, Style) else Style(str(style).lower())
        self.reference = reference
        self.created_at = created_at or datetime.now(timezone.utc)
        self.is_custom = is_custom
        self.display_name = display_name or name  # Fallback to name if not provided
        self.id = id  # Custom id field from database
        self._id = None  # MongoDB _id field

    def to_dict(self) -> Dict[str, Any]:
        """Convert garment to dictionary for database storage."""
        if self.is_custom and self.id:
            try:
                model_url = url_for(
                    "garments.download_custom_garment",
                    garment_id=self.id,
                    _external=True,
                )
            except RuntimeError:
                model_url = self.reference

        return {
            "id": self.id or (str(self._id) if self._id else None),
            "type": self.get_type(),
            "name": self.name,
            "user_id": self.user_id,
            "gender": self.gender.value,
            "style": self.style.value,
            "reference": self.reference,
            "model_url": model_url,
            "created_at": self.created_at,
            "is_custom": self.is_custom,
            "display_name": self.display_name,
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
        from .skirt import Skirt
        from .accessory import Accessory

        garment_type = data.get("type")

        if garment_type == "shirt":
            return Shirt.from_dict(data)
        elif garment_type == "pants":
            return Pants.from_dict(data)
        elif garment_type == "skirt":
            return Skirt.from_dict(data)
        elif garment_type == "accessory":
            return Accessory.from_dict(data)
        else:
            raise ValueError(f"Unknown garment type: {garment_type}")
