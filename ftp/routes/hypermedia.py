#ftp/routes/hypermedia.py
# It prepares HTML responses and adds hypermedia-specific headers.
from flask import render_template, make_response, request
import datetime

def hypermedia_directory_response(dirpath, directories, files):
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
