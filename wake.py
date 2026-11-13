import re
import threading
import time
import winsound
from collections import deque

import numpy as np
import sounddevice as sd
import speech_recognition as sr

import nova_core

WAKE_WORD_ENABLED = True       # set to False to turn "Hey Nova" off completely
SAMPLE_RATE = 16000
BLOCK = 1600                   # 0.1 second of sound per block
END_SILENCE_SECONDS = 1.0      # stop recording after this much silence
MAX_SPEECH_SECONDS = 8
FOLLOWUP_SECONDS = 8           # after Nova answers, no wake word is needed for this long

# "nova", "hey nova", "ok nova", and common mishearings. Group 1 is what comes after.
WAKE_RE = re.compile(
    r"\b(?:(?:hey|hi|hello|ok|okay)\s+)?(?:nova|noah|noa|novah|no\s?va)\b[\s,.!?]*(.*)$",
    re.IGNORECASE)

_enabled = WAKE_WORD_ENABLED
_started = False
_threshold = None
_last_speech_start = 0.0


def is_enabled():
    return _enabled


def toggle():
    global _enabled
    _enabled = not _enabled
    print(f"[wake] 'Hey Nova' listening is now {'ON' if _enabled else 'OFF'}")


def _rms(data):
    return float(np.sqrt(np.mean(data.astype(np.float32) ** 2)))


def _capture_utterance():
    """Wait until someone speaks, record until they stop. Returns audio, or None."""
    global _threshold, _last_speech_start
    preroll = deque(maxlen=3)
    chunks = []
    speaking = False
    silence = 0.0
    speech_start = 0.0

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16",
                        blocksize=BLOCK) as stream:
        if _threshold is None:
            levels = [_rms(stream.read(BLOCK)[0]) for _ in range(8)]
            _threshold = min(max(float(np.mean(levels)) * 3, 300.0), 2000.0)
            print(f"[wake] room noise calibrated, threshold {_threshold:.0f}")

        while True:
            if not _enabled or nova_core.is_busy():
                return None
            data = stream.read(BLOCK)[0].copy()
            level = _rms(data)

            if level > _threshold:
                if not speaking:
                    speaking = True
                    speech_start = time.time()
                    chunks.extend(preroll)
                chunks.append(data)
                silence = 0.0
            elif speaking:
                chunks.append(data)
                silence += BLOCK / SAMPLE_RATE
                if silence >= END_SILENCE_SECONDS:
                    break
            else:
                preroll.append(data)

            if speaking and time.time() - speech_start > MAX_SPEECH_SECONDS:
                break

    if not chunks:
        return None
    audio = np.concatenate(chunks)
    if len(audio) < SAMPLE_RATE * 0.3:
        return None
    _last_speech_start = speech_start
    return audio


def _transcribe(recognizer, audio):
    data = sr.AudioData(audio.tobytes(), SAMPLE_RATE, 2)
    try:
        return recognizer.recognize_google(data, language="en-IN")
    except (sr.UnknownValueError, sr.RequestError):
        return ""


def _handle(text):
    in_followup = (_last_speech_start - nova_core.last_done()) < FOLLOWUP_SECONDS
    match = WAKE_RE.search(text)
    if match:
        command = match.group(1).strip()
        winsound.Beep(880, 120)
        if command:
            nova_core.run_command(command, speak_reply=True)
        else:
            nova_core.run_command(None, by_voice=True)  # she listens for your command
    elif in_followup and nova_core.last_done() > 0:
        nova_core.run_command(text, speak_reply=True)


def _loop():
    recognizer = sr.Recognizer()
    while True:
        try:
            if not _enabled or nova_core.is_busy():
                time.sleep(0.3)
                continue
            if time.time() - nova_core.last_done() < 1.0:
                time.sleep(0.2)  # let the room go quiet after Nova finishes speaking
                continue
            audio = _capture_utterance()
            if audio is None:
                continue
            text = _transcribe(recognizer, audio)
            if not text:
                continue
            print(f"[wake] heard: {text}")
            _handle(text)
            time.sleep(0.5)  # give the command time to take the microphone
        except Exception as e:
            print(f"[wake error: {e}]")
            time.sleep(2)


def start():
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_loop, daemon=True).start()