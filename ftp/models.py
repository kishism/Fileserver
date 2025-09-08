# ftp/models.py
import sqlite3

DB_PATH = "ftp.db"

def get_db_connection():
    """Return a SQLite connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
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
