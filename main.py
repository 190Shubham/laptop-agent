from agent import run_agent
from voice import listen, speak
from offline import try_offline

print("Laptop Agent ready. Type 'exit' to quit, or 'v' to speak a command.")

while True:
    command = input("You: ").strip()
    if command.lower() in ("exit", "quit"):
        break

    by_voice = False
    if command.lower() in ("v", "voice"):
        command = listen()
        if not command:
            continue
        by_voice = True
        print("You (voice):", command)

    if command:
        reply = try_offline(command)
        if reply is None:
            reply = run_agent(command)
        print("Agent:", reply)
        if by_voice:
            speak(reply[:200])