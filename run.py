import os

from flask import Flask, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient

from api.config import Config
from api.routes.auth import auth_bp
from api.routes.users import users_bp
from api.routes.outfits import outfits_bp
from api.routes.follows import follows_bp


def create_app():
    app = Flask(__name__)
    
    # Enable CORS for all routes
    CORS(app)
    
    # Load configuration
    app.config.from_object(Config)

    # MongoDB connection
    mongo_uri = app.config.get('MONGO_URI')
    if not mongo_uri:
        raise RuntimeError('MONGO_URI is not set. Define it in environment variables.')

    client = MongoClient(mongo_uri)
    app.db = client[app.config.get('ChicForGeeks', 'database')]

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(users_bp, url_prefix='/api')
    app.register_blueprint(outfits_bp, url_prefix='/api')
    app.register_blueprint(follows_bp, url_prefix='/api')
    
    # Serve uploaded files
    @app.route('/uploads/<path:filepath>')
    def serve_uploads(filepath):
        upload_dir = os.path.join(app.root_path, '..', 'uploads')
        return send_from_directory(upload_dir, filepath)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=app.config.get('DEBUG', False))
