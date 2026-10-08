#!/usr/bin/env python3
"""Compare identity, gzip, and zstd requests to a Responses endpoint."""

from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from canary import inspect

TEXT = {
    "en": {"title": "Compressed request check", "encoding": "Encoding", "status": "HTTP", "usable": "Usable response", "yes": "yes", "no": "no", "fallback": "Backend fallback is not observable from this probe", "invalid": "Invalid input or probe failed", "dependency": "Install dependencies with: python3 -m pip install -r requirements.txt"},
    "fr": {"title": "Contrôle des requêtes compressées", "encoding": "Encodage", "status": "HTTP", "usable": "Réponse utilisable", "yes": "oui", "no": "non", "fallback": "Le basculement de backend n’est pas observable par cette sonde", "invalid": "Entrée invalide ou sonde en échec", "dependency": "Installez les dépendances avec : python3 -m pip install -r requirements.txt"},
    "es": {"title": "Comprobación de solicitudes comprimidas", "encoding": "Codificación", "status": "HTTP", "usable": "Respuesta utilizable", "yes": "sí", "no": "no", "fallback": "Esta sonda no permite observar el cambio de backend", "invalid": "Entrada no válida o fallo de la sonda", "dependency": "Instale las dependencias con: python3 -m pip install -r requirements.txt"},
}
ENCODINGS = ("identity", "gzip", "zstd")
MAX_RESPONSE = 2_000_000


def encode(payload: dict, encoding: str) -> bytes:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    if encoding == "identity":
        return raw
    if encoding == "gzip":
        return gzip.compress(raw, mtime=0)
    if encoding == "zstd":
        import zstandard
        return zstandard.ZstdCompressor().compress(raw)
    raise ValueError("unsupported encoding")


def send(url: str, payload: dict, encoding: str, token: str | None, timeout: float) -> dict:
    headers = {"Content-Type": "application/json", "Accept": "text/event-stream", "Accept-Encoding": "identity"}
    if encoding != "identity":
        headers["Content-Encoding"] = encoding
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, data=encode(payload, encoding), headers=headers, method="POST")
    try:
        response = urllib.request.urlopen(request, timeout=timeout)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        status = response.status
        content_type = response.headers.get("Content-Type", "")
        body = response.read(MAX_RESPONSE + 1)
    if len(body) > MAX_RESPONSE:
        raise ValueError("response too large")
    result = inspect(status, content_type, body.decode("utf-8", errors="replace"))
    return {"encoding": encoding, "http_status": status, "transport_accepted": 200 <= status < 300,
            "usable_response": result["ok"], "reason": result["reason"]}


def compare(url: str, payload: dict, token: str | None = None, timeout: float = 15) -> dict:
    if not isinstance(payload, dict) or not url.startswith(("http://", "https://")) or timeout <= 0:
        raise ValueError("invalid input")
    rows = [send(url, payload, encoding, token, timeout) for encoding in ENCODINGS]
    return {"results": rows, "backend_fallback_observed": None,
            "note_code": "three_requests_same_payload_no_backend_visibility"}


def demo() -> dict:
    """A local mock reproduces identity success and compressed-body rejection."""
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            if self.headers.get("Content-Encoding", "identity") == "identity" and json.loads(body):
                data = b'data: {"type":"response.completed"}\n\n'
                status, content_type = 200, "text/event-stream"
            else:
                data = b'{"error":"expected a JSON object"}'
                status, content_type = 400, "application/json"
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *_args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        return compare(f"http://127.0.0.1:{server.server_port}/v1/responses",
                       {"model": "demo", "input": "synthetic", "stream": True}, timeout=2)
    finally:
        server.shutdown()
        worker.join(timeout=2)
        server.server_close()


def render(report: dict, lang: str) -> str:
    words = TEXT[lang]
    lines = [words["title"], f"{words['encoding']} | {words['status']} | {words['usable']}"]
    lines += [f"{row['encoding']} | {row['http_status']} | {words['yes'] if row['usable_response'] else words['no']}"
              for row in report["results"]]
    lines.append(words["fallback"])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("demo", "probe"))
    parser.add_argument("--url")
    parser.add_argument("--payload", type=Path)
    parser.add_argument("--token-env")
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--lang", choices=TEXT, default="en")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            report = demo()
        else:
            if not args.url or not args.payload:
                raise ValueError("missing arguments")
            token = os.environ.get(args.token_env) if args.token_env else None
            if args.token_env and token is None:
                raise ValueError("missing token")
            report = compare(args.url, json.loads(args.payload.read_text(encoding="utf-8")), token, args.timeout)
    except ModuleNotFoundError:
        print(TEXT[args.lang]["dependency"], file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError, json.JSONDecodeError, urllib.error.URLError):
        print(TEXT[args.lang]["invalid"], file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render(report, args.lang))
    if args.command == "demo":
        return 0 if [row["usable_response"] for row in report["results"]] == [True, False, False] else 1
    return 0 if all(row["usable_response"] for row in report["results"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
