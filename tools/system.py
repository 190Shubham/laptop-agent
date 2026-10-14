import os
import datetime
import psutil
import pyautogui


def get_system_info() -> str:
    """Get the laptop's battery percentage, CPU usage and RAM usage."""
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    if battery:
        status = "charging" if battery.power_plugged else "not charging"
        bat = f"{battery.percent:.0f}% ({status})"
    else:
        bat = "no battery found"
    return f"Battery: {bat}, CPU: {cpu}%, RAM: {ram}%"


def take_screenshot() -> str:
    """Take a screenshot of the screen and save it in the AgentFiles folder."""
    folder = os.path.join(os.path.expanduser("~"), "AgentFiles", "screenshots")
    os.makedirs(folder, exist_ok=True)
    name = datetime.datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png")
    path = os.path.join(folder, name)
    pyautogui.screenshot(path)
    return f"Screenshot saved: {path}"


def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.datetime.now().strftime("%A, %d %B %Y, %I:%M %p")