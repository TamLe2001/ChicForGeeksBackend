from flask import Blueprint, Response, jsonify, request, current_app, send_file, stream_with_context, g
import requests
from requests.auth import HTTPBasicAuth
from io import BytesIO
import os
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId

from api.routes.auth import token_required


files_bp = Blueprint('files', __name__)


@files_bp.route('/upload', methods=['POST'])
def upload_to_cloud():
    """Legacy endpoint kept for compatibility. Prefer /upload/models and /upload/images."""
    return jsonify({'error': 'Endpoint deprecated. Use /upload/models for GLB/GLTF or /upload/images for images.'}), 410


@files_bp.route('/upload/models', methods=['POST'])
@token_required
def upload_model_to_cloud():
    """Upload GLB/GLTF files to NextCloud storage with category organization.
    
    Required fields:
    - file: GLB/GLTF file
    - category: shirt, pants, skirt, or accessory
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        category = request.form.get('category') or request.args.get('category')
        if not category:
            return jsonify({'error': 'category is required (shirt, pants, skirt, accessory)'}), 400

        user_id = str(g.current_user.get('_id'))
        
        cloud = getattr(current_app, 'cloud_service', None)
        if not cloud:
            return jsonify({'error': 'cloud service not available'}), 500

        result, status_code = cloud.upload_model(file, file.filename, user_id, category)
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@files_bp.route('/upload/profile', methods=['POST'])
@token_required
def upload_profile_picture_to_cloud():
    """Upload profile image to cloud and return profile picture URL."""
    try:
        profile_file = request.files.get('profile_picture') or request.files.get('file')
        if not profile_file or not profile_file.filename:
            return jsonify({'error': 'profile_picture file is required'}), 400

        user_id = str(g.current_user.get('_id'))
        
        cloud = getattr(current_app, 'cloud_service', None)
        if not cloud:
            return jsonify({'error': 'cloud service not available'}), 500

        upload_result, upload_code = cloud.upload_image_profile(profile_file, user_id)
        if upload_code != 201:
            return jsonify(upload_result), upload_code

        profile_picture = upload_result.get('cloud_url')
        if not profile_picture:
            return jsonify({'error': 'upload succeeded but no profile URL returned'}), 500

        try:
            current_app.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'profile_picture': profile_picture}},
            )
        except Exception:
            # If update fails, still return upload URL
            pass

        return jsonify({
            'status': 'success',
            'message': 'Profile picture uploaded successfully',
            'profile_picture': profile_picture,
            'file_id': upload_result.get('file_id'),
            'filename': upload_result.get('filename'),
        }), 201

    except Exception as e:
        return jsonify({'error': f'Failed to upload profile picture: {str(e)}'}), 500


@files_bp.route('/upload/images', methods=['POST'])
@token_required
def upload_image_to_cloud():
    """Upload image files to NextCloud storage (PNG/JPG/JPEG)."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        user_id = str(g.current_user.get('_id'))
        
        cloud = getattr(current_app, 'cloud_service', None)
        if not cloud:
            return jsonify({'error': 'cloud service not available'}), 500

        result, status_code = cloud.upload_image_custom(file, file.filename)
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({'error': f'Failed to upload image: {str(e)}'}), 500


@files_bp.route('/files', methods=['GET'])
def list_files():
    """List all uploaded files, optionally filtered by user_id and category."""
    try:
        user_id = request.args.get('user_id')
        category = request.args.get('category')
        
        query = {}
        if user_id:
            query['user_id'] = user_id
        if category:
            query['category'] = category.lower()
        
        files = list(current_app.db.files.find(
            query, 
            {'_id': 1, 'filename': 1, 'url': 1, 'size': 1, 'user_id': 1, 'category': 1, 'uploaded_at': 1}
        ))
        
        # Convert ObjectId to string for JSON serialization
        for f in files:
            f['_id'] = str(f['_id'])
        
        return jsonify({'status': 'success', 'files': files}), 200

    except Exception as e:
        return jsonify({'error': f'Failed to fetch files: {str(e)}'}), 500


@files_bp.route('/files/<file_id>', methods=['GET'])
def get_file(file_id):
    """Get file metadata by ID."""
    try:
        file_doc = current_app.db.files.find_one({'_id': ObjectId(file_id)})
        
        if not file_doc:
            return jsonify({'error': 'File not found'}), 404
        
        file_doc['_id'] = str(file_doc['_id'])
        return jsonify({'status': 'success', 'file': file_doc}), 200

    except Exception as e:
        return jsonify({'error': f'Failed to fetch file: {str(e)}'}), 500


@files_bp.route('/files/<file_id>', methods=['DELETE'])
@token_required
def delete_file(file_id):
    """Delete file from NextCloud and database."""
    try:
        cloud = getattr(current_app, 'cloud_service', None)
        if not cloud:
            return jsonify({'error': 'cloud service not available'}), 500

        result, status_code = cloud.delete_file(file_id)
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({'error': f'Failed to delete file: {str(e)}'}), 500


@files_bp.route('/files', methods=['DELETE'])
@token_required
def delete_file_by_url():
    """Delete file by URL payload."""
    try:
        payload = request.get_json(silent=True) or {}
        file_url = payload.get('url')
        if not file_url:
            return jsonify({'error': 'url is required'}), 400

        file_doc = current_app.db.files.find_one({'url': file_url})
        if not file_doc:
            return jsonify({'error': 'File not found'}), 404

        cloud = getattr(current_app, 'cloud_service', None)
        if not cloud:
            return jsonify({'error': 'cloud service not available'}), 500

        result, status_code = cloud.delete_file(str(file_doc['_id']))
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({'error': f'Failed to delete file: {str(e)}'}), 500


@files_bp.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    """Download file from NextCloud storage."""
    try:
        file_doc = current_app.db.files.find_one({'_id': ObjectId(file_id)})
        if not file_doc:
            return jsonify({'error': 'File not found'}), 404
        
        cloud = getattr(current_app, 'cloud_service', None)
        if not cloud:
            return jsonify({'error': 'cloud service not available'}), 500

        response = requests.get(
            file_doc['url'],
            auth=HTTPBasicAuth(cloud.nextcloud_user, cloud.nextcloud_pass),
            timeout=30
        )
        
        if response.status_code != 200:
            return jsonify({'error': f'Failed to download file: {response.status_code}'}), 500
        
        return send_file(
            BytesIO(response.content),
            mimetype=file_doc.get('content_type', 'application/octet-stream'),
            as_attachment=True,
            download_name=file_doc['filename']
        )

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Download timeout - file may be too large'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 502
    except Exception as e:
        return jsonify({'error': f'Failed to download file: {str(e)}'}), 500


@files_bp.route('/files/<file_id>/content', methods=['GET'])
def get_file_content(file_id):
    """Stream file content from NextCloud for frontend consumption."""
    try:
        file_doc = current_app.db.files.find_one({'_id': ObjectId(file_id)})
        if not file_doc:
            return jsonify({'error': 'File not found'}), 404

        cloud = getattr(current_app, 'cloud_service', None)
        if not cloud:
            return jsonify({'error': 'cloud service not available'}), 500

        response = requests.get(
            file_doc['url'],
            auth=HTTPBasicAuth(cloud.nextcloud_user, cloud.nextcloud_pass),
            stream=True,
            timeout=(5, 60)
        )

        if response.status_code == 404:
            response.close()
            return jsonify({'error': 'File not found in cloud storage'}), 404

        if response.status_code != 200:
            response.close()
            return jsonify({'error': f'Failed to stream file: {response.status_code}'}), 502

        content_type = response.headers.get('Content-Type') or file_doc.get('content_type') or 'application/octet-stream'
        content_length = response.headers.get('Content-Length')

        def generate():
            try:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        yield chunk
            finally:
                response.close()

        headers = {
            'Content-Type': content_type,
            'Cache-Control': 'public, max-age=86400',
        }
        if content_length:
            headers['Content-Length'] = content_length

        return Response(stream_with_context(generate()), headers=headers, status=200)

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Download timeout - file may be too large'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 502
    except Exception as e:
        return jsonify({'error': f'Failed to stream file: {str(e)}'}), 500


@files_bp.post('/images')
def get_custom_image():
    """Download file directly from NextCloud custom folder."""
    try:
        cloud = getattr(current_app, 'cloud_service', None)
        if not cloud or not cloud.nextcloud_url:
            return jsonify({'error': 'NextCloud not configured'}), 500

        safe_file_name = secure_filename(request.json.get('filename'))
        user_id = request.json.get('user_id')
        if not safe_file_name or not user_id:
            return jsonify({'error': 'Invalid file name or user ID'}), 400
        
        cloud_url = cloud.get_url_custom(user_id, safe_file_name)
        
        auth = (cloud.nextcloud_user, cloud.nextcloud_pass) if cloud.nextcloud_user and cloud.nextcloud_pass else None
        response = requests.get(
            cloud_url,
            auth=auth,
            stream=True,
            timeout=(5, 60),
        )
        
        if response.status_code == 404:
            return jsonify({'error': 'File not found in cloud storage'}), 404
        
        if response.status_code != 200:
            response.close()
            return jsonify({'error': f'Failed to download file from cloud: {response.status_code}'}), 502
        
        content_type = response.headers.get('Content-Type', 'application/octet-stream')
        content_length = response.headers.get('Content-Length')

        def generate():
            try:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        yield chunk
            finally:
                response.close()

        headers = {
            'Content-Type': content_type,
            'Cache-Control': 'public, max-age=86400',
        }
        if content_length:
            headers['Content-Length'] = content_length

        return Response(stream_with_context(generate()), headers=headers, status=200)

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Download timeout - file may be too large'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 502
    except Exception as e:
        return jsonify({'error': f'Failed to download file: {str(e)}'}), 500


@files_bp.route('/uploads/<path:filepath>')
def serve_uploads(filepath):
    """Serve uploaded files from the uploads directory."""
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads')
    return send_file(os.path.join(upload_dir, filepath))
