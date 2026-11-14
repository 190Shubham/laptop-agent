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
END_SILENCE_SECONDS = 0.8      # stop recording after this much silence
MAX_SPEECH_SECONDS = 8
FOLLOWUP_SECONDS = 30          # after Nova answers, no wake word is needed for this long
AWAKE_SECONDS = 300            # "stay awake" mode lasts this long (5 minutes)

# "nova", "hey nova", "ok nova", and common mishearings. Group 1 is what comes after.
WAKE_RE = re.compile(
    r"\b(?:(?:hey|hi|hello|ok|okay)\s+)?(?:nova|noah|noa|novah|no\s?va)\b[\s,.!?]*(.*)$",
    re.IGNORECASE)
STAY_AWAKE_RE = re.compile(
    r"\b(stay awake|keep listening|listen continuously|always listen|stay on)\b", re.IGNORECASE)
SLEEP_RE = re.compile(
    r"\b(go to sleep|stop listening|sleep mode|that'?s all|that is all)\b", re.IGNORECASE)

# Answers to Allow / Deny questions. "No" words are checked first ("don't allow" means no).
NO_RE = re.compile(
    r"\b(deny|denied|no|nope|nah|cancel|don'?t|do not|stop|never mind|reject|negative)\b",
    re.IGNORECASE)
YES_RE = re.compile(
    r"\b(allow|a low|yes|yeah|yep|yup|ok|okay|sure|go ahead|do it|approve|confirm|proceed|affirmative)\b",
    re.IGNORECASE)

_enabled = WAKE_WORD_ENABLED
_started = False
_threshold = None
_last_speech_start = 0.0
_awake_until = 0.0


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
            if not _enabled or (nova_core.is_busy() and not nova_core.is_confirming()):
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


def _handle_confirm_answer(text):
    """Nova asked Allow or Deny. Listen for the answer."""
    if NO_RE.search(text):
        print("[wake] answer: DENY")
        nova_core.answer_confirm(False)
    elif YES_RE.search(text):
        print("[wake] answer: ALLOW")
        nova_core.answer_confirm(True)
    else:
        print("[wake] not an answer, still waiting for allow or deny")


def _handle(text):
    global _awake_until

    if nova_core.is_confirming():
        _handle_confirm_answer(text)
        return

    done = nova_core.last_done()
    in_followup = done > 0 and (_last_speech_start - done) < FOLLOWUP_SECONDS
    awake = time.time() < _awake_until
    match = WAKE_RE.search(text)

    if match:
        command = match.group(1).strip()
        heard_wake = True
    elif awake or in_followup:
        command = text.strip()
        heard_wake = False
    else:
        print("[wake] ignored (no 'Hey Nova' and not in follow-up time)")
        return

    if SLEEP_RE.search(command):
        _awake_until = 0.0
        nova_core.announce("Okay, I will wait until you say Hey Nova.")
        return
    if STAY_AWAKE_RE.search(command):
        _awake_until = time.time() + AWAKE_SECONDS
        minutes = AWAKE_SECONDS // 60
        nova_core.announce(f"Okay, I will keep listening for {minutes} minutes. "
                           "Say go to sleep to stop me.")
        return

    if heard_wake:
        winsound.Beep(880, 120)
        if command:
            nova_core.run_command(command, speak_reply=True)
        else:
            nova_core.run_command(None, by_voice=True)  # she listens for your command
    else:
        nova_core.run_command(command, speak_reply=True)

    if awake:
        _awake_until = time.time() + AWAKE_SECONDS  # every command keeps her awake


def _loop():
    recognizer = sr.Recognizer()
    while True:
        try:
            confirming = nova_core.is_confirming()
            if not _enabled or (nova_core.is_busy() and not confirming):
                time.sleep(0.3)
                continue
            if not confirming and time.time() - nova_core.last_done() < 1.0:
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