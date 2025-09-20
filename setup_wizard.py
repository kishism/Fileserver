# setup_wizard.py
from pathlib import Path
import questionary
import secrets

def run_wizard(env_path: Path):
    # ASCII banner for Opabinia
    ascii_banner = r"""
      ____                 _       _ _ _       
     / __ \ ___  ___ _ __ | |_ ___| | (_)_ __  
    / / _` / __|/ _ \ '_ \| __/ _ \ | | | '_ \ 
   | | (_| \__ \  __/ | | | ||  __/ | | | | | |
    \ \__,_|___/\___|_| |_|\__\___|_|_|_|_| |_|
     \____/                                     
    """
    print(ascii_banner)
    print("Welcome to the Opabinia File Server Setup Wizard!\n")

    # Ask for base directory
    base_path = questionary.path(
        "Enter the base path for your files (where all files/folders will be stored):",
        only_directories=True
    ).ask()
    if not Path(base_path).exists():
        print(f"⚠️ Warning: Base path '{base_path}' does not exist. Server may fail to start.")

    # Ask for upload path (default to base path)
    upload_base_path = questionary.path(
        "Enter the upload path (press Enter to use the base path):",
        default=base_path,
        only_directories=True
    ).ask()
    if not Path(upload_base_path).exists():
        print(f"⚠️ Warning: Upload path '{upload_base_path}' does not exist. Server may fail to start.")

    # Ask for Flask secret key
    secret_key = questionary.text(
        "Enter a secret key for Flask session (leave empty for auto-generated):",
        default=""
    ).ask()
    if not secret_key:
        secret_key = secrets.token_hex(16)
        print(f"Generated secret key: {secret_key}")

    # Ask for port
    port = questionary.text(
        "Enter port to run the server on:",
        default="5000"
    ).ask()

    # Ask for host
    host = questionary.text(
        "Enter host to bind the server to (127.0.0.1 for local only, 0.0.0.0 for LAN):",
        default="127.0.0.1"
    ).ask()

    # Write values to .env
    env_content = f"""BASE_PATH={base_path}
UPLOAD_BASE_PATH={upload_base_path}
FLASK_SECRET_KEY={secret_key}
PORT={port}
HOST={host}
FLASK_ENV=development
"""
    with open(env_path, "w") as f:
        f.write(env_content)

    print(f"\n✅ Setup complete! .env file created at {env_path.resolve()}")
    print("You can now start the server with `python start.py`")
