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
	MONGO_URI = os.getenv('MONGO_URI')
	MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'chicforgeeks')

	# NextCloud settings
	NEXTCLOUD_URL = os.getenv('NEXTCLOUD_URL')
	NEXTCLOUD_USER = os.getenv('NEXTCLOUD_USER')
	NEXTCLOUD_PASS = os.getenv('NEXTCLOUD_PASS')
	
	# File upload settings
	MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
	ALLOWED_EXTENSIONS = {'glb', 'gltf'}

	# Meshy settings
	MESHY_API_KEY = os.getenv('MESHY_API_KEY')
	INTERNAL_API_KEY = os.getenv('INTERNAL_API_KEY')
