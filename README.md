
# Opabinia - Self-hosted File Web Server

Opabinia is a lightweight, self-hosted web interface for managing your local files.  
It allows you to browse directories, view previews, download files, and manage uploads all from your browser.

![Opabinia Screenshot](opabinia.png)

Before you can run `Opabinia`, you need these followings. 

1) Git 
2) Python 3.10+
3) pip

Make sure to latest recommended, do 
`python -m pip install --upgrade pip`

No special web server is required (we use Waitress).

## Installation

Clone the repo, and cd into a directory

    clone https://github.com/kishism/Fileserver.git
    cd Fileserver

You need to construct a virtual environment (unless you don't mind using Python installed on your system) to install the required libraries to run the server. We recommend this approach as this prevent running into dependencies conflict if you have other python codes.

Run

    python -m venv venv 

(note: you can name whatever you want for the last env. It's just a folder name)

and, to activate the environment:


If you are on Window: 

    venv\Scripts\Activate.ps1 # Powershell
    venv\Scripts\activate.bat  # CMD

or, if you are on linux

    source /venv/Scripts/activate

If you see `(venv)` beside the file path, then the virtual environment is on.

After this, we will install all libraries from **requirements.txt**.
From the project root folder, `run pip install -r requirements.txt`

The installation process is completed, and next, we will start a startup wizard terminal by directly running start.py from the root.

    python start.py

## Setup Wizard

-   Pick a folder to use as the file root (this will become `BASE_PATH`). Example: `C:\ftp-server` (Windows) or `/home/you/ftp-server` (Linux). You can create it now, or let the wizard warn you and create it.
    
-   Ensure the running user (you) has read/write access to that folder.

-   Default server port: **5000** (configurable). If you plan to use port **80/443**, elevated privileges may be required on some OSes.
    
-   For local-only usage (recommended by default), bind to `127.0.0.1` so the app is not accessible from other machines.

The setup is completed, and you can visit the web UI at  http://127.0.0.1:5000 in your browser.

**Contributors**

<div>
  <div>
  <a href="https://github.com/kishism">
    <img src="https://avatars.githubusercontent.com/u/157962042?v=4" width="100" style="margin: 0 10px;" alt="Kishi"/> 
  </a>

  <a href="https://github.com/DazeAkaRiku">
    <img src="https://avatars.githubusercontent.com/u/121934782?v=4" width="100" style="margin: 0 10px;" alt="Riku"/>
  </a>

  <a href="https://github.com/Janica-Max">
    <img src="https://avatars.githubusercontent.com/u/218932649?v=4" width="100" style="margin: 0 10px;" alt="Riku"/>
  </a>

  <a href="https://github.com/Yokkathsoe">
    <img src="https://avatars.githubusercontent.com/u/159621518?v=4" width="100" style="margin: 0 10px;" alt="Riku"/>
  </a>

  <a href="https://github.com/saipanesaing">
    <img src="https://avatars.githubusercontent.com/u/159633689?v=4" width="100" style="margin: 0 10px;" alt="Riku"/>
  </a>
  
</div>