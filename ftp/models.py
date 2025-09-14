# ftp/models.py
import sqlite3
from flask import current_app

def get_db_connection():
    """Return a SQLite connection with row factory."""
    db_path = current_app.config.get("DATABASE")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_directory_contents(path=None):
    """
    Fetch directories and files for a given directory.
    Returns two lists: directories and files.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get directory id
    if path is None or path == "root":
       # root directory 
       dir_id = None   # keep None for root
    else:
        parts = path.strip("/").split("/")
        dir_id = None
        for part in parts:
            cursor.execute(
                "SELECT id FROM directories WHERE name=? AND parent_id IS ?",
                (part, dir_id)
            )
            row = cursor.fetchone()
            if row is None:
                return None, None  # Path does not exist
            dir_id = row["id"]

    # Fetch subdirectories
    if dir_id is None:
        cursor.execute("SELECT name FROM directories WHERE parent_id IS NULL")
    else:
        cursor.execute("SELECT name FROM directories WHERE parent_id = ?", (dir_id,))
    directories = [r["name"] for r in cursor.fetchall()]

    # Fetch files
    if dir_id is None:
        cursor.execute("SELECT name, mime_type FROM files WHERE directory_id IS NULL")
    else:
        cursor.execute("SELECT name, mime_type FROM files WHERE directory_id = ?", (dir_id,))
    files = [{"name": r["name"], "mime_type": r["mime_type"]} for r in cursor.fetchall()]

    conn.close()
    return directories, files


def save_file_to_directory(file, dirpath):
    """
    Save uploaded file into the database under the given directory.
    """
    conn = sqlite3.connect(current_app.config["DATABASE"])
    cursor = conn.cursor()

    if dirpath == "root" or not dirpath:
        dir_id = None
    else:
        parts = dirpath.strip("/").split("/")
        dir_id = None
        for part in parts:
            cursor.execute(
                "SELECT id FROM directories WHERE name=? AND parent_id IS ?",
                (part, dir_id)
            )
            row = cursor.fetchone()
            if row is None:
                conn.close()
                raise ValueError(f"Directory {dirpath} does not exist")
            dir_id = row[0]

    # Insert file metadata
    cursor.execute(
        "INSERT INTO files (name, mime_type, content, directory_id) VALUES (?, ?, ?, ?)",
        (file.filename, file.mimetype, file.read(), dir_id)
    )
    conn.commit()
    conn.close()

def save_file_from_folder(file, path):
    """
    Save a file into the given directory path.
    Automatically ensures the directory path exists.
    """
    # Split path into directory part + filename
    parts = path.strip("/").split("/")
    dirname = "/".join(parts[:-1]) if len(parts) > 1 else None
    filename = parts[-1]

    conn = get_db_connection()
    cursor = conn.cursor()

    # Ensure directory exists (create if missing)
    dir_id = None
    if dirname:
        dir_id = ensure_directory_exists(dirname)

    # Save file metadata into DB
    cursor.execute(
        "INSERT INTO files (name, mime_type, directory_id) VALUES (?, ?, ?)",
        (filename, file.mimetype, dir_id)
    )
    conn.commit()
    conn.close()


def ensure_directory_exists(path):
    """
    Ensure that a directory path exists in the DB.
    Creates any missing directories along the path.
    Returns the final directory_id.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Start from root
    dir_id = None
    parts = path.strip("/").split("/")

    for part in parts:
        cursor.execute(
            "SELECT id FROM directories WHERE name = ? AND parent_id IS ?",
            (part, dir_id)
        )
        row = cursor.fetchone()
        if row:
            dir_id = row["id"]
        else:
            # Insert new directory
            cursor.execute(
                "INSERT INTO directories (name, parent_id) VALUES (?, ?)",
                (part, dir_id)
            )
            dir_id = cursor.lastrowid
            conn.commit()

    conn.close()
    return dir_id

def create_directory_in_db(parent_path, new_dir_name):
    """
    Creates a new directory in the database under parent_path.
    Raises ValueError if directory already exists.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Determine parent_id
    if parent_path is None or parent_path == "root" or parent_path == "":
        parent_id = None
    else:
        parts = parent_path.strip("/").split("/")
        parent_id = None
        for part in parts:
            cursor.execute(
                "SELECT id FROM directories WHERE name=? AND parent_id IS ?",
                (part, parent_id)
            )
            row = cursor.fetchone()
            if row is None:
                conn.close()
                raise ValueError(f"Parent directory {parent_path} does not exist")
            parent_id = row["id"]

    # Check if directory already exists
    cursor.execute(
        "SELECT 1 FROM directories WHERE name=? AND parent_id IS ?",
        (new_dir_name, parent_id)
    )
    if cursor.fetchone():
        conn.close()
        raise ValueError(f"Directory {new_dir_name} already exists in {parent_path}")

    # Insert new directory
    cursor.execute(
        "INSERT INTO directories (name, parent_id) VALUES (?, ?)",
        (new_dir_name, parent_id)
    )
    conn.commit()
    conn.close()

def get_file_from_db(filepath):
    """
    Retrieve file bytes and MIME type from DB by full path.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Split into directory + filename
    parts = filepath.strip("/").split("/")
    filename = parts[-1]
    dir_path_parts = parts[:-1]

    print("DEBUG: filename =", filename)
    print("DEBUG: dir_path_parts =", dir_path_parts)

    parent_id = None
    for part in dir_path_parts:
        cursor.execute(
            "SELECT id FROM directories WHERE name=? AND parent_id IS ?",
            (part, parent_id)
        )
        row = cursor.fetchone()
        print("DEBUG: checking directory part =", part, "found row:", row)
        if row is None:
            conn.close()
            return None, None
        parent_id = row["id"]

    cursor.execute(
        "SELECT content, mime_type FROM files WHERE name=? AND directory_id IS ?",
        (filename, parent_id)
    )
    row = cursor.fetchone()
    print("DEBUG: final file row:", row)
    conn.close()
    if row:
        print("DEBUG: returning content type =", type(row["content"]))
        return row["content"], row["mime_type"]
    return None, None
