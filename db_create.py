# db_create.py
import sqlite3
from datetime import datetime

DB_PATH = "ftp.db"

def setup_database():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create directories table
    cursor.execute("""
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
    cursor.execute("""
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
    
if __name__ == "__main__":
    setup_database()