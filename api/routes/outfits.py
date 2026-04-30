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


@outfits_bp.get('/outfits/published')
def get_published_outfits():

	try:
		limit = request.args.get('limit', 100, type=int)
		skip = request.args.get('skip', 0, type=int)
		
		limit = min(abs(limit), 100) if limit > 0 else 100
		skip = max(0, skip)
		
		print(f"[GET /api/outfits/published] Fetching published outfits (limit={limit}, skip={skip})", flush=True)
		
		pipeline = [
			{'$match': {'published': True}},
			{'$sort': {'created_at': -1}},
			{'$skip': skip},
			{'$limit': limit},
			{
				'$lookup': {
					'from': 'users',
					'localField': 'user_id',
					'foreignField': '_id',
					'as': 'user_data'
				}
			},
			{
				'$addFields': {
					'user': {'$arrayElemAt': ['$user_data', 0]}
				}
			},
			{
				'$project': {
					'_id': 1,
					'name': 1,
					'gender': 1,
					'description': {'$ifNull': ['$description', '$bio']},
					'shirt': 1,
					'pants': 1,
					'skirt': 1,
					'accessory': 1,
					'user_id': 1,
					'published': 1,
					'created_at': 1,
					'user_name': '$user.name',
					'user_profile_pic': '$user.profile_picture'
				}
			}
		]
		
		results = list(current_app.db.outfits.aggregate(pipeline))
		print(f"[GET /api/outfits/published] Found {len(results)} published outfits", flush=True)
		
		outfits = []
		for doc in results:
			user_name = doc.get('user_name')
			user_profile_pic = doc.get('user_profile_pic')
			user_id = doc.get('user_id')
			
			outfit_dict = Outfit.from_doc(doc).to_dict()
			
			outfit_dict['userId'] = str(user_id) if user_id else None
			outfit_dict['userName'] = user_name
			outfit_dict['userProfilePic'] = user_profile_pic
			outfits.append(outfit_dict)
		
		return jsonify(outfits), 200
		
	except Exception as e:
		print(f"[GET /api/outfits/published] ERROR: {str(e)}", flush=True)
		import traceback
		print(f"[GET /api/outfits/published] Traceback: {traceback.format_exc()}", flush=True)
		return jsonify({'error': 'Failed to retrieve published outfits'}), 500


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
			'gender': outfit.gender,
			'description': outfit.description,
			'shirt': outfit.shirt,
			'pants': outfit.pants,
			'skirt': outfit.skirt,
			'accessory': outfit.accessory,
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
	oid = _parse_object_id(outfit_id, 'outfit id')
	if not oid:
		return jsonify({'error': 'invalid outfit id'}), 400

	outfit = current_app.db.outfits.find_one({'_id': oid})
	if not outfit:
		return jsonify({'error': 'outfit not found'}), 404

	return jsonify(Outfit.from_doc(outfit).to_dict()), 200


@outfits_bp.put('/outfits/<outfit_id>')
@token_required
def update_outfit(outfit_id):
	oid = _parse_object_id(outfit_id, 'outfit id')
	if not oid:
		return jsonify({'error': 'invalid outfit id'}), 400

	payload = request.get_json(silent=True) or {}
	if 'description' not in payload and 'bio' in payload:
		payload['description'] = payload.get('bio')
	if 'bio' in payload:
		payload.pop('bio')

	allowed_fields = {
		'name',
		'description',
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
	oid = _parse_object_id(outfit_id, 'outfit id')
	if not oid:
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
