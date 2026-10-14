import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types, errors
from tools.apps import open_website, open_app, create_folder
from tools.system import get_system_info, take_screenshot, get_current_time
from tools.files import organize_folder
from tools.launcher import open_any_app

load_dotenv()
client = genai.Client(api_key=os.getenv("API_KEY"))

TOOLS = [open_website, open_app, open_any_app, create_folder,
         get_system_info, take_screenshot, get_current_time,
         organize_folder]

MODELS = ["gemini-3.5-flash", "gemini-3-flash-preview"]

SYSTEM_PROMPT = (
   "You are a laptop assistant. Use the provided tools to do what the user asks. "
    "To open an app, use open_app for notepad, calculator, paint, chrome and vscode, "
    "and use open_any_app for every other app (WhatsApp, Spotify, Settings and so on). "
    "Remember what was said earlier in this conversation. "
    "If no tool can do it, say you can't do that yet. Reply in one short line."
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