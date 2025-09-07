# This is for codes that want to create/run the Flask app

from flask import Flask
from .routes import register_routes

def create_app():
    
    app = Flask(__name__)

    # Configuration
    app.config["DATABASE"] = "instance/ftp.db"
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB upload limit

    # Register routes / blueprints
    register_routes(app)

    return app
