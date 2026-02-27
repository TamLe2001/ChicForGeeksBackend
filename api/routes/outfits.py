from bson import ObjectId
from flask import Blueprint, current_app, g, jsonify, request
from datetime import datetime
import os

from api.models.outfit import Outfit
from api.routes.auth import token_required

outfits_bp = Blueprint('outfits', __name__)


def allowed_file(filename):
	"""Check if file extension is allowed for GLB files"""
	allowed_ext = {'glb', 'gltf'}
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_ext


@outfits_bp.post('/outfits/default')
def upload_default_outfit():
	"""Upload GLB files for default outfits"""
	try:
		# Validate file presence
		if 'file' not in request.files:
			return jsonify({'error': 'No file provided'}), 400
		
		file = request.files['file']
		
		if file.filename == '':
			return jsonify({'error': 'No file selected'}), 400
		
		if not allowed_file(file.filename):
			return jsonify({'error': 'Only GLB/GLTF files allowed'}), 400
		
		# Get category from request
		category = request.form.get('category') or request.args.get('category')
		
		if not category:
			return jsonify({'error': 'category is required (shirt, hat, pants, shoes)'}), 400
		
		valid_categories = {'shirt', 'hat', 'pants', 'shoes'}
		if category.lower() not in valid_categories:
			return jsonify({'error': f'Invalid category. Must be one of: {", ".join(valid_categories)}'}), 400
		
		# Check file size (max 100MB)
		max_size = current_app.config.get('MAX_FILE_SIZE', 100 * 1024 * 1024)
		if file.content_length and file.content_length > max_size:
			return jsonify({'error': 'File too large (max 100MB)'}), 413
		
		# Save file to local uploads/default directory
		upload_dir = os.path.join(current_app.root_path, '..', 'uploads', 'default', category.lower())
		os.makedirs(upload_dir, exist_ok=True)
		
		file_path = os.path.join(upload_dir, file.filename)
		file.save(file_path)
		
		# Save metadata to MongoDB
		file_doc = {
			'filename': file.filename,
			'user_id': 'default',
			'category': category.lower(),
			'file_path': file_path,
			'size': os.path.getsize(file_path),
			'content_type': file.content_type or 'application/octet-stream',
			'uploaded_at': datetime.utcnow()
		}
		
		result = current_app.db.files.insert_one(file_doc)
		
		return jsonify({
			'status': 'success',
			'message': 'Default outfit file uploaded successfully',
			'file_id': str(result.inserted_id),
			'filename': file.filename,
			'category': category.lower(),
			'file_path': file_path
		}), 201
		
	except Exception as e:
		return jsonify({'error': f'Server error: {str(e)}'}), 500


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
		'hat': outfit.hat.to_dict() if outfit.hat else None,
		'shirt': outfit.shirt.to_dict() if outfit.shirt else None,
		'pants': outfit.pants.to_dict() if outfit.pants else None,
		'shoes': outfit.shoes.to_dict() if outfit.shoes else None,
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
		oid = ObjectId(outfit_id)
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
		oid = ObjectId(outfit_id)
	except Exception:
		return jsonify({'error': 'invalid outfit id'}), 400

	payload = request.get_json(silent=True) or {}
	allowed_fields = {
		'name',
		'style',
		'bio',
		'hat',
		'shirt',
		'pants',
		'shoes',
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
		oid = ObjectId(outfit_id)
	except Exception:
		return jsonify({'error': 'invalid outfit id'}), 400

	result = current_app.db.outfits.delete_one({'_id': oid})
	if result.deleted_count == 0:
		return jsonify({'error': 'outfit not found'}), 404

	return jsonify({'status': 'deleted'}), 200
