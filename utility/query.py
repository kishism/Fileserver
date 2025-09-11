import sqlite3

DB_PATH = "../ftp.db"

def get_directory_contents(dir_id=None, conn=None):
    """Fetch directories and files for a given directory id."""
    cursor = conn.cursor()

    # Fetch subdirectories
    if dir_id is None:
        cursor.execute("SELECT id, name FROM directories WHERE parent_id IS NULL")
    else:
        cursor.execute("SELECT id, name FROM directories WHERE parent_id = ?", (dir_id,))
    directories = cursor.fetchall()

    # Fetch files
    if dir_id is None:
        cursor.execute("SELECT name FROM files WHERE directory_id IS NULL")
    else:
        cursor.execute("SELECT name FROM files WHERE directory_id = ?", (dir_id,))
    files = cursor.fetchall()

    return directories, files

def print_tree(dir_id=None, prefix="", conn=None):
    """Recursively print directories and files."""
    directories, files = get_directory_contents(dir_id, conn)

    for d_id, d_name in directories:
        print(f"{prefix}[DIR] {d_name}/")
        # Recursive call for subdirectory
        print_tree(d_id, prefix + "    ", conn)

    for f in files:
        print(f"{prefix}[FILES] {f[0]}")

def main():
    conn = sqlite3.connect(DB_PATH)
    print("FTP Server Directory Tree:\n")
    print_tree(conn=conn)
    conn.close()

if __name__ == "__main__":
    main()
