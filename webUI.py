

import sys
import os
import threading
import webbrowser
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8420
DIR  = os.path.dirname(os.path.abspath(__file__))

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress request noise

def serve():
    os.chdir(DIR)
    server = HTTPServer(("localhost", PORT), QuietHandler)
    print("\n Bonboneka WebUI Ver1.0 Launcher")
    print("Serving from: ./WebUI/index.html")
    print(f"CLICK THIS! :3 -> http://localhost:{PORT} <- ")
    print("Ctrl+C to stop\n")
    server.serve_forever()

def open_browser():
    time.sleep(0.4)  # let the server start first
    webbrowser.open(f"http://localhost:{PORT}/WebUI/index.html")

if __name__ == "__main__":
    t = threading.Thread(target=open_browser, daemon=True)
    t.start()
    try:
        serve()
    except KeyboardInterrupt:
        print("\nServer ki***d. Byeeee! :D")