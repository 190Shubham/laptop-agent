import json
import os
import secrets
import signal
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Without a console (pythonw), print() has nowhere to go, so write it to a log file
if sys.stdout is None or sys.stderr is None:
    _log = open(os.path.join(BASE_DIR, "nova_log.txt"), "a", encoding="utf-8")
    sys.stdout = sys.stderr = _log

from PyQt6.QtCore import QObject, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QColor, QGuiApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QMenu

import nova_core

AVATAR_DIR = os.path.join(BASE_DIR, "avatar")
PORT = 8765
WIDTH, HEIGHT = 380, 620
MARGIN = 12
TOKEN = secrets.token_urlsafe(16)
ALLOWED_HOSTS = (f"127.0.0.1:{PORT}", f"localhost:{PORT}")


class Mover(QObject):
    moved = pyqtSignal(int, int)


mover = Mover()


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.headers.get("Host") not in ALLOWED_HOSTS:
            return self._send_json({"error": "bad host"}, 403)
        url = urlparse(self.path)
        query = parse_qs(url.query)

        if url.path == "/state":
            return self._send_json(nova_core.get_state())

        if url.path in ("/command", "/voice", "/confirm", "/move"):
            token = query.get("token", [""])[0]
            if not secrets.compare_digest(token, TOKEN):
                return self._send_json({"error": "forbidden"}, 403)
            if url.path == "/command":
                text = query.get("text", [""])[0].strip()
                if text:
                    nova_core.run_command(text)
            elif url.path == "/voice":
                nova_core.run_command(None, by_voice=True)
            elif url.path == "/move":
                try:
                    dx = int(float(query.get("dx", ["0"])[0]))
                    dy = int(float(query.get("dy", ["0"])[0]))
                    mover.moved.emit(dx, dy)
                except ValueError:
                    pass
            else:
                nova_core.answer_confirm(query.get("answer", ["n"])[0] == "y")
            return self._send_json({"ok": True})

        super().do_GET()


def start_server():
    handler = partial(Handler, directory=AVATAR_DIR)
    server = ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()


class NovaWindow(QWebEngineView):
    def __init__(self, model_file):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.page().setBackgroundColor(QColor(0, 0, 0, 0))

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)
        mover.moved.connect(self.nudge)

        area = QGuiApplication.primaryScreen().availableGeometry()
        self.resize(WIDTH, min(HEIGHT, area.height() - 2 * MARGIN))
        self.move_to_top_right()
        self.load(QUrl(
            f"http://127.0.0.1:{PORT}/index.html?model={quote(model_file)}&token={TOKEN}"
        ))

    def move_to_top_right(self):
        area = QGuiApplication.primaryScreen().availableGeometry()
        self.move(area.x() + area.width() - self.width() - MARGIN, area.y() + MARGIN)

    def nudge(self, dx, dy):
        self.move(self.x() + dx, self.y() + dy)

    def show_menu(self, pos):
        menu = QMenu(self)
        menu.addAction("Move to top right", self.move_to_top_right)
        menu.addAction("Quit Nova", QApplication.quit)
        menu.exec(self.mapToGlobal(pos))


def main():
    vrm_files = [f for f in os.listdir(AVATAR_DIR) if f.lower().endswith(".vrm")]
    if not vrm_files:
        print("No .vrm file found in the avatar folder.")
        return
    start_server()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    window = NovaWindow(vrm_files[0])
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()