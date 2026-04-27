from __future__ import annotations

import json
import mimetypes
import os
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from employee_ml.service import EmployeeIntelligenceService  # noqa: E402


SERVICE = EmployeeIntelligenceService()
STATIC_ROOT = ROOT / "web"


class PortfolioHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/dashboard":
            self._send_json(SERVICE.dashboard_payload())
            return

        if parsed.path == "/api/health":
            self._send_json({"status": "ok"})
            return

        self._serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/predict":
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
            prediction = SERVICE.predict(payload)
        except Exception as exc:  # noqa: BLE001
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        self._send_json(prediction)

    def _serve_static(self, route: str) -> None:
        normalized = route.strip("/") or "index.html"
        requested = (STATIC_ROOT / normalized).resolve()

        if STATIC_ROOT not in requested.parents and requested != STATIC_ROOT / "index.html":
            self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
            return

        if requested.is_dir():
            requested = requested / "index.html"
        if not requested.exists():
            requested = STATIC_ROOT / "index.html"

        content_type, _ = mimetypes.guess_type(str(requested))
        with requested.open("rb") as handle:
            body = handle.read()

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def run() -> None:
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), PortfolioHandler)
    print(f"Employee intelligence dashboard running on http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
