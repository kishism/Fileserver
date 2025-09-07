# Collect and register all route blueprints,
# serve as central import point

# Import blueprints 
from .directories import bp as directories_bp
from .files import bp as files_bp

def register_routes(app):
    
    app.register_blueprint(directories_bp)
    app.register_blueprint(files_bp)
