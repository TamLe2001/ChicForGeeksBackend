from datetime import datetime, timezone

from bson import ObjectId
from flask import Blueprint, current_app, g, jsonify

from api.models.outfit import Outfit
from api.models.wardrobe import Wardrobe
from api.routes.auth import token_required

wardrobes_bp = Blueprint('wardrobes', __name__)


def _parse_object_id(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


def _get_or_create_wardrobe(user_id: str):
    now = datetime.now(timezone.utc)
    wardrobe_doc = current_app.db.wardrobes.find_one({'user_id': user_id})

    if wardrobe_doc:
        return wardrobe_doc

    created_doc = {
        'user_id': user_id,
        'outfit_ids': [],
        'created_at': now,
        'updated_at': now,
    }
    result = current_app.db.wardrobes.insert_one(created_doc)
    return current_app.db.wardrobes.find_one({'_id': result.inserted_id})


@wardrobes_bp.get('/wardrobes/me')
@token_required
def get_my_wardrobe():
    user_id = str(g.current_user.get('_id'))
    wardrobe_doc = _get_or_create_wardrobe(user_id)

    outfit_object_ids = [oid for oid in (wardrobe_doc.get('outfit_ids') or []) if isinstance(oid, ObjectId)]
    outfits = []
    if outfit_object_ids:
        outfit_docs = current_app.db.outfits.find({'_id': {'$in': outfit_object_ids}}).sort('created_at', -1)
        outfits = [Outfit.from_doc(outfit_doc).to_dict() for outfit_doc in outfit_docs]

    wardrobe = Wardrobe.from_doc(wardrobe_doc)
    return jsonify({'wardrobe': wardrobe.to_dict(), 'outfits': outfits}), 200


@wardrobes_bp.post('/wardrobes/me/outfits/<outfit_id>')
@token_required
def add_outfit_to_wardrobe(outfit_id):
    outfit_oid = _parse_object_id(outfit_id)
    if not outfit_oid:
        return jsonify({'error': 'invalid outfit id'}), 400

    user_id = str(g.current_user.get('_id'))
    outfit_doc = current_app.db.outfits.find_one({'_id': outfit_oid})
    if not outfit_doc:
        return jsonify({'error': 'outfit not found'}), 404

    if outfit_doc.get('user_id') != user_id:
        return jsonify({'error': 'forbidden'}), 403

    _get_or_create_wardrobe(user_id)
    current_app.db.wardrobes.update_one(
        {'user_id': user_id},
        {
            '$addToSet': {'outfit_ids': outfit_oid},
            '$set': {'updated_at': datetime.now(timezone.utc)},
        },
    )

    updated = current_app.db.wardrobes.find_one({'user_id': user_id})
    return jsonify(Wardrobe.from_doc(updated).to_dict()), 200


@wardrobes_bp.delete('/wardrobes/me/outfits/<outfit_id>')
@token_required
def remove_outfit_from_wardrobe(outfit_id):
    outfit_oid = _parse_object_id(outfit_id)
    if not outfit_oid:
        return jsonify({'error': 'invalid outfit id'}), 400

    user_id = str(g.current_user.get('_id'))
    _get_or_create_wardrobe(user_id)

    result = current_app.db.wardrobes.update_one(
        {'user_id': user_id},
        {
            '$pull': {'outfit_ids': outfit_oid},
            '$set': {'updated_at': datetime.now(timezone.utc)},
        },
    )

    if result.modified_count == 0:
        return jsonify({'error': 'outfit not in wardrobe'}), 404

    updated = current_app.db.wardrobes.find_one({'user_id': user_id})
    return jsonify(Wardrobe.from_doc(updated).to_dict()), 200
