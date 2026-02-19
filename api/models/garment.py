"""Garment model and related classes for clothing items."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from bson import ObjectId


class Garment(ABC):
    """Abstract base class for all garment types."""

    def __init__(
        self,
        name: str,
        created_by: str,
        gender: str,
        reference: Optional[str] = None,
        created_at: Optional[datetime] = None,
        **kwargs
    ):
        """
        Initialize a Garment.

        Args:
            name: Name of the garment
            created_by: User ID who created this garment
            gender: Target gender ('male', 'female', 'unisex')
            reference: Reference URL or path to the garment model
            created_at: Creation timestamp
            **kwargs: Additional attributes specific to garment type
        """
        self.name = name
        self.created_by = created_by
        self.gender = gender
        self.reference = reference
        self.created_at = created_at or datetime.now(timezone.utc)

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert garment to dictionary for database storage."""
        pass

    @abstractmethod
    def get_type(self) -> str:
        """Return the type of garment."""
        pass

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Garment":
        """Factory method to create garment from dictionary."""
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


class Shirt(Garment):
    """Shirt garment class."""

    def __init__(
        self,
        name: str,
        created_by: str,
        gender: str,
        reference: Optional[str] = None,
        sleeve_type: str = "short",
        color: Optional[str] = None,
        pattern: str = "solid",
        created_at: Optional[datetime] = None,
        **kwargs
    ):
        """
        Initialize a Shirt.

        Args:
            name: Name of the shirt
            created_by: User ID who created this shirt
            gender: Target gender ('male', 'female', 'unisex')
            reference: Reference URL or path to the shirt model
            sleeve_type: Type of sleeves ('short', 'long', 'sleeveless')
            color: Color of the shirt
            pattern: Pattern type ('solid', 'striped', 'checkered', etc.)
            created_at: Creation timestamp
        """
        super().__init__(name, created_by, gender, reference, created_at)
        self.sleeve_type = sleeve_type
        self.color = color
        self.pattern = pattern

    def get_type(self) -> str:
        return "shirt"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.get_type(),
            "name": self.name,
            "created_by": self.created_by,
            "gender": self.gender,
            "reference": self.reference,
            "sleeve_type": self.sleeve_type,
            "color": self.color,
            "pattern": self.pattern,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Shirt":
        return Shirt(
            name=data.get("name"),
            created_by=data.get("created_by"),
            gender=data.get("gender"),
            reference=data.get("reference"),
            sleeve_type=data.get("sleeve_type", "short"),
            color=data.get("color"),
            pattern=data.get("pattern", "solid"),
            created_at=data.get("created_at"),
        )


class Pants(Garment):
    """Pants garment class."""

    def __init__(
        self,
        name: str,
        created_by: str,
        gender: str,
        reference: Optional[str] = None,
        fit: str = "regular",
        length: str = "full",
        color: Optional[str] = None,
        material: str = "cotton",
        created_at: Optional[datetime] = None,
        **kwargs
    ):
        """
        Initialize Pants.

        Args:
            name: Name of the pants
            created_by: User ID who created these pants
            gender: Target gender ('male', 'female', 'unisex')
            reference: Reference URL or path to the pants model
            fit: Fit type ('slim', 'regular', 'loose', 'baggy')
            length: Length type ('full', 'crop', 'capri')
            color: Color of the pants
            material: Material type ('cotton', 'denim', 'leather', etc.)
            created_at: Creation timestamp
        """
        super().__init__(name, created_by, gender, reference, created_at)
        self.fit = fit
        self.length = length
        self.color = color
        self.material = material

    def get_type(self) -> str:
        return "pants"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.get_type(),
            "name": self.name,
            "created_by": self.created_by,
            "gender": self.gender,
            "reference": self.reference,
            "fit": self.fit,
            "length": self.length,
            "color": self.color,
            "material": self.material,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Pants":
        return Pants(
            name=data.get("name"),
            created_by=data.get("created_by"),
            gender=data.get("gender"),
            reference=data.get("reference"),
            fit=data.get("fit", "regular"),
            length=data.get("length", "full"),
            color=data.get("color"),
            material=data.get("material", "cotton"),
            created_at=data.get("created_at"),
        )


class Hat(Garment):
    """Hat garment class."""

    def __init__(
        self,
        name: str,
        created_by: str,
        gender: str,
        reference: Optional[str] = None,
        hat_style: str = "baseball",
        color: Optional[str] = None,
        material: str = "cotton",
        created_at: Optional[datetime] = None,
        **kwargs
    ):
        """
        Initialize a Hat.

        Args:
            name: Name of the hat
            created_by: User ID who created this hat
            gender: Target gender ('male', 'female', 'unisex')
            reference: Reference URL or path to the hat model
            hat_style: Style of hat ('baseball', 'beanie', 'fedora', 'beret', etc.)
            color: Color of the hat
            material: Material type ('cotton', 'wool', 'leather', etc.)
            created_at: Creation timestamp
        """
        super().__init__(name, created_by, gender, reference, created_at)
        self.hat_style = hat_style
        self.color = color
        self.material = material

    def get_type(self) -> str:
        return "hat"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.get_type(),
            "name": self.name,
            "created_by": self.created_by,
            "gender": self.gender,
            "reference": self.reference,
            "hat_style": self.hat_style,
            "color": self.color,
            "material": self.material,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Hat":
        return Hat(
            name=data.get("name"),
            created_by=data.get("created_by"),
            gender=data.get("gender"),
            reference=data.get("reference"),
            hat_style=data.get("hat_style", "baseball"),
            color=data.get("color"),
            material=data.get("material", "cotton"),
            created_at=data.get("created_at"),
        )


class Shoes(Garment):
    """Shoes garment class."""

    def __init__(
        self,
        name: str,
        created_by: str,
        gender: str,
        reference: Optional[str] = None,
        shoe_type: str = "sneaker",
        color: Optional[str] = None,
        size_range: str = "all",
        material: str = "fabric",
        created_at: Optional[datetime] = None,
        **kwargs
    ):
        """
        Initialize Shoes.

        Args:
            name: Name of the shoes
            created_by: User ID who created these shoes
            gender: Target gender ('male', 'female', 'unisex')
            reference: Reference URL or path to the shoes model
            shoe_type: Type of shoe ('sneaker', 'boot', 'heels', 'loafers', etc.)
            color: Color of the shoes
            size_range: Size range available ('all', 'small', 'medium', 'large')
            material: Material type ('fabric', 'leather', 'suede', etc.)
            created_at: Creation timestamp
        """
        super().__init__(name, created_by, gender, reference, created_at)
        self.shoe_type = shoe_type
        self.color = color
        self.size_range = size_range
        self.material = material

    def get_type(self) -> str:
        return "shoes"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.get_type(),
            "name": self.name,
            "created_by": self.created_by,
            "gender": self.gender,
            "reference": self.reference,
            "shoe_type": self.shoe_type,
            "color": self.color,
            "size_range": self.size_range,
            "material": self.material,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Shoes":
        return Shoes(
            name=data.get("name"),
            created_by=data.get("created_by"),
            gender=data.get("gender"),
            reference=data.get("reference"),
            shoe_type=data.get("shoe_type", "sneaker"),
            color=data.get("color"),
            size_range=data.get("size_range", "all"),
            material=data.get("material", "fabric"),
            created_at=data.get("created_at"),
        )
