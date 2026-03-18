from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from flask import Blueprint, current_app, g, jsonify, request
from datetime import datetime, timezone
from api.models.comment import Comment
from api.models.like import Like
from api.models.outfit import Outfit
from api.routes.auth import token_required

outfits_bp = Blueprint('outfits', __name__)


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


@outfits_bp.get('/outfits')
def list_outfits():
	user_id = request.args.get('user_id')
	query = {'user_id': user_id} if user_id else {}

	outfits = current_app.db.outfits.find(query).sort('created_at', -1)
	return jsonify([Outfit.from_doc(o).to_dict() for o in outfits]), 200


@outfits_bp.post('/outfits')
@token_required
def create_outfit():
	payload = request.get_json(silent=True) or {}

	if not payload.get('name'):
		return jsonify({'error': 'name is required'}), 400

	user_id = str(g.current_user.get('_id'))
	payload['user_id'] = user_id

	outfit = Outfit.from_payload(payload)
	outfit_doc = {
		'name': outfit.name,
		'user_id': outfit.user_id,
		'bio': outfit.bio,
		'shirt': outfit.shirt.to_dict() if outfit.shirt else None,
		'pants': outfit.pants.to_dict() if outfit.pants else None,
		'published': outfit.published,
		'created_at': outfit.created_at,
	}
	result = current_app.db.outfits.insert_one(outfit_doc)

	created = current_app.db.outfits.find_one({'_id': result.inserted_id})
	return jsonify(Outfit.from_doc(created).to_dict()), 201


@outfits_bp.get('/outfits/<outfit_id>')
@token_required
def get_outfit(outfit_id):
	try:
		oid = _parse_object_id(outfit_id, 'outfit id')
	except Exception:
		return jsonify({'error': 'invalid outfit id'}), 400

	outfit = current_app.db.outfits.find_one({'_id': oid})
	if not outfit:
		return jsonify({'error': 'outfit not found'}), 404

	return jsonify(Outfit.from_doc(outfit).to_dict()), 200


@outfits_bp.put('/outfits/<outfit_id>')
@token_required
def update_outfit(outfit_id):
	try:
		oid = _parse_object_id(outfit_id, 'outfit id')
	except Exception:
		return jsonify({'error': 'invalid outfit id'}), 400

	payload = request.get_json(silent=True) or {}
	allowed_fields = {
		'name',
		'style',
		'bio',
		'shirt',
		'pants',
		'published',
	}
	update_fields = {k: v for k, v in payload.items() if k in allowed_fields}

	if not update_fields:
		return jsonify({'error': 'nothing to update'}), 400

	result = current_app.db.outfits.update_one({'_id': oid}, {'$set': update_fields})
	if result.matched_count == 0:
		return jsonify({'error': 'outfit not found'}), 404

	outfit = current_app.db.outfits.find_one({'_id': oid})
	return jsonify(Outfit.from_doc(outfit).to_dict()), 200


@outfits_bp.delete('/outfits/<outfit_id>')
@token_required
def delete_outfit(outfit_id):
	try:
		oid = _parse_object_id(outfit_id, 'outfit id')
	except Exception:
		return jsonify({'error': 'invalid outfit id'}), 400

	result = current_app.db.outfits.delete_one({'_id': oid})
	if result.deleted_count == 0:
		return jsonify({'error': 'outfit not found'}), 404

	current_app.db.likes.delete_many({'outfit_id': oid})
	current_app.db.comments.delete_many({'outfit_id': oid})
	current_app.db.wardrobes.update_many({}, {'$pull': {'outfit_ids': oid}})

	return jsonify({'status': 'deleted'}), 200


@outfits_bp.get('/outfits/<outfit_id>/likes')
def get_outfit_likes(outfit_id):
	outfit, error_response = _get_outfit_doc_or_404(outfit_id)
	if error_response:
		return error_response

	outfit_oid = outfit.get('_id')
	likes_cursor = current_app.db.likes.find({'outfit_id': outfit_oid}).sort('created_at', -1)
	likes = [Like.from_doc(doc).to_dict() for doc in likes_cursor]

	return jsonify({'count': len(likes), 'likes': likes}), 200


@outfits_bp.post('/outfits/<outfit_id>/likes')
@token_required
def like_outfit(outfit_id):
	outfit, error_response = _get_outfit_doc_or_404(outfit_id)
	if error_response:
		return error_response

	user_id = g.current_user.get('_id')
	outfit_oid = outfit.get('_id')

	like_doc = {
		'outfit_id': outfit_oid,
		'user_id': user_id,
		'created_at': datetime.now(timezone.utc),
	}

	try:
		result = current_app.db.likes.insert_one(like_doc)
		created = current_app.db.likes.find_one({'_id': result.inserted_id})
		return jsonify(Like.from_doc(created).to_dict()), 201
	except DuplicateKeyError:
		existing = current_app.db.likes.find_one({'outfit_id': outfit_oid, 'user_id': user_id})
		return jsonify(Like.from_doc(existing).to_dict()), 200


@outfits_bp.delete('/outfits/<outfit_id>/likes')
@token_required
def unlike_outfit(outfit_id):
	outfit, error_response = _get_outfit_doc_or_404(outfit_id)
	if error_response:
		return error_response

	user_id = g.current_user.get('_id')
	outfit_oid = outfit.get('_id')

	result = current_app.db.likes.delete_one({'outfit_id': outfit_oid, 'user_id': user_id})
	if result.deleted_count == 0:
		return jsonify({'error': 'like not found'}), 404

	return jsonify({'status': 'unliked'}), 200


@outfits_bp.get('/outfits/<outfit_id>/comments')
def get_outfit_comments(outfit_id):
	outfit, error_response = _get_outfit_doc_or_404(outfit_id)
	if error_response:
		return error_response

	outfit_oid = outfit.get('_id')
	comments_cursor = current_app.db.comments.find({'outfit_id': outfit_oid}).sort('created_at', -1)
	comments = [Comment.from_doc(doc).to_dict() for doc in comments_cursor]

	return jsonify({'count': len(comments), 'comments': comments}), 200


@outfits_bp.post('/outfits/<outfit_id>/comments')
@token_required
def create_comment(outfit_id):
	outfit, error_response = _get_outfit_doc_or_404(outfit_id)
	if error_response:
		return error_response

	payload = request.get_json(silent=True) or {}
	content = (payload.get('content') or '').strip()
	if not content:
		return jsonify({'error': 'content is required'}), 400
	if len(content) > 1000:
		return jsonify({'error': 'content must be at most 1000 characters'}), 400

	user = g.current_user
	comment_doc = {
		'outfit_id': outfit.get('_id'),
		'user_id': user.get('_id'),
		'author': {
			'name': user.get('name'),
			'profile_picture': user.get('profile_picture'),
		},
		'content': content,
		'created_at': datetime.now(timezone.utc),
		'updated_at': datetime.now(timezone.utc),
	}

	result = current_app.db.comments.insert_one(comment_doc)
	created = current_app.db.comments.find_one({'_id': result.inserted_id})
	return jsonify(Comment.from_doc(created).to_dict()), 201


@outfits_bp.put('/outfits/<outfit_id>/comments/<comment_id>')
@token_required
def update_comment(outfit_id, comment_id):
	outfit, error_response = _get_outfit_doc_or_404(outfit_id)
	if error_response:
		return error_response

	comment_oid = _parse_object_id(comment_id, 'comment id')
	if not comment_oid:
		return jsonify({'error': 'invalid comment id'}), 400

	comment = current_app.db.comments.find_one({'_id': comment_oid, 'outfit_id': outfit.get('_id')})
	if not comment:
		return jsonify({'error': 'comment not found'}), 404

	is_owner = comment.get('user_id') == g.current_user.get('_id')
	is_admin = g.current_user.get('role') == 'admin'
	if not is_owner and not is_admin:
		return jsonify({'error': 'forbidden'}), 403

	payload = request.get_json(silent=True) or {}
	content = (payload.get('content') or '').strip()
	if not content:
		return jsonify({'error': 'content is required'}), 400
	if len(content) > 1000:
		return jsonify({'error': 'content must be at most 1000 characters'}), 400

	current_app.db.comments.update_one(
		{'_id': comment_oid},
		{'$set': {'content': content, 'updated_at': datetime.now(timezone.utc)}},
	)

	updated = current_app.db.comments.find_one({'_id': comment_oid})
	return jsonify(Comment.from_doc(updated).to_dict()), 200


@outfits_bp.delete('/outfits/<outfit_id>/comments/<comment_id>')
@token_required
def delete_comment(outfit_id, comment_id):
	outfit, error_response = _get_outfit_doc_or_404(outfit_id)
	if error_response:
		return error_response

	comment_oid = _parse_object_id(comment_id, 'comment id')
	if not comment_oid:
		return jsonify({'error': 'invalid comment id'}), 400

	comment = current_app.db.comments.find_one({'_id': comment_oid, 'outfit_id': outfit.get('_id')})
	if not comment:
		return jsonify({'error': 'comment not found'}), 404

	is_owner = comment.get('user_id') == g.current_user.get('_id')
	is_admin = g.current_user.get('role') == 'admin'
	if not is_owner and not is_admin:
		return jsonify({'error': 'forbidden'}), 403

	current_app.db.comments.delete_one({'_id': comment_oid})
	return jsonify({'status': 'deleted'}), 200
