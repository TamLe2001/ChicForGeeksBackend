from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from flask import Blueprint, current_app, g, jsonify, request, send_file
from datetime import datetime, timezone
from api.models.comment import Comment
from api.models.like import Like
from api.models.outfit import Outfit
from api.routes.auth import token_required
from api.services.thumbnail_service import ThumbnailService
from io import BytesIO
from api.services.outfit_service import OutfitService

outfits_bp = Blueprint('outfits', __name__)


def _get_thumbnail_service() -> ThumbnailService:
	"""Get or create thumbnail service instance."""
	uploads_path = current_app.config.get('UPLOAD_PATH', 'uploads')
	return ThumbnailService(current_app.db, uploads_path)


def _get_outfit_service() -> OutfitService:
	"""Get or create outfit service instance."""
	return OutfitService(current_app.db)


def _parse_object_id(value, label):
	try:
		return ObjectId(value)
	except Exception:
		return None


def _get_outfit_doc_or_404(outfit_id):
	oid = _parse_object_id(outfit_id, 'outfit id')
	if not oid:
		return None, (jsonify({'error': 'invalid outfit id'}), 400)

	outfit = current_app.db.outfits.find_one({'_id': oid})
	if not outfit:
		return None, (jsonify({'error': 'outfit not found'}), 404)

	return outfit, None


@outfits_bp.get('/outfits/published')
def get_published_outfits():
	limit = request.args.get('limit', 100, type=int)
	skip = request.args.get('skip', 0, type=int)
	service = _get_outfit_service()
	result, status = service.list_published(limit=limit, skip=skip)
	return jsonify(result), status


@outfits_bp.get('/outfits')
def list_outfits():
	user_id = request.args.get('user_id')
	service = _get_outfit_service()
	result, status = service.list_by_user(user_id)
	return jsonify(result), status


@outfits_bp.post('/outfits')
@token_required
def create_outfit():
	payload = request.get_json(silent=True) or {}
	user_id = str(g.current_user.get('_id'))
	service = _get_outfit_service()
	result, status = service.create_outfit(payload, user_id)
	return jsonify(result), status


@outfits_bp.get('/outfits/<outfit_id>')
@token_required
def get_outfit(outfit_id):
	service = _get_outfit_service()
	result, status = service.get_outfit(outfit_id)
	return jsonify(result), status


@outfits_bp.put('/outfits/<outfit_id>')
@token_required
def update_outfit(outfit_id):
	payload = request.get_json(silent=True) or {}
	service = _get_outfit_service()
	result, status = service.update_outfit(outfit_id, payload)
	return jsonify(result), status


@outfits_bp.delete('/outfits/<outfit_id>')
@token_required
def delete_outfit(outfit_id):
	service = _get_outfit_service()
	result, status = service.delete_outfit(outfit_id)
	return jsonify(result), status


@outfits_bp.get('/outfits/<outfit_id>/thumbnail')
def get_outfit_thumbnail(outfit_id):
	"""Get thumbnail image for an outfit."""
	try:
		thumbnail_service = _get_thumbnail_service()
		thumbnail_bytes = thumbnail_service.get_thumbnail(outfit_id)
		
		if not thumbnail_bytes:
			return jsonify({'error': 'thumbnail not found'}), 404
		
		return send_file(
			BytesIO(thumbnail_bytes),
			mimetype='image/png',
			as_attachment=False,
			download_name=f'{outfit_id}_thumbnail.png'
		)
	except Exception as e:
		return jsonify({'error': f'Failed to retrieve thumbnail: {str(e)}'}), 500
