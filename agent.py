import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types, errors

from tools.apps import open_website, open_app, create_folder, search_web, play_on_youtube
from tools.system import get_system_info, take_screenshot, get_current_time
from tools.files import organize_folder
from tools.writer import type_text, press_key
from tools.controls import (volume_change, set_volume, toggle_mute, set_brightness,
                            change_brightness, lock_computer, shutdown_computer,
                            cancel_shutdown)
from tools.closer import close_any_app
from tools.media import media_control
from tools.reminders import remind_in, remind_at, list_reminders, clear_reminders
from tools.weather import get_weather
from tools.folders import open_folder, open_file
from tools.system_settings import open_settings, open_system_tool, set_radio

load_dotenv()
client = genai.Client(api_key=os.getenv("API_KEY"))

TOOLS = [
    open_website, open_app, create_folder, search_web, play_on_youtube,
    get_system_info, take_screenshot, get_current_time, organize_folder,
    type_text, press_key,
    volume_change, set_volume, toggle_mute, set_brightness, change_brightness,
    lock_computer, shutdown_computer, cancel_shutdown, close_any_app, media_control,
    remind_in, remind_at, list_reminders, clear_reminders,
    get_weather, open_folder, open_file,
    open_settings, open_system_tool, set_radio,
]

# Tries the first model, then the backup if the first is busy
MODELS = ["gemini-3.5-flash", "gemini-3-flash-preview"]

SYSTEM_PROMPT = (
    "You are Nova, a friendly laptop assistant. Use the provided tools to do what the user asks. "
    "Remember what was said earlier in this conversation. "
    "If no tool can do it, say you can't do that yet. Reply in one or two short sentences. "
    "Only press Enter if the user asks to press enter or send. "
    "To play a song or video, use play_on_youtube. "
    "If the user names a browser (brave or chrome), pass it as the browser argument. "
    "For reminders and timers, use remind_in or remind_at. "
    "Risky tools ask the user for permission themselves, so call them when asked."
)

CONFIG = types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, tools=TOOLS)

# One chat session keeps the conversation history
state = {"model": MODELS[0], "chat": client.chats.create(model=MODELS[0], config=CONFIG)}


def run_agent(user_input: str) -> str:
    for model in MODELS:
        # If we switch models, carry the history over to the new chat
        if state["model"] != model:
            history = state["chat"].get_history()
            state["chat"] = client.chats.create(model=model, config=CONFIG, history=history)
            state["model"] = model

        for attempt in range(3):
            try:
                response = state["chat"].send_message(user_input)
                return response.text or "Done."
            except errors.ServerError:
                time.sleep(2 * (attempt + 1))  # Google is busy: wait and retry
            except errors.APIError as e:
                print(f"[{model} failed with code {e.code}]")
                break
    return "Sorry, the AI service is busy right now. Please try again in a minute."