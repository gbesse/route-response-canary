#!/usr/bin/env python3
"""Check whether an HTTP success is a valid Responses SSE completion."""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

TEXT = {
    "en": ("Route response canary", "valid completion", "invalid model response"),
    "fr": ("Canari de réponse de route", "réponse complète", "réponse modèle invalide"),
    "es": ("Canario de respuesta de ruta", "respuesta completa", "respuesta del modelo no válida"),
}


def inspect(status, content_type, body):
    if status != 200:
        return {"ok": False, "reason": "http_status", "status": status}
    if "text/event-stream" not in content_type.lower():
        return {"ok": False, "reason": "wrong_content_type", "status": status}
    if not body.strip():
        return {"ok": False, "reason": "empty_stream", "status": status}
    events = []
    for block in body.replace("\r\n", "\n").split("\n\n"):
        fields = [line[6:].strip() for line in block.splitlines() if line.startswith("data: ")]
        for field in fields:
            if field == "[DONE]":
                continue
            try:
                payload = json.loads(field)
            except json.JSONDecodeError:
                return {"ok": False, "reason": "invalid_json_event", "status": status}
            if not isinstance(payload, dict) or not isinstance(payload.get("type"), str):
                return {"ok": False, "reason": "invalid_event", "status": status}
            events.append(payload["type"])
    if "response.completed" not in events:
        return {"ok": False, "reason": "missing_completion", "status": status,
                "event_count": len(events)}
    if "response.failed" in events:
        return {"ok": False, "reason": "failed_event", "status": status,
                "event_count": len(events)}
    return {"ok": True, "reason": "completed", "status": status, "event_count": len(events)}


def inspect_attempts(attempts):
    rows = [inspect(a["status"], a["content_type"], a["body"]) for a in attempts]
    return {"attempts": rows, "fallback_observed": len(rows) > 1 and not rows[0]["ok"]
            and any(row["ok"] for row in rows[1:])}


def probe(url, payload, token, timeout):
    headers = {"content-type": "application/json", "accept": "text/event-stream"}
    if token:
        headers["authorization"] = "Bearer " + token
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers,
                                     method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read(2_000_001)
        if len(body) > 2_000_000:
            raise ValueError("response exceeds 2 MB limit")
        return inspect(response.status, response.headers.get("content-type", ""),
                       body.decode("utf-8", errors="replace"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("demo", "check", "probe"))
    ap.add_argument("--attempts", type=Path, help="JSON array of captured attempts")
    ap.add_argument("--url", help="authorized Responses endpoint")
    ap.add_argument("--payload", type=Path, help="request JSON for probe")
    ap.add_argument("--token-env", help="environment variable containing bearer token")
    ap.add_argument("--timeout", type=float, default=15)
    ap.add_argument("--lang", choices=TEXT, default="en")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        if args.command == "demo":
            attempts = [{"status": 200, "content_type": "text/html", "body": "<html>error</html>"},
                        {"status": 200, "content_type": "text/event-stream",
                         "body": 'data: {"type":"response.completed"}\n\n'}]
            result = inspect_attempts(attempts)
            ok = result["fallback_observed"]
        elif args.command == "check":
            if not args.attempts:
                ap.error("check requires --attempts")
            result = inspect_attempts(json.loads(args.attempts.read_text()))
            ok = result["fallback_observed"]
        else:
            if not args.url or not args.payload:
                ap.error("probe requires --url and --payload")
            token = os.environ.get(args.token_env) if args.token_env else None
            if args.token_env and token is None:
                ap.error("token environment variable is not set")
            result = probe(args.url, json.loads(args.payload.read_text()), token, args.timeout)
            ok = result["ok"]
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        title, good, bad = TEXT[args.lang]
        print(title)
        if "attempts" in result:
            for index, row in enumerate(result["attempts"], 1):
                print(f"{index}: {good if row['ok'] else bad} ({row['reason']})")
            print(f"fallback_observed={str(result['fallback_observed']).lower()}")
        else:
            print(f"{good if ok else bad} ({result['reason']})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
