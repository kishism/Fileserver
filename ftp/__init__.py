# ftp/__init__.py

import os
from flask import Flask
from dotenv import load_dotenv
from .routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config["BASE_PATH"] = os.getenv("BASE_PATH", "")
    app.config["UPLOAD_BASE_PATH"] = os.getenv("UPLOAD_BASE_PATH", app.config["BASE_PATH"])
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "")

    app.config["DATABASE"] = "ftp.db"
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB

    import ftp.models as models
    import ftp.routes.hypermedia as hypermedia
    import ftp.routes.directories as directories
    
    models.init_app(app)
    hypermedia.init_app(app)
    directories.init_app(app)

    register_routes(app)

    return app
