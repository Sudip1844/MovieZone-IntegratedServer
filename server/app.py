# IntegratedServer/server/app.py
# Flask application - serves API + frontend on one port

import os
import logging
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

logger = logging.getLogger(__name__)


def create_app():
    """Create Flask app"""
    app = Flask(__name__,
                static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'),
                static_url_path='/static')

    # CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register route blueprints
    from routes import movie_bp, admin_bp, redirect_bp
    app.register_blueprint(movie_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(redirect_bp)

    # --- Serve Frontend Pages ---

    @app.route('/')
    def index():
        """Landing page"""
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/sudip')
    def owner_panel():
        """Owner panel (hardcoded route)"""
        return send_from_directory(app.static_folder, 'owner.html')

    @app.route('/admin')
    def admin_panel():
        """Admin panel"""
        return send_from_directory(app.static_folder, 'admin.html')

    @app.route('/ad_page.html')
    def ad_page():
        """Ad page SPA"""
        return send_from_directory(app.static_folder, 'ad_page.html')

    # --- Health Check ---

    @app.route('/api/health')
    def health():
        return jsonify({
            'status': 'ok',
            'service': 'MovieZone Integrated Server',
            'bot': 'running',
            'web': 'running'
        })

    # --- Error Handlers ---

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'Internal server error'}), 500

    logger.info("✅ Flask app created with all routes")
    return app
