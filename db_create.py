# db_create.py
import sqlite3
from datetime import datetime

DB_PATH = "ftp.db"

# Helper function -> get database connection
def get_connection():
    return sqlite3.connect(DB_PATH)

# Helper function -> create directory
def create_directory(name, parent_id=None):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now()
    c.execute(
        "INSERT INTO directories (name, parent_id, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (name, parent_id, now, now)
    )
    conn.commit()
    conn.close()

# Helper function -> create file
def create_file(name, directory_id=None, mime_type=None, size=None, content=None):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now()
    c.execute(
        "INSERT INTO files (name, directory_id, mime_type, size, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, directory_id, mime_type, size, content, now, now)
    )
    conn.commit()
    conn.close()

# Main function to create database and tables
def setup_database():
    conn = get_connection()
    c = conn.cursor()

    # Create directories table
    c.execute("""
    CREATE TABLE IF NOT EXISTS directories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        parent_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(parent_id) REFERENCES directories(id)
    )
    """)

    # Create files table
    c.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        directory_id INTEGER,
        mime_type TEXT,
        size INTEGER,
        content BLOB,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(directory_id) REFERENCES directories(id)
    )
    """)

    conn.commit()
    conn.close()

    print(f"{DB_PATH} created.")

    # Insert some initial directories
    create_directory("documents")
    create_directory("images")

    # Get IDs of root directories to attach files
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM directories WHERE name='documents'")
    documents_id = c.fetchone()[0]
    c.execute("SELECT id FROM directories WHERE name='images'")
    images_id = c.fetchone()[0]
    conn.close()

    print(f"{DB_PATH} created with initial directories and files.")

if __name__ == "__main__":
    setup_database()