"""Routes for outfit comments management."""

from bson import ObjectId
from flask import Blueprint, current_app, g, jsonify, request

from api.routes.auth import token_required
from api.services.comment_service import CommentService


outfit_comments_bp = Blueprint('outfit_comments', __name__)


def _get_comment_service() -> CommentService:
	"""Get or create comment service instance."""
	return CommentService(current_app.db)


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


@outfit_comments_bp.get('/outfits/<outfit_id>/comments')
def get_outfit_comments(outfit_id):
	"""Get all comments for an outfit."""
	outfit, error_response = _get_outfit_doc_or_404(outfit_id)
	if error_response:
		return error_response

	outfit_oid = outfit.get('_id')
	comment_service = _get_comment_service()
	result, status_code = comment_service.get_outfit_comments(outfit_oid)
	return jsonify(result), status_code


@outfit_comments_bp.post('/outfits/<outfit_id>/comments')
@token_required
def create_comment(outfit_id):
	"""Create a comment on an outfit."""
	outfit, error_response = _get_outfit_doc_or_404(outfit_id)
	if error_response:
		return error_response

	payload = request.get_json(silent=True) or {}
	content = payload.get('content', '')

	user = g.current_user
	comment_service = _get_comment_service()
	result, status_code = comment_service.create_comment(
		outfit.get('_id'),
		user.get('_id'),
		user.get('name'),
		user.get('profile_picture'),
		content
	)
	return jsonify(result), status_code


@outfit_comments_bp.put('/outfits/<outfit_id>/comments/<comment_id>')
@token_required
def update_comment(outfit_id, comment_id):
	"""Update a comment."""
	outfit, error_response = _get_outfit_doc_or_404(outfit_id)
	if error_response:
		return error_response

	comment_oid = _parse_object_id(comment_id, 'comment id')
	if not comment_oid:
		return jsonify({'error': 'invalid comment id'}), 400

	payload = request.get_json(silent=True) or {}
	content = payload.get('content', '')

	comment_service = _get_comment_service()
	result, status_code = comment_service.update_comment(
		comment_oid,
		outfit.get('_id'),
		g.current_user.get('_id'),
		g.current_user.get('role', 'user'),
		content
	)
	return jsonify(result), status_code


@outfit_comments_bp.delete('/outfits/<outfit_id>/comments/<comment_id>')
@token_required
def delete_comment(outfit_id, comment_id):
	"""Delete a comment."""
	outfit, error_response = _get_outfit_doc_or_404(outfit_id)
	if error_response:
		return error_response

	comment_oid = _parse_object_id(comment_id, 'comment id')
	if not comment_oid:
		return jsonify({'error': 'invalid comment id'}), 400

	comment_service = _get_comment_service()
	result, status_code = comment_service.delete_comment(
		comment_oid,
		outfit.get('_id'),
		g.current_user.get('_id'),
		g.current_user.get('role', 'user')
	)
	return jsonify(result), status_code
