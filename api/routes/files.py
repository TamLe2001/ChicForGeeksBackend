from flask import Blueprint, Response, jsonify, request, current_app, send_file, send_from_directory, stream_with_context, url_for
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from io import BytesIO
import os
from werkzeug.utils import secure_filename


files_bp = Blueprint('files', __name__)


def allowed_file(filename):
    """Check if file extension is allowed"""
    allowed_ext = current_app.config.get('ALLOWED_EXTENSIONS', {'glb', 'gltf', 'png', 'jpg', 'jpeg'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_ext


def allowed_file_by_extensions(filename, allowed_extensions):
    """Check if filename extension is in a specific allowed set"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions



# Model upload: requires category
def _upload_model_to_cloud(allowed_extensions, file_type_label):
    try:
        if 'file' not in request.files:
            return {"error": "No file provided"}, 400

        file = request.files['file']
        if file.filename == '':
            return {"error": "No file selected"}, 400
        if not allowed_file_by_extensions(file.filename, allowed_extensions):
            allowed_text = ', '.join(sorted(allowed_extensions))
            return {"error": f"Only {file_type_label} files allowed ({allowed_text})"}, 400

        user_id = request.form.get('user_id') or request.args.get('user_id')
        category = request.form.get('category') or request.args.get('category')
        if not user_id:
            return {"error": "user_id is required"}, 400
        if not category:
            return {"error": "category is required (shirt, pants, skirt, accessory)"}, 400
        valid_categories = {'shirt', 'pants', 'skirt', 'accessory'}
        if category.lower() not in valid_categories:
            return {"error": f"Invalid category. Must be one of: {', '.join(valid_categories)}"}, 400

        max_size = current_app.config.get('MAX_FILE_SIZE', 100 * 1024 * 1024)
        if file.content_length and file.content_length > max_size:
            return {"error": "File too large (max 100MB)"}, 413

        nextcloud_url = current_app.config.get('NEXTCLOUD_URL')
        nextcloud_user = current_app.config.get('NEXTCLOUD_USER')
        nextcloud_pass = current_app.config.get('NEXTCLOUD_PASS')
        if not all([nextcloud_url, nextcloud_user, nextcloud_pass]):
            return {"error": "NextCloud not configured"}, 500

        base_path = f"{nextcloud_url}{user_id}/"
        category_path = f"{base_path}{category}/"
        create_folder_response = requests.request(
            "MKCOL",
            base_path,
            auth=HTTPBasicAuth(nextcloud_user, nextcloud_pass),
            timeout=10
        )
        if create_folder_response.status_code not in [201, 405]:
            return {"error": f"Failed to create user folder: {create_folder_response.status_code}"}, 500
        create_category_response = requests.request(
            "MKCOL",
            category_path,
            auth=HTTPBasicAuth(nextcloud_user, nextcloud_pass),
            timeout=10
        )
        if create_category_response.status_code not in [201, 405]:
            return {"error": f"Failed to create category folder: {create_category_response.status_code}"}, 500
        upload_url = f"{category_path}{file.filename}"
        headers = {"Content-Type": file.content_type or "application/octet-stream"}
        response = requests.put(
            upload_url,
            data=file.stream,
            auth=HTTPBasicAuth(nextcloud_user, nextcloud_pass),
            headers=headers,
            timeout=30
        )
        if response.status_code not in [201, 204]:
            return {
                "error": f"NextCloud error: {response.status_code}",
                "details": response.text
            }, 500
        file_doc = {
            "filename": file.filename,
            "user_id": user_id,
            "category": category.lower(),
            "url": upload_url,
            "size": file.content_length or 0,
            "content_type": file.content_type or "application/octet-stream",
            "uploaded_at": datetime.utcnow(),
            "file_type": file_type_label
        }
        result = current_app.db.files.insert_one(file_doc)
        file_id = str(result.inserted_id)
        return {
            "status": "success",
            "message": f"{file_type_label.capitalize()} file uploaded successfully",
            "file_id": file_id,
            "filename": file.filename,
            "file_url": url_for('files.get_file_content', file_id=file_id, _external=True),
            "download_url": url_for('files.download_file', file_id=file_id, _external=True),
            "file_type": file_type_label
        }, 201
    except requests.exceptions.Timeout:
        return {"error": "Upload timeout - file may be too large"}, 504
    except requests.exceptions.RequestException as e:
        return {"error": f"Upload failed: {str(e)}"}, 500
    except Exception as e:
        return {"error": f"Server error: {str(e)}"}, 500

# Image upload: does NOT require category
def _upload_image_to_cloud(allowed_extensions, file_type_label):
    try:
        if 'file' not in request.files:
            return {"error": "No file provided"}, 400
        file = request.files['file']
        if file.filename == '':
            return {"error": "No file selected"}, 400
        if not allowed_file_by_extensions(file.filename, allowed_extensions):
            allowed_text = ', '.join(sorted(allowed_extensions))
            return {"error": f"Only {file_type_label} files allowed ({allowed_text})"}, 400
        user_id = request.form.get('user_id') or request.args.get('user_id')
        if not user_id:
            return {"error": "user_id is required"}, 400
        max_size = current_app.config.get('MAX_FILE_SIZE', 100 * 1024 * 1024)
        if file.content_length and file.content_length > max_size:
            return {"error": "File too large (max 100MB)"}, 413
        nextcloud_url = current_app.config.get('NEXTCLOUD_URL')
        nextcloud_user = current_app.config.get('NEXTCLOUD_USER')
        nextcloud_pass = current_app.config.get('NEXTCLOUD_PASS')
        if not all([nextcloud_url, nextcloud_user, nextcloud_pass]):
            return {"error": "NextCloud not configured"}, 500
        base_path = f"{nextcloud_url}{user_id}/"
        create_folder_response = requests.request(
            "MKCOL",
            base_path,
            auth=HTTPBasicAuth(nextcloud_user, nextcloud_pass),
            timeout=10
        )
        if create_folder_response.status_code not in [201, 405]:
            return {"error": f"Failed to create user folder: {create_folder_response.status_code}"}, 500
        upload_url = f"{base_path}{file.filename}"
        headers = {"Content-Type": file.content_type or "application/octet-stream"}
        response = requests.put(
            upload_url,
            data=file.stream,
            auth=HTTPBasicAuth(nextcloud_user, nextcloud_pass),
            headers=headers,
            timeout=30
        )
        if response.status_code not in [201, 204]:
            return {
                "error": f"NextCloud error: {response.status_code}",
                "details": response.text
            }, 500
        file_doc = {
            "filename": file.filename,
            "user_id": user_id,
            "url": upload_url,
            "size": file.content_length or 0,
            "content_type": file.content_type or "application/octet-stream",
            "uploaded_at": datetime.utcnow(),
            "file_type": file_type_label
        }
        result = current_app.db.files.insert_one(file_doc)
        file_id = str(result.inserted_id)
        return {
            "status": "success",
            "message": f"{file_type_label.capitalize()} file uploaded successfully",
            "file_id": file_id,
            "filename": file.filename,
            "file_url": url_for('files.get_file_content', file_id=file_id, _external=True),
            "download_url": url_for('files.download_file', file_id=file_id, _external=True),
            "file_type": file_type_label
        }, 201
    except requests.exceptions.Timeout:
        return {"error": "Upload timeout - file may be too large"}, 504
    except requests.exceptions.RequestException as e:
        return {"error": f"Upload failed: {str(e)}"}, 500
    except Exception as e:
        return {"error": f"Server error: {str(e)}"}, 500


@files_bp.route('/upload', methods=['POST'])
def upload_to_cloud():
    """Legacy endpoint kept for compatibility. Prefer /upload/models and /upload/images."""
    return {"error": "Endpoint deprecated. Use /upload/models for GLB/GLTF or /upload/images for images."}, 410


@files_bp.route('/upload/models', methods=['POST'])
def upload_model_to_cloud():
    """Upload GLB/GLTF files to NextCloud storage with folder organization (category required)"""
    return _upload_model_to_cloud({'glb', 'gltf'}, 'model')


@files_bp.route('/upload/images', methods=['POST'])
def upload_image_to_cloud():
    """Upload image files to NextCloud storage with folder organization (no category required)"""
    return _upload_image_to_cloud({'png', 'jpg', 'jpeg'}, 'image')


@files_bp.route('/files', methods=['GET'])
def list_files():
    """List all uploaded files, optionally filtered by user_id"""
    try:
        user_id = request.args.get('user_id')
        category = request.args.get('category')
        
        query = {}
        if user_id:
            query['user_id'] = user_id
        if category:
            query['category'] = category.lower()
        
        files = list(current_app.db.files.find(query, {'_id': 1, 'filename': 1, 'url': 1, 'size': 1, 'user_id': 1, 'category': 1, 'uploaded_at': 1}))
        
        # Convert ObjectId to string for JSON serialization
        for f in files:
            f['_id'] = str(f['_id'])
        
        return {"status": "success", "files": files}, 200
    except Exception as e:
        return {"error": f"Failed to fetch files: {str(e)}"}, 500


@files_bp.route('/files/<file_id>', methods=['GET'])
def get_file(file_id):
    """Get file metadata by ID"""
    try:
        from bson.objectid import ObjectId
        file_doc = current_app.db.files.find_one({'_id': ObjectId(file_id)})
        
        if not file_doc:
            return {"error": "File not found"}, 404
        
        file_doc['_id'] = str(file_doc['_id'])
        return {"status": "success", "file": file_doc}, 200
    except Exception as e:
        return {"error": f"Failed to fetch file: {str(e)}"}, 500


@files_bp.route('/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Delete file from NextCloud and database"""
    try:
        from bson.objectid import ObjectId
        
        # Get file from database
        file_doc = current_app.db.files.find_one({'_id': ObjectId(file_id)})
        if not file_doc:
            return {"error": "File not found"}, 404
        
        # Delete from NextCloud
        nextcloud_user = current_app.config.get('NEXTCLOUD_USER')
        nextcloud_pass = current_app.config.get('NEXTCLOUD_PASS')
        
        response = requests.delete(
            file_doc['url'],
            auth=HTTPBasicAuth(nextcloud_user, nextcloud_pass),
            timeout=30
        )
        
        if response.status_code not in [204, 200]:
            return {"error": f"Failed to delete from NextCloud: {response.status_code}"}, 500
        
        # Delete from MongoDB
        current_app.db.files.delete_one({'_id': ObjectId(file_id)})
        
        return {"status": "success", "message": "File deleted successfully"}, 200
    except Exception as e:
        return {"error": f"Failed to delete file: {str(e)}"}, 500


@files_bp.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    """Download file from NextCloud storage"""
    try:
        from bson.objectid import ObjectId
        
        # Get file metadata from database
        file_doc = current_app.db.files.find_one({'_id': ObjectId(file_id)})
        if not file_doc:
            return {"error": "File not found"}, 404
        
        # Get NextCloud credentials
        nextcloud_user = current_app.config.get('NEXTCLOUD_USER')
        nextcloud_pass = current_app.config.get('NEXTCLOUD_PASS')
        
        # Download file from NextCloud
        response = requests.get(
            file_doc['url'],
            auth=HTTPBasicAuth(nextcloud_user, nextcloud_pass),
            timeout=30
        )
        
        if response.status_code != 200:
            return {"error": f"Failed to download file: {response.status_code}"}, 500
        
        # Return file as download
        return send_file(
            BytesIO(response.content),
            mimetype=file_doc.get('content_type', 'application/octet-stream'),
            as_attachment=True,
            download_name=file_doc['filename']
        )
    except Exception as e:
        return {"error": f"Failed to download file: {str(e)}"}, 500


@files_bp.route('/files/<file_id>/content', methods=['GET'])
def get_file_content(file_id):
    """Stream file content from NextCloud for frontend consumption."""
    try:
        from bson.objectid import ObjectId

        file_doc = current_app.db.files.find_one({'_id': ObjectId(file_id)})
        if not file_doc:
            return {"error": "File not found"}, 404

        nextcloud_user = current_app.config.get('NEXTCLOUD_USER')
        nextcloud_pass = current_app.config.get('NEXTCLOUD_PASS')

        response = requests.get(
            file_doc['url'],
            auth=HTTPBasicAuth(nextcloud_user, nextcloud_pass),
            stream=True,
            timeout=(5, 60)
        )

        if response.status_code == 404:
            response.close()
            return {"error": "File not found in cloud storage"}, 404
        if response.status_code != 200:
            response.close()
            return {"error": f"Failed to stream file: {response.status_code}"}, 502

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
        return {"error": "Download timeout - file may be too large or network issues"}, 504
    except requests.exceptions.RequestException as e:
        return {"error": f"Download failed: {str(e)}"}, 502
    except Exception as e:
        return {"error": f"Failed to stream file: {str(e)}"}, 500


@files_bp.route('/uploads/<path:filepath>')
def serve_uploads(filepath):
    """Serve uploaded files from the uploads directory."""
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads')
    return send_from_directory(upload_dir, filepath)


@files_bp.post('/images')
def get_custom_image():
    """Download file directly from NextCloud custom folder"""
    try:
        cloud = current_app.cloud_service
        
        if not cloud.nextcloud_url:
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
        return jsonify({'error': 'Download timeout - file may be too large or network issues'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 502
    except Exception as e:
        return jsonify({'error': f'Failed to download file: {str(e)}'}), 500