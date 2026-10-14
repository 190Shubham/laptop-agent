import difflib
import json
import subprocess

from tools.safety import require_confirmation

_apps_cache = None


def _installed_apps():
    """Returns {lowercase name: (display name, app id)} for every app in the Start Menu."""
    global _apps_cache
    if _apps_cache is None:
        command = ("[Console]::OutputEncoding=[Text.Encoding]::UTF8; "
                   "Get-StartApps | ConvertTo-Json")
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True, text=True, encoding="utf-8",
        ).stdout
        data = json.loads(out) if out.strip() else []
        if isinstance(data, dict):
            data = [data]
        _apps_cache = {a["Name"].lower(): (a["Name"], a["AppID"]) for a in data}
    return _apps_cache


def _find(name: str):
    apps = _installed_apps()
    name = name.lower().strip()
    if name in apps:
        return name
    contains = [k for k in apps if name in k]
    if contains:
        return min(contains, key=len)  # shortest match, e.g. "paint" over "paint 3d"
    close = difflib.get_close_matches(name, list(apps.keys()), n=1, cutoff=0.6)
    return close[0] if close else None


@require_confirmation
def open_any_app(app_name: str) -> str:
    """Open any app installed on this laptop by its name (for example WhatsApp or Spotify)."""
    key = _find(app_name)
    if key is None:
        return f"I could not find an installed app called '{app_name}'."
    display_name, app_id = _installed_apps()[key]
    subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{app_id}"])
    return f"Opened {display_name}"