from datetime import datetime
import os

import requests
from requests.auth import HTTPBasicAuth
from flask import Blueprint, current_app, request
from werkzeug.utils import secure_filename

chicforgeeks_ar_bp = Blueprint("chicforgeeks_ar", __name__)


@chicforgeeks_ar_bp.route("/fbx", methods=["POST"])
def upload_fbx_to_cloud():
	"""Upload an FBX file to NextCloud under /fbx/."""
	try:
		if "file" not in request.files:
			return {"error": "No file provided"}, 400

		file = request.files["file"]
		if not file or file.filename == "":
			return {"error": "No file selected"}, 400

		filename = secure_filename(file.filename)
		if "." not in filename or filename.rsplit(".", 1)[1].lower() != "fbx":
			return {"error": "Only .fbx files are allowed"}, 400

		# File size validation
		MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
		if file.content_length and file.content_length > MAX_FILE_SIZE:
			return {"error": f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)} MB"}, 413

		nextcloud_url = current_app.config.get("NEXTCLOUD_URL") or os.getenv(
			"NEXTCLOUD_URL", ""
		)
		nextcloud_user = current_app.config.get("NEXTCLOUD_USER") or os.getenv(
			"NEXTCLOUD_USER", ""
		)
		nextcloud_pass = current_app.config.get("NEXTCLOUD_PASS") or os.getenv(
			"NEXTCLOUD_PASS", ""
		)

		if not all([nextcloud_url, nextcloud_user, nextcloud_pass]):
			return {"error": "NextCloud not configured"}, 500

		if not nextcloud_url.endswith("/"):
			nextcloud_url = f"{nextcloud_url}/"

		folder_url = f"{nextcloud_url}fbx/"
		mkcol_response = requests.request(
			"MKCOL",
			folder_url,
			auth=HTTPBasicAuth(nextcloud_user, nextcloud_pass),
			timeout=10,
		)
		if mkcol_response.status_code not in (201, 405):
			return {
				"error": f"Failed to create fbx folder: {mkcol_response.status_code}",
				"details": mkcol_response.text,
			}, 500

		upload_url = f"{folder_url}{filename}"
		headers = {"Content-Type": file.content_type or "application/octet-stream"}

		response = requests.put(
			upload_url,
			data=file.stream,
			auth=HTTPBasicAuth(nextcloud_user, nextcloud_pass),
			headers=headers,
			timeout=60,
		)

		if response.status_code not in (201, 204):
			return {
				"error": f"NextCloud upload failed: {response.status_code}",
				"details": response.text,
			}, 500

		try:
			current_app.db.files.insert_one(
				{
					"filename": filename,
					"category": "fbx",
					"url": upload_url,
					"content_type": file.content_type or "application/octet-stream",
					"uploaded_at": datetime.utcnow(),
				}
			)
		except Exception:
			pass

		return {
			"status": "success",
			"message": "FBX uploaded successfully",
			"filename": filename,
			"cloud_url": upload_url,
		}, 201

	except requests.exceptions.Timeout:
		return {"error": "Upload timeout"}, 504
	except requests.exceptions.RequestException as e:
		return {"error": f"Upload failed: {str(e)}"}, 500
	except Exception as e:
		return {"error": f"Server error: {str(e)}"}, 500
