#ftp/routes/hypermedia.py
# It prepares HTML responses and adds hypermedia-specific headers.
from flask import render_template, make_response, request
import datetime

def hypermedia_response(dirpath, directories, files):
    """
    Prepare a hypermedia HTML response for a directory.
    Automatically selects 'root.html' for root, 'directory.html' for others.
    """
    # Pick template based on whether it's the root or a subdirectory
    template_name = "root.html" if dirpath == "root" else "directory.html"

    # Render the HTML with the directory and file contents
    html = render_template(template_name,
                           dirpath=dirpath,
                           directories=directories,
                           files=files)

    # Build response with hypermedia headers
    response = make_response(html)
    response.headers["Content-Type"] = "text/html"
    response.headers["Last-Modified"] = datetime.datetime.utcnow().isoformat() + "Z"
    response.headers["Allow"] = "GET, PUT, DELETE"

    # Hypermedia-specific links
    links = []

    # 'self' points to the current resource
    links.append(f'<{request.path}>; rel="self"')

    # 'parent' points to root if not already root
    if dirpath != "root":
        links.append(f'</>; rel="parent"')

    # Join all links and set the Link header
    response.headers["Link"] = ", ".join(links)

    return response

def hypermedia_file_response(filepath, filename, mime_type, size):
    """
    Prepare a hypermedia HTML response for a file view.
    Renders 'file.html' with file metadata.
    """
    # Render the HTML content with file metadata
    html = render_template(
        "file.html",
        filepath=filepath,
        filename=filename,
        mime_type=mime_type,
        size=size,
    )

    # Build Flask response with hypermedia headers
    response = make_response(html)
    response.headers["Content-Type"] = "text/html"
    response.headers["Last-Modified"] = datetime.datetime.utcnow().isoformat() + "Z"
    response.headers["Allow"] = "GET, PUT, DELETE"

    # Hypermedia links
    links = []

    # 'self' points to the current file resource
    links.append(f'<{request.path}>; rel="self"')

    # 'parent' points to the directory containing the file in the FTP hierarchy
    # Strip leading/trailing slashes and split
    parts = filepath.strip("/").split("/")
    parent_parts = parts[:-1]  # all but the last element (the file itself)
    if parent_parts:
        parent_path = "/" + "/".join(parent_parts)  
    else:
        parent_path = "/"  # top-level file parent is root

    links.append(f'<{parent_path}>; rel="parent"')

    # Set Link header with all links
    response.headers["Link"] = ", ".join(links)

    return response