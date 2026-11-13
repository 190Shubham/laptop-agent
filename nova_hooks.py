import agent
import offline
import voice
from nova import set_state

_listen = voice.listen
_speak = voice.speak
_try_offline = offline.try_offline
_run_agent = agent.run_agent


def listen(*args, **kwargs):
    set_state("listening")
    try:
        return _listen(*args, **kwargs)
    finally:
        set_state("idle")


def speak(*args, **kwargs):
    set_state("speaking")
    try:
        return _speak(*args, **kwargs)
    finally:
        set_state("idle")


def try_offline(*args, **kwargs):
    set_state("thinking")
    try:
        result = _try_offline(*args, **kwargs)
    except Exception:
        set_state("idle")
        raise
    if result is not None:
        set_state("idle")
    return result


def run_agent(*args, **kwargs):
    set_state("thinking")
    try:
        return _run_agent(*args, **kwargs)
    finally:
        set_state("idle")


voice.listen = listen
voice.speak = speak
offline.try_offline = try_offline
agent.run_agent = run_agent