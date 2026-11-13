from voice import speak

speak("Hello, I am Nova. How can I help you today?",
      on_start=lambda: print("voice started"),
      on_end=lambda: print("voice ended"))