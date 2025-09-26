# ftp/routes/directories.py
# This file defines all routes related to directory browsing.
# Each route calls helper functions from models.py to fetch data
# and uses hypermedia.py to render the response with headers.

import io
import requests
import mimetypes
import datetime
from pathlib import Path
from flask import current_app
from flask import Response, abort
from flask import Blueprint, abort, flash, render_template, request, redirect, send_file, url_for
from ftp.models import *
from ftp.routes.hypermedia import hypermedia_response, hypermedia_file_response
import os 
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename
from colorama import init, Fore, Style

base_path = None
upload_base_path = None

def init_app(app):
    global base_path, go_file_server_url

    base_path = app.config["BASE_PATH"]
    go_file_server_url = app.config["GO_FILE_SERVER_URL"]
    
# Initialize Colorama
init(autoreset=True)

# 510 status code from HTTPException
# 510 is not a standard HTTP status code, hence Flask doesn't recongize it
class NotExtended(HTTPException):
    code = 510
    description = "Not Extended"

# Create a blueprint for directory routes.
# This groups all directory-related endpoints together.
# No url_prefix here; it will be set when registering the blueprint in __init__.py
bp = Blueprint("directories", __name__) 

@bp.route("/raw/<path:filepath>", methods=["GET"], endpoint="serve_file")
def proxy_to_file_rendering(filepath):
    go_url = f"{go_file_server_url}/raw/{filepath}"
    try:

        headers = {}
        if "Range" in request.headers:
            headers["Range"] = request.headers["Range"]

        print(f"[DEBUG] Proxying file request to Go: {go_url}")
        r = requests.get(go_url, stream=True, headers=headers, timeout=(5, 30))
        
        if r.status_code == 404:
            print(f"[WARN] File not found on Go server: {filepath}")
            abort(404)
        elif r.status_code >= 500:
            print(f"[ERROR] Go server error for file {filepath}: {r.status_code}")
            abort(502, description="Upstream service error")
        
        forwarded_headers = dict(r.headers)
        forwarded_headers.setdefault("Cache-Control", "no-cache")
        forwarded_headers["X-Proxy-By"] = "Flask"
        forwarded_headers["X-Served-By"] = "Go-Microservice"

        print(f"[INFO] Streaming file through Flask: {filepath}, headers: {forwarded_headers}")
        return Response(
            r.iter_content(chunk_size=8192),
            status=r.status_code,
            content_type=r.headers.get("Content-Type", "application/octet-stream"),
            headers=forwarded_headers
        )
    
    except requests.Timeout:
        print(f"[ERROR] Timeout when contacting Go service for {filepath}")
        abort(504, description="Upstream service timeout")
    except requests.RequestException as e:
        print(f"[ERROR] Failed to contact Go service: {e}")
        abort(502, description=f"Failed to contact Go service: {e}")

# Syncing with filesystem
def scan_physical_directory(dirpath):
    abs_path = os.path.join(base_path, dirpath) if dirpath else base_path
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Scanning physical directory at: '{abs_path}'")

    if not os.path.exists(abs_path):
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Path does not exist: '{abs_path}'")
        return None, None
    if not os.path.isdir(abs_path):
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Path is not a directory: '{abs_path}'")
        return None, None

    try:
        entries = os.listdir(abs_path)
        print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Found {len(entries)} entries in directory")
    except PermissionError:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Permission denied when accessing: '{abs_path}'")
        return None, None

    directories = [d for d in entries if os.path.isdir(os.path.join(abs_path, d))]
    print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Subdirectories found: {directories}")

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
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Listing contents of root directory")
    
    directories, files = scan_physical_directory("")
    if directories is None and files is None:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Root directory not found or inaccessible, returning 404")
        abort(404)
    
    print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Root directory contains {len(directories)} directories and {len(files)} files")
    return hypermedia_response(dirpath="root", directories=directories, files=files)

# List subdirectories
@bp.route("/<path:dirpath>/", methods=["GET"])
def list_directory(dirpath):
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Listing contents of subdirectory: '{dirpath}'")
    
    directories, files = scan_physical_directory(dirpath)
    if directories is None and files is None:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Subdirectory not found or inaccessible, returning 404")
        abort(404)

    print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Subdirectory contains {len(directories)} directories and {len(files)} files")
    return hypermedia_response(dirpath=dirpath or "root", directories=directories, files=files)

@bp.route("/upload", defaults={"dirpath": None}, methods=["POST"])
@bp.route("/<path:dirpath>/upload", methods=["POST"])
def upload_file(dirpath):
    file = request.files.get("file")
    if not file or file.filename == "":
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Upload failed: No file provided.")
        abort(400, description="No file provided")
    
    filename = secure_filename(file.filename)
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Uploading file '{filename}' to directory '{dirpath or 'root'}'")
    
    actual_dirpath = dirpath or ""
    physical_dir = os.path.join(base_path, actual_dirpath)
    try:
        os.makedirs(physical_dir, exist_ok=True)
        print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Ensured upload directory exists: '{physical_dir}'")
    except Exception as e:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Failed to create upload directory '{physical_dir}': {e}")
        flash(f"Failed to create upload directory: {e}", "error")
        return redirect(request.referrer or url_for("directories.list_directory", dirpath=actual_dirpath))
    
    physical_file_path = os.path.join(physical_dir, filename)
    try:
        file.save(physical_file_path)
        print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} File saved physically to '{physical_file_path}'")
    except Exception as e:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Failed to save uploaded file '{filename}': {e}")
        flash(f"Failed to save uploaded file: {e}", "error")
        return redirect(request.referrer or url_for("directories.list_directory", dirpath=actual_dirpath))
    
    mime_type, _ = mimetypes.guess_type(physical_file_path)
    mime_type = mime_type or file.mimetype or "application/octet-stream"
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Guessed MIME type: '{mime_type}'")
    
    created_timestamp = os.path.getctime(physical_file_path)
    created_date = datetime.datetime.fromtimestamp(created_timestamp)
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Added created date: '{created_date}'")

    # Save metadata into DB
    try:
        save_file_to_directory(file, dirpath)
        print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} File metadata saved into database")
    except Exception as e:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Failed to save file metadata: {e}")

    if not actual_dirpath:
        print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Redirecting to root directory listing after upload")
        return redirect(url_for("directories.list_root_directory"))
    else:
        print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Redirecting to directory listing '{actual_dirpath}' after upload")
        return redirect(url_for("directories.list_directory", dirpath=actual_dirpath))
    
# Folder Upload
@bp.route("/upload_folder", methods=["POST"])
@bp.route("/<path:dirpath>/upload_folder", methods=["POST"])
def upload_folder(dirpath=None):
    """
    Handle folder upload.
    The browser sends multiple files with relative paths.
    """
    uploaded_files = request.files.getlist("files")
    if not uploaded_files:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Upload failed: No files provided")
        abort(400, description="No files provided")

    actual_dirpath = dirpath or ""
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Uploading folder contents to directory: '{actual_dirpath or 'root'}'")
    saved_files = []

    for file in uploaded_files:
        # Extract relative path; webkitRelativePath is supported by some browsers
        rel_path = getattr(file, "webkitRelativePath", file.filename)
        print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Processing file with relative path: '{rel_path}'")

        # Normalize path delimiter to OS format and prepend parent dir if any
        rel_path = rel_path.replace("/", os.path.sep)
        full_path = os.path.normpath(os.path.join(base_path, actual_dirpath, rel_path))
        print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Resolved full file path: '{full_path}'")

        # Ensure parent directories exist
        parent_dir = os.path.dirname(full_path)
        try:
            os.makedirs(parent_dir, exist_ok=True)
            print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Ensured directory exists: '{parent_dir}'")
        except Exception as e:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Failed to create directory '{parent_dir}': {e}")
            flash(f"Failed to create directory: {e}", "error")
            return redirect(url_for("directories.list_directory", dirpath=actual_dirpath or ""))

        # Save file physically
        try:
            file.save(full_path)
            print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Saved file to '{full_path}'")
            saved_files.append(full_path)
        except Exception as e:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Failed to save file '{full_path}': {e}")
            flash(f"Failed to save file: {e}", "error")
            return redirect(url_for("directories.list_directory", dirpath=actual_dirpath or ""))

        # Optionally update database with file metadata
        # e.g., create_file_in_db(rel_path, actual_dirpath, ...)

    flash(f"Uploaded {len(saved_files)} files successfully.", "success")
    print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Uploaded {len(saved_files)} files successfully to '{actual_dirpath or 'root'}'")
    return redirect(url_for("directories.list_directory", dirpath=actual_dirpath or ""))

# Create Directory 
@bp.route("/create_directory", methods=["POST"])
def create_directory():
    parent_dir = request.form.get("parent_dir") or ""  # "" means root
    new_dir_name = request.form.get("dirname")

    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Received parent_dir: '{parent_dir}'")
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} New directory name: '{new_dir_name}'")

    if not new_dir_name:
        flash("Folder name is required.", "error")
        return redirect(request.referrer or url_for("directories.list_root_directory"))

    path_parts = [secure_filename(p) for p in new_dir_name.strip("/").split("/") if p]
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} path_parts after split and sanitize: {path_parts}")

    if not path_parts:
        flash("Invalid folder name.", "error")
        return redirect(request.referrer or url_for("directories.list_root_directory"))

    physical_parent = os.path.abspath(os.path.join(base_path, parent_dir))
    physical_folder_path = os.path.abspath(os.path.normpath(os.path.join(physical_parent, *path_parts)))
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Resolved physical folder path (absolute): {physical_folder_path}")

    if not physical_folder_path.startswith(os.path.abspath(base_path)):
        flash("Invalid folder path.", "error")
        return redirect(request.referrer or url_for("directories.list_root_directory"))

    if os.path.exists(physical_folder_path):
        flash("Folder already exists on disk.", "error")
        return redirect(request.referrer or url_for("directories.list_directory", dirpath=parent_dir))

    try:
        os.makedirs(physical_folder_path, exist_ok=False)
        print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Created folder: {physical_folder_path}")
    except Exception as e:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Exception during folder creation: {e}")
        flash(f"Failed to create folder on disk: {e}", "error")
        return redirect(request.referrer or url_for("directories.list_directory", dirpath=parent_dir))

    print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Folders currently in parent directory: {os.listdir(physical_parent)}")

    # Defensive DB insertion with debugging
    try:
        print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Calling create_directory_in_db with parent_dir='{parent_dir}' new_dir='{ '/'.join(path_parts) }'")
        result = create_directory_in_db(parent_dir, "/".join(path_parts))

        if result is None:
            raise ValueError("Database insertion function returned None unexpectedly")

        print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Database insert successful: {result}")
    except Exception as e:
        # Roll back folder creation on DB insertion failure
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Database insertion failed: {e}. Rolling back folder creation...")
        try:
            os.rmdir(physical_folder_path)
            print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Rolled back folder at {physical_folder_path}")
        except Exception as rollback_e:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Rollback folder removal failed: {rollback_e}")
        flash(f"Database error: {e}", "error")
        return redirect(request.referrer or url_for("directories.list_directory", dirpath=parent_dir))

    flash(f"Folder '{'/'.join(path_parts)}' created successfully.", "success")
    return redirect(url_for("directories.list_directory", dirpath=parent_dir))


# File Viewing
@bp.route("/file/<path:filepath>", methods=["GET"])
def view_file(filepath):

    normalized_path = Path(base_path) / Path(filepath)
    full_path = str(normalized_path.resolve())
    print(f"{Fore.CYAN}[DEBUG]{Style.RESET_ALL} Requested file path: '{filepath}', resolved full path: '{full_path}'")

    if not os.path.isfile(full_path):
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} File not found: '{full_path}', returning 404")
        abort(404)

    mime_type, _ = mimetypes.guess_type(full_path)
    if mime_type is None:
        mime_type = "application/octet-stream"
    file_size = os.path.getsize(full_path)

    dirpath = str(Path(filepath).parent)
    filename = Path(filepath).name

    created_date = None
    try: 
        with get_db_connection() as conn:
            cursor = conn.cursor()

            if dirpath == ".":
                dir_id = None
            else:
                cursor.execute("SELECT id FROM directories WHERE name = ?", (dirpath,))
                row = cursor.fetchone()
                dir_id = row[0] if row else None

            cursor.execute(
                "SELECT creation_date FROM files WHERE name = ? and directory_id is ?",
                (filename, dir_id)
            )
            row = cursor.fetchone()
            if row:
                created_date = row[0]
    except Exception as e:
          print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Failed to fetch creation date: {e}")

    # Fallback if DB lookup fails
    if not created_date:
        created_date = datetime.datetime.utcnow().isoformat()

    print(f"{Fore.GREEN}[INFO]{Style.RESET_ALL} Serving file '{filepath}' with MIME type '{mime_type}', size {file_size} bytes, creation date {created_date}")
    return hypermedia_file_response(
        filepath=filepath,
        filename=os.path.basename(full_path),
        mime_type=mime_type,
        size=file_size,
        created_date=created_date
    )


# File Serving
#
#   This function is moved to Go microservices.
#
# @bp.route("/raw/<path:filepath>", methods=["GET"])
# def serve_file(filepath):
#     full_path = os.path.join(base_path, filepath)
#     print(f"{Fore.CYAN}[DEBUG]{Style.RESET_ALL} Serving raw file request for: '{filepath}', resolved full path: '{full_path}'")

#     if not os.path.isfile(full_path):
#         print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} File not found at path: '{full_path}', returning 404")
#         abort(404)

#     mime_type, _ = mimetypes.guess_type(full_path)
#     if mime_type is None:
#         mime_type = "application/octet-stream"
#     print(f"{Fore.GREEN}[INFO]{Style.RESET_ALL} Determined MIME type: '{mime_type}'")

#     return send_file(full_path, mimetype=mime_type, as_attachment=False)

# debug route for file creation
@bp.route('/test_create_folder/')
def test_create_folder():
    test_folder = os.path.join(base_path, "testfolder")
    try:
        os.makedirs(test_folder, exist_ok=True)
        return f"Test folder created at {test_folder}"
    except Exception as e:
        return f"Failed to create test folder: {e}"

# File Deletion
@bp.route("/delete_file", methods=["POST"])
def delete_file():
    filepath = request.form.get("filepath")
    print(f"{Fore.CYAN}[DEBUG]{Style.RESET_ALL} Received filepath: {filepath}")

    if not filepath:
        flash("File path is required.", "error")
        return redirect(request.referrer or url_for("directories.list_root_directory"))

    # Normalize path
    physical_path = os.path.normpath(os.path.join(base_path, filepath))
    print(f"{Fore.CYAN}[DEBUG]{Style.RESET_ALL} Physical path resolved: {physical_path}")

    if not physical_path.startswith(os.path.abspath(base_path)):
        flash("Invalid file path.", "error")
        return redirect(request.referrer)

    try:
        delete_file_from_db_and_disk(filepath)
        flash(f"File '{filepath}' deleted successfully.", "success")
        print(f"{Fore.GREEN}[INFO]{Style.RESET_ALL} File '{filepath}' deleted successfully.")
    except Exception as e:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Failed to delete file '{filepath}': {e}")
        flash(f"Failed to delete file '{filepath}': {e}", "error")

    return redirect(request.referrer or url_for("directories.list_root_directory"))

# Folder Deletion
@bp.route("/delete_directory", methods=["POST"])
def delete_directory():
    dirpath = request.form.get("dirpath")
    print(f"{Fore.CYAN}[DEBUG]{Style.RESET_ALL} Received dirpath: {dirpath}")

    if not dirpath:
        flash("Directory path is required.", "error")
        return redirect(request.referrer or url_for("directories.list_root_directory"))

    # Normalize path
    physical_path = os.path.normpath(os.path.join(base_path, dirpath))
    print(f"{Fore.CYAN}[DEBUG]{Style.RESET_ALL} Physical path resolved: {physical_path}")

    if not physical_path.startswith(os.path.abspath(base_path)):
        flash("Invalid directory path.", "error")
        return redirect(request.referrer)

    try:
        delete_directory_from_db_and_disk(dirpath)
        flash(f"Directory '{dirpath}' deleted successfully.", "success")
        print(f"{Fore.GREEN}[INFO]{Style.RESET_ALL} Directory '{dirpath}' deleted successfully.")
    except Exception as e:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Failed to delete directory '{dirpath}': {e}")
        flash(f"Failed to delete directory '{dirpath}': {e}", "error")

    return redirect(request.referrer or url_for("directories.list_root_directory"))

INLINE_PREVIEW_TYPES = [
    'image/',      
    'text/',       
    'application/pdf',  
    'audio/',     
    'video/'       
]
    
@bp.route('/download')
def download_file():
    requested_path = request.args.get("path", "")
    if not requested_path:
        abort(404)

    abs_path = os.path.abspath(os.path.join(base_path, requested_path))

    if os.path.commonpath([base_path, abs_path]) != os.path.abspath(base_path):
        abort(403)

    if os.path.islink(abs_path):
        abort(403)

    if not os.path.isfile(abs_path):
        abort(404)

    mime_type, _ = mimetypes.guess_type(abs_path)
    if not mime_type:
        mime_type = "application/octet-stream"

    as_attachment = True
    for inline_type in INLINE_PREVIEW_TYPES: 
        if mime_type.startswith(inline_type) or mime_type == inline_type:
            as_attachment = False
            break

    return send_file(abs_path, mimetype=mime_type, as_attachment=as_attachment, download_name=os.path.basename(abs_path))    

@bp.route("/favicon.ico")
def favicon():
    return "", 204  # No content, no errors

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
