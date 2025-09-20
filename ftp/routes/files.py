# from flask import Blueprint, request, make_response
# from ..models import save_file, get_file, delete_file

# bp = Blueprint("files", __name__, url_prefix="/files")

# @bp.route("/<filename>", methods=["GET"])
# def download_file(filename):
#     file_data = get_file(filename)
#     if not file_data:
#         return "File not found", 404

#     response = make_response(file_data["content"])
#     response.headers["Content-Type"] = file_data["mime_type"]
#     response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
#     return response


# @bp.route("/<filename>", methods=["PUT"])
# def upload_file(filename):
#     if "content" not in request.files:
#         return "No file uploaded", 400

#     file_obj = request.files["content"]
#     save_file(filename, file_obj)

#     return f"Uploaded {filename}", 201


# @bp.route("/<filename>", methods=["DELETE"])
# def remove_file(filename):
#     success = delete_file(filename)
#     if not success:
#         return "File not found", 404
#     return f"Deleted {filename}", 200
# 
# commented for now