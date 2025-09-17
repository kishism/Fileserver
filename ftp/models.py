# ftp/models.py
from contextlib import contextmanager
import shutil
import sqlite3
import time
from flask import current_app
import os 
from werkzeug.utils import secure_filename

UPLOAD_BASE_PATH = "C:/ftp-server"

@contextmanager
def get_db_connection():
    conn = sqlite3.connect("ftp.db")
    conn.row_factory = sqlite3.Row 
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_directory_contents(path=None):
    """
    Fetch directories and files for a given directory.
    Returns two lists: directories and files.
    """
    print(f"Fetching contents for directory path: '{path or 'root'}'")
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get directory id
        if path is None or path == "root":
            dir_id = None  # root directory
            print("Target is root directory (dir_id=None)")
        else:
            parts = path.strip("/").split("/")
            dir_id = None
            for part in parts:
                print(f"Looking up directory '{part}' with parent_id {dir_id}")
                cursor.execute(
                    "SELECT id FROM directories WHERE name=? AND parent_id IS ?",
                    (part, dir_id)
                )
                row = cursor.fetchone()
                if row is None:
                    print(f"Directory path '{path}' does not exist")
                    return None, None  # Path does not exist
                dir_id = row["id"]
            print(f"Found directory ID: {dir_id}")

        # Fetch subdirectories
        if dir_id is None:
            cursor.execute("SELECT name FROM directories WHERE parent_id IS NULL")
        else:
            cursor.execute("SELECT name FROM directories WHERE parent_id = ?", (dir_id,))
        directories = [r["name"] for r in cursor.fetchall()]
        print(f"Found subdirectories: {directories}")

        # Fetch files
        if dir_id is None:
            cursor.execute("SELECT name, mime_type FROM files WHERE directory_id IS NULL")
        else:
            cursor.execute("SELECT name, mime_type FROM files WHERE directory_id = ?", (dir_id,))
        files = [{"name": r["name"], "mime_type": r["mime_type"]} for r in cursor.fetchall()]
        print(f"Found files: {[f['name'] for f in files]}")

    return directories, files


def ensure_directory_exists(path):
    """
    For implicit root directory (parent_id IS NULL), return None for root.
    Only create and return IDs for non-root directories.
    """
    if not path or path == "root":
        print("Path is root or empty, returning None as directory ID")
        return None

    print(f"Ensuring directory path '{path}' exists in DB")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        dir_id = None
        parts = path.strip("/").split("/")

        for part in parts:
            print(f"Looking for directory '{part}' with parent_id {dir_id}")
            cursor.execute(
                "SELECT id FROM directories WHERE name = ? AND parent_id IS ?",
                (part, dir_id)
            )
            row = cursor.fetchone()
            if row:
                dir_id = row["id"]
                print(f"Found existing directory '{part}' with ID {dir_id}")
            else:
                print(f"Directory '{part}' not found. Creating new one")
                cursor.execute(
                    "INSERT INTO directories (name, parent_id) VALUES (?, ?)",
                    (part, dir_id)
                )
                dir_id = cursor.lastrowid
                conn.commit()
                print(f"Created directory '{part}' with new ID {dir_id}")

    print(f"Final directory ID for path '{path}' is {dir_id}")
    return dir_id


def save_file_to_directory(file, dirpath):
    """
    Save uploaded file into the database under the given directory,
    and also save the physical file in the folder structure.
    """
    dir_to_use = dirpath or "root"
    print(f"Ensuring directory '{dir_to_use}' exists in DB")
    dir_id = ensure_directory_exists(dir_to_use)
    print(f"Directory ID obtained: {dir_id}")

    # Read file content for BLOB saving
    file_content = file.read()
    # Reset file stream position to beginning to allow physical save after reading
    file.stream.seek(0)

    print(f"Saving file '{file.filename}' metadata and content into database")
    with sqlite3.connect(current_app.config["DATABASE"]) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO files (name, mime_type, content, directory_id) VALUES (?, ?, ?, ?)",
            (file.filename, file.mimetype, file_content, dir_id)
        )
        conn.commit()
        print(f"File '{file.filename}' saved in DB with directory ID {dir_id}")

    # Physical file saving
    physical_dir = UPLOAD_BASE_PATH if dir_to_use == "root" else os.path.join(UPLOAD_BASE_PATH, dir_to_use)
    print(f"Ensuring physical directory '{physical_dir}' exists")
    os.makedirs(physical_dir, exist_ok=True)

    filename = secure_filename(file.filename)
    physical_file_path = os.path.join(physical_dir, filename)
    print(f"Saving physical file to '{physical_file_path}'")
    file.save(physical_file_path)
    print(f"Physical file saved successfully")


def save_file_from_folder(file, path):
    """
    Save a file into the given directory path.
    Automatically ensures the directory path exists.
    """
    parts = path.strip("/").split("/")
    dirname = "/".join(parts[:-1]) if len(parts) > 1 else None
    filename = parts[-1]

    print(f"Saving file '{filename}' to path '{path}'")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        print("Database connection opened")

        dir_id = None
        if dirname:
            print(f"Ensuring directory '{dirname}' exists")
            dir_id = ensure_directory_exists(dirname)
            print(f"Directory ID obtained: {dir_id}")
        
        cursor.execute(
            "INSERT INTO files (name, mime_type, directory_id) VALUES (?, ?, ?)",
            (filename, file.mimetype, dir_id)
        )
        conn.commit()
        print(f"File '{filename}' saved to database with directory ID {dir_id}")


def create_directory_in_db(parent_path, new_dir_path):
    with get_db_connection() as conn:
        # Create cursor inside the same context
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS directories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                parent_id INTEGER,
                FOREIGN KEY(parent_id) REFERENCES directories(id) ON DELETE CASCADE
            );
        """)
        conn.commit()

        parent_id = None
        if parent_path:
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
                    cursor.execute(
                        "INSERT INTO directories (name, parent_id) VALUES (?, ?) RETURNING id",
                        (part, parent_id)
                    )
                    row = cursor.fetchone()
                    if row is None:
                        raise ValueError(f"Failed to create intermediate directory '{part}' in DB.")
                parent_id = row[0]

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
                parent_id = row[0]
                continue
            cursor.execute(
                "INSERT INTO directories (name, parent_id) VALUES (?, ?) RETURNING id",
                (part, parent_id)
            )
            row = cursor.fetchone()
            if row is None:
                raise ValueError(f"Failed to create new directory '{part}' in DB.")
            parent_id = row[0]

        return parent_id


def get_file_from_db(filepath):
    """
    Retrieve file bytes and MIME type from DB by full path.
    """
    print(f"Retrieving file from DB at path: '{filepath}'")
    with get_db_connection() as conn:
        cursor = conn.cursor()

        parts = filepath.strip("/").split("/")
        filename = parts[-1]
        dir_path_parts = parts[:-1]

        print(f"Filename: '{filename}', Directory parts: {dir_path_parts}")

        parent_id = None
        for part in dir_path_parts:
            print(f"Looking up directory '{part}' with parent_id {parent_id}")
            cursor.execute(
                "SELECT id FROM directories WHERE name=? AND parent_id IS ?",
                (part, parent_id)
            )
            row = cursor.fetchone()
            if row is None:
                print(f"Directory '{part}' not found. File path invalid.")
                return None, None
            parent_id = row["id"]

        cursor.execute(
            "SELECT content, mime_type FROM files WHERE name=? AND directory_id IS ?",
            (filename, parent_id)
        )
        row = cursor.fetchone()
        print(f"Query result for file '{filename}': {row is not None}")

        if row:
            return row["content"], row["mime_type"]
        return

def delete_file_from_db_and_disk(filepath):
    if filepath.startswith("root/"):
        filepath = filepath[5:]
    elif filepath == "root":
        raise ValueError("Cannot delete root")

    physical_path = os.path.join(UPLOAD_BASE_PATH, filepath)
    print(f"[DEBUG] Deleting file '{filepath}' at physical path '{physical_path}'")

    # Delete physical file
    if os.path.exists(physical_path):
        os.remove(physical_path)
        print(f"[DEBUG] Physical file deleted: {physical_path}")
    else:
        print(f"[DEBUG] Physical file does not exist: {physical_path}")

    # Delete from DB
    parts = filepath.strip("/").split("/")
    filename = parts[-1]
    dir_parts = parts[:-1]
    with get_db_connection() as conn:
        cursor = conn.cursor()
        parent_id = None
        for part in dir_parts:
            cursor.execute(
                "SELECT id FROM directories WHERE name=? AND parent_id IS ?",
                (part, parent_id)
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Directory '{'/'.join(dir_parts)}' does not exist in DB.")
            parent_id = row["id"]

        cursor.execute(
            "DELETE FROM files WHERE name=? AND directory_id IS ?",
            (filename, parent_id)
        )
        print(f"[DEBUG] Deleted file '{filename}' from DB")

def delete_directory_from_db_and_disk(dirpath):
    if dirpath.startswith("root/"):
        dirpath = dirpath[5:]
    elif dirpath == "root":
        raise ValueError("Cannot delete root directory")

    physical_path = os.path.join(UPLOAD_BASE_PATH, dirpath)
    print(f"[DEBUG] Deleting directory '{dirpath}' at physical path '{physical_path}'")

    # Delete physical directory recursively
    if os.path.exists(physical_path):
        shutil.rmtree(physical_path)
        print(f"[DEBUG] Physical directory deleted: {physical_path}")
    else:
        print(f"[DEBUG] Physical directory does not exist: {physical_path}")

    # Delete from DB recursively using a single connection
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Find directory ID
        parts = dirpath.strip("/").split("/")
        parent_id = None
        for part in parts:
            cursor.execute(
                "SELECT id FROM directories WHERE name=? AND parent_id IS ?",
                (part, parent_id)
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Directory '{dirpath}' does not exist in DB.")
            parent_id = row["id"]

        # Recursive deletion function
        def delete_dir_recursive(cursor, parent_id):
            # Delete files in this directory
            cursor.execute("DELETE FROM files WHERE directory_id=?", (parent_id,))
            print(f"[DEBUG] Deleted files in directory ID {parent_id}")

            # Find subdirectories
            cursor.execute("SELECT id FROM directories WHERE parent_id=?", (parent_id,))
            subdirs = cursor.fetchall()
            for subdir in subdirs:
                delete_dir_recursive(cursor, subdir["id"])

            # Delete the directory itself
            cursor.execute("DELETE FROM directories WHERE id=?", (parent_id,))
            print(f"[DEBUG] Deleted directory ID {parent_id}")

        delete_dir_recursive(cursor, parent_id)
        print(f"[DEBUG] Finished deleting directory '{dirpath}' and all nested contents")