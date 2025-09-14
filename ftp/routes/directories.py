# ftp/routes/directories.py
# This file defines all routes related to directory browsing.
# Each route calls helper functions from models.py to fetch data
# and uses hypermedia.py to render the response with headers.

import io
from flask import Blueprint, abort, render_template, request, redirect, send_file, url_for
from ftp.models import *
from ftp.routes.hypermedia import hypermedia_directory_response
import os 
from werkzeug.exceptions import HTTPException

# 510 status code from HTTPException
# 510 is not a standard HTTP status code, hence Flask doesn't recongize it
class NotExtended(HTTPException):
    code = 510
    description = "Not Extended"

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

# File Viewing
@bp.route("/file/<path:filepath>", methods=["GET"])
def view_file(filepath):
    """
    Render a page showing file metadata and optional preview.
    """
    file_data, mime_type = get_file_from_db(filepath)
    if file_data is None:
        print("DEBUG: file not found in DB")
        abort(404)

    return render_template(
        "file.html",
        filepath=filepath,
        filename=os.path.basename(filepath),
        mime_type=mime_type,
        size=len(file_data)
    )

# File Serving
@bp.route("/raw/<path:filepath>")
def serve_file(filepath):
    """ 
    Return raw file bytes for download or inline viewing.
    """
    file_data, mime_type = get_file_from_db(filepath)
    if not file_data:
        abort(404)
    return send_file(io.BytesIO(file_data),
                     mimetype=mime_type,
                     as_attachment=False,  # False = render inline if possible
                     download_name=os.path.basename(filepath))

# Error Handling Pages 
# NNL
# Handle 404 Not Found errors
@bp.app_errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# Handle 500 Internal Server errors
@bp.app_errorhandler(500)
def internal_server_errors(e):
    return render_template("500.html"), 500

# Handle 403 Forbidden errors
@bp.app_errorhandler(403)
def access_forbidden(e):
    return render_template("403.html"), 403

# Handle 503 Service Unavailable errors
@bp.app_errorhandler(503)
def service_unavailable(e):
    return render_template("503.html"), 503

# Handle 400 Bad Request errors
@bp.app_errorhandler(400)
def bad_service(e):
    return render_template("400.html"), 400

# Handle 408 Request Timeout errors
@bp.app_errorhandler(408)
def request_timeout(e):
    return render_template("408.html"), 408

# Handle 429 Too Many Requests errors
@bp.app_errorhandler(429)
def too_many_request(e):
    return render_template("429.html"), 429

# Handle 502 Bad Gateway errors
@bp.app_errorhandler(502)
def bad_gateway(e):
    return render_template("502.html"), 502

# Handle 504 Gateway Timeout errors
@bp.app_errorhandler(504)
def gateway_timeout(e):
    return render_template("504.html"), 504

# Handle 510 Not Extended / Gone errors
@bp.app_errorhandler(NotExtended)
def not_extended(e):
    return "Not Extended", 510
