from bson import ObjectId
from flask import Blueprint, current_app, jsonify, request, send_file
from api.models.user import User
from api.routes.auth import token_required
from io import BytesIO
import requests
from requests.auth import HTTPBasicAuth

users_bp = Blueprint('users', __name__)


@users_bp.get('/users')
@token_required
def list_users():
	users = current_app.db.users.find().sort('created_at', -1)
	return jsonify([User.from_doc(u).to_dict() for u in users]), 200


@users_bp.post('/users')
@token_required
def create_user():
	payload = request.get_json(silent=True) or {}

	if not payload.get('name') or not payload.get('email'):
		return jsonify({'error': 'name and email are required'}), 400

	user = User.from_payload(payload)
	
	user_doc = {
		'name': user.name.strip(),
		'email': user.email.strip(),
		'profile_picture': user.profile_picture,
		'bio': user.bio.strip(),
		'birthday': user.birthday,
		'created_at': user.created_at,
	}
	
	result = current_app.db.users.insert_one(user_doc)
	created = current_app.db.users.find_one({'_id': result.inserted_id})
	return jsonify(User.from_doc(created).to_dict()), 201


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

	return jsonify(User.from_doc(user).to_dict()), 200

@users_bp.put('/users/<user_id>')
@token_required
def update_user(user_id):
	try:
		oid = ObjectId(user_id)
	except Exception:
		return jsonify({'error': 'invalid user id'}), 400

	payload = request.get_json(silent=True) or {}
	update_fields = {k: v for k, v in payload.items() if k in {'name', 'email', 'profile_picture', 'bio', 'birthday'}}

	if not update_fields:
		return jsonify({'error': 'nothing to update'}), 400

	result = current_app.db.users.update_one({'_id': oid}, {'$set': update_fields})
	if result.matched_count == 0:
		return jsonify({'error': 'user not found'}), 404

	user = current_app.db.users.find_one({'_id': oid})
	return jsonify(User.from_doc(user).to_dict()), 200


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


@users_bp.get('/users/<user_id>/profile-picture')
def get_user_profile_picture(user_id):
	"""Serve profile picture from NextCloud, bypassing CORS restrictions."""
	try:
		oid = ObjectId(user_id)
	except Exception:
		return jsonify({'error': 'invalid user id'}), 400

	user = current_app.db.users.find_one({'_id': oid})
	if not user or not user.get('profile_picture'):
		return jsonify({'error': 'profile picture not found'}), 404

	cloud = getattr(current_app, 'cloud_service', None)
	if not cloud:
		return jsonify({'error': 'cloud service not available'}), 500

	try:
		response = requests.get(
			user.get('profile_picture'),
			auth=HTTPBasicAuth(cloud.nextcloud_user, cloud.nextcloud_pass),
			timeout=30
		)
		if response.status_code != 200:
			return jsonify({'error': 'failed to fetch profile picture'}), 500

		content_type = response.headers.get('Content-Type', 'image/jpeg')
		return send_file(
			BytesIO(response.content),
			mimetype=content_type,
			download_name=f"profile_{user_id}.jpg"
		)
	except requests.exceptions.Timeout:
		return jsonify({'error': 'download timeout'}), 504
	except requests.exceptions.RequestException as e:
		return jsonify({'error': f'failed to download: {str(e)}'}), 500
	except Exception as e:
		return jsonify({'error': f'server error: {str(e)}'}), 500
