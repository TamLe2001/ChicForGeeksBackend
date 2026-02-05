from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash


def normalize_user_payload(payload):
	if payload is None:
		return {}

	return {
		'name': payload.get('name'),
		'email': payload.get('email'),
		'profile_picture': payload.get('profile_picture'),
		'bio': payload.get('bio'),
		'birthday': payload.get('birthday'),
		'created_at': payload.get('created_at') or datetime.now(timezone.utc),
	}


def serialize_user(user_doc):
	if not user_doc:
		return None

	return {
		'id': str(user_doc.get('_id')),
		'name': user_doc.get('name'),
		'email': user_doc.get('email'),
		'profile_picture': user_doc.get('profile_picture'),
		'bio': user_doc.get('bio'),
		'birthday': user_doc.get('birthday'),
		'role': user_doc.get('role', 'user'),
		'created_at': user_doc.get('created_at'),
	}


def hash_password(password):
	return generate_password_hash(password)


def verify_password(password, password_hash):
	return check_password_hash(password_hash, password)
