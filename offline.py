import re

from tools.apps import (open_app, open_website, create_folder,
                        search_web, play_on_youtube)
from tools.files import organize_folder
from tools.launcher import open_any_app
from tools.system import get_system_info, take_screenshot, get_current_time
from tools import controls, folders, reminders, weather
from tools.closer import close_any_app
from tools import system_settings
from tools.media import media_control

try:
    from tools.writer import type_text, press_key
except ImportError:  # typing tool not set up yet
    type_text = press_key = None

# Words that start a NEW command. "and play ..." starts a new command, but
# "open calculator and paint" stays one command because "paint" is not in this list.
VERBS = (r"(?:play|search|google|type|press|open|close|create|make|organi[sz]e|take|"
         r"volume|mute|unmute|brightness|lock|shutdown|restart|cancel|remind|pause|resume|skip|stop)")
SPLIT = re.compile(rf"\s*(?:,|\band then\b|\bthen\b|\band\b)\s+(?={VERBS}\b)", re.IGNORECASE)

# "in brave" / "on chrome" anywhere in the sentence picks the browser
BROWSER = re.compile(r"\s+(?:in|on|using|with|via)\s+(brave|chrome)\b", re.IGNORECASE)

# Names that should open a website (not an installed app)
WEBSITES = {
    "google": "google.com", "youtube": "youtube.com", "gmail": "mail.google.com",
    "github": "github.com", "linkedin": "linkedin.com", "facebook": "facebook.com",
    "instagram": "instagram.com", "amazon": "amazon.in", "flipkart": "flipkart.com",
    "wikipedia": "wikipedia.org", "chatgpt": "chatgpt.com", "claude": "claude.ai",
}

UNITS = r"(second|sec|minute|min|hour|hr)"


def _open_names(names_text: str, browser: str) -> str:
    results = []
    for name in re.split(r"\s+and\s+|\s*,\s*", names_text):
        name = name.strip()
        if not name:
            continue
        key = name.lower()
        if key in WEBSITES:
            results.append(str(open_website(WEBSITES[key], browser)))
        elif "." in name:
            url = name if name.startswith("http") else "https://" + name
            results.append(str(open_website(url, browser)))
        else:
            reply = str(open_app(name))
            if reply.startswith("Unknown app"):
                reply = str(open_any_app(app_name=name))
            results.append(reply)
    return "\n".join(results)


def _handle_part(part: str, browser: str):
    """Handle ONE command. Returns a reply, or None if not understood."""
    part = part.strip()
    text = part.lower()

    # ---- files and folders ----
    m = re.match(r"(?:create|make)\s+(?:a\s+)?(?:new\s+)?folder\s+(?:called\s+|named\s+)?(.+)", text)
    if m:
        return str(create_folder(m.group(1).strip()))

    m = re.match(r"organi[sz]e\s+(?:the\s+)?(?:folder\s+)?(.+)", text)
    if m:
        return str(organize_folder(m.group(1).strip()))

    m = re.match(r"open\s+(?:my\s+|the\s+)?(downloads|documents|desktop|pictures|music|videos|project)(?:\s+folder)?$", text)
    if m:
        return str(folders.open_folder(m.group(1)))
    m = re.match(r"(?:open|find)\s+(?:the\s+|my\s+)?file\s+(?:called\s+|named\s+)?(.+)", text)
    if m:
        return str(folders.open_file(m.group(1).strip()))

    # ---- computer controls ----
    if re.search(r"\b(?:cancel|stop|abort)\b.*\b(?:shutdown|shut down|restart)\b", text):
        return str(controls.cancel_shutdown())
    if re.match(r"(?:shut\s?down|turn\s+off|power\s+off)(?:\s+(?:the|my))?(?:\s+(?:laptop|computer|pc))?$", text):
        return str(controls.shutdown_computer(False))
    if re.match(r"(?:restart|reboot)(?:\s+(?:the|my))?(?:\s+(?:laptop|computer|pc))?$", text):
        return str(controls.shutdown_computer(True))
    if re.match(r"lock(?:\s+(?:the|my))?(?:\s+(?:laptop|computer|pc|screen))?$", text):
        return str(controls.lock_computer())

    if re.match(r"(?:un)?mute\b", text) and len(text.split()) <= 3:
        return str(controls.toggle_mute())
    m = re.match(r"(?:set\s+)?(?:the\s+)?volume\s+(?:to\s+)?(\d{1,3})", text)
    if m:
        return str(controls.set_volume(int(m.group(1))))
    m = re.match(r"(?:turn\s+)?(?:the\s+)?volume\s+(up|down)|(increase|raise|decrease|lower)\s+(?:the\s+)?volume", text)
    if m:
        up = m.group(1) == "up" or m.group(2) in ("increase", "raise")
        return str(controls.volume_change("up" if up else "down"))

    m = re.match(r"(?:set\s+)?(?:the\s+)?brightness\s+(?:to\s+)?(\d{1,3})", text)
    if m:
        return str(controls.set_brightness(int(m.group(1))))
    m = re.match(r"(?:turn\s+)?(?:the\s+)?brightness\s+(up|down)|(increase|raise|decrease|lower)\s+(?:the\s+)?brightness", text)
    if m:
        up = m.group(1) == "up" or m.group(2) in ("increase", "raise")
        return str(controls.change_brightness("up" if up else "down"))

        # ---- Windows settings, Bluetooth, Wi-Fi, system tools ----
    m = (re.match(r"(?:turn|switch)\s+(on|off)\s+(?:the\s+|my\s+)?(bluetooth|wi-?\s?fi)$", text)
         or re.match(r"(enable|disable)\s+(?:the\s+|my\s+)?(bluetooth|wi-?\s?fi)$", text)
         or re.match(r"(bluetooth|wi-?\s?fi)\s+(on|off)$", text))
    if m:
        words = m.groups()
        on = any(w in ("on", "enable") for w in words)
        radio = "bluetooth" if any("bluetooth" in w for w in words) else "wifi"
        return str(system_settings.set_radio(radio, on))

    m = re.match(r"open\s+(?:the\s+|my\s+)?(task manager|control panel|file explorer|device manager|snipping tool|this pc)$", text)
    if m:
        return str(system_settings.open_system_tool(m.group(1)))
    m = re.match(r"(?:open|go to)\s+(?:the\s+|my\s+)?(.+?)\s+(?:settings|setting|tab|page)$", text)
    if m:
        return str(system_settings.open_settings(m.group(1)))
    if re.match(r"(?:open|go to)\s+settings?$", text):
        return str(system_settings.open_settings(""))
    m = re.match(r"open\s+(?:the\s+|my\s+)?(.+)$", text)
    if m and m.group(1).strip() in system_settings.BARE_NAMES:
        return str(system_settings.open_settings(m.group(1)))

    # ---- music and video that is playing ----
    if (re.match(r"(?:pause|stop|resume|continue)(?:\s+(?:playing|playback))?(?:\s+(?:the\s+)?(?:song|music|video|media|it))?$", text)
            or re.match(r"play\s+(?:the\s+)?(?:song|music|video)$", text) or text == "play"):
        return str(media_control("pause" if text.startswith(("pause", "stop")) else "play"))
    if re.match(r"(?:next|skip)(?:\s+(?:the\s+)?(?:song|track|video))?$", text):
        return str(media_control("next"))
    if re.match(r"(?:previous|prev)(?:\s+(?:song|track|video))?$", text):
        return str(media_control("previous"))

    # ---- close programs ----
    m = re.match(r"(?:close|quit)\s+(?:the\s+)?(.+)", text)
    if m:
        return str(close_any_app(m.group(1).strip()))

    # ---- reminders, timers, weather ----
    m = re.match(rf"(?:(?:please\s+)?remind me\s+)?in\s+(\d+)\s*{UNITS}s?\s+(?:to\s+|about\s+|for\s+)?(.+)", text)
    if m:
        return str(reminders.remind_in(int(m.group(1)), m.group(2), m.group(3)))
    m = re.match(rf"remind me\s+(?:to\s+|about\s+)?(.+?)\s+in\s+(\d+)\s*{UNITS}s?$", text)
    if m:
        return str(reminders.remind_in(int(m.group(2)), m.group(3), m.group(1)))
    m = re.match(r"remind me at (\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)?\s+(?:to\s+|about\s+)?(.+)", text)
    if m:
        ampm = (m.group(3) or "").replace(".", "")
        return str(reminders.remind_at(int(m.group(1)), int(m.group(2) or 0), ampm, m.group(4)))
    m = re.match(rf"(?:set\s+(?:a\s+)?)?timer\s+(?:for\s+)?(\d+)\s*{UNITS}s?", text)
    if m:
        return str(reminders.remind_in(int(m.group(1)), m.group(2), "your timer is finished"))
    if re.match(r"(?:list|show|what are)\s+(?:my\s+)?reminders", text):
        return str(reminders.list_reminders())
    if re.match(r"(?:clear|delete|cancel)\s+(?:all\s+)?(?:my\s+)?reminders", text):
        return str(reminders.clear_reminders())

    if re.search(r"\b(?:weather|temperature)\b", text) and len(text.split()) <= 8:
        m = re.search(r"\b(?:in|at|for)\s+([a-z ]+?)\s*$", text)
        return str(weather.get_weather(m.group(1) if m else ""))

    # ---- typing ----
    m = re.match(r"press\s+(enter|tab|backspace|esc|escape)$", text)
    if m:
        if press_key is None:
            return "The typing tool is not set up yet (tools/writer.py)."
        return str(press_key("esc" if m.group(1) == "escape" else m.group(1)))

    m = re.match(r"type\s+(.+)", part, re.IGNORECASE)
    if m:
        if type_text is None:
            return "The typing tool is not set up yet (tools/writer.py)."
        return str(type_text(m.group(1).strip()))

    # ---- YouTube and web search ----
    m = re.match(r"play\s+(.+?)(?:\s+on\s+youtube)?$", part, re.IGNORECASE)
    if m:
        return str(play_on_youtube(m.group(1).strip(), True, browser))

    m = re.match(
        r"(?:search|google)\s+(?:for\s+)?(.+?)"
        r"(?:\s+(?:on|in)\s+(google|youtube|amazon|flipkart|wikipedia|github))?$",
        part, re.IGNORECASE)
    if m:
        site = (m.group(2) or "google").lower()
        return str(search_web(m.group(1).strip(), site, browser))

    # ---- open apps and websites ----
    m = re.match(r"open\s+(.+)", part, re.IGNORECASE)
    if m:
        return _open_names(m.group(1), browser)

    # Short questions only, so long sentences still go to Gemini
    if len(text.split()) <= 6:
        if re.search(r"\bscreen\s?shot\b", text):
            return str(take_screenshot())
        if re.search(r"\b(battery|cpu|ram|system info)\b", text):
            return str(get_system_info())
        if re.search(r"\b(time|date)\b", text):
            return str(get_current_time())

    return None


def try_offline(command: str):
    """Handle commands without Gemini. Returns a reply, or None if not understood."""
    original = command.strip().rstrip(".!?")

    # Find "in brave" / "in chrome" and remove it from the sentence
    browser = ""
    m = BROWSER.search(original)
    if m:
        browser = m.group(1).lower()
        original = BROWSER.sub("", original)

    parts = [p for p in SPLIT.split(original) if p.strip()]

    # "open youtube and play ..." should not open YouTube twice
    if any(re.match(r"(?:play|search|google)\b", p.strip(), re.IGNORECASE) for p in parts):
        parts = [p for p in parts
                 if not re.match(r"open\s+(?:google|youtube)(?:\.com)?$", p.strip(), re.IGNORECASE)]

    replies = []
    for part in parts:
        reply = _handle_part(part, browser)
        if reply is None:
            return None  # not understood: let Gemini handle the whole sentence
        replies.append(reply)
    return "\n".join(replies) if replies else None