"""
server.py — Zero-dependency HTTP server for the AI Career Navigator.

Serves the static frontend from ./static and exposes JSON endpoints:
    POST /api/generate   { profile }  -> structured roadmap JSON
    POST /api/chat       { message, profile } -> profile-aware reply
    GET  /api/health                  -> { ok, mode, demo_mode }

Run:  python server.py   (default http://127.0.0.1:8000, override with PORT)
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import ai_client
import db

STATIC_DIR = Path(__file__).parent / "static"
PORT = int(os.environ.get("PORT", "8000"))

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
}

MODE = "mock" if (os.environ.get("DEMO_MODE") == "1" or not os.environ.get("OPENAI_API_KEY")) else "ai"


class Handler(BaseHTTPRequestHandler):
    server_version = "Avenir/0.1"

    # ------------------------------------------------------------------ utils
    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, path):
        # Resolve relative to STATIC_DIR, guard against path traversal
        rel = path.lstrip("/")
        if not rel:
            rel = "index.html"
        target = (STATIC_DIR / rel).resolve()
        if not str(target).startswith(str(STATIC_DIR.resolve())) or not target.is_file():
            self.send_error(404, "Not found")
            return
        ctype = CONTENT_TYPES.get(target.suffix.lower(), "application/octet-stream")
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    # ------------------------------------------------------------------ routes
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send_json({"ok": True, "mode": MODE, "demo_mode": MODE == "mock",
                             "ai_configured": bool(os.environ.get("OPENAI_API_KEY")),
                             "db_connected": db.is_available()})
        elif path == "/api/roadmaps":
            self._handle_list_roadmaps()
        else:
            self._send_static(path)

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/generate":
            self._handle_generate()
        elif path == "/api/chat":
            self._handle_chat()
        else:
            self._send_json({"error": "not found"}, status=404)

    def _handle_generate(self):
        profile = self._read_json().get("profile", {})
        if not profile or not isinstance(profile, dict):
            self._send_json({"error": "missing profile"}, status=400)
            return
        try:
            result = ai_client.generate_roadmap(profile)
            # Persist to database (best-effort, never block the response)
            try:
                profile_id = db.save_profile(profile)
                if profile_id:
                    db.save_roadmap(profile_id, result)
                    result["profile_id"] = profile_id
            except Exception as db_exc:
                print(f"[server] db persist warning: {db_exc}", file=sys.stderr)
            self._send_json(result)
        except Exception as exc:  # never let the demo crash
            print(f"[server] /api/generate error: {exc}", file=sys.stderr)
            self._send_json({"error": "internal error", "detail": str(exc)}, status=500)

    def _handle_list_roadmaps(self):
        try:
            roadmaps = db.list_recent_roadmaps(limit=20)
            self._send_json({"roadmaps": roadmaps})
        except Exception as exc:
            self._send_json({"roadmaps": [], "error": str(exc)})

    def _handle_chat(self):
        body = self._read_json()
        message = body.get("message", "")
        profile = body.get("profile", {}) or {}
        if not message:
            self._send_json({"error": "missing message"}, status=400)
            return
        try:
            self._send_json(ai_client.answer_chat(message, profile))
        except Exception as exc:
            print(f"[server] /api/chat error: {exc}", file=sys.stderr)
            self._send_json({"error": "internal error"}, status=500)

    def log_message(self, fmt, *args):
        # quieter logs: only print API hits
        if "/api/" in (args[0] if args else ""):
            super().log_message(fmt, *args)


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"AVENIR running at http://127.0.0.1:{PORT}")
    print(f"Mode: {MODE.upper()} "
          + ("(DEMO_MODE=1 forced)" if os.environ.get("DEMO_MODE") == "1" else
             "(no OPENAI_API_KEY, using offline mock)" if MODE == "mock" else "(AI connected)"))
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == "__main__":
    main()
