import urllib.request


def set_state(state: str) -> None:
    """Tell Nova what the agent is doing: idle, listening, thinking or speaking."""
    try:
        urllib.request.urlopen(f"http://127.0.0.1:8765/set?state={state}", timeout=1).read()
    except Exception:
        pass  # Nova is not running, so ignore