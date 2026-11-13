import ctypes
import subprocess

import pyautogui

from tools.safety import _log

NO_WINDOW = subprocess.CREATE_NO_WINDOW

CLOSABLE = {
    "notepad": ["notepad.exe"],
    "calculator": ["CalculatorApp.exe", "calc.exe"],
    "paint": ["mspaint.exe"],
    "chrome": ["chrome.exe"],
    "brave": ["brave.exe"],
    "edge": ["msedge.exe"],
    "vscode": ["Code.exe"],
    "word": ["WINWORD.EXE"],
    "excel": ["EXCEL.EXE"],
    "powerpoint": ["POWERPNT.EXE"],
    "spotify": ["Spotify.exe"],
    "vlc": ["vlc.exe"],
    "whatsapp": ["WhatsApp.exe", "WhatsApp.Root.exe"],
    "telegram": ["Telegram.exe"],
    "discord": ["Discord.exe"],
}

# Closing these could lose a lot of open work, so Nova asks first
ASK_FIRST = {"chrome", "brave", "edge", "vscode", "word", "excel", "powerpoint"}


def _confirm(action: str) -> bool:
    """Ask Allow / Deny (in Nova's bubble, or in the terminal)."""
    answer = input(f"[CONFIRM] {action}. Allow? (y/n): ").strip().lower()
    allowed = answer in ("y", "yes")
    _log(f"{'ALLOWED' if allowed else 'DENIED '} | {action}")
    return allowed


def _powershell(script: str):
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True, text=True, creationflags=NO_WINDOW, timeout=15)
    return result.returncode, (result.stdout or "").strip()


# ---------- Volume ----------
def volume_change(direction: str, steps: int = 5) -> str:
    """Raise or lower the laptop volume. direction is 'up' or 'down'. Each step is about 2 percent."""
    key = "volumeup" if direction.lower().startswith("u") else "volumedown"
    pyautogui.press(key, presses=max(1, min(int(steps), 50)), interval=0.01)
    return "Volume up" if key == "volumeup" else "Volume down"


def set_volume(percent: int) -> str:
    """Set the laptop volume to a number from 0 to 100 percent."""
    percent = max(0, min(int(percent), 100))
    pyautogui.press("volumedown", presses=50, interval=0.005)
    pyautogui.press("volumeup", presses=round(percent / 2), interval=0.01)
    return f"Volume set to about {percent} percent"


def toggle_mute() -> str:
    """Mute the sound, or unmute it if it is already muted."""
    pyautogui.press("volumemute")
    return "Toggled mute"


# ---------- Brightness ----------
def get_brightness():
    code, out = _powershell(
        "(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness).CurrentBrightness")
    try:
        return int(out.split()[0]) if code == 0 and out else None
    except ValueError:
        return None


def set_brightness(percent: int) -> str:
    """Set the laptop screen brightness to a number from 0 to 100 percent."""
    percent = max(0, min(int(percent), 100))
    code, _ = _powershell(
        "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
        f".WmiSetBrightness(1,{percent})")
    if code == 0:
        return f"Brightness set to {percent} percent"
    return "I could not change the brightness on this screen."


def change_brightness(direction: str, amount: int = 20) -> str:
    """Make the laptop screen brighter ('up') or dimmer ('down')."""
    current = get_brightness()
    if current is None:
        return "I could not read the brightness on this screen."
    change = int(amount) if direction.lower().startswith("u") else -int(amount)
    return set_brightness(current + change)


# ---------- Apps and the computer ----------
def close_app(app_name: str) -> str:
    """Close an app politely (it may ask to save your work). Works for notepad, calculator,
    paint, chrome, brave, edge, vscode, word, excel, powerpoint, spotify, vlc, whatsapp,
    telegram and discord."""
    key = app_name.lower().strip()
    if key not in CLOSABLE:
        return f"I don't know how to close '{app_name}'. I can close: {', '.join(CLOSABLE)}"
    if key in ASK_FIRST and not _confirm(f"Close {key} and all its windows"):
        return "Okay, I did not close it."
    closed = False
    for exe in CLOSABLE[key]:
        result = subprocess.run(["taskkill", "/IM", exe], capture_output=True,
                                text=True, creationflags=NO_WINDOW)
        if result.returncode == 0:
            closed = True
    return f"Closed {key}" if closed else f"{key} is not running"


def lock_computer() -> str:
    """Lock the laptop screen."""
    ctypes.windll.user32.LockWorkStation()
    return "Locking the laptop"


def shutdown_computer(restart: bool = False) -> str:
    """Shut down the laptop, or restart it if restart is true. Always asks first and waits 30 seconds."""
    action = "Restart" if restart else "Shut down"
    if not _confirm(f"{action} the laptop in 30 seconds"):
        return "Okay, I did not do it."
    subprocess.run(["shutdown", "/r" if restart else "/s", "/t", "30"], creationflags=NO_WINDOW)
    return f"{action} in 30 seconds. Say cancel shutdown to stop it."


def cancel_shutdown() -> str:
    """Cancel a shutdown or restart that was already started."""
    subprocess.run(["shutdown", "/a"], creationflags=NO_WINDOW)
    return "Shutdown cancelled"
