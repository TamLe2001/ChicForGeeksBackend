import os
from datetime import datetime, timezone

from bson import ObjectId
from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from api.models.user import normalize_user_payload, serialize_user
from api.routes.auth import token_required

users_bp = Blueprint('users', __name__)


@users_bp.get('/users')
@token_required
def list_users():
	users = current_app.db.users.find().sort('created_at', -1)
	return jsonify([serialize_user(u) for u in users]), 200

@users_bp.get('/usersnotoken')
def list_users_notoken():
	users = current_app.db.users.find().sort('created_at', -1)
	return jsonify([serialize_user(u) for u in users]), 200


@users_bp.post('/users')
@token_required
def create_user():
	# Check if request has file upload
	if request.content_type and 'multipart/form-data' in request.content_type:
		# Handle file upload
		name = request.form.get('name')
		email = request.form.get('email')
		
		if not name or not email:
			return jsonify({'error': 'name and email are required'}), 400
		
		payload = {
			'name': name,
			'email': email,
			'bio': request.form.get('bio'),
			'birthday': request.form.get('birthday'),
		}
		
		# Handle profile picture upload
		if 'profile_picture' in request.files:
			file = request.files['profile_picture']
			if file and file.filename:
				filename = secure_filename(file.filename)
				timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
				unique_filename = f"{timestamp}_{filename}"
				
				upload_folder = os.path.join(current_app.root_path, '..', 'uploads', 'profiles')
				os.makedirs(upload_folder, exist_ok=True)
				
				filepath = os.path.join(upload_folder, unique_filename)
				file.save(filepath)
				
				payload['profile_picture'] = f"/uploads/profiles/{unique_filename}"
		
		user_doc = normalize_user_payload(payload)
		result = current_app.db.users.insert_one(user_doc)
		
		created = current_app.db.users.find_one({'_id': result.inserted_id})
		return jsonify(serialize_user(created)), 201
	else:
		# Handle JSON request
		payload = request.get_json(silent=True) or {}
		
		if not payload.get('name') or not payload.get('email'):
			return jsonify({'error': 'name and email are required'}), 400
		
		user_doc = normalize_user_payload(payload)
		result = current_app.db.users.insert_one(user_doc)
		
		created = current_app.db.users.find_one({'_id': result.inserted_id})
		return jsonify(serialize_user(created)), 201


@users_bp.get('/users/<user_id>')
@token_required
def get_user(user_id):
	try:
		oid = ObjectId(user_id)
	except Exception:
		return jsonify({'error': 'invalid user id'}), 400

	user = current_app.db.users.find_one({'_id': oid})
	if not user:
		return jsonify({'error': 'user not found'}), 404

	return jsonify(serialize_user(user)), 200

@users_bp.put('/users/<user_id>')
@token_required
def update_user(user_id):
	try:
		oid = ObjectId(user_id)
	except Exception:
		return jsonify({'error': 'invalid user id'}), 400
	
	# Check if request has file upload
	if request.content_type and 'multipart/form-data' in request.content_type:
		# Handle file upload
		update_fields = {}
		
		for field in ['name', 'email', 'bio', 'birthday']:
			value = request.form.get(field)
			if value is not None:
				update_fields[field] = value
		
		# Handle profile picture upload
		if 'profile_picture' in request.files:
			file = request.files['profile_picture']
			if file and file.filename:
				filename = secure_filename(file.filename)
				timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
				unique_filename = f"{timestamp}_{filename}"
				
				upload_folder = os.path.join(current_app.root_path, '..', 'uploads', 'profiles')
				os.makedirs(upload_folder, exist_ok=True)
				
				filepath = os.path.join(upload_folder, unique_filename)
				file.save(filepath)
				
				update_fields['profile_picture'] = f"/uploads/profiles/{unique_filename}"
	else:
		# Handle JSON request
		payload = request.get_json(silent=True) or {}
		update_fields = {k: v for k, v in payload.items() if k in {'name', 'email', 'profile_picture', 'bio', 'birthday'}}

	if not update_fields:
		return jsonify({'error': 'nothing to update'}), 400

	result = current_app.db.users.update_one({'_id': oid}, {'$set': update_fields})
	if result.matched_count == 0:
		return jsonify({'error': 'user not found'}), 404

	user = current_app.db.users.find_one({'_id': oid})
	return jsonify(serialize_user(user)), 200


@users_bp.delete('/users/<user_id>')
@token_required
def delete_user(user_id):
	try:
		oid = ObjectId(user_id)
	except Exception:
		return jsonify({'error': 'invalid user id'}), 400

	result = current_app.db.users.delete_one({'_id': oid})
	if result.deleted_count == 0:
		return jsonify({'error': 'user not found'}), 404

	return jsonify({'status': 'deleted'}), 200
