import subprocess

import psutil

from tools.controls import CLOSABLE, NO_WINDOW, _confirm, close_app

# Windows and Nova's own programs are never closed
PROTECTED = {"explorer", "winlogon", "csrss", "svchost", "system", "wininit",
             "services", "lsass", "dwm", "smss", "registry", "msmpeng",
             "python", "pythonw", "python3"}


def close_any_app(app_name: str) -> str:
    """Close any running program by its name, for example mongodb, steam or telegram.
    It asks the user first, unless the program is a common app."""
    key = app_name.lower().strip()
    if key in CLOSABLE:
        return close_app(key)

    flat = key.replace(" ", "")
    if len(flat) < 3:
        return "Please tell me the full name of the program."

    found = set()
    for proc in psutil.process_iter(["name"]):
        name = proc.info.get("name") or ""
        stem = name.lower()[:-4] if name.lower().endswith(".exe") else name.lower()
        stem = stem.replace(" ", "")
        if stem in PROTECTED:
            continue
        if flat in stem or (len(stem) >= 4 and stem in flat):
            found.add(name)
    if not found:
        return f"I could not find a running program called '{app_name}'."

    names = sorted(found)[:5]
    if not _confirm(f"Close {', '.join(names)}"):
        return "Okay, I did not close it."

    closed, need_force = [], []
    for name in names:
        result = subprocess.run(["taskkill", "/IM", name], capture_output=True,
                                text=True, creationflags=NO_WINDOW)
        output = ((result.stdout or "") + (result.stderr or "")).lower()
        if result.returncode == 0:
            closed.append(name)
        elif "forcefully" in output:
            need_force.append(name)

    if need_force and _confirm(f"{', '.join(need_force)} will not close politely. Force close it"):
        for name in need_force:
            result = subprocess.run(["taskkill", "/F", "/IM", name], capture_output=True,
                                    text=True, creationflags=NO_WINDOW)
            if result.returncode == 0:
                closed.append(name)

    if closed:
        return f"Closed {', '.join(closed)}."
    return f"I could not close {', '.join(names)}. It may need administrator rights."