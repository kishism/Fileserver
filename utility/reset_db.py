# ftp/scripts/reset_db.py
import sqlite3

DB_PATH = "../ftp.db"

def reset_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Drop tables if they exist
    cursor.execute("DROP TABLE IF EXISTS files")
    cursor.execute("DROP TABLE IF EXISTS directories")

    # Recreate tables
    cursor.execute("""
        CREATE TABLE directories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_id INTEGER,
            FOREIGN KEY(parent_id) REFERENCES directories(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            directory_id INTEGER,
            mime_type TEXT,
            FOREIGN KEY(directory_id) REFERENCES directories(id)
        )
    """)

    conn.commit()
    conn.close()
    print("Database has been reset.")

if __name__ == "__main__":
    reset_database()
