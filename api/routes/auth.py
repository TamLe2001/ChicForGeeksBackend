from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from bson import ObjectId
from flask import Blueprint, current_app, g, jsonify, request

from api.models.user import hash_password, serialize_user, verify_password

auth_bp = Blueprint('auth', __name__)


def _get_jwt_secret():
	return current_app.config.get('JWT_SECRET', current_app.config.get('SECRET_KEY'))


def _generate_token(user_doc):
	expires_in = current_app.config.get('JWT_EXPIRES_MINUTES', 60)
	now = datetime.now(timezone.utc)

	payload = {
		'sub': str(user_doc.get('_id')),
		'email': user_doc.get('email'),
		'role': user_doc.get('role', 'user'),
		'iat': now,
		'exp': now + timedelta(minutes=expires_in),
	}

	return jwt.encode(payload, _get_jwt_secret(), algorithm='HS256')


def token_required(handler):
	@wraps(handler)
	def wrapper(*args, **kwargs):
		auth_header = request.headers.get('Authorization', '')
		if not auth_header.startswith('Bearer '):
			return jsonify({'error': 'missing or invalid authorization header'}), 401

		token = auth_header.split(' ', 1)[1].strip()
		if not token:
			return jsonify({'error': 'missing token'}), 401

		try:
			decoded = jwt.decode(token, _get_jwt_secret(), algorithms=['HS256'])
		except jwt.ExpiredSignatureError:
			return jsonify({'error': 'token expired'}), 401
		except jwt.InvalidTokenError:
			return jsonify({'error': 'invalid token'}), 401

		try:
			user_id = ObjectId(decoded.get('sub'))
		except Exception:
			return jsonify({'error': 'invalid token user id'}), 401

		user = current_app.db.users.find_one({'_id': user_id})
		if not user:
			return jsonify({'error': 'user not found'}), 401

		g.current_user = user
		return handler(*args, **kwargs)

	return wrapper


def role_required(*roles):
	def decorator(handler):
		@wraps(handler)
		def wrapper(*args, **kwargs):
			user = getattr(g, 'current_user', None)
			if not user or user.get('role') not in roles:
				return jsonify({'error': 'forbidden'}), 403
			return handler(*args, **kwargs)

		return wrapper

	return decorator


@auth_bp.post('/auth/register')
def register():
	payload = request.get_json(silent=True) or {}
	name = payload.get('name')
	email = payload.get('email')
	password = payload.get('password')

	if not name or not email or not password:
		return jsonify({'error': 'name, email, and password are required'}), 400

	if current_app.db.users.find_one({'email': email}):
		return jsonify({'error': 'email already registered'}), 409

	user_doc = {
		'name': name,
		'email': email,
		'password_hash': hash_password(password),
		'role': payload.get('role', 'user'),
		'profile_picture': payload.get('profile_picture'),
		'bio': payload.get('bio', ''),
		'birthday': payload.get('birthday'),
		'created_at': datetime.now(timezone.utc),
	}

	result = current_app.db.users.insert_one(user_doc)
	created = current_app.db.users.find_one({'_id': result.inserted_id})

	token = _generate_token(created)
	return jsonify({'token': token, 'user': serialize_user(created)}), 201


@auth_bp.post('/auth/login')
def login():
	payload = request.get_json(silent=True) or {}
	email = payload.get('email')
	password = payload.get('password')

	if not email or not password:
		return jsonify({'error': 'email and password are required'}), 400

	user = current_app.db.users.find_one({'email': email})
	if not user or not verify_password(password, user.get('password_hash', '')):
		return jsonify({'error': 'invalid credentials'}), 401

	token = _generate_token(user)
	return jsonify({'token': token, 'user': serialize_user(user)}), 200


@auth_bp.get('/auth/me')
@token_required
def me():
	return jsonify(serialize_user(g.current_user)), 200