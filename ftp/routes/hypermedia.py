def render_directory(name, directories, files, parent=None):
    html = f"""
    <html>
      <head><title>{name}/</title></head>
      <body>
        <h1>{name}/</h1>
        <ul>
    """
    for d in directories:
        html += f'<li><a href="/directories/{d}/">{d}/</a></li>'
    for f in files:
        html += f'<li><a href="/files/{f}">{f}</a></li>'
    html += """
        </ul>
        <form action="/files/newfile.txt" method="PUT" enctype="multipart/form-data">
          <input type="file" name="content">
          <button type="submit">Upload File</button>
        </form>
      </body>
    </html>
    """
    return html
