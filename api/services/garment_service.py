"""Service for managing garments in the database."""

from typing import List, Optional, Dict, Any
from bson import ObjectId
from api.models.garment import Garment, Shirt, Pants, Hat, Shoes


class GarmentService:
    """Service for managing garment operations."""

    def __init__(self, db):
        """
        Initialize GarmentService.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.garments

    def create_garment(self, garment: Garment) -> str:
        """
        Create a new garment in the database.

        Args:
            garment: Garment instance to create

        Returns:
            ID of the created garment
        """
        garment_dict = garment.to_dict()
        result = self.collection.insert_one(garment_dict)
        return str(result.inserted_id)

    def get_garment(self, garment_id: str) -> Optional[Garment]:
        """
        Get a garment by ID.

        Args:
            garment_id: ID of the garment

        Returns:
            Garment instance or None if not found
        """
        try:
            doc = self.collection.find_one({"_id": ObjectId(garment_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
                return Garment.from_dict(doc)
        except Exception:
            pass
        return None

    def get_garments_by_type(
        self, garment_type: str, gender: Optional[str] = None
    ) -> List[Garment]:
        """
        Get garments filtered by type and optionally by gender.

        Args:
            garment_type: Type of garment ('shirt', 'pants', 'hat', 'shoes')
            gender: Optional gender filter ('male', 'female', 'unisex')

        Returns:
            List of matching garments
        """
        query = {"type": garment_type}
        if gender:
            query["gender"] = gender

        docs = list(self.collection.find(query).sort("created_at", -1))
        garments = []
        for doc in docs:
            doc["_id"] = str(doc["_id"])
            garments.append(Garment.from_dict(doc))
        return garments

    def get_garments_by_creator(self, creator_id: str) -> List[Garment]:
        """
        Get all garments created by a user.

        Args:
            creator_id: ID of the creator/user

        Returns:
            List of garments created by the user
        """
        docs = list(
            self.collection.find({"created_by": creator_id}).sort(
                "created_at", -1
            )
        )
        garments = []
        for doc in docs:
            doc["_id"] = str(doc["_id"])
            garments.append(Garment.from_dict(doc))
        return garments

    def update_garment(self, garment_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a garment.

        Args:
            garment_id: ID of the garment to update
            updates: Dictionary of fields to update

        Returns:
            True if update was successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(garment_id)}, {"$set": updates}
            )
            return result.modified_count > 0
        except Exception:
            return False

    def delete_garment(self, garment_id: str) -> bool:
        """
        Delete a garment.

        Args:
            garment_id: ID of the garment to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            result = self.collection.delete_one({"_id": ObjectId(garment_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    def search_garments(self, query: Dict[str, Any]) -> List[Garment]:
        """
        Search for garments with flexible query.

        Args:
            query: MongoDB query dictionary

        Returns:
            List of matching garments
        """
        docs = list(self.collection.find(query).sort("created_at", -1))
        garments = []
        for doc in docs:
            doc["_id"] = str(doc["_id"])
            garments.append(Garment.from_dict(doc))
        return garments
