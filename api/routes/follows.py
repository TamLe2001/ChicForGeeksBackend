from datetime import datetime, timezone

from bson import ObjectId
from flask import Blueprint, current_app, g, jsonify, request
from pymongo.errors import DuplicateKeyError

from api.models.follow import Follow
from api.models.user import User
from api.routes.auth import token_required

follows_bp = Blueprint('follows', __name__)


def _parse_object_id(value):
	try:
		return ObjectId(value)
	except Exception:
		return None


def _normalize_follow_doc(follow_doc):
	if not follow_doc:
		return None

	if 'followed_id' not in follow_doc and follow_doc.get('following_id'):
		follow_doc['followed_id'] = follow_doc.get('following_id')

	return follow_doc


@follows_bp.post('/follows')
@token_required
def follow_user():
	payload = request.get_json(silent=True) or {}
	target_user_id = payload.get('followed_id') or payload.get('user_id')

	if not target_user_id:
		return jsonify({'error': 'followed_id is required'}), 400

	target_oid = _parse_object_id(target_user_id)
	if not target_oid:
		return jsonify({'error': 'invalid followed_id'}), 400

	current_user_id = str(g.current_user.get('_id'))

	if current_user_id == target_user_id:
		return jsonify({'error': 'cannot follow yourself'}), 400

	# Check if target user exists
	target_user = current_app.db.users.find_one({'_id': target_oid})
	if not target_user:
		return jsonify({'error': 'target user not found'}), 404

	# Create follow relationship
	follow_doc = {
		'follower_id': current_user_id,
		'followed_id': target_user_id,
		'created_at': datetime.now(timezone.utc),
	}

	try:
		result = current_app.db.follows.insert_one(follow_doc)
	except DuplicateKeyError:
		return jsonify({'error': 'already following'}), 409

	created = current_app.db.follows.find_one({'_id': result.inserted_id})
	created_follow = Follow.from_doc(_normalize_follow_doc(created)).to_dict()
	created_follow['following_id'] = created_follow['followed_id']

	return jsonify(created_follow), 201


@follows_bp.delete('/follows/<followed_id>')
@token_required
def unfollow_user(followed_id):
	followed_oid = _parse_object_id(followed_id)
	if not followed_oid:
		return jsonify({'error': 'invalid followed_id'}), 400

	current_user_id = str(g.current_user.get('_id'))

	result = current_app.db.follows.delete_one({
		'follower_id': current_user_id,
		'followed_id': followed_id,
	})

	if result.deleted_count == 0:
		return jsonify({'error': 'not following'}), 404

	return jsonify({'status': 'unfollowed'}), 200


@follows_bp.get('/follows/followers')
@token_required
def get_followers():
	user_id = request.args.get('user_id')

	if not user_id:
		user_id = str(g.current_user.get('_id'))

	if not _parse_object_id(user_id):
		return jsonify({'error': 'invalid user_id'}), 400

	# Get all followers of the user
	followers = list(current_app.db.follows.find({'followed_id': user_id}).sort('created_at', -1))
	follower_ids = [f.get('follower_id') for f in followers]
	follower_object_ids = [ObjectId(fid) for fid in follower_ids if ObjectId.is_valid(fid)]

	if not follower_object_ids:
		return jsonify([]), 200

	follower_users = list(current_app.db.users.find({'_id': {'$in': follower_object_ids}}))
	user_map = {str(user.get('_id')): User.from_doc(user).to_dict() for user in follower_users}
	ordered_users = [user_map[fid] for fid in follower_ids if fid in user_map]

	return jsonify(ordered_users), 200


@follows_bp.get('/follows/following')
@token_required
def get_following():
	user_id = request.args.get('user_id')

	if not user_id:
		user_id = str(g.current_user.get('_id'))

	if not _parse_object_id(user_id):
		return jsonify({'error': 'invalid user_id'}), 400

	# Get all users that this user is following
	following = list(current_app.db.follows.find({'follower_id': user_id}))
	followed_ids = [f.get('followed_id') or f.get('following_id') for f in following]
	followed_object_ids = [ObjectId(fid) for fid in followed_ids if ObjectId.is_valid(fid)]

	if not followed_object_ids:
		return jsonify([]), 200

	following_users = list(current_app.db.users.find({'_id': {'$in': followed_object_ids}}))
	user_map = {str(user.get('_id')): User.from_doc(user).to_dict() for user in following_users}
	ordered_users = [user_map[fid] for fid in followed_ids if fid in user_map]

	return jsonify(ordered_users), 200


@follows_bp.get('/follows/is-following/<target_user_id>')
@token_required
def is_following(target_user_id):
	current_user_id = str(g.current_user.get('_id'))
	if not _parse_object_id(target_user_id):
		return jsonify({'error': 'invalid target_user_id'}), 400

	existing = current_app.db.follows.find_one({
		'follower_id': current_user_id,
		'$or': [
			{'followed_id': target_user_id},
			{'following_id': target_user_id},
		],
	})

	return jsonify({'is_following': existing is not None}), 200
