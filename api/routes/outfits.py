from bson import ObjectId
from flask import Blueprint, current_app, g, jsonify, request, send_from_directory
from datetime import datetime
import os

from api.models.outfit import Outfit
from api.routes.auth import token_required

outfits_bp = Blueprint('outfits', __name__)


@outfits_bp.get('/outfits/default')
def get_default_outfits():
	"""Get list of default GLB files or serve a specific file"""
	try:
		# Check if requesting a specific file
		filename = request.args.get('filename')
		category = request.args.get('category')
		
		uploads_dir = os.path.join(current_app.root_path, '..', 'uploads', 'default')
		
		# If filename is provided, serve the file
		if filename:
			if category:
				file_path = os.path.join(uploads_dir, category.lower(), filename)
			else:
				file_path = os.path.join(uploads_dir, filename)
			
			if os.path.exists(file_path):
				directory = os.path.dirname(file_path)
				filename_only = os.path.basename(file_path)
				return send_from_directory(directory, filename_only)
			else:
				return jsonify({'error': 'File not found'}), 404
		
		# Otherwise, return list of available files
		files_list = []
		valid_extensions = {'.glb', '.gltf'}
		
		# Filter by category if provided
		if category:
			category_dir = os.path.join(uploads_dir, category.lower())
			if os.path.exists(category_dir):
				for filename in os.listdir(category_dir):
					if any(filename.lower().endswith(ext) for ext in valid_extensions):
						file_path = os.path.join(category_dir, filename)
						files_list.append({
							'filename': filename,
							'category': category.lower(),
							'size': os.path.getsize(file_path),
							'url': f'/outfits/default?category={category.lower()}&filename={filename}'
						})
		else:
			# List all default files from all categories
			if os.path.exists(uploads_dir):
				for category_name in os.listdir(uploads_dir):
					category_path = os.path.join(uploads_dir, category_name)
					if os.path.isdir(category_path):
						for filename in os.listdir(category_path):
							if any(filename.lower().endswith(ext) for ext in valid_extensions):
								file_path = os.path.join(category_path, filename)
								files_list.append({
									'filename': filename,
									'category': category_name,
									'size': os.path.getsize(file_path),
									'url': f'/outfits/default?category={category_name}&filename={filename}'
								})
		
		return jsonify({
			'status': 'success',
			'count': len(files_list),
			'files': files_list
		}), 200
		
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
