# ftp/routes/directories.py
# This file defines all routes related to directory browsing.
# Each route calls helper functions from models.py to fetch data
# and uses hypermedia.py to render the response with headers.

from flask import Blueprint, abort, render_template
from ftp.models import get_directory_contents
from ftp.routes.hypermedia import hypermedia_directory_response

# Create a blueprint for directory routes.
# This groups all directory-related endpoints together.
# No url_prefix here; it will be set when registering the blueprint in __init__.py
bp = Blueprint("directories", __name__)  

@bp.route("/", methods=["GET"])
def list_root_directory():
    """ 
    Handle GET requests to the root path "/".
    Fetches the contents of the root directory from the database and
    renders it using hypermedia_directory_response.
    """
    directories, files = get_directory_contents(None)  # None = root
    return hypermedia_directory_response("root", directories, files)

@bp.route("/<path:dirpath>/", methods=["GET"])
def list_directory(dirpath):
    """
    Handle GET requests to any subdirectory "/<dirname>/".
    Fetches contents of the subdirectory from the database.

    404 Not Found if the directory does not exist.
    """
    directories, files = get_directory_contents(dirpath)

    """
    Database will return for None for directories and files
    if they don't exist, instead of {[], []}.
    """
    if directories is None and files is None:
        abort(404) # triggers custom 404 error page
        
    return hypermedia_directory_response(dirpath, directories, files)

# Error Handling Pages 
# NNL
@bp.app_errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@bp.app_errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500