from typing import Any, Dict, List, Optional, Tuple

from bson import ObjectId
from flask import current_app

from api.models.outfit import Outfit


class OutfitService:
    """Service for outfit CRUD and listing operations."""

    def __init__(self, db):
        self.db = db

    def list_published(self, limit: int = 100, skip: int = 0) -> Tuple[List[Dict[str, Any]], int]:
        try:
            limit = min(abs(limit), 100) if limit > 0 else 100
            skip = max(0, skip)

            pipeline = [
                {"$match": {"published": True}},
                {"$sort": {"created_at": -1}},
                {"$skip": skip},
                {"$limit": limit},
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "user_id",
                        "foreignField": "_id",
                        "as": "user_data",
                    }
                },
                {"$addFields": {"user": {"$arrayElemAt": ["$user_data", 0]}}},
                {
                    "$project": {
                        "_id": 1,
                        "name": 1,
                        "gender": 1,
                        "description": {"$ifNull": ["$description", "$bio"]},
                        "shirt": 1,
                        "pants": 1,
                        "skirt": 1,
                        "accessory": 1,
                        "thumbnail": 1,
                        "user_id": 1,
                        "published": 1,
                        "created_at": 1,
                        "user_name": "$user.name",
                        "user_profile_pic": "$user.profile_picture",
                    }
                },
            ]

            results = list(self.db.outfits.aggregate(pipeline))

            outfits: List[Dict[str, Any]] = []
            for doc in results:
                user_id = doc.get("user_id")
                outfit_dict = Outfit.from_doc(doc).to_dict()
                outfit_dict["userId"] = str(user_id) if user_id else None
                outfits.append(outfit_dict)

            return outfits, 200
        except Exception as e:
            current_app.logger.exception("Failed to list published outfits")
            return {"error": "Failed to retrieve published outfits"}, 500

    def list_by_user(self, user_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
        try:
            query = {"user_id": user_id} if user_id else {}
            outfits = list(self.db.outfits.find(query).sort("created_at", -1))
            return [Outfit.from_doc(o).to_dict() for o in outfits], 200
        except Exception:
            current_app.logger.exception("Failed to list outfits by user")
            return {"error": "Failed to list outfits"}, 500

    def create_outfit(self, payload: Dict[str, Any], user_id: str) -> Tuple[Dict[str, Any], int]:
        try:
            if not payload.get("name"):
                return {"error": "name is required"}, 400

            payload["user_id"] = user_id
            outfit = Outfit.from_payload(payload)

            outfit_doc = {
                "name": outfit.name,
                "user_id": outfit.user_id,
                "gender": outfit.gender,
                "description": outfit.description,
                "shirt": outfit.shirt,
                "pants": outfit.pants,
                "skirt": outfit.skirt,
                "accessory": outfit.accessory,
                "published": outfit.published,
                "thumbnail": outfit.thumbnail,
                "created_at": outfit.created_at,
            }

            result = self.db.outfits.insert_one(outfit_doc)
            outfit_id = str(result.inserted_id)

            # Generate file-based thumbnail if provided
            if payload.get("thumbnail"):
                try:
                    uploads_path = current_app.config.get("UPLOAD_PATH", "uploads")
                    from api.services.thumbnail_service import ThumbnailService

                    thumbnail_service = ThumbnailService(self.db, uploads_path)
                    thumbnail_service.generate_thumbnail(
                        outfit_id, payload.get("thumbnail"), outfit.name
                    )
                except Exception:
                    current_app.logger.exception("Failed to generate file-based thumbnail")

            created = self.db.outfits.find_one({"_id": result.inserted_id})
            outfit_dict = Outfit.from_doc(created).to_dict()

            return outfit_dict, 201
        except Exception:
            current_app.logger.exception("Failed to create outfit")
            return {"error": "Server error creating outfit"}, 500

    def get_outfit(self, outfit_id: str) -> Tuple[Dict[str, Any], int]:
        oid = None
        try:
            oid = ObjectId(outfit_id)
        except Exception:
            return {"error": "invalid outfit id"}, 400

        outfit = self.db.outfits.find_one({"_id": oid})
        if not outfit:
            return {"error": "outfit not found"}, 404

        return Outfit.from_doc(outfit).to_dict(), 200

    def update_outfit(self, outfit_id: str, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        try:
            oid = ObjectId(outfit_id)
        except Exception:
            return {"error": "invalid outfit id"}, 400

        if "description" not in payload and "bio" in payload:
            payload["description"] = payload.get("bio")
        if "bio" in payload:
            payload.pop("bio")

        allowed_fields = {"name", "description", "shirt", "pants", "published", "thumbnail"}
        update_fields = {k: v for k, v in payload.items() if k in allowed_fields}

        if not update_fields:
            return {"error": "nothing to update"}, 400

        # Handle thumbnail file update if thumbnail is being updated
        if "thumbnail" in update_fields and update_fields["thumbnail"]:
            try:
                uploads_path = current_app.config.get("UPLOAD_PATH", "uploads")
                from api.services.thumbnail_service import ThumbnailService
                
                thumbnail_service = ThumbnailService(self.db, uploads_path)
                thumbnail_service.generate_thumbnail(
                    outfit_id, update_fields["thumbnail"], payload.get("name")
                )
            except Exception:
                current_app.logger.exception("Failed to update file-based thumbnail")

        result = self.db.outfits.update_one({"_id": oid}, {"$set": update_fields})
        if result.matched_count == 0:
            return {"error": "outfit not found"}, 404

        updated = self.db.outfits.find_one({"_id": oid})
        return Outfit.from_doc(updated).to_dict(), 200

    def delete_outfit(self, outfit_id: str) -> Tuple[Dict[str, Any], int]:
        try:
            oid = ObjectId(outfit_id)
        except Exception:
            return {"error": "invalid outfit id"}, 400

        result = self.db.outfits.delete_one({"_id": oid})
        if result.deleted_count == 0:
            return {"error": "outfit not found"}, 404

        # cascade deletes/cleanup
        try:
            self.db.likes.delete_many({"outfit_id": oid})
            self.db.comments.delete_many({"outfit_id": oid})
            self.db.wardrobes.update_many({}, {"$pull": {"outfit_ids": oid}})
        except Exception:
            current_app.logger.exception("Failed to perform cascade cleanup for outfit delete")

        # Delete associated thumbnail (best-effort)
        try:
            uploads_path = current_app.config.get("UPLOAD_PATH", "uploads")
            from api.services.thumbnail_service import ThumbnailService

            thumbnail_service = ThumbnailService(self.db, uploads_path)
            thumbnail_service.delete_thumbnail(outfit_id)
        except Exception:
            current_app.logger.exception("Failed to delete thumbnail for outfit")

        return {"status": "deleted"}, 200
