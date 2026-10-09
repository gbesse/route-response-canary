#!/usr/bin/env python3
"""Compare a saved gateway test with the route that served an agent request."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

WORDS = {
    "en": {"match": "Tested route matches the request", "mismatch": "Tested route differs from the request", "stale": "Test is too old", "inconclusive": "Route evidence is incomplete", "invalid": "Invalid evidence"},
    "fr": {"match": "La route testée correspond à la requête", "mismatch": "La route testée diffère de la requête", "stale": "Le test est trop ancien", "inconclusive": "Preuve de route incomplète", "invalid": "Preuve invalide"},
    "es": {"match": "La ruta probada coincide con la solicitud", "mismatch": "La ruta probada difiere de la solicitud", "stale": "La prueba es demasiado antigua", "inconclusive": "Evidencia de ruta incompleta", "invalid": "Evidencia no válida"},
}
FIELDS = ("model", "protocol", "config_revision")


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone")
    return parsed.astimezone(timezone.utc)


def inspect(test, route, max_age_seconds=3600):
    if not isinstance(test, dict) or not isinstance(route, dict):
        raise ValueError("objects required")
    if not isinstance(max_age_seconds, int) or max_age_seconds < 0:
        raise ValueError("max age")
    missing = [f for f in FIELDS if not isinstance(test.get(f), str) or not test.get(f)
               or not isinstance(route.get(f), str) or not route.get(f)]
    if test.get("config_state") != "saved":
        missing.append("saved_config")
    if test.get("outcome") != "usable":
        missing.append("usable_test")
    if not test.get("tested_at") or not route.get("served_at"):
        missing.append("timestamp")
    if missing:
        return {"status": "inconclusive", "missing": missing}
    tested_at, served_at = timestamp(test["tested_at"]), timestamp(route["served_at"])
    differences = [f for f in FIELDS if test[f] != route[f]]
    if differences:
        return {"status": "mismatch", "different_fields": differences}
    age = (served_at - tested_at).total_seconds()
    if age < 0:
        return {"status": "inconclusive", "missing": ["test_before_request"]}
    if age > max_age_seconds:
        return {"status": "stale", "age_seconds": int(age)}
    return {"status": "match", "age_seconds": int(age)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("demo", "check"))
    parser.add_argument("--test", type=Path)
    parser.add_argument("--route", type=Path)
    parser.add_argument("--max-age-seconds", type=int, default=3600)
    parser.add_argument("--lang", choices=WORDS, default="en")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            test = {"model": "model-a", "protocol": "responses", "config_revision": "rev-1", "config_state": "saved", "outcome": "usable", "tested_at": "2026-10-09T10:00:00Z"}
            route = {"model": "model-b", "protocol": "responses", "config_revision": "rev-1", "served_at": "2026-10-09T10:00:05Z"}
        else:
            if not args.test or not args.route:
                parser.error("check requires --test and --route")
            test = json.loads(args.test.read_text(encoding="utf-8"))
            route = json.loads(args.route.read_text(encoding="utf-8"))
        result = inspect(test, route, args.max_age_seconds)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        print(f"{WORDS[args.lang]['invalid']}: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False) if args.json else WORDS[args.lang][result["status"]])
    return 0 if args.command == "demo" or result["status"] == "match" else 2


if __name__ == "__main__":
    raise SystemExit(main())
