"""Routes for garment management."""

from flask import Blueprint, Response, current_app, g, jsonify, request, stream_with_context
from api.models.garment import Shirt, Pants, Skirt, Accessory
from api.services.garment_service import GarmentService
from api.routes.auth import token_required
from werkzeug.utils import secure_filename
import requests
from requests.auth import HTTPBasicAuth
from io import BytesIO
from uuid import uuid4

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
     
@garments_bp.get('/default-glb/<path:file_name>')
def get_default_glb(file_name):
    """Download file directly from NextCloud default folder"""
    try:
        cloud = current_app.cloud_service
        
        if not cloud.nextcloud_url:
            return jsonify({'error': 'NextCloud not configured'}), 500

        safe_file_name = secure_filename(file_name)
        if not safe_file_name:
            return jsonify({'error': 'Invalid file name'}), 400
        
        cloud_url = cloud.get_url_garment_default(safe_file_name)
        
        auth = (cloud.nextcloud_user, cloud.nextcloud_pass) if cloud.nextcloud_user and cloud.nextcloud_pass else None
        response = requests.get(
            cloud_url,
            auth=auth,
            stream=True,
            timeout=(5, 60),
        )
        
        if response.status_code == 404:
            return jsonify({'error': 'File not found in cloud storage'}), 404
        
        if response.status_code != 200:
            response.close()
            return jsonify({'error': f'Failed to download file from cloud: {response.status_code}'}), 502
        
        content_type = response.headers.get('Content-Type', 'application/octet-stream')
        content_length = response.headers.get('Content-Length')

        def generate():
            try:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        yield chunk
            finally:
                response.close()

        headers = {
            'Content-Type': content_type,
            'Cache-Control': 'public, max-age=86400',
        }
        if content_length:
            headers['Content-Length'] = content_length

        return Response(stream_with_context(generate()), headers=headers, status=200)
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Download timeout - file may be too large or network issues'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 502
    except Exception as e:
        return jsonify({'error': f'Failed to download file: {str(e)}'}), 500


@garments_bp.get("/garments/custom-glb/<garment_id>")
@token_required
def download_custom_garment(garment_id):
    """Stream a custom garment GLB through the backend to avoid browser CORS issues."""
    user_id = str(g.current_user.get("_id"))

    try:
        service = _get_garment_service()
        garment = service.get_garment(garment_id)

        if not garment:
            return jsonify({"error": "garment not found"}), 404

        if garment.user_id != user_id:
            return jsonify({"error": "not authorized to view this garment"}), 403

        cloud = getattr(current_app, "cloud_service", None)
        if not cloud:
            return jsonify({"error": "cloud service not available"}), 500

        source_url = f"{cloud.nextcloud_url}customs/{secure_filename(garment.id)}"

        auth = (
            HTTPBasicAuth(cloud.nextcloud_user, cloud.nextcloud_pass)
            if cloud.nextcloud_user and cloud.nextcloud_pass
            else None
        )

        response = requests.get(
            source_url,
            auth=auth,
            stream=True,
            timeout=(5, 60),
        )

        if response.status_code == 404:
            response.close()
            return jsonify({'error': 'File not found in cloud storage'}), 404

        if response.status_code != 200:
            response.close()
            return jsonify({'error': f'Failed to download file from cloud: {response.status_code}'}), 502

        content_type = response.headers.get('Content-Type', 'application/octet-stream')
        content_length = response.headers.get('Content-Length')

        def generate():
            try:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        yield chunk
            finally:
                response.close()

        headers = {
            'Content-Type': content_type,
            'Cache-Control': 'public, max-age=86400',
        }
        if content_length:
            headers['Content-Length'] = content_length

        return Response(stream_with_context(generate()), headers=headers, status=200)
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Download timeout - file may be too large or network issues'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 502
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
        model_source_url = payload.get("source_url")
        if not model_source_url:
            return jsonify({"error": "source_url is required"}), 400

        # Extract common fields
        common_kwargs = {
            "name": payload.get("name", f"Untitled {garment_type.capitalize()}"),
            "user_id": user_id,
            "gender": payload.get("gender", "unisex"),
            "style": payload.get("style", "casual"),
            "display_name": payload.get("display_name"),
            "is_custom": True,  # Mark all garments created through this endpoint as custom
            "id": uuid4().hex,
        }
        
        # Add optional common fields if present
        if payload.get("display_name"):
            common_kwargs["display_name"] = payload.get("display_name")
        if payload.get("thumbnail_url"):
            common_kwargs["thumbnail_url"] = payload.get("thumbnail_url")
        if payload.get("is_custom") is not None:
            common_kwargs["is_custom"] = payload.get("is_custom")
        if payload.get("default") is not None:
            common_kwargs["default"] = payload.get("default")
        if payload.get("created_at"):
            common_kwargs["created_at"] = payload.get("created_at")

        # Create appropriate garment type with type-specific fields
        if garment_type == "shirt":
            garment = Shirt(**common_kwargs,)
        elif garment_type == "pants":
            garment = Pants(**common_kwargs)
        elif garment_type == "skirt":
            garment = Skirt(**common_kwargs)
        elif garment_type == "accessory" or garment_type == "accessories":
            garment = Accessory(**common_kwargs)
        else:
            return jsonify({"error": f"unknown garment type: {garment_type}"}), 400

        service = _get_garment_service()
        garment_id = service.create_garment(garment)
        garment.id = garment_id
        service.update_garment(garment_id, {"id": garment_id})

        cloud = getattr(current_app, "cloud_service", None)
        if not cloud:
            return jsonify({"error": "cloud service not available"}), 500

        try:
            source_response = requests.get(model_source_url, stream=True, timeout=(5, 120))
            if source_response.status_code != 200:
                return jsonify({"error": f"failed to fetch source model: {source_response.status_code}"}), 502

            model_bytes = source_response.content
            payload = {
                "stream": BytesIO(model_bytes),
                "content_type": source_response.headers.get("Content-Type", "application/octet-stream"),
                "content_length": len(model_bytes),
            }
            upload_result, upload_code = cloud.upload_glb(payload, garment.id)
            if upload_code != 201:
                service.delete_garment(garment_id)
                return jsonify(upload_result), upload_code
        finally:
            if 'source_response' in locals():
                source_response.close()

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
    
@garments_bp.get("/garments/user/<creator_id>")
@token_required
def get_garments_by_user(creator_id: str):
    """Get all garments created by the authenticated user."""
    user_id = str(g.current_user.get("_id"))
    if creator_id != user_id:
        return jsonify({"error": "not authorized to view these garments"}), 403

    service = _get_garment_service()
    try:
        garments = service.get_garments_by_creator(creator_id)
        return (
            jsonify(
                {
                    "status": "success",
                    "count": len(garments),
                    "garments": [garment.to_dict() for garment in garments],
                }
            ),
            200,
        )
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