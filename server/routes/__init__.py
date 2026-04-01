# IntegratedServer/server/routes/__init__.py
from flask import Blueprint

# Create blueprints
movie_bp = Blueprint('movies', __name__)
admin_bp = Blueprint('admin', __name__)
redirect_bp = Blueprint('redirect', __name__)

# Import route handlers to register them
from routes.movie_routes import *
from routes.admin_routes import *
from routes.redirect_routes import *
