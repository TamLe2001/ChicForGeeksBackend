import os
from flask import Flask
from flask_cors import CORS
from pymongo import ASCENDING, DESCENDING, MongoClient

from api.config import Config
from api.routes import register_blueprints
from api.middleware.error_handler import handle_errors

# Initialize file service and cloud service
from api.services.file_service import FileService
from api.services.cloud_service import CloudService


def ensure_indexes(db):
    """Create required MongoDB indexes."""
    db.users.create_index([('email', ASCENDING)], unique=True)
    db.follows.create_index([('follower_id', ASCENDING), ('followed_id', ASCENDING)], unique=True)
    db.follows.create_index([('followed_id', ASCENDING), ('created_at', DESCENDING)])
    db.follows.create_index([('follower_id', ASCENDING), ('created_at', DESCENDING)])
    db.outfits.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)])
    db.wardrobes.create_index([('user_id', ASCENDING)], unique=True)
    db.wardrobes.create_index([('outfit_ids', ASCENDING)])
    db.likes.create_index([('outfit_id', ASCENDING), ('user_id', ASCENDING)], unique=True)
    db.comments.create_index([('outfit_id', ASCENDING), ('created_at', DESCENDING)])
    db.comments.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)])

    # Legacy garments.id index caused duplicate key errors when id was missing or null.
    try:
        db.garments.drop_index('id_1')
    except Exception:
        pass


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)

    # Enable CORS
    CORS(
        app,
        resources={r"/api/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "expose_headers": ["Content-Type", "Authorization"]
        }},
        supports_credentials=True,
    )

    # MongoDB connection
    mongo_uri = app.config.get('MONGO_URI')
    if not mongo_uri:
        raise RuntimeError('MONGO_URI is not set. Define it in environment variables.')

    client_options = {
        'connectTimeoutMS': 5000,
        'serverSelectionTimeoutMS': 5000,
        'retryWrites': False,
        'tlsAllowInvalidCertificates': True,
        'tlsAllowInvalidHostnames': True,
    }
    
    client = MongoClient(mongo_uri, **client_options)
    app.db = client[app.config.get('MONGO_DB_NAME', 'database')]
    ensure_indexes(app.db)

    # Register error handlers
    handle_errors(app)

    # Register blueprints
    register_blueprints(app)
    
    with app.app_context():
        try:
            file_service = FileService(app.db, app.config)
            uploads_path = os.path.join(app.root_path, '..', 'uploads')
            file_service.download_default_files(uploads_path)
        except Exception as e:
            print(f"⚠ Warning: Failed to initialize default files: {e}")
        try:
            app.cloud_service = CloudService(app.db, app.config)
            print("CloudService initialized and attached to app as app.cloud_service")
        except Exception as e:
            print(f"⚠ Warning: Failed to initialize CloudService: {e}")
    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 8000))
    debug = app.config.get('DEBUG', False)
    print(f"\n🚀 Starting server on http://0.0.0.0:{port}")
    print(f"📝 Debug mode: {debug}\n")
    print(f"Mongodb is connected to: {app.config.get('MONGO_URI')} - {app.config.get('MONGO_DB_NAME')}\n")
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
