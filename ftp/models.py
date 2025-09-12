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
        "INSERT INTO files (name, mime_type, directory_id) VALUES (?, ?, ?)",
        (file.filename, file.mimetype, dir_id)
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
