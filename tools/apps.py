import os
import subprocess
import webbrowser


# Only these apps are allowed (safe list). You can add more later.
APPS = {
    "notepad": "notepad",
    "calculator": "calc",
    "paint": "mspaint",
    "chrome": "chrome",
    "vscode": "code",
}


def open_website(url: str) -> str:
    """Open a website in the default browser."""
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url}"


def open_app(app_name: str) -> str:
    """Open an app from the allowed list."""
    key = app_name.lower().strip()
    if key not in APPS:
        return f"Unknown app '{app_name}'. Available: {', '.join(APPS)}"
    subprocess.Popen(f'start "" {APPS[key]}', shell=True)
    return f"Opened {key}"


def create_folder(name: str) -> str:
    """Create a folder inside C:\\Users\\<you>\\AgentFiles."""
    base = os.path.join(os.path.expanduser("~"), "AgentFiles")
    path = os.path.join(base, name)
    os.makedirs(path, exist_ok=True)
    return f"Created folder: {path}"