import os
import subprocess

from tools.controls import NO_WINDOW, _confirm

SETTINGS_PAGES = {
    "bluetooth": "bluetooth", "wifi": "network-wifi", "wi-fi": "network-wifi",
    "wi fi": "network-wifi", "network": "network", "internet": "network",
    "display": "display", "screen": "display", "brightness": "display",
    "sound": "sound", "volume": "sound", "battery": "batterysaver",
    "power": "powersleep", "sleep": "powersleep", "apps": "appsfeatures",
    "installed apps": "appsfeatures", "default apps": "defaultapps",
    "update": "windowsupdate", "windows update": "windowsupdate",
    "personalization": "personalization", "wallpaper": "personalization-background",
    "background": "personalization-background", "notifications": "notifications",
    "storage": "storagesense", "privacy": "privacy", "accounts": "yourinfo",
    "time": "dateandtime", "date and time": "dateandtime", "language": "regionlanguage",
    "airplane mode": "network-airplanemode", "night light": "nightlight",
    "about": "about", "printers": "printers", "mouse": "mousetouchpad",
    "touchpad": "devices-touchpad", "keyboard": "typing", "vpn": "network-vpn",
    "hotspot": "network-mobilehotspot", "camera": "privacy-webcam",
    "microphone": "privacy-microphone", "startup apps": "startupapps",
    "accessibility": "easeofaccess", "gaming": "gaming-gamebar",
}

# Names that can be opened without saying "settings" (safe, not confused with other apps)
BARE_NAMES = ("bluetooth", "wifi", "wi-fi", "wi fi", "display", "screen", "sound",
              "network", "battery", "vpn", "hotspot", "airplane mode", "night light",
              "windows update", "storage", "personalization", "wallpaper",
              "notifications", "privacy", "accessibility")

SYSTEM_TOOLS = {
    "task manager": "taskmgr", "control panel": "control", "file explorer": "explorer",
    "device manager": "devmgmt.msc", "snipping tool": "snippingtool",
    "this pc": "explorer shell:MyComputerFolder",
}


def open_settings(page: str = "") -> str:
    """Open a Windows Settings page, for example bluetooth, wifi, display, sound,
    battery, network, apps, update or privacy. Leave empty for the main Settings window."""
    key = page.lower().strip()
    for word in ("settings", "setting", "tab", "page", "the", "my"):
        key = " ".join(w for w in key.split() if w != word)
    if not key:
        os.startfile("ms-settings:")
        return "Opened Settings."
    uri = SETTINGS_PAGES.get(key)
    if uri is None:
        for name, value in SETTINGS_PAGES.items():
            if key in name or name in key:
                uri = value
                break
    if uri is None:
        os.startfile("ms-settings:")
        return f"I opened Settings, but I do not know the page '{page}'."
    os.startfile(f"ms-settings:{uri}")
    return f"Opened {key} settings."


def open_system_tool(name: str) -> str:
    """Open a Windows tool: task manager, control panel, file explorer,
    device manager, snipping tool or this pc."""
    key = name.lower().strip()
    command = SYSTEM_TOOLS.get(key)
    if not command:
        return f"I do not know the tool '{name}'. I can open: {', '.join(SYSTEM_TOOLS)}"
    subprocess.Popen(f'start "" {command}', shell=True)
    return f"Opened {key}."


RADIO_SCRIPT = r'''
[Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
[Windows.Devices.Radios.RadioAccessStatus,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
function Await($task, $type) {
  $m = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
  $t = $m.MakeGenericMethod($type).Invoke($null, @($task))
  $t.Wait(-1) | Out-Null
  $t.Result
}
Await ([Windows.Devices.Radios.Radio]::RequestAccessAsync()) ([Windows.Devices.Radios.RadioAccessStatus]) | Out-Null
$radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
$radio = $radios | Where-Object { $_.Kind -eq '__KIND__' } | Select-Object -First 1
if (-not $radio) { Write-Output 'NOT_FOUND'; exit 0 }
[Windows.Devices.Radios.RadioState,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
$result = Await ($radio.SetStateAsync('__STATE__')) ([Windows.Devices.Radios.RadioAccessStatus])
Write-Output $result
'''


# def set_radio(radio: str, on: bool) -> str:
#     """Turn Bluetooth or Wi-Fi on or off. radio is 'bluetooth' or 'wifi'.
#     Turning Wi-Fi off asks the user first."""
#     key = radio.lower().replace("-", "").replace(" ", "")
#     if key not in ("bluetooth", "wifi"):
#         return "I can switch bluetooth or wifi."
#     label = "Bluetooth" if key == "bluetooth" else "Wi-Fi"

#     if key == "wifi" and not on:
#         if not _confirm("Turn off Wi-Fi. Nova needs the internet for voice, "
#                         "so type 'turn on wifi' in her box to turn it back on"):
#             return "Okay, I left Wi-Fi on."

#     script = (RADIO_SCRIPT.replace("__KIND__", "Bluetooth" if key == "bluetooth" else "WiFi")
#               .replace("__STATE__", "On" if on else "Off"))
#     try:
#         result = subprocess.run(
#             ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
#             capture_output=True, text=True, creationflags=NO_WINDOW, timeout=30)
#     except subprocess.TimeoutExpired:
#         return f"Windows took too long to switch {label}."

#     output = (result.stdout or "").strip().splitlines()
#     status = output[-1].strip() if output else ""
#     if status == "NOT_FOUND":
#         return f"I could not find a {label} adapter on this laptop."
#     if status == "Allowed":
#         return f"{label} turned {'on' if on else 'off'}."
#     open_settings(key)
#     return f"Windows did not let me switch {label} ({status or 'no answer'}). I opened its settings so you can do it."




# ---------- Bluetooth and Wi-Fi switch (uses tools/radio.ps1) ----------
RADIO_PS1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "radio.ps1")


def set_radio(radio: str, on: bool) -> str:
    """Turn Bluetooth or Wi-Fi on or off. radio is 'bluetooth' or 'wifi'.
    Turning Wi-Fi off asks the user first."""
    key = radio.lower().replace("-", "").replace(" ", "")
    if key not in ("bluetooth", "wifi"):
        return "I can switch bluetooth or wifi."
    label = "Bluetooth" if key == "bluetooth" else "Wi-Fi"

    if key == "wifi" and not on:
        if not _confirm("Turn off Wi-Fi. Nova needs the internet for voice, "
                        "so type 'turn on wifi' in her box to turn it back on"):
            return "Okay, I left Wi-Fi on."

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", RADIO_PS1,
             "-Kind", "Bluetooth" if key == "bluetooth" else "WiFi",
             "-State", "On" if on else "Off"],
            capture_output=True, text=True, creationflags=NO_WINDOW, timeout=30)
    except subprocess.TimeoutExpired:
        return f"Windows took too long to switch {label}."

    lines = (result.stdout or "").strip().splitlines()
    status = lines[-1].strip() if lines else (result.stderr or "").strip()[:120]
    print(f"[radio] {label} -> {status}")

    if status == "NOT_FOUND":
        return f"I could not find a {label} adapter on this laptop."
    if status == "Allowed":
        return f"{label} turned {'on' if on else 'off'}."
    open_settings(key)
    return (f"Windows did not let me switch {label} ({status or 'no answer'}). "
            "I opened its settings so you can do it.")