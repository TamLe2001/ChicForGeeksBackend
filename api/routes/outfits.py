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

outfits_bp = Blueprint('outfits', __name__)


def _get_thumbnail_service() -> ThumbnailService:
	"""Get or create thumbnail service instance."""
	uploads_path = current_app.config.get('UPLOAD_PATH', 'uploads')
	return ThumbnailService(current_app.db, uploads_path)


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
	print(f"[POST /api/outfits] User {g.current_user.get('_id')} creating outfit", flush=True)
	payload = request.get_json(silent=True) or {}

	if not payload.get('name'):
		return jsonify({'error': 'name is required'}), 400

	user_id = str(g.current_user.get('_id'))
	payload['user_id'] = user_id

	try:
		outfit = Outfit.from_payload(payload)
		print(f"[POST /api/outfits] Outfit object created: {outfit.name}", flush=True)
		
		outfit_doc = {
			'name': outfit.name,
			'user_id': outfit.user_id,
			'bio': outfit.bio,
			'shirt': outfit.shirt.to_dict() if outfit.shirt else None,
			'pants': outfit.pants.to_dict() if outfit.pants else None,
			'published': outfit.published,
			'created_at': outfit.created_at,
		}
		print(f"[POST /api/outfits] Outfit doc prepared: {outfit_doc}", flush=True)
		
		result = current_app.db.outfits.insert_one(outfit_doc)
		outfit_id = str(result.inserted_id)
		print(f"[POST /api/outfits] Outfit inserted with ID: {outfit_id}", flush=True)

		# Handle thumbnail generation if provided
		thumbnail_url = None
		if payload.get('thumbnail'):
			try:
				thumbnail_service = _get_thumbnail_service()
				thumbnail_url = thumbnail_service.generate_thumbnail(
					outfit_id,
					payload.get('thumbnail'),
					outfit.name
				)
				print(f"[POST /api/outfits] Thumbnail generated: {thumbnail_url}", flush=True)
			except Exception as e:
				print(f"[POST /api/outfits] Warning: Failed to generate thumbnail: {str(e)}", flush=True)
				# Continue without thumbnail rather than fail the entire request

		created = current_app.db.outfits.find_one({'_id': result.inserted_id})
		outfit_dict = Outfit.from_doc(created).to_dict()
		
		# Add thumbnail URL to response
		if thumbnail_url:
			outfit_dict['thumbnail'] = thumbnail_url

		print(f"[POST /api/outfits] Success! Outfit created: {outfit_id}", flush=True)
		return jsonify(outfit_dict), 201
		
	except Exception as e:
		print(f"[POST /api/outfits] ERROR: {str(e)}", flush=True)
		print(f"[POST /api/outfits] Exception type: {type(e).__name__}", flush=True)
		import traceback
		print(f"[POST /api/outfits] Traceback: {traceback.format_exc()}", flush=True)
		return jsonify({'error': f'Server error: {str(e)}'}), 500


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
	
	# Delete associated thumbnail
	try:
		thumbnail_service = _get_thumbnail_service()
		thumbnail_service.delete_thumbnail(outfit_id)
	except Exception as e:
		print(f"Warning: Failed to delete thumbnail: {str(e)}")

	return jsonify({'status': 'deleted'}), 200


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
