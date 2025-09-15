# ftp/routes/directories.py
# This file defines all routes related to directory browsing.
# Each route calls helper functions from models.py to fetch data
# and uses hypermedia.py to render the response with headers.

import io
import mimetypes
from flask import Blueprint, abort, flash, render_template, request, redirect, send_file, url_for
from ftp.models import *
from ftp.routes.hypermedia import hypermedia_response, hypermedia_file_response
import os 
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename

BASE_PATH = "C:/ftp-server"

# 510 status code from HTTPException
# 510 is not a standard HTTP status code, hence Flask doesn't recongize it
class NotExtended(HTTPException):
    code = 510
    description = "Not Extended"

# Create a blueprint for directory routes.
# This groups all directory-related endpoints together.
# No url_prefix here; it will be set when registering the blueprint in __init__.py
bp = Blueprint("directories", __name__)  

# Syncing with filesystem
def scan_physical_directory(dirpath):
    abs_path = os.path.join(BASE_PATH, dirpath) if dirpath else BASE_PATH
    if not os.path.exists(abs_path) or not os.path.isdir(abs_path):
        return None, None

    try:
        entries = os.listdir(abs_path)
    except PermissionError:
        return None, None

    directories = [d for d in entries if os.path.isdir(os.path.join(abs_path, d))]
    files = []
    for f in entries:
        full_file_path = os.path.join(abs_path, f)
        if os.path.isfile(full_file_path):
            mime_type, _ = mimetypes.guess_type(full_file_path)
            files.append({"name": f, "mime_type": mime_type or "application/octet-stream"})
    return directories, files

# List root directory
@bp.route("/", methods=["GET"])
def list_root_directory():
    directories, files = scan_physical_directory("")
    if directories is None and files is None:
        abort(404)
    
    return hypermedia_response(dirpath="root", directories=directories, files=files)

# List subdirectories
@bp.route("/<path:dirpath>/", methods=["GET"])
def list_directory(dirpath):
    directories, files = scan_physical_directory(dirpath)
    if directories is None and files is None:
        abort(404)

    print(f"Serving directory: {dirpath}")
    return hypermedia_response(dirpath=dirpath or "root", directories=directories, files=files)

@bp.route("/upload", defaults={"dirpath": None}, methods=["POST"])
@bp.route("/<path:dirpath>/upload", methods=["POST"])
def upload_file(dirpath):
    file = request.files.get("file")
    if not file or file.filename == "":
        abort(400, description="No file provided")
    
    # Secure the filename to avoid directory traversal attacks etc
    filename = secure_filename(file.filename)
    
    # Determine directory path on disk
    actual_dirpath = dirpath or ""
    physical_dir = os.path.join(UPLOAD_BASE_PATH, actual_dirpath)
    try:
        os.makedirs(physical_dir, exist_ok=True)  # Ensure target dir exists
    except Exception as e:
        flash(f"Failed to create upload directory: {e}", "error")
        return redirect(request.referrer or url_for("directories.list_directory", dirpath=actual_dirpath))
    
    # Save file physically on disk
    physical_file_path = os.path.join(physical_dir, filename)
    try:
        file.save(physical_file_path)  # Save uploaded file
    except Exception as e:
        flash(f"Failed to save uploaded file: {e}", "error")
        return redirect(request.referrer or url_for("directories.list_directory", dirpath=actual_dirpath))
    
    
    # Guess mime type from the physical file for metadata storage
    mime_type, _ = mimetypes.guess_type(physical_file_path)
    if not mime_type:
        mime_type = file.mimetype or "application/octet-stream"
    
    # Redirect back to the directory listing page
    if not actual_dirpath:
        return redirect(url_for("directories.list_root_directory"))
    else:
        return redirect(url_for("directories.list_directory", dirpath=actual_dirpath))

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
@bp.route("/create_directory", methods=["POST"])
def create_directory():
    parent_dir = request.form.get("parent_dir") or ""  # "" means root
    new_dir_name = request.form.get("dirname")

    print(f"Received parent_dir: '{parent_dir}'")
    print(f"New directory name: '{new_dir_name}'")

    if not new_dir_name:
        flash("Folder name is required.", "error")
        return redirect(request.referrer or url_for("directories.list_root_directory"))

    # Allow nested folders like "project/2025/september"
    path_parts = [secure_filename(p) for p in new_dir_name.strip("/").split("/") if p]
    if not path_parts:
        flash("Invalid folder name.", "error")
        return redirect(request.referrer or url_for("directories.list_root_directory"))

    # Build physical path
    physical_parent = os.path.join(BASE_PATH, parent_dir)
    physical_folder_path = os.path.normpath(os.path.join(physical_parent, *path_parts))

    # Safety check: prevent escaping BASE_PATH
    if not physical_folder_path.startswith(os.path.abspath(BASE_PATH)):
        flash("Invalid folder path.", "error")
        return redirect(request.referrer or url_for("directories.list_root_directory"))

    # Check if folder already exists on disk
    if os.path.exists(physical_folder_path):
        flash("Folder already exists on disk.", "error")
        return redirect(request.referrer or url_for("directories.list_directory", dirpath=parent_dir))

    # Create folder(s) on disk
    try:
        os.makedirs(physical_folder_path, exist_ok=False)
        print(f"Created folder: {physical_folder_path}")
    except Exception as e:
        flash(f"Failed to create folder on disk: {e}", "error")
        return redirect(request.referrer or url_for("directories.list_directory", dirpath=parent_dir))

    # Insert into DB
    try:
        create_directory_in_db(parent_dir, "/".join(path_parts))
    except Exception as e:
        # Roll back disk if DB insertion fails
        try:
            os.rmdir(physical_folder_path)
        except Exception:
            pass
        flash(f"Database error: {e}", "error")
        return redirect(request.referrer or url_for("directories.list_directory", dirpath=parent_dir))

    flash(f"Folder '{'/'.join(path_parts)}' created successfully.", "success")
    return redirect(url_for("directories.list_directory", dirpath=parent_dir))

# File Viewing
@bp.route("/file/<path:filepath>", methods=["GET"])
def view_file(filepath):
    full_path = os.path.join(BASE_PATH, filepath)
    if not os.path.isfile(full_path):
        abort(404)
    mime_type, _ = mimetypes.guess_type(full_path)
    if mime_type is None:
        mime_type = "application/octet-stream"
    file_size = os.path.getsize(full_path)

    return hypermedia_file_response(
        filepath=filepath,
        filename=os.path.basename(full_path),
        mime_type=mime_type,
        size=file_size,
    )

# File Serving
@bp.route("/raw/<path:filepath>", methods=["GET"])
def serve_file(filepath):
    full_path = os.path.join(BASE_PATH, filepath)
    if not os.path.isfile(full_path):
        abort(404)
    mime_type, _ = mimetypes.guess_type(full_path)
    if mime_type is None:
        mime_type = "application/octet-stream"
    return send_file(full_path, mimetype=mime_type, as_attachment=False)

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
<<<<<<< HEAD
@bp.app_errorhandler(510)
def Gone(e):
    return render_template("510.html"), 510
@bp.app_errorhandler(409)
def Files_or_Foler_is_exit(e):
    return render_template("409.html"), 409
=======

# Handle 510 Not Extended / Gone errors
@bp.app_errorhandler(NotExtended)
def not_extended(e):
    return "Not Extended", 510
>>>>>>> 908988c95b3752a03aef2b4e4b47aec9102cc193
