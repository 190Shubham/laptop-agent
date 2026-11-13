import time
import pyautogui
import pyperclip

TYPE_DELAY = 5  # seconds you get to click the target window or box
ALLOWED_KEYS = ("enter", "tab", "backspace", "esc")


def type_text(text: str) -> str:
    """Write text into the currently active window (any app or website text box).
    It waits a few seconds first so the user can click the right place.
    It never presses Enter by itself."""
    text = " ".join(text.splitlines())  # one line, so Enter is never pressed by accident
    print(f"[Typing in {TYPE_DELAY} seconds: click where you want the text]")
    time.sleep(TYPE_DELAY)

    old_clipboard = pyperclip.paste()
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.3)
    pyperclip.copy(old_clipboard)  # put your old clipboard back
    return f"Typed: {text}"


def press_key(key: str) -> str:
    """Press one key (enter, tab, backspace or esc) in the active window.
    Use enter only when the user clearly asks to press enter or send."""
    key = key.lower().strip()
    if key not in ALLOWED_KEYS:
        return f"Not allowed. I can only press: {', '.join(ALLOWED_KEYS)}"
    pyautogui.press(key)
    return f"Pressed {key}"