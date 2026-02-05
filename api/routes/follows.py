from bson import ObjectId
from flask import Blueprint, current_app, g, jsonify, request

from api.routes.auth import token_required

follows_bp = Blueprint('follows', __name__)


@follows_bp.post('/follows')
@token_required
def follow_user():
	payload = request.get_json(silent=True) or {}
	target_user_id = payload.get('user_id')

	if not target_user_id:
		return jsonify({'error': 'user_id is required'}), 400

	try:
		target_oid = ObjectId(target_user_id)
	except Exception:
		return jsonify({'error': 'invalid user_id'}), 400

	current_user_id = str(g.current_user.get('_id'))

	if current_user_id == target_user_id:
		return jsonify({'error': 'cannot follow yourself'}), 400

	# Check if target user exists
	target_user = current_app.db.users.find_one({'_id': target_oid})
	if not target_user:
		return jsonify({'error': 'target user not found'}), 404

	# Check if already following
	existing = current_app.db.follows.find_one({
		'follower_id': current_user_id,
		'following_id': target_user_id,
	})
	if existing:
		return jsonify({'error': 'already following'}), 409

	# Create follow relationship
	follow_doc = {
		'follower_id': current_user_id,
		'following_id': target_user_id,
	}
	result = current_app.db.follows.insert_one(follow_doc)

	return jsonify({
		'id': str(result.inserted_id),
		'follower_id': current_user_id,
		'following_id': target_user_id,
	}), 201


@follows_bp.delete('/follows/<following_id>')
@token_required
def unfollow_user(following_id):
	try:
		following_oid = ObjectId(following_id)
	except Exception:
		return jsonify({'error': 'invalid user_id'}), 400

	current_user_id = str(g.current_user.get('_id'))

	result = current_app.db.follows.delete_one({
		'follower_id': current_user_id,
		'following_id': following_id,
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

	try:
		user_oid = ObjectId(user_id)
	except Exception:
		return jsonify({'error': 'invalid user_id'}), 400

	# Get all followers of the user
	followers = list(current_app.db.follows.find({'following_id': user_id}))
	follower_ids = [f.get('follower_id') for f in followers]

	# Get user details for each follower
	follower_users = [
		current_app.db.users.find_one({'_id': ObjectId(fid)})
		for fid in follower_ids
	]

	from api.models.user import serialize_user
	return jsonify([serialize_user(u) for u in follower_users if u]), 200


@follows_bp.get('/follows/following')
@token_required
def get_following():
	user_id = request.args.get('user_id')

	if not user_id:
		user_id = str(g.current_user.get('_id'))

	try:
		user_oid = ObjectId(user_id)
	except Exception:
		return jsonify({'error': 'invalid user_id'}), 400

	# Get all users that this user is following
	following = list(current_app.db.follows.find({'follower_id': user_id}))
	following_ids = [f.get('following_id') for f in following]

	# Get user details for each followed user
	following_users = [
		current_app.db.users.find_one({'_id': ObjectId(fid)})
		for fid in following_ids
	]

	from api.models.user import serialize_user
	return jsonify([serialize_user(u) for u in following_users if u]), 200


@follows_bp.get('/follows/is-following/<target_user_id>')
@token_required
def is_following(target_user_id):
	current_user_id = str(g.current_user.get('_id'))

	existing = current_app.db.follows.find_one({
		'follower_id': current_user_id,
		'following_id': target_user_id,
	})

	return jsonify({'is_following': existing is not None}), 200
