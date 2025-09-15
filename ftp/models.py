# ftp/models.py
import sqlite3
from flask import current_app
import os 
from werkzeug.utils import secure_filename

UPLOAD_BASE_PATH = "C:/ftp-server"

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

def ensure_directory_exists(path):
    """
    For implicit root directory (parent_id IS NULL), return None for root.
    Only create and return IDs for non-root directories.
    """
    if not path or path == "root":
        # Root is implicit, so return None
        return None

    conn = get_db_connection()
    cursor = conn.cursor()

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
            cursor.execute(
                "INSERT INTO directories (name, parent_id) VALUES (?, ?)",
                (part, dir_id)
            )
            dir_id = cursor.lastrowid
            conn.commit()

    conn.close()
    return dir_id


def save_file_to_directory(file, dirpath):
    """
    Save uploaded file into the database under the given directory.
    """
    dir_id = ensure_directory_exists(dirpath or "root")
    
    # Read file content for BLOB saving
    file_content = file.read()
    
    # Reset file stream position to beginning to save physically after reading for blob
    file.stream.seek(0)
    
    # Save metadata and blob content in DB
    conn = sqlite3.connect(current_app.config["DATABASE"])
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO files (name, mime_type, content, directory_id) VALUES (?, ?, ?, ?)",
        (file.filename, file.mimetype, file_content, dir_id)
    )
    conn.commit()
    conn.close()

    # Physical file saving part:
    physical_dir = UPLOAD_BASE_PATH if not dirpath or dirpath == "root" else os.path.join(UPLOAD_BASE_PATH, dirpath)
    os.makedirs(physical_dir, exist_ok=True)
    filename = secure_filename(file.filename)
    physical_file_path = os.path.join(physical_dir, filename)
    file.save(physical_file_path)

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

def create_directory_in_db(parent_path, new_dir_path):
    """
    Creates directories in the database, auto-creating any missing intermediate folders.
    parent_path: path relative to root ("" = root)
    new_dir_path: can be nested, e.g., "folder/subfolder"
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Ensure table exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS directories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        parent_id INTEGER,
        FOREIGN KEY(parent_id) REFERENCES directories(id) ON DELETE CASCADE
    );
    """)
    conn.commit()

    # Start from root
    parent_id = None if not parent_path else None
    if parent_path:
        # Resolve parent_path
        parts = parent_path.strip("/").split("/")
        for part in parts:
            if parent_id is None:
                cursor.execute(
                    "SELECT id FROM directories WHERE name=? AND parent_id IS NULL",
                    (part,)
                )
            else:
                cursor.execute(
                    "SELECT id FROM directories WHERE name=? AND parent_id=?",
                    (part, parent_id)
                )
            row = cursor.fetchone()
            if row is None:
                # Auto-create intermediate folder
                cursor.execute(
                    "INSERT INTO directories (name, parent_id) VALUES (?, ?)",
                    (part, parent_id)
                )
                conn.commit()
                cursor.execute(
                    "SELECT id FROM directories WHERE name=? AND parent_id=?",
                    (part, parent_id)
                )
                row = cursor.fetchone()
            parent_id = row["id"]

    # Create nested folders in new_dir_path
    for part in new_dir_path.strip("/").split("/"):
        if parent_id is None:
            cursor.execute(
                "SELECT id FROM directories WHERE name=? AND parent_id IS NULL",
                (part,)
            )
        else:
            cursor.execute(
                "SELECT id FROM directories WHERE name=? AND parent_id=?",
                (part, parent_id)
            )
        row = cursor.fetchone()
        if row:
            parent_id = row["id"]
            continue
        # Insert folder
        cursor.execute(
            "INSERT INTO directories (name, parent_id) VALUES (?, ?)",
            (part, parent_id)
        )
        conn.commit()
        cursor.execute(
            "SELECT id FROM directories WHERE name=? AND parent_id=?",
            (part, parent_id)
        )
        row = cursor.fetchone()
        parent_id = row["id"]

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

    # print("DEBUG: filename =", filename)
    # print("DEBUG: dir_path_parts =", dir_path_parts)

    parent_id = None
    for part in dir_path_parts:
        cursor.execute(
            "SELECT id FROM directories WHERE name=? AND parent_id IS ?",
            (part, parent_id)
        )
        row = cursor.fetchone()
        # print("DEBUG: checking directory part =", part, "found row:", row)
        if row is None:
            conn.close()
            return None, None
        parent_id = row["id"]

    cursor.execute(
        "SELECT content, mime_type FROM files WHERE name=? AND directory_id IS ?",
        (filename, parent_id)
    )
    row = cursor.fetchone()
    # print("DEBUG: final file row:", row)
    conn.close()
    if row:
        # print("DEBUG: returning content type =", type(row["content"]))
        return row["content"], row["mime_type"]
    return None, None
