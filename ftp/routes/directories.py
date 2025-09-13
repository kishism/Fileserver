# ftp/routes/directories.py
# This file defines all routes related to directory browsing.
# Each route calls helper functions from models.py to fetch data
# and uses hypermedia.py to render the response with headers.

from flask import Blueprint, abort, render_template, request, redirect, url_for
from ftp.models import *
from ftp.routes.hypermedia import hypermedia_directory_response
import os 

# Create a blueprint for directory routes.
# This groups all directory-related endpoints together.
# No url_prefix here; it will be set when registering the blueprint in __init__.py
bp = Blueprint("directories", __name__)  

# List root directory
@bp.route("/", methods=["GET"])
def list_root_directory():
    """ 
    Handle GET requests to the root path "/".
    Fetches the contents of the root directory from the database and
    renders it using hypermedia_directory_response.
    """
    directories, files = get_directory_contents(None)  # None = root
    return hypermedia_directory_response("root", directories, files)

# List subdirectories
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

# File Upload
@bp.route("/upload", methods=["POST"])
@bp.route("/<path:dirpath>/upload", methods=["POST"])
def upload_file(dirpath=None):
    """
    Handle file upload for root or subdirectory.
    dirpath=None for root
    """
    file = request.files.get("file")
    if not file:
        abort(400, description="No file provided")

    actual_dirpath = dirpath if dirpath else "root"

    # Save file using helper in models.py
    save_file_to_directory(file, dirpath)

    # After upload, redirect back to directory view
    return redirect(url_for("directories.list_directory", dirpath=actual_dirpath if actual_dirpath != "root" else ""))

# Folder Upload (webkitdirectory)
@bp.route("/upload_folder", methods=["POST"])
@bp.route("/<path:dirpath>/upload_folder", methods=["POST"])
def upload_folder(dirpath=None):
    """
    Handle folder upload.
    The browser sends multiple files with relative paths.
    """
    uploaded_files = request.files.getlist("files")
    if not uploaded_files:
        abort(400, description="No files provided")

    actual_dirpath = dirpath if dirpath else None

    for file in uploaded_files:

        # Extract relative path
        rel_path = file.filename  # In Flask, name comes from the uploaded file

        # If using Chrome/WebKit, you can access webkitRelativePath
        rel_path = getattr(file, "webkitRelativePath", file.filename)

        # Combine with dirpath if uploading into a subdirectory
        full_path = rel_path if actual_dirpath is None else os.path.join(actual_dirpath, rel_path).replace("\\", "/")

        # Save file using your existing helper
        save_file_from_folder(file, full_path)

    return redirect(url_for("directories.list_directory", dirpath=actual_dirpath if actual_dirpath != None else ""))

# Create Directory 
@bp.route("/<path:dirpath>/create_directory", methods=["POST"])
@bp.route("/create_directory", methods=["POST"])
def create_directory(dirpath=None):
    """
    Handle creation of a new subdirectory.
    """
    dir_name = request.form.get("dirname")
    if not dir_name:
        abort(400, description="Directory name required")

    actual_dirpath = dirpath if dirpath else "root"

    create_directory_in_db(actual_dirpath, dir_name) 
     
    return redirect(url_for("directories.list_directory", dirpath=actual_dirpath if actual_dirpath != "root" else ""))

# Error Handling Pages 
# NNL
@bp.app_errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@bp.app_errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500

@bp.app_errorhandler(403)
def Access_Forbidden(e):
    return render_template("403.html"), 403

@bp.app_errorhandler(503)
def Service_Unavailable(e):
    return render_template("503.html"), 503

@bp.app_errorhandler(400)
def Bad_Service(e):
    return render_template("400.html"), 400

