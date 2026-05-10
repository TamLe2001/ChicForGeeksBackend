"""Garment base model and related classes for clothing items."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from .enums import Gender

class Garment(ABC):
    """Abstract base class for all garment types."""

    def __init__(
        self,
        name: str,
        user_id: str,
        gender: Gender,
        display_name: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        created_at: Optional[datetime] = None,
        is_custom: bool = False,
        id: Optional[str] = None,
        custom_position: Optional[list] = None,
        custom_scale: Optional[list] = None,
        **kwargs
    ):
        """
        Initialize a Garment.

        Args:
            name: Name of the garment
            user_id: User ID who created this garment
            gender: Target gender (Gender enum)
            display_name: Name to display for the garment (defaults to name if not provided)
            thumbnail_url: Optional thumbnail URL for UI previews
            created_at: Creation timestamp
            is_custom: Flag indicating if the garment is custom
            id: Optional custom ID field from database
            custom_position: Optional 3D position coordinates [x, y, z], range -2 to 2
            custom_scale: Optional uniform scale factor [x, y, z], range 0.1 to 5
            **kwargs: Additional attributes specific to garment type
        """
        self.name = name
        self.user_id = user_id
        self.gender = gender if isinstance(gender, Gender) else Gender(str(gender).lower())
        self.created_at = created_at or datetime.now(timezone.utc)
        self.is_custom = is_custom
        self.display_name = display_name or name  # Fallback to name if not provided
        self.thumbnail_url = thumbnail_url
        self.id = id  # Custom id field from database
        self._id = None  # MongoDB _id field
        self.custom_position = custom_position  # [x, y, z] position coordinates
        self.custom_scale = custom_scale  # [x, y, z] scale factors

    def to_dict(self) -> Dict[str, Any]:
        """Convert garment to dictionary for database storage."""
        result = {
            "id": self.id or (str(self._id) if self._id else None),
            "type": self.get_type(),
            "name": self.name,
            "user_id": self.user_id,
            "gender": self.gender.value,
            "created_at": self.created_at,
            "is_custom": self.is_custom,
            "display_name": self.display_name,
            "thumbnail_url": self.thumbnail_url,
        }
        # Include optional custom position and scale if present
        if self.custom_position is not None:
            result["custom_position"] = self.custom_position
        if self.custom_scale is not None:
            result["custom_scale"] = self.custom_scale
        return result

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
