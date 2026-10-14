import builtins
import queue
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

from agent import run_agent
from offline import try_offline
from voice import listen, speak

ui_queue = queue.Queue()  # messages from the background thread to the window


def ask_yes_no(prompt=""):
    """Replaces input() so the safety y/n question appears as a popup."""
    answer = {}
    done = threading.Event()
    ui_queue.put(("confirm", prompt, answer, done))
    done.wait()
    return "y" if answer.get("ok") else "n"


builtins.input = ask_yes_no


class App:
    def __init__(self, root):
        self.root = root
        root.title("Laptop Agent")
        root.geometry("600x560")
        root.minsize(420, 320)

        # Bottom bar first, so it is always visible
        bottom = tk.Frame(root)
        bottom.pack(side="bottom", fill="x", padx=8, pady=8)
        self.entry = tk.Entry(bottom, font=("Segoe UI", 11))
        self.entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.entry.bind("<Return>", lambda e: self.send_text())
        self.send_btn = tk.Button(bottom, text="Send", command=self.send_text)
        self.send_btn.pack(side="left", padx=(6, 0))
        self.mic_btn = tk.Button(bottom, text="Speak", command=self.send_voice)
        self.mic_btn.pack(side="left", padx=(6, 0))

        self.chat = scrolledtext.ScrolledText(
            root, state="disabled", wrap="word", height=10, font=("Segoe UI", 10))
        self.chat.pack(side="top", fill="both", expand=True, padx=8, pady=(8, 0))

        self.add("Agent", "Ready. Type a command in the box below, or press Speak.")
        self.entry.focus_force()
        self.poll_queue()

    def add(self, who, text):
        self.chat.config(state="normal")
        self.chat.insert("end", f"{who}: {text}\n\n")
        self.chat.config(state="disabled")
        self.chat.see("end")

    def set_busy(self, busy):
        state = "disabled" if busy else "normal"
        self.send_btn.config(state=state)
        self.mic_btn.config(state=state)
        self.entry.config(state=state)
        if not busy:
            self.entry.focus()

    def send_text(self):
        command = self.entry.get().strip()
        if not command:
            return
        self.entry.delete(0, "end")
        self.add("You", command)
        self.run_in_background(command, by_voice=False)

    def send_voice(self):
        self.add("Agent", "Listening for 5 seconds... speak now")
        self.run_in_background(None, by_voice=True)

    def run_in_background(self, command, by_voice):
        self.set_busy(True)
        threading.Thread(target=self.worker, args=(command, by_voice),
                         daemon=True).start()

    def worker(self, command, by_voice):
        try:
            if by_voice:
                command = listen()
                if not command:
                    ui_queue.put(("say", "Agent", "I did not catch that."))
                    return
                ui_queue.put(("say", "You (voice)", command))
            reply = try_offline(command)
            if reply is None:
                reply = run_agent(command)
            ui_queue.put(("say", "Agent", reply))
            if by_voice:
                speak(reply[:200])
        except Exception as e:
            ui_queue.put(("say", "Agent", f"Error: {e}"))
        finally:
            ui_queue.put(("done",))

    def poll_queue(self):
        try:
            while True:
                item = ui_queue.get_nowait()
                kind = item[0]
                if kind == "say":
                    self.add(item[1], item[2])
                elif kind == "confirm":
                    _, prompt, answer, done = item
                    text = prompt.replace("(y/n):", "").strip() or "Allow this action?"
                    answer["ok"] = messagebox.askyesno("Safety check", text)
                    done.set()
                elif kind == "done":
                    self.set_busy(False)
        except queue.Empty:
            pass
        self.root.after(100, self.poll_queue)


root = tk.Tk()
App(root)
root.mainloop()