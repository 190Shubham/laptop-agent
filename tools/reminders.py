import datetime
import json
import os
import threading
import time

FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reminders.json")
UNIT_SECONDS = {"second": 1, "sec": 1, "minute": 60, "min": 60, "hour": 3600, "hr": 3600}

_lock = threading.Lock()
_notify = None
_started = False


def _load():
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def _save(items):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)


def _clean(text):
    text = text.strip().rstrip(".!?")
    return (" " + text + " ").replace(" my ", " your ").strip()


def _add(text, due):
    with _lock:
        items = _load()
        items.append({"text": _clean(text), "due": due})
        _save(items)


def remind_in(amount: int, unit: str, text: str) -> str:
    """Set a reminder after some time. unit is second, minute or hour.
    Example: amount 10, unit minute, text 'drink water'."""
    amount = int(amount)
    seconds = amount * UNIT_SECONDS.get(unit.lower().rstrip("s"), 60)
    _add(text, time.time() + seconds)
    label = f"{amount} {unit}" + ("" if amount == 1 else "s")
    return f"Okay, I will remind you in {label} to {_clean(text)}."


def remind_at(hour: int, minute: int, ampm: str, text: str) -> str:
    """Set a reminder for a clock time, today or tomorrow. ampm is 'am', 'pm' or empty."""
    now = datetime.datetime.now()
    hour, minute = int(hour), int(minute)
    ampm = (ampm or "").lower()
    if ampm == "pm":
        hours = [hour if hour >= 12 else hour + 12]
    elif ampm == "am":
        hours = [0 if hour == 12 else hour]
    elif hour > 12:
        hours = [hour]
    else:
        hours = [hour % 12, hour % 12 + 12]
    candidates = [now.replace(hour=h % 24, minute=minute, second=0, microsecond=0) for h in hours]
    future = [c for c in candidates if c > now]
    due = min(future) if future else candidates[0] + datetime.timedelta(days=1)
    _add(text, due.timestamp())
    return f"Okay, I will remind you at {due.strftime('%I:%M %p').lstrip('0')} to {_clean(text)}."


def list_reminders() -> str:
    """Tell the user which reminders are waiting."""
    items = sorted(_load(), key=lambda i: i["due"])
    if not items:
        return "You have no reminders."
    parts = [f"{datetime.datetime.fromtimestamp(i['due']).strftime('%I:%M %p').lstrip('0')}: {i['text']}"
             for i in items]
    return "Your reminders: " + "; ".join(parts)


def clear_reminders() -> str:
    """Delete all reminders."""
    with _lock:
        _save([])
    return "All reminders cleared."


def _loop():
    while True:
        try:
            now = time.time()
            due_items = []
            with _lock:
                items = _load()
                keep = [i for i in items if i["due"] > now]
                due_items = [i for i in items if i["due"] <= now]
                if due_items:
                    _save(keep)
            for item in due_items:
                if _notify:
                    prefix = "Reminder" if now - item["due"] < 120 else "You missed a reminder"
                    _notify(f"{prefix}: {item['text']}.")
        except Exception as e:
            print(f"[reminders error: {e}]")
        time.sleep(2)


def start(notifier):
    """Start checking reminders. notifier(text) is called when one is due."""
    global _notify, _started
    _notify = notifier
    if _started:
        return
    _started = True
    threading.Thread(target=_loop, daemon=True).start()