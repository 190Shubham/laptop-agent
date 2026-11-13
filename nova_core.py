import builtins
import threading

from agent import run_agent
from offline import try_offline
from voice import listen, speak

STATE = {"state": "idle", "message": "", "msg_id": 0, "heard": "", "confirm": ""}
_lock = threading.Lock()
_work_lock = threading.Lock()
_confirm_event = threading.Event()
_confirm_answer = {"ok": False}


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


def run_command(command, by_voice=False):
    threading.Thread(target=_worker, args=(command, by_voice), daemon=True).start()


def _worker(command, by_voice):
    if not _work_lock.acquire(blocking=False):
        _say("I'm still working on the last command.")
        return
    try:
        if by_voice:
            _set(state="listening", heard="")
            command = listen()
            if not command:
                _say("I did not catch that.")
                return
        _set(state="thinking", heard=command)
        reply = try_offline(command)
        if reply is None:
            reply = run_agent(command)
        _say(reply)
        if by_voice:
            speak(reply[:200],
                  on_start=lambda: _set(state="speaking"),
                  on_end=lambda: _set(state="idle"))
    except Exception as e:
        _say(f"Error: {e}")
    finally:
        _set(state="idle", confirm="")
        _work_lock.release()