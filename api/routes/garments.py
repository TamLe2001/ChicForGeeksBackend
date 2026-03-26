"""Routes for garment management."""

from api.models.garment.accessory import Accessory
from flask import Blueprint, current_app, g, jsonify, request, send_file
from api.models.garment import Shirt, Pants, Skirt, Accessory
from api.services.garment_service import GarmentService
from api.routes.auth import token_required
import os
from io import BytesIO
import requests

garments_bp = Blueprint("garments", __name__)


def _get_garment_service() -> GarmentService:
    """Get or create garment service instance."""
    return GarmentService(current_app.db)


@garments_bp.get('/default')
def get_default_garments():
	"""Get all default garments metadata grouped by type."""
	try:
		service = _get_garment_service()
		garments = service.get_default_garments()
		
		# Group by type
		grouped = {
			"shirts": [],
			"pants": [],
			"skirts": [],
			"accessories": []
		}
		
		for garment in garments:
			garment_dict = garment.to_dict()
			garment_type = garment_dict.get("type", "").lower()
			
			if garment_type == "shirt":
				grouped["shirts"].append(garment_dict)
			elif garment_type == "pants":
				grouped["pants"].append(garment_dict)
			elif garment_type == "skirt":
				grouped["skirts"].append(garment_dict)
			elif garment_type == "accessory":
				grouped["accessories"].append(garment_dict)
		
		return jsonify(grouped), 200
		
	except Exception as e:
		return jsonify({'error': f'Server error: {str(e)}'}), 500
     
@garments_bp.get('/default-glb/<file_name>')
def get_default_glb(file_name):
    """Download file directly from NextCloud default folder"""
    try:
        # Get NextCloud credentials from environment
        cloud = current_app.cloud_service      
        
        if not cloud.nextcloud_url:
            return jsonify({'error': 'NextCloud not configured'}), 500
        
        # Normalize URL to ensure it ends with slash
        if not cloud.nextcloud_url.endswith('/'):
            cloud.nextcloud_url = f"{cloud.nextcloud_url}/"
        
        # Construct cloud URL
        cloud_url = cloud.get_url_garment_default(file_name)
        
        # Download file from NextCloud
        auth = (cloud.nextcloud_user, cloud.nextcloud_pass) if cloud.nextcloud_user and cloud.nextcloud_pass else None
        response = requests.get(
            cloud_url,
            auth=auth,
            timeout=30
        )
        
        if response.status_code == 404:
            return jsonify({'error': 'File not found in cloud storage'}), 404
        
        if response.status_code != 200:
            return jsonify({'error': f'Failed to download file from cloud: {response.status_code}'}), 500
        
        # Detect content type from response headers or filename
        content_type = response.headers.get('Content-Type', 'application/octet-stream')
        
        # Return file as download
        return send_file(
            BytesIO(response.content),
            mimetype=content_type,
            as_attachment=True,
            download_name=file_name
        )
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Download timeout - file may be too large or network issues'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to download file: {str(e)}'}), 500
     
     

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
                user_id=user_id,
                gender=payload.get("gender", "unisex"),
                style=payload.get("style", "casual"),
                reference=payload.get("reference"),
                sleeve_type=payload.get("sleeve_type", "short"),
                color=payload.get("color"),
                pattern=payload.get("pattern", "solid"),
            )
        elif garment_type == "pants":
            garment = Pants(
                name=payload.get("name", "Untitled Pants"),
                user_id=user_id,
                gender=payload.get("gender", "unisex"),
                style=payload.get("style", "casual"),
                reference=payload.get("reference"),
                fit=payload.get("fit", "regular"),
                length=payload.get("length", "full"),
                color=payload.get("color"),
                material=payload.get("material", "cotton"),
            )
        elif garment_type == "skirt":
            garment = Skirt(
                name=payload.get("name", "Untitled Skirt"),
                user_id=user_id,
                gender=payload.get("gender", "female"),
                style=payload.get("style", "casual"),
                reference=payload.get("reference"),
                length=payload.get("length", "knee"),
                color=payload.get("color"),
                material=payload.get("material", "cotton"),
            )
        elif garment_type == "accessories":
            garment = Accessory(
                name=payload.get("name", "Untitled Accessory"),
                user_id=user_id,
                gender=payload.get("gender", "unisex"),
                style=payload.get("style", "casual"),
                reference=payload.get("reference"),
                accessory_type=payload.get("accessory_type", "generic"),
                color=payload.get("color"),
                material=payload.get("material", "mixed"),
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

        if garment.user_id != user_id:
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

        if garment.user_id != user_id:
            return jsonify({"error": "not authorized to delete this garment"}), 403

        service.delete_garment(garment_id)
        return jsonify({"status": "deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@garments_bp.get("/meshy-key/key")
@token_required
def get_meshy_key():
    """Get meshy api key for authenticated user."""
    meshy_api_key = current_app.config.get('MESHY_AI_API_KEY')
    if not meshy_api_key:
        return jsonify({'error': 'meshy api key not configured'}), 500

    return jsonify({'meshy_api_key': meshy_api_key}), 200