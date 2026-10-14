import datetime
import functools

LOG_FILE = "agent_log.txt"


def _log(text: str) -> None:
    """Add one line to agent_log.txt with the time."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} | {text}\n")


def require_confirmation(func):
    """Ask the user y/n before running a risky tool."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        details = ", ".join([repr(a) for a in args] + [f"{k}={v!r}" for k, v in kwargs.items()])
        call = f"{func.__name__}({details})"

        answer = input(f"\n[CONFIRM] Agent wants to run {call}. Allow? (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            _log(f"ALLOWED | {call}")
            return func(*args, **kwargs)

        _log(f"DENIED  | {call}")
        return "Cancelled: the user said no."

    return wrapper