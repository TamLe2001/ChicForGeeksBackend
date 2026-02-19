from datetime import datetime

import requests
from flask import Blueprint, current_app, jsonify, request

retexture_bp = Blueprint('retexture', __name__)


def _require_api_key():
    api_key = request.headers.get('X-API-Key')
    expected = current_app.config.get('INTERNAL_API_KEY')
    if not expected or api_key != expected:
        return jsonify({'error': 'unauthorized'}), 401
    return None


@retexture_bp.post('/retexture')
def retexture():
    auth_error = _require_api_key()
    if auth_error:
        return auth_error

    payload = request.get_json(silent=True) or {}

    model_url = payload.get('model_url')
    text_style_prompt = payload.get('text_style_prompt')

    if not model_url or not text_style_prompt:
        return jsonify({'error': 'model_url and text_style_prompt are required'}), 400

    request_body = {
        'model_url': model_url,
        'text_style_prompt': text_style_prompt,
        'enable_original_uv': bool(payload.get('enable_original_uv', True)),
        'enable_pbr': bool(payload.get('enable_pbr', True)),
    }

    meshy_api_key = current_app.config.get('MESHY_API_KEY')
    if not meshy_api_key:
        return jsonify({'error': 'meshy api key not configured'}), 500

    try:
        response = requests.post(
            'https://api.meshy.ai/openapi/v1/retexture',
            json=request_body,
            headers={
                'Authorization': f'Bearer {meshy_api_key}',
                'Content-Type': 'application/json',
            },
            timeout=60,
        )
    except requests.RequestException as exc:
        return jsonify({'error': f'request failed: {exc}'}), 502

    try:
        response_json = response.json()
    except ValueError:
        response_json = {'raw': response.text}

    job_doc = {
        'request': request_body,
        'response': response_json,
        'status_code': response.status_code,
        'created_at': datetime.utcnow(),
    }
    current_app.db.meshy_jobs.insert_one(job_doc)

    return jsonify(response_json), response.status_code
