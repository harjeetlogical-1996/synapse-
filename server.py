"""
Synapse - local web server (frontend ke liye).

Stdlib http.server - koi extra library nahi. Do cheezein serve karta hai:
  GET  /            -> frontend page (index.html)
  GET  /run?company=..&website=..  -> Server-Sent Events stream:
        har step ka progress live bhejta hai, phir final brief.

Chalao:  python server.py    (phir browser: http://localhost:8000)
"""
import os
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import agent

HERE = Path(__file__).parent
# Render (and most hosts) provide PORT via env; default 8000 for local.
PORT = int(os.environ.get("PORT", "8000"))
# Bind to 0.0.0.0 when hosted so the platform can route to it; localhost otherwise.
HOST = os.environ.get("HOST", "127.0.0.1")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # console saaf rakho

    def _send_html(self, path: Path):
        try:
            body = path.read_bytes()
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"index.html nahi mila")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _sse(self, event: str, data: dict):
        """Ek SSE message bhejo."""
        payload = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        self.wfile.write(payload.encode("utf-8"))
        self.wfile.flush()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path in ("/", "/index.html"):
            self._send_html(HERE / "index.html")
            return

        # serve saved briefs (for the "Open full page" button)
        if parsed.path.startswith("/briefs/"):
            fname = urllib.parse.unquote(parsed.path[len("/briefs/"):])
            target = (HERE / "briefs" / fname).resolve()
            # safety: keep it inside briefs/
            if str(target).startswith(str((HERE / "briefs").resolve())) and target.exists():
                self._send_html(target)
            else:
                self.send_response(404)
                self.end_headers()
            return

        if parsed.path == "/run":
            qs = urllib.parse.parse_qs(parsed.query)
            company = (qs.get("company", [""])[0]).strip()
            website = (qs.get("website", [""])[0]).strip()

            # optional "your company" (playbook) overrides from the frontend panel
            pb_name = (qs.get("pb_name", [""])[0]).strip()
            pb_oneliner = (qs.get("pb_oneliner", [""])[0]).strip()
            pb_services = (qs.get("pb_services", [""])[0]).strip()
            pb_ideal = (qs.get("pb_ideal", [""])[0]).strip()

            playbook = None
            if pb_name or pb_services or pb_ideal:
                playbook = agent.build_playbook_override(
                    pb_name, pb_oneliner, pb_services, pb_ideal)

            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            if not company:
                self._sse("error", {"message": "Company name is required."})
                return

            try:
                for update in agent.run_steps(company, website, playbook):
                    if update.get("step") == "final":
                        self._sse("final", update)
                    else:
                        self._sse("step", update)
            except Exception as e:
                self._sse("error", {"message": f"Something went wrong: {e}"})
            return

        # baaki sab -> 404
        self.send_response(404)
        self.end_headers()


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    where = f"http://localhost:{PORT}" if HOST == "127.0.0.1" else f"port {PORT}"
    print(f"\n  Synapse is running:  {where}\n")
    print("  Press Ctrl+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.\n")
        server.shutdown()


if __name__ == "__main__":
    main()
