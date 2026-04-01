"""API routes module - organize all blueprints here."""

from api.routes.auth import auth_bp
from api.routes.users import users_bp
from api.routes.outfits import outfits_bp
from api.routes.follows import follows_bp
from api.routes.files import files_bp
from api.routes.chicforgeeksAR import chicforgeeks_ar_bp
from api.routes.garments import garments_bp
from api.routes.wardrobes import wardrobes_bp


def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    blueprints = [
        auth_bp,
        users_bp,
        outfits_bp,
        follows_bp,
        wardrobes_bp,
        files_bp,
        chicforgeeks_ar_bp,
        garments_bp,
    ]
    
    for blueprint in blueprints:
        app.register_blueprint(blueprint, url_prefix='/api')


__all__ = [
    'auth_bp',
    'users_bp',
    'outfits_bp',
    'follows_bp',
    'wardrobes_bp',
    'files_bp',
    'chicforgeeks_ar_bp',
    'garments_bp',
    'register_blueprints',
]
