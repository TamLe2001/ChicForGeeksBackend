"""Routes for garment management."""

from flask import Blueprint, current_app, g, jsonify, request
from api.models.garment import Shirt, Pants, Hat, Shoes
from api.services.garment_service import GarmentService
from api.routes.auth import token_required

garments_bp = Blueprint("garments", __name__)


def _get_garment_service() -> GarmentService:
    """Get or create garment service instance."""
    return GarmentService(current_app.db)


@garments_bp.post("/garments")
@token_required
def create_garment():
    """Create a new garment."""
    payload = request.get_json(silent=True) or {}
    garment_type = payload.get("type")

    if not garment_type:
        return jsonify({"error": "garment type is required"}), 400

    user_id = str(g.current_user.get("_id"))

    try:
        # Create appropriate garment type
        if garment_type == "shirt":
            garment = Shirt(
                name=payload.get("name", "Untitled Shirt"),
                created_by=user_id,
                gender=payload.get("gender", "unisex"),
                reference=payload.get("reference"),
                sleeve_type=payload.get("sleeve_type", "short"),
                color=payload.get("color"),
                pattern=payload.get("pattern", "solid"),
            )
        elif garment_type == "pants":
            garment = Pants(
                name=payload.get("name", "Untitled Pants"),
                created_by=user_id,
                gender=payload.get("gender", "unisex"),
                reference=payload.get("reference"),
                fit=payload.get("fit", "regular"),
                length=payload.get("length", "full"),
                color=payload.get("color"),
                material=payload.get("material", "cotton"),
            )
        elif garment_type == "hat":
            garment = Hat(
                name=payload.get("name", "Untitled Hat"),
                created_by=user_id,
                gender=payload.get("gender", "unisex"),
                reference=payload.get("reference"),
                hat_style=payload.get("hat_style", "baseball"),
                color=payload.get("color"),
                material=payload.get("material", "cotton"),
            )
        elif garment_type == "shoes":
            garment = Shoes(
                name=payload.get("name", "Untitled Shoes"),
                created_by=user_id,
                gender=payload.get("gender", "unisex"),
                reference=payload.get("reference"),
                shoe_type=payload.get("shoe_type", "sneaker"),
                color=payload.get("color"),
                size_range=payload.get("size_range", "all"),
                material=payload.get("material", "fabric"),
            )
        else:
            return jsonify({"error": f"unknown garment type: {garment_type}"}), 400

        service = _get_garment_service()
        garment_id = service.create_garment(garment)

        return (
            jsonify(
                {
                    "status": "created",
                    "garment_id": garment_id,
                    "garment": garment.to_dict(),
                }
            ),
            201,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@garments_bp.get("/garments")
def list_garments():
    """List garments with optional filters."""
    garment_type = request.args.get("type")
    gender = request.args.get("gender")
    creator_id = request.args.get("creator_id")

    service = _get_garment_service()

    try:
        if creator_id:
            garments = service.get_garments_by_creator(creator_id)
        elif garment_type:
            garments = service.get_garments_by_type(garment_type, gender)
        else:
            garments = service.search_garments({})

        return (
            jsonify(
                {
                    "status": "success",
                    "count": len(garments),
                    "garments": [g.to_dict() for g in garments],
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@garments_bp.get("/garments/<garment_id>")
def get_garment(garment_id):
    """Get a specific garment by ID."""
    service = _get_garment_service()

    try:
        garment = service.get_garment(garment_id)
        if not garment:
            return jsonify({"error": "garment not found"}), 404

        return jsonify({"status": "success", "garment": garment.to_dict()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@garments_bp.put("/garments/<garment_id>")
@token_required
def update_garment(garment_id):
    """Update a garment."""
    payload = request.get_json(silent=True) or {}
    user_id = str(g.current_user.get("_id"))

    service = _get_garment_service()

    try:
        garment = service.get_garment(garment_id)
        if not garment:
            return jsonify({"error": "garment not found"}), 404

        if garment.created_by != user_id:
            return jsonify({"error": "not authorized to update this garment"}), 403

        # Allowed fields to update based on garment type
        allowed_fields = {
            "name",
            "reference",
            "color",
            "pattern",
            "fit",
            "length",
            "material",
            "sleeve_type",
            "hat_style",
            "shoe_type",
            "size_range",
        }

        updates = {k: v for k, v in payload.items() if k in allowed_fields}

        if not updates:
            return jsonify({"error": "no valid fields to update"}), 400

        service.update_garment(garment_id, updates)

        updated_garment = service.get_garment(garment_id)
        return (
            jsonify(
                {"status": "updated", "garment": updated_garment.to_dict()}
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@garments_bp.delete("/garments/<garment_id>")
@token_required
def delete_garment(garment_id):
    """Delete a garment."""
    user_id = str(g.current_user.get("_id"))
    service = _get_garment_service()

    try:
        garment = service.get_garment(garment_id)
        if not garment:
            return jsonify({"error": "garment not found"}), 404

        if garment.created_by != user_id:
            return jsonify({"error": "not authorized to delete this garment"}), 403

        service.delete_garment(garment_id)
        return jsonify({"status": "deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
