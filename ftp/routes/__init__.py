#ftp/routes/__init__.puy
# Collect and register all route blueprints,
# serve as central import point

# Import blueprints for routes
from .directories import bp as directories_bp

def register_routes(app):
    """
    This function is called in ftp/__init__.py when creating the Flask app.
    """
    # The url_prefix determines the base URL for all routes in this blueprint.
    # For example, if url_prefix="/", the route @bp.route("/") in directories.py
    # will respond to GET requests at "/".
    app.register_blueprint(directories_bp, url_prefix="/")


    
