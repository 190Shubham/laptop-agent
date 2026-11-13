import os
import re
import subprocess
import urllib.parse
import urllib.request
import webbrowser

# Only these apps are allowed (safe list). You can add more later.
APPS = {
    "notepad": "notepad",
    "calculator": "calc",
    "paint": "mspaint",
    "chrome": "chrome",
    "brave": "brave",
    "vscode": "code",
}

BROWSERS = {
    "brave": [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        os.path.join(os.path.expanduser("~"), r"AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"),
    ],
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.join(os.path.expanduser("~"), r"AppData\Local\Google\Chrome\Application\chrome.exe"),
    ],
}

# Used when you don't say which browser. Change to "chrome" if you prefer.
DEFAULT_BROWSER = "brave"

# Optional: open a specific profile, for example "Default" or "Profile 1".
# None means the last-used profile. Find the name at brave://version or chrome://version
# (look at "Profile Path").
PROFILES = {"brave": None, "chrome": None}

SEARCH_SITES = {
    "google": "https://www.google.com/search?q=",
    "youtube": "https://www.youtube.com/results?search_query=",
    "amazon": "https://www.amazon.in/s?k=",
    "flipkart": "https://www.flipkart.com/search?q=",
    "wikipedia": "https://en.wikipedia.org/w/index.php?search=",
    "github": "https://github.com/search?q=",
}


def _find_browser(name: str):
    for path in BROWSERS.get(name, []):
        if os.path.exists(path):
            return path
    return None


def _open_url(url: str, browser: str = "") -> str:
    """Open a URL in the chosen browser (brave or chrome). If it isn't installed,
    try the other one, then the default browser."""
    name = (browser or DEFAULT_BROWSER).lower().strip()
    for b in [name] + [x for x in BROWSERS if x != name]:
        path = _find_browser(b)
        if path:
            command = [path]
            if PROFILES.get(b):
                command.append(f"--profile-directory={PROFILES[b]}")
            command.append(url)
            subprocess.Popen(command)
            return b.capitalize()
    webbrowser.open(url)
    return "your default browser"


def open_website(url: str, browser: str = "") -> str:
    """Open a website. browser can be 'brave' or 'chrome'; leave empty for the default."""
    if not url.startswith("http"):
        url = "https://" + url
    used = _open_url(url, browser)
    return f"Opened {url} in {used}"


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


def search_web(query: str, site: str = "google", browser: str = "") -> str:
    """Search for something on a website. Supported sites: google, youtube, amazon,
    flipkart, wikipedia, github. Use google if no site is named.
    browser can be 'brave' or 'chrome'; leave empty for the default."""
    base = SEARCH_SITES.get(site.lower().strip())
    if base is None:
        base = SEARCH_SITES["google"]
        query = f"{query} {site}"
    url = base + urllib.parse.quote_plus(query)
    used = _open_url(url, browser)
    return f"Searched '{query}' on {site} in {used}"


def _first_video_url(query: str):
    """Find the first YouTube video for a search. Returns None if it fails."""
    try:
        from yt_dlp import YoutubeDL
        opts = {"quiet": True, "no_warnings": True,
                "extract_flat": True, "skip_download": True}
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
        entries = info.get("entries") or []
        if entries and entries[0].get("id"):
            return f"https://www.youtube.com/watch?v={entries[0]['id']}"
    except Exception as e:
        print(f"[YouTube lookup failed: {e}]")
    return None


def play_on_youtube(query: str, autoplay: bool = True, browser: str = "") -> str:
    """Use for 'play <song or video>' on YouTube. If autoplay is True, open and play
    the first video result. If autoplay is False, only open the search results page.
    browser can be 'brave' or 'chrome'; leave empty for the default."""
    if autoplay:
        video_url = _first_video_url(query)
        if video_url:
            used = _open_url(video_url, browser)
            return f"Playing the first YouTube result for '{query}' in {used}"
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)
    used = _open_url(url, browser)
    return f"Opened YouTube search results for '{query}' in {used}"