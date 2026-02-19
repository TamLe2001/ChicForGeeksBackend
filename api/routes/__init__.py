"""API routes module - organize all blueprints here."""

from api.routes.auth import auth_bp
from api.routes.users import users_bp
from api.routes.outfits import outfits_bp
from api.routes.follows import follows_bp
from api.routes.files import files_bp
from api.routes.retexture import retexture_bp
from api.routes.garments import garments_bp

__all__ = [
    'auth_bp',
    'users_bp',
    'outfits_bp',
    'follows_bp',
    'files_bp',
    'retexture_bp',
    'garments_bp',
]
