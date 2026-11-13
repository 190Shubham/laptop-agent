import re

from tools.apps import (open_app, open_website, create_folder,
                        search_web, play_on_youtube)
from tools.files import organize_folder
from tools.launcher import open_any_app
from tools.system import get_system_info, take_screenshot, get_current_time

try:
    from tools.writer import type_text, press_key
except ImportError:  # typing tool not set up yet
    type_text = press_key = None

# Words that start a NEW command. "and play ..." starts a new command, but
# "open calculator and paint" stays one command because "paint" is not in this list.
VERBS = r"(?:play|search|google|type|press|open|create|make|organi[sz]e|take)"
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

    m = re.match(r"(?:create|make)\s+(?:a\s+)?(?:new\s+)?folder\s+(?:called\s+|named\s+)?(.+)", text)
    if m:
        return str(create_folder(m.group(1).strip()))

    m = re.match(r"organi[sz]e\s+(?:the\s+)?(?:folder\s+)?(.+)", text)
    if m:
        return str(organize_folder(m.group(1).strip()))

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