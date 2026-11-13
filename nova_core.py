import builtins
import threading
import time

from agent import run_agent
from offline import try_offline
from voice import listen, speak

STATE = {"state": "idle", "message": "", "msg_id": 0, "heard": "", "confirm": ""}
_lock = threading.Lock()
_work_lock = threading.Lock()
_confirm_event = threading.Event()
_confirm_answer = {"ok": False}
_last = {"command": "", "done": 0.0}

AGAIN_WORDS = ("again", "do it again", "repeat", "repeat that", "once more",
               "open it again", "play it again")


def get_state():
    with _lock:
        return dict(STATE)


def _set(**kwargs):
    with _lock:
        STATE.update(kwargs)


def _say(text):
    with _lock:
        STATE["message"] = text
        STATE["msg_id"] += 1


def is_busy():
    return _work_lock.locked()


def last_done():
    return _last["done"]


def ask_yes_no(prompt=""):
    """Replaces input(): the safety question appears in Nova's bubble."""
    text = prompt.replace("[CONFIRM]", "").replace("(y/n):", "").strip()
    _confirm_answer["ok"] = False
    _confirm_event.clear()
    _set(confirm=text or "Allow this action?")
    _confirm_event.wait(timeout=60)
    _set(confirm="")
    return "y" if _confirm_answer["ok"] else "n"


builtins.input = ask_yes_no


def answer_confirm(ok):
    _confirm_answer["ok"] = ok
    _confirm_event.set()


def run_command(command, by_voice=False, speak_reply=None):
    """by_voice=True: Nova listens first. speak_reply: say the reply out loud
    (default: only when the command came by voice)."""
    threading.Thread(target=_worker, args=(command, by_voice, speak_reply),
                     daemon=True).start()


def _worker(command, by_voice, speak_reply):
    if not _work_lock.acquire(blocking=False):
        _say("I'm still working on the last command.")
        return
    if speak_reply is None:
        speak_reply = by_voice
    try:
        if by_voice:
            _set(state="listening", heard="")
            command = listen()
            if not command:
                _say("I did not catch that.")
                return
            speak_reply = True

        if command.lower().strip(" .!?") in AGAIN_WORDS and _last["command"]:
            command = _last["command"]
        else:
            _last["command"] = command

        _set(state="thinking", heard=command)
        reply = try_offline(command)
        if reply is None:
            reply = run_agent(command)
        _say(reply)
        if speak_reply:
            speak(reply[:200],
                  on_start=lambda: _set(state="speaking"),
                  on_end=lambda: _set(state="idle"))
    except Exception as e:
        _say(f"Error: {e}")
    finally:
        _set(state="idle", confirm="")
        _last["done"] = time.time()
        _work_lock.release()


# ---------- Greeting when Nova starts ----------
GREET_ON_START = True
USER_NAME = "Shubham"


def _wait_for_internet(max_seconds=20):
    """After login the internet can take a few seconds. Wait a bit so the natural voice works."""
    import socket

    for _ in range(max_seconds // 2):
        try:
            socket.create_connection(("1.1.1.1", 443), timeout=2).close()
            return
        except OSError:
            time.sleep(2)


def build_greeting():
    import datetime

    import psutil

    now = datetime.datetime.now()
    if now.hour < 12:
        part = "Good morning"
    elif now.hour < 17:
        part = "Good afternoon"
    else:
        part = "Good evening"

    time_text = now.strftime("%I:%M %p").lstrip("0")
    date_text = now.strftime("%A, %d %B")
    text = f"{part}, {USER_NAME}! It is {time_text} on {date_text}."

    battery = psutil.sensors_battery()
    if battery:
        text += f" Battery is at {battery.percent:.0f} percent."
        if not battery.power_plugged and battery.percent < 20:
            text += " Please plug in the charger."
    return text + " How can I help you today?"


def greet_on_start():
    if GREET_ON_START:
        threading.Thread(target=_greeting_worker, daemon=True).start()


def _greeting_worker():
    if not _work_lock.acquire(blocking=False):
        return
    try:
        _wait_for_internet()
        text = build_greeting()
        _set(heard="")
        _say(text)
        speak(text,
              on_start=lambda: _set(state="speaking"),
              on_end=lambda: _set(state="idle"))
    except Exception as e:
        print(f"[greeting failed: {e}]")
    finally:
        _set(state="idle")
        _last["done"] = time.time()
        _work_lock.release()




# ---------- Nova speaks on her own (reminders) ----------
def announce(text):
    """Say something out loud without being asked, for example a reminder."""
    threading.Thread(target=_announce_worker, args=(text,), daemon=True).start()


def _announce_worker(text):
    for _ in range(90):            # wait up to 90 seconds until Nova is free
        if _work_lock.acquire(blocking=False):
            break
        time.sleep(1)
    else:
        return
    try:
        _set(heard="")
        _say(text)
        speak(text,
              on_start=lambda: _set(state="speaking"),
              on_end=lambda: _set(state="idle"))
    except Exception as e:
        print(f"[announce failed: {e}]")
    finally:
        _set(state="idle")
        _last["done"] = time.time()
        _work_lock.release()