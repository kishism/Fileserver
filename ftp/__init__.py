# This is for codes that want to create/run the Flask app

import os
from flask import Flask
from dotenv import load_dotenv
from .routes import register_routes

def create_app():
    
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-for-local-only")
    # In production, please omit the second argument.

    # app.secret_key = os.getenv("FLASK_SECRET_KEY")
    # if app.secret_key is None:
    #     raise RuntimeError("FLASK_SECRET_KEY environment variable not set!")

    # Configuration
    app.config["DATABASE"] = "ftp.db"
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB upload limit

    # Register routes / blueprints
    register_routes(app)

    return app
