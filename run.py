import os
from flask import Flask
from flask_cors import CORS
from pymongo import MongoClient

from api.config import Config
from api.routes import register_blueprints
from api.middleware.error_handler import handle_errors
from api.services import FileService


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)

    # Enable CORS
    CORS(
        app,
        resources={r"/*": {"origins": app.config['CORS_ORIGINS']}},
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

    # Register error handlers
    handle_errors(app)

    # Register blueprints
    register_blueprints(app)
    
    # Initialize file service
    with app.app_context():
        try:
            file_service = FileService(app.db, app.config)
            uploads_path = os.path.join(app.root_path, '..', 'uploads')
            file_service.download_default_files(uploads_path)
        except Exception as e:
            print(f"⚠ Warning: Failed to initialize default files: {e}")
    
    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 8000))
    debug = app.config.get('DEBUG', False)
    print(f"\n🚀 Starting server on http://0.0.0.0:{port}")
    print(f"📝 Debug mode: {debug}\n")
    print(f"Mongodb is connected to: {app.config.get('MONGO_URI')} - {app.config.get('MONGO_DB_NAME')}\n")
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
