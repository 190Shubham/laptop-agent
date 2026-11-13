import asyncio
import ctypes
import os
import re
import tempfile

import pyttsx3
import sounddevice as sd
import speech_recognition as sr

SAMPLE_RATE = 16000

# ---- Natural (online) voice settings ----
USE_NEURAL_VOICE = True
NEURAL_VOICE_EN = "en-IN-NeerjaNeural"   # Indian English, female
NEURAL_VOICE_HI = "hi-IN-SwaraNeural"    # Hindi, female
NEURAL_RATE = "+0%"      # speed, for example "-10%" slower or "+10%" faster
NEURAL_PITCH = "+0Hz"    # pitch, for example "+5Hz" for a slightly higher voice

# ---- Windows (offline backup) voice settings ----
PREFERRED_VOICE = ""     # part of a voice name to force it, for example "zira"
VOICE_RATE = 165
_voice_id = None


def listen(seconds: int = 5) -> str:
    """Record from the microphone and return the text. Returns '' if nothing was understood."""
    print(f"Listening for {seconds} seconds... speak now")
    audio = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                   channels=1, dtype="int16")
    sd.wait()

    recognizer = sr.Recognizer()
    audio_data = sr.AudioData(audio.tobytes(), SAMPLE_RATE, 2)  # 2 bytes per sample
    try:
        return recognizer.recognize_google(audio_data, language="en-IN")
    except sr.UnknownValueError:
        print("Could not understand the audio.")
        return ""
    except sr.RequestError:
        print("Speech service not reachable. Check your internet.")
        return ""


# ---------- Natural voice (needs internet) ----------
def _play_mp3(path, on_start, on_end):
    """Play an mp3 with Windows' built-in player and wait until it finishes."""
    winmm = ctypes.windll.winmm
    alias = "novavoice"

    def mci(command):
        buffer = ctypes.create_unicode_buffer(255)
        error = winmm.mciSendStringW(command, buffer, 254, 0)
        return error

    mci(f"close {alias}")
    if mci(f'open "{path}" type mpegvideo alias {alias}'):
        raise RuntimeError("could not open the audio file")
    try:
        if on_start:
            on_start()
        mci(f"play {alias} wait")
    finally:
        mci(f"close {alias}")
        if on_end:
            on_end()


def _speak_neural(text, on_start, on_end):
    import edge_tts

    voice = NEURAL_VOICE_HI if re.search(r"[\u0900-\u097F]", text) else NEURAL_VOICE_EN
    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        async def make():
            communicate = edge_tts.Communicate(text, voice, rate=NEURAL_RATE, pitch=NEURAL_PITCH)
            await communicate.save(path)

        asyncio.run(make())
        _play_mp3(path, on_start, on_end)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


# ---------- Windows voice (works offline) ----------
def _pick_female_voice(engine):
    """Choose a female voice once, then remember it."""
    global _voice_id
    if _voice_id:
        return _voice_id
    voices = engine.getProperty("voices")

    hints = [PREFERRED_VOICE.lower()] if PREFERRED_VOICE else []
    hints += ["heera", "zira", "hazel", "susan", "kalpana", "aria", "jenny"]
    for hint in hints:
        for v in voices:
            if hint and hint in v.name.lower():
                _voice_id = v.id
                return _voice_id

    for v in voices:
        if "female" in str(getattr(v, "gender", "")).lower():
            _voice_id = v.id
            return _voice_id
    return None


def _speak_windows(text, on_start, on_end):
    try:
        try:
            import pythoncom
            pythoncom.CoInitialize()  # needed when speaking from a background thread
        except Exception:
            pass
        engine = pyttsx3.init()  # created fresh each time so it never gets stuck
        voice_id = _pick_female_voice(engine)
        if voice_id:
            engine.setProperty("voice", voice_id)
        engine.setProperty("rate", VOICE_RATE)
        if on_start:
            engine.connect("started-utterance", lambda **kw: on_start())
        if on_end:
            engine.connect("finished-utterance", lambda **kw: on_end())
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"[voice reply failed: {e}]")


def speak(text: str, on_start=None, on_end=None):
    """Say the text out loud. on_start and on_end are called when the sound really starts and ends."""
    if USE_NEURAL_VOICE:
        try:
            _speak_neural(text, on_start, on_end)
            return
        except Exception as e:
            print(f"[natural voice failed, using the Windows voice instead: {e}]")
    _speak_windows(text, on_start, on_end)