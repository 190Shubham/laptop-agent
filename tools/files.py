import os
import shutil
from tools.safety import require_confirmation

HOME = os.path.expanduser("~")
AGENT_DIR = os.path.join(HOME, "AgentFiles")

CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".ppt", ".pptx", ".xls", ".xlsx", ".csv"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov"],
    "Audio": [".mp3", ".wav", ".m4a"],
    "Archives": [".zip", ".rar", ".7z"],
    "Code": [".py", ".js", ".html", ".css", ".java", ".json"],
    "Programs": [".exe", ".msi"],
}

# Files still being downloaded: never touch these
SKIP_EXTENSIONS = (".crdownload", ".tmp", ".part")


def _resolve_folder(folder_name: str):
    """Only 'downloads' or a folder inside AgentFiles is allowed."""
    if folder_name.lower().strip() == "downloads":
        return os.path.join(HOME, "Downloads")
    path = os.path.abspath(os.path.join(AGENT_DIR, folder_name))
    if os.path.commonpath([path, AGENT_DIR]) != AGENT_DIR:
        return None
    return path


@require_confirmation
def organize_folder(folder_name: str) -> str:
    """Sort the files in a folder into subfolders by file type (Images, Documents,
    Videos, Audio, Archives, Code, Programs, Others). Works only on 'downloads' or
    a folder inside AgentFiles. Moves files, never deletes them."""
    folder = _resolve_folder(folder_name)
    if folder is None or not os.path.isdir(folder):
        return "I can only organize 'downloads' or a folder inside AgentFiles, and it must exist."

    moved = 0
    for item in os.listdir(folder):
        src = os.path.join(folder, item)
        if not os.path.isfile(src) or item.lower().endswith(SKIP_EXTENSIONS):
            continue

        base, ext = os.path.splitext(item)
        category = next((c for c, exts in CATEGORIES.items() if ext.lower() in exts), "Others")
        dest_dir = os.path.join(folder, category)
        os.makedirs(dest_dir, exist_ok=True)

        # Never overwrite: add _1, _2 ... if the name already exists
        dest = os.path.join(dest_dir, item)
        n = 1
        while os.path.exists(dest):
            dest = os.path.join(dest_dir, f"{base}_{n}{ext}")
            n += 1

        shutil.move(src, dest)
        moved += 1

    return f"Organized {moved} files in {folder}"