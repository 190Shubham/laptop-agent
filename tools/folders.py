import os
import time
from pathlib import Path

HOME = Path.home()
PROJECT = Path(__file__).resolve().parent.parent

FOLDERS = {
    "downloads": [HOME / "Downloads"],
    "documents": [HOME / "Documents", HOME / "OneDrive" / "Documents"],
    "desktop": [HOME / "Desktop", HOME / "OneDrive" / "Desktop"],
    "pictures": [HOME / "Pictures", HOME / "OneDrive" / "Pictures"],
    "music": [HOME / "Music"],
    "videos": [HOME / "Videos"],
    "project": [PROJECT],
}
SEARCH_ROOTS = (FOLDERS["documents"] + FOLDERS["downloads"] + FOLDERS["desktop"])
SKIP_DIRS = {"venv", "node_modules", "__pycache__", ".git"}

# Never open program or script files by voice
BLOCKED = {".exe", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".msi", ".scr",
           ".com", ".lnk", ".reg", ".dll"}


def open_folder(name: str) -> str:
    """Open a folder in File Explorer: downloads, documents, desktop, pictures,
    music, videos or project."""
    key = name.lower().strip()
    for path in FOLDERS.get(key, []):
        if path.exists():
            os.startfile(str(path))
            return f"Opened your {key} folder"
    return f"I could not find the folder '{name}'."


def open_file(name: str) -> str:
    """Find a file by part of its name in Documents, Downloads and Desktop and open it."""
    needle = name.lower().strip()
    if not needle:
        return "Tell me the file name."

    matches = []
    deadline = time.time() + 8
    for root in SEARCH_ROOTS:
        if not root.exists() or time.time() > deadline:
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d.lower() not in SKIP_DIRS and not d.startswith(".")]
            matches += [Path(dirpath) / f for f in filenames if needle in f.lower()]
            if time.time() > deadline:
                break

    if not matches:
        return f"I could not find a file with '{name}' in its name."
    newest = max(matches, key=lambda p: p.stat().st_mtime)
    if newest.suffix.lower() in BLOCKED:
        return "That is a program file, so I will not open it."
    os.startfile(str(newest))
    return f"Opened {newest.name}"