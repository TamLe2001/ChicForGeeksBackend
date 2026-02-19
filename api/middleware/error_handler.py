"""Error handling middleware."""

from flask import jsonify


def handle_errors(app):
    """Register error handlers for the Flask app."""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'bad request'}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'unauthorized'}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'forbidden'}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'internal server error'}), 500
