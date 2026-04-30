"""Routes for outfit likes management."""

from bson import ObjectId
from flask import Blueprint, current_app, g, jsonify

from api.routes.auth import token_required
from api.services.like_service import LikeService


outfit_likes_bp = Blueprint('outfit_likes', __name__)


def _get_like_service() -> LikeService:
	"""Get or create like service instance."""
	return LikeService(current_app.db)


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


@outfit_likes_bp.get('/outfits/<outfit_id>/likes')
def get_outfit_likes(outfit_id):
	"""Get all likes for an outfit."""
	outfit, error_response = _get_outfit_doc_or_404(outfit_id)
	if error_response:
		return error_response

	outfit_oid = outfit.get('_id')
	like_service = _get_like_service()
	result, status_code = like_service.get_outfit_likes(outfit_oid)
	return jsonify(result), status_code


@outfit_likes_bp.post('/outfits/<outfit_id>/likes')
@token_required
def like_outfit(outfit_id):
	"""Like an outfit."""
	outfit, error_response = _get_outfit_doc_or_404(outfit_id)
	if error_response:
		return error_response

	user_id = g.current_user.get('_id')
	outfit_oid = outfit.get('_id')

	like_service = _get_like_service()
	result, status_code = like_service.like_outfit(outfit_oid, user_id)
	return jsonify(result), status_code


@outfit_likes_bp.delete('/outfits/<outfit_id>/likes')
@token_required
def unlike_outfit(outfit_id):
	"""Unlike an outfit."""
	outfit, error_response = _get_outfit_doc_or_404(outfit_id)
	if error_response:
		return error_response

	user_id = g.current_user.get('_id')
	outfit_oid = outfit.get('_id')

	like_service = _get_like_service()
	result, status_code = like_service.unlike_outfit(outfit_oid, user_id)
	return jsonify(result), status_code
