import os
import subprocess
import webbrowser
import urllib.parse


# Only these apps are allowed (safe list). You can add more later.
APPS = {
    "notepad": "notepad",
    "calculator": "calc",
    "paint": "mspaint",
    "chrome": "chrome",
    "vscode": "code",
}


def open_website(url: str) -> str:
    """Open a website in Chrome, for example google.com or youtube.com."""
    if not url.startswith("http"):
        url = "https://" + url
    browser = _open_url(url)
    return f"Opened {url} in {browser}"

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.join(os.path.expanduser("~"), r"AppData\Local\Google\Chrome\Application\chrome.exe"),
]

SEARCH_SITES = {
    "google": "https://www.google.com/search?q=",
    "youtube": "https://www.youtube.com/results?search_query=",
    "amazon": "https://www.amazon.in/s?k=",
    "flipkart": "https://www.flipkart.com/search?q=",
    "wikipedia": "https://en.wikipedia.org/w/index.php?search=",
    "github": "https://github.com/search?q=",
}


def _open_url(url: str) -> str:
    """Open a URL in Chrome if it is installed, otherwise in the default browser."""
    for path in CHROME_PATHS:
        if os.path.exists(path):
            subprocess.Popen([path, url])
            return "Chrome"
    webbrowser.open(url)
    return "your default browser"


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

def search_web(query: str, site: str = "google") -> str:
    """Search for something on a website in Chrome. Supported sites: google,
    youtube, amazon, flipkart, wikipedia, github. Use google if no site is named."""
    base = SEARCH_SITES.get(site.lower().strip())
    if base is None:
        # Unknown site: search Google with the site name added
        base = SEARCH_SITES["google"]
        query = f"{query} {site}"
    url = base + urllib.parse.quote_plus(query)
    browser = _open_url(url)
    return f"Searched '{query}' on {site} in {browser}"