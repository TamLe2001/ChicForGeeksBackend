import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import ssl
import certifi

from api.config import Config
from api.routes import (
    auth_bp, users_bp, outfits_bp, follows_bp, files_bp, retexture_bp, garments_bp
)
from api.services import FileService


def create_app():
    app = Flask(__name__)
    
    # Enable CORS for all routes
    CORS(
        app,
        resources={r"/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000", "http://85.191.37.69:3000"]}},
        supports_credentials=True,
    )
    
    # Load configuration
    app.config.from_object(Config)

    # MongoDB connection with SSL/TLS support
    mongo_uri = app.config.get('MONGO_URI')
    if not mongo_uri:
        raise RuntimeError('MONGO_URI is not set. Define it in environment variables.')

    # Create client with SSL configuration
    # Note: For Windows + Python 3.13+, we disable strict cert verification
    # Connection will be tested on first use
    client_options = {
        'connectTimeoutMS': 5000,
        'serverSelectionTimeoutMS': 5000,
        'retryWrites': False,
        'tlsAllowInvalidCertificates': True,
        'tlsAllowInvalidHostnames': True,
    }
    
    client = MongoClient(mongo_uri, **client_options)
    print("✓ MongoDB client created (lazy connection)")
    
    app.db = client[app.config.get('MONGO_DB_NAME', 'chicforgeeks')]

    # Register error handlers
    from api.middleware.error_handler import handle_errors
    handle_errors(app)

    # Register blueprints
    blueprints = [
        auth_bp,
        users_bp,
        outfits_bp,
        follows_bp,
        files_bp,
        retexture_bp,
        garments_bp,
    ]
    for blueprint in blueprints:
        app.register_blueprint(blueprint, url_prefix='/api')
    
    # Initialize file service and download default files on startup
    with app.app_context():
        try:
            file_service = FileService(app.db, app.config)
            uploads_path = os.path.join(app.root_path, '..', 'uploads')
            file_service.download_default_files(uploads_path)
            print("✓ Default files initialization complete")
        except Exception as e:
            print(f"⚠ Warning: Failed to initialize default files: {e}")
            # Don't fail startup if default files fail to download
    
    # Serve uploaded files
    @app.route('/uploads/<path:filepath>')
    def serve_uploads(filepath):
        upload_dir = os.path.join(app.root_path, '..', 'uploads')
        return send_from_directory(upload_dir, filepath)
    
    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 8000))
    debug = app.config.get('DEBUG', False)
    print(f"\n🚀 Starting server on http://0.0.0.0:{port}")
    print(f"📝 Debug mode: {debug}\n")
    app.run(host='0.0.0.0', port=port, debug=debug)
