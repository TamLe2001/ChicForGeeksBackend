from flask import Blueprint, request, current_app, send_file, send_from_directory
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from io import BytesIO
import os

files_bp = Blueprint('files', __name__)


def allowed_file(filename):
    """Check if file extension is allowed"""
    allowed_ext = current_app.config.get('ALLOWED_EXTENSIONS', {'glb', 'gltf'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_ext


@files_bp.route('/upload', methods=['POST'])
def upload_to_cloud():
    """Upload GLB/GLTF files to NextCloud storage with folder organization"""
    try:
        # Validate file presence
        if 'file' not in request.files:
            return {"error": "No file provided"}, 400
        
        file = request.files['file']
        
        if file.filename == '':
            return {"error": "No file selected"}, 400
        
        if not allowed_file(file.filename):
            return {"error": "Only GLB/GLTF files allowed"}, 400
        
        # Get user_id and category from request args or form data
        user_id = request.form.get('user_id') or request.args.get('user_id')
        category = request.form.get('category') or request.args.get('category')
        
        if not user_id:
            return {"error": "user_id is required"}, 400
        
        if not category:
            return {"error": "category is required (shirt, hat, pants, shoes)"}, 400
        
        valid_categories = {'shirt', 'hat', 'pants', 'shoes'}
        if category.lower() not in valid_categories:
            return {"error": f"Invalid category. Must be one of: {', '.join(valid_categories)}"}, 400
        
        # Check file size
        max_size = current_app.config.get('MAX_FILE_SIZE', 100 * 1024 * 1024)
        if file.content_length and file.content_length > max_size:
            return {"error": "File too large (max 100MB)"}, 413
        
        # Get NextCloud credentials from config
        nextcloud_url = current_app.config.get('NEXTCLOUD_URL')
        nextcloud_user = current_app.config.get('NEXTCLOUD_USER')
        nextcloud_pass = current_app.config.get('NEXTCLOUD_PASS')
        
        if not all([nextcloud_url, nextcloud_user, nextcloud_pass]):
            return {"error": "NextCloud not configured"}, 500
        
        # Create folders if they don't exist: user_id/category/
        base_path = f"{nextcloud_url}{user_id}/"
        category_path = f"{base_path}{category}/"
        
        # Create user folder
        create_folder_response = requests.mkcol(
            base_path,
            auth=HTTPBasicAuth(nextcloud_user, nextcloud_pass),
            timeout=10
        )
        # Status 201 = created, 405 = already exists, both are OK
        if create_folder_response.status_code not in [201, 405]:
            return {"error": f"Failed to create user folder: {create_folder_response.status_code}"}, 500
        
        # Create category folder
        create_category_response = requests.mkcol(
            category_path,
            auth=HTTPBasicAuth(nextcloud_user, nextcloud_pass),
            timeout=10
        )
        # Status 201 = created, 405 = already exists, both are OK
        if create_category_response.status_code not in [201, 405]:
            return {"error": f"Failed to create category folder: {create_category_response.status_code}"}, 500
        
        # Upload to NextCloud in organized folder
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
        
        # Save metadata to MongoDB
        file_doc = {
            "filename": file.filename,
            "user_id": user_id,
            "category": category.lower(),
            "url": upload_url,
            "size": file.content_length or 0,
            "content_type": file.content_type or "application/octet-stream",
            "uploaded_at": datetime.utcnow()
        }
        
        result = current_app.db.files.insert_one(file_doc)
        
        return {
            "status": "success",
            "message": "File uploaded successfully",
            "file_id": str(result.inserted_id),
            "filename": file.filename,
            "cloud_url": upload_url
        }, 201
        
    except requests.exceptions.Timeout:
        return {"error": "Upload timeout - file may be too large"}, 504
    except requests.exceptions.RequestException as e:
        return {"error": f"Upload failed: {str(e)}"}, 500
    except Exception as e:
        return {"error": f"Server error: {str(e)}"}, 500


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


@files_bp.route('/uploads/<path:filepath>')
def serve_uploads(filepath):
    """Serve uploaded files from the uploads directory."""
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads')
    return send_from_directory(upload_dir, filepath)
