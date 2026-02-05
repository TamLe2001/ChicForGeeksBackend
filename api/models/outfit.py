from datetime import datetime, timezone

def normalize_outfit_payload(payload):
	if payload is None:
		return {}

	return {
		'name': payload.get('name'),
		'user_id': payload.get('user_id'),
		'style': payload.get('style'),
		'bio': payload.get('bio'),
		'hat': payload.get('hat'),
		'shirt': payload.get('shirt'),
		'pants': payload.get('pants'),
        'shoes': payload.get('shoes'),
		'published': payload.get('published', False),
		'created_at': payload.get('created_at') or datetime.now(timezone.utc),
	}


def serialize_outfit(outfit_doc):
	if not outfit_doc:
		return None

	return {
		'id': str(outfit_doc.get('_id')),
		'name': outfit_doc.get('name'),
		'user_id': outfit_doc.get('user_id'),
		'style': outfit_doc.get('style'),
		'bio': outfit_doc.get('bio'),
		'hat': outfit_doc.get('hat'),
		'shirt': outfit_doc.get('shirt'),
		'pants': outfit_doc.get('pants'),
        'shoes': outfit_doc.get('shoes'),
        'published': outfit_doc.get('published', False),
		'created_at': outfit_doc.get('created_at'),
	}
