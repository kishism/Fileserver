# start.py
from pathlib import Path
import os
from dotenv import load_dotenv
from waitress import serve
from ftp import create_app

ENV_PATH = Path(".env")

if not ENV_PATH.exists():
    from setup_wizard import run_wizard
    run_wizard(ENV_PATH)

load_dotenv(dotenv_path=ENV_PATH)

app = create_app()

if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 5000))
    HOST = os.getenv("HOST", "127.0.0.1")

    print("Starting FTP server via Waitress...")
    print(f"Webserver serving at: {HOST}:{PORT}")
    serve(app, host=HOST, port=PORT, threads=8)