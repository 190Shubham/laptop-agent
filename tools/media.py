import pyautogui

KEYS = {
    "pause": "playpause", "play": "playpause", "resume": "playpause",
    "stop": "playpause", "next": "nexttrack", "skip": "nexttrack",
    "previous": "prevtrack",
}


def media_control(action: str) -> str:
    """Control the music or video that is playing on the laptop.
    action is pause, play, resume, stop, next, skip or previous."""
    key = KEYS.get(action.lower().strip())
    if not key:
        return "I can pause, play, go to the next one, or go to the previous one."
    pyautogui.press(key)
    return f"Okay, {action.lower().strip()}."