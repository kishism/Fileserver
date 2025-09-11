# ftp/scripts/seed_db.py
import sqlite3

DB_PATH = "../ftp.db"

def seed_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Root directories
    cursor.execute("INSERT INTO directories (name, parent_id) VALUES (?, ?)", ("documents", None))
    cursor.execute("INSERT INTO directories (name, parent_id) VALUES (?, ?)", ("images", None))

    # Subdirectory
    cursor.execute("INSERT INTO directories (name, parent_id) VALUES (?, ?)", ("papers", 1))  # parent_id=1 => documents

    # Files in root
    cursor.execute("INSERT INTO files (name, directory_id, mime_type) VALUES (?, ?, ?)", ("readme.txt", None, "text/plain"))
    cursor.execute("INSERT INTO files (name, directory_id, mime_type) VALUES (?, ?, ?)", ("cat.png", None, "image/png"))

    # File in subdirectory
    cursor.execute("INSERT INTO files (name, directory_id, mime_type) VALUES (?, ?, ?)", ("paper1.pdf", 3, "application/pdf"))  # papers

    conn.commit()
    conn.close()
    print("Database has been seeded with sample data.")

if __name__ == "__main__":
    seed_database()
