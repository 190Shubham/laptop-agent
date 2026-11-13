# Nova: AI Desktop Agent

Nova is a 3D cartoon assistant that lives in the top-right corner of your desktop.
Talk to her or type, and she controls your laptop.

![Nova](docs/nova.png)

## What she can do
- Open apps and websites in Brave or Chrome ("open youtube in brave")
- Play a song on YouTube by name, in English or Hindi
- Search Google, YouTube, Amazon, Flipkart and more
- Type text into any app or website
- Organize folders, take screenshots, show battery, CPU and RAM
- Ask Allow / Deny before any risky action
- Answer in a natural female voice, with her mouth moving in sync

## How it works
- **Brain:** Gemini with tool calling, plus an offline command parser that works when the API is busy
- **Voice:** SpeechRecognition for input, Microsoft neural voices (edge-tts) for output, Windows voice as a backup
- **Face:** a VRoid 3D model rendered with three.js and three-vrm inside a transparent PyQt6 window
- **Safety:** app allow-list, confirmation popup, action log, and a secret token on the local server

## Run it
1. `pip install -r requirements.txt`
2. Put your Gemini key in `.env` as `API_KEY=...`
3. Put your VRM model in the `avatar` folder
4. `python avatar.py` (or double-click `start_nova.vbs`)



\# Laptop Agent



A Python desktop assistant that controls your Windows laptop with text or voice commands. It uses Google Gemini tool calling for complex requests and runs simple commands offline, so it still works when the AI service is busy.



!\[Laptop Agent window](screenshot.png)



\## Features



\- Open any installed app or website (`open whatsapp`, `open youtube.com`)

\- Create folders and organize a folder's files by type

\- Battery, CPU and RAM info, current time, screenshots

\- Voice commands (speech to text) and spoken replies

\- Simple window with a text box and a Speak button

\- Safety layer: risky actions need your confirmation, and actions are logged

\- Offline fallback: common commands run without any API call



\## How it works



1\. A command is first checked against local rules (`offline.py`). If it matches, Python runs the tool directly.

2\. Otherwise it is sent to Gemini, which picks the right tool function (tool calling) and the agent runs it (`agent.py`).

3\. Risky tools ask for confirmation first (`tools/safety.py`).



\## Setup



```powershell

git clone https://github.com/190Shubham/laptop-agent.git
cd laptop-agent

python -m venv venv

venv\\Scripts\\activate

pip install -r requirements.txt

```



Create a `.env` file (see `.env.example`) with a free Gemini API key from Google AI Studio:



```

API\_KEY=your\_gemini\_api\_key\_here

```



\## Run



```powershell

python gui.py    # window version

python main.py   # terminal version (type v to speak)

```



\## Project structure



```

agent.py        Gemini tool calling and chat memory

offline.py      commands that run without the API

voice.py        speech to text and text to speech

gui.py          tkinter window

main.py         terminal version

tools/          apps, files, system, launcher, safety

```



\## Built with



Python, Google Gemini API, tkinter, SpeechRecognition, pyttsx3, psutil, pyautogui



Built by Shubham Kumar.

