import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
	SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
	DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
	JWT_SECRET = os.getenv('JWT_SECRET', SECRET_KEY)
	JWT_EXPIRES_MINUTES = int(os.getenv('JWT_EXPIRES_MINUTES', '60'))

	# MongoDB settings
	# Priority: explicit MONGO_URI > MONGO_DEV_URI (for local/non-docker dev) > fallback
	MONGO_URI = (
		os.getenv('MONGO_URI')
		or os.getenv('MONGO_DEV_URI')
		or 'mongodb://mongo:27017/'
	)
	MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'database')

	# NextCloud settings
	NEXTCLOUD_URL = os.getenv('NEXTCLOUD_URL')
	NEXTCLOUD_USER = os.getenv('NEXTCLOUD_USER')
	NEXTCLOUD_PASS = os.getenv('NEXTCLOUD_PASS')
	
	# File upload settings
	MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
	ALLOWED_EXTENSIONS = {'glb', 'gltf'}

	# CORS settings
	CORS_ORIGINS = [
		"http://localhost:3000",
		"http://127.0.0.1:3000",
		"http://85.191.37.69:3000"
	]

	# Meshy settings
	MESHY_API_KEY = os.getenv('MESHY_API_KEY')
	INTERNAL_API_KEY = os.getenv('INTERNAL_API_KEY')
