import pyttsx3
import sounddevice as sd
import speech_recognition as sr

SAMPLE_RATE = 16000


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


def speak(text: str):
    """Say the text out loud."""
    try:
        try:
            import pythoncom
            pythoncom.CoInitialize()  # needed when speaking from a background thread
        except Exception:
            pass
        engine = pyttsx3.init()  # created fresh each time so it never gets stuck
        engine.setProperty("rate", 175)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"[voice reply failed: {e}]")