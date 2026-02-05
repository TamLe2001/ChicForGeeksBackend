from datetime import datetime, timezone

def normalize_follow_payload(payload):
	if payload is None:
		return {}

	return {
		'follower_id': payload.get('follower_id'),
		'followed_id': payload.get('followed_id'),
		'created_at': payload.get('created_at') or datetime.now(timezone.utc),
	}
		

def serialize_follow(follow_doc):
    if not follow_doc:
        return None

    return {
        'id': str(follow_doc.get('_id')),
        'follower_id': follow_doc.get('follower_id'),
        'followed_id': follow_doc.get('followed_id'),
        'created_at': follow_doc.get('created_at'),
    }