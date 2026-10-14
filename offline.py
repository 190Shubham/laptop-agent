import re

from tools.apps import open_app, open_website, create_folder
from tools.files import organize_folder
from tools.launcher import open_any_app
from tools.system import get_system_info, take_screenshot, get_current_time


def try_offline(command: str):
    """Handle simple commands without Gemini. Returns a reply, or None if not understood."""
    text = command.lower().strip().rstrip(".!?")

    m = re.match(r"(?:create|make)\s+(?:a\s+)?(?:new\s+)?folder\s+(?:called\s+|named\s+)?(.+)", text)
    if m:
        return str(create_folder(m.group(1).strip()))

    m = re.match(r"organi[sz]e\s+(?:the\s+)?(?:folder\s+)?(.+)", text)
    if m:
        return str(organize_folder(m.group(1).strip()))

    m = re.match(r"open\s+(.+)", text)
    if m:
        results = []
        for name in re.split(r"\s+and\s+|\s*,\s*", m.group(1)):
            name = name.strip()
            if not name:
                continue
            if "." in name:
                url = name if name.startswith("http") else "https://" + name
                results.append(str(open_website(url)))
            else:
                reply = str(open_app(name))
                if reply.startswith("Unknown app"):
                    reply = str(open_any_app(app_name=name))
                results.append(reply)
        return "\n".join(results)

    # Short questions only, so long sentences still go to Gemini
    if len(text.split()) <= 6:
        if re.search(r"\bscreen\s?shot\b", text):
            return str(take_screenshot())
        if re.search(r"\b(battery|cpu|ram|system info)\b", text):
            return str(get_system_info())
        if re.search(r"\b(time|date)\b", text):
            return str(get_current_time())

    return None