# ftp/__init__.py

import os
import subprocess
import atexit
import threading
import time
from flask import Flask
from dotenv import load_dotenv
import requests
from .routes import register_routes

go_process = None

def start_go_service():
    global go_process
    go_executable = os.path.join("microservices", "main.go")

    if not os.path.exists(go_executable):
        raise FileNotFoundError(f"Go executable not found: {go_executable}")
    
    env = os.environ.copy()
    env["BASE_PATH"] = os.getenv("BASE_PATH", "C:/ftp-server")
    env["UPLOAD_BASE_PATH"] = os.getenv("UPLOAD_BASE_PATH", env["BASE_PATH"])
    env["GO_FILE_SERVER_URL"] = os.getenv("GO_FILE_SERVER_URL", "http://localhost:8000")
                                
    go_process = subprocess.Popen(
        ["go", "run", go_executable],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env
    )
    print("[INFO] Go microservice started.")

    ready_event = threading.Event()

    go_url = os.getenv("GO_FILE_SERVER_URL", "http://localhost:8000")
    ready = False
    max_wait_seconds = 10
    start_time = time.time()

    def monitor_stdout():
        for line in go_process.stdout:
            line = line.strip()
            print(f"[GO] {line}")
            if "Go file server running" in line:
                ready_event.set()
        if go_process.poll() is not None:
            print("[ERROR] Go process exited unexpectedly.")

    threading.Thread(target=monitor_stdout, daemon=True).start()

    if not ready_event.wait(timeout=200):
        print("[WARNING] Go microservice did not signal readiness in 10 seconds. Requests may fail.")

def stop_go_service():
    global go_process 
    if go_process:
        go_process.terminate()
        print("[INFO] Go microservice terminated.")

def create_app():
    app = Flask(__name__)
    app.config["BASE_PATH"] = os.getenv("BASE_PATH", "")
    app.config["UPLOAD_BASE_PATH"] = os.getenv("UPLOAD_BASE_PATH", app.config["BASE_PATH"])
    app.config["GO_FILE_SERVER_URL"] = os.getenv("GO_FILE_SERVER_URL")
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "")

    app.config["DATABASE"] = "ftp.db"
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB

    start_go_service()
    atexit.register(stop_go_service)

    import ftp.models as models
    import ftp.routes.hypermedia as hypermedia
    import ftp.routes.directories as directories
    
    models.init_app(app)
    hypermedia.init_app(app)
    directories.init_app(app)

    register_routes(app)

    return app
