#!/usr/bin/env python3
"""Compare saved upstream/downstream SSE captures without printing their contents."""

import argparse
import json
import sys
from pathlib import Path

TEXT = {
    "en": {
        "title": "SSE failure preservation receipt",
        "invalid": "Invalid or oversized capture",
        "false_success": "Upstream failure became downstream success",
        "preserved": "Upstream failure remains a downstream failure",
        "healthy": "Both captured streams completed with usable downstream output",
        "inconclusive": "The captures do not establish failure preservation",
        "empty": "Completed response has no usable output",
        "file": "Paired capture JSON file",
        "scope": "Saved captures only; pairing is declared by the caller. Retries and backend identity are not verified.",
    },
    "fr": {
        "title": "Reçu de préservation des erreurs SSE",
        "invalid": "Capture invalide ou trop volumineuse",
        "false_success": "Une erreur amont est devenue un succès aval",
        "preserved": "L’erreur amont reste une erreur aval",
        "healthy": "Les deux flux capturés sont complets, avec une sortie aval exploitable",
        "inconclusive": "Les captures ne démontrent pas la préservation de l’erreur",
        "empty": "La réponse terminée ne contient aucune sortie exploitable",
        "file": "Fichier JSON des captures appariées",
        "scope": "Captures enregistrées uniquement ; l’appariement est déclaré par l’appelant. Les reprises et l’identité du backend ne sont pas vérifiées.",
    },
    "es": {
        "title": "Recibo de conservación de errores SSE",
        "invalid": "Captura no válida o demasiado grande",
        "false_success": "Un error de origen se convirtió en éxito de destino",
        "preserved": "El error de origen sigue siendo un error de destino",
        "healthy": "Ambos flujos capturados terminaron, con una salida de destino utilizable",
        "inconclusive": "Las capturas no demuestran la conservación del error",
        "empty": "La respuesta terminada no tiene una salida utilizable",
        "file": "Archivo JSON de capturas emparejadas",
        "scope": "Solo capturas guardadas; quien llama declara el emparejamiento. No se verifican los reintentos ni la identidad del backend.",
    },
}


class CaptureError(ValueError):
    pass


def events(body):
    """Dispatch SSE data on blank lines, including multiline data and event names."""
    if not isinstance(body, str) or len(body.encode("utf-8")) > 2_000_000:
        raise CaptureError()
    rows, data, name = [], [], ""
    for line in (
        body.removeprefix("\ufeff")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .split("\n")[:-1]
    ):
        if not line:
            if data:
                raw = "\n".join(data)
                try:
                    payload = json.loads(raw) if raw != "[DONE]" else None
                    valid = payload is None or isinstance(payload, dict)
                    if not valid:
                        payload = None
                except (ValueError, RecursionError):
                    payload, valid = None, False
                rows.append({"event": name, "payload": payload, "valid": valid})
            data, name = [], ""
        elif not line.startswith(":"):
            field, _, value = line.partition(":")
            value = value.removeprefix(" ")
            if field == "data":
                data.append(value)
            elif field == "event":
                name = value
    return rows


def output_usable(output):
    if not isinstance(output, list):
        return False
    for item in output:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "function_call" and all(
            isinstance(item.get(k), str) and item[k].strip()
            for k in ("name", "arguments")
        ):
            return True
        content = item.get("content", [])
        if item.get("type") == "message" and isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    key = {"output_text": "text", "refusal": "refusal"}.get(
                        part.get("type")
                    )
                    if key and isinstance(part.get(key), str) and part[key].strip():
                        return True
    return False


def inspect(capture, protocol):
    if not isinstance(capture, dict) or protocol not in ("messages", "responses"):
        raise CaptureError()
    status, content_type, body = (
        capture.get(k) for k in ("status", "content_type", "body")
    )
    if (
        not isinstance(status, int)
        or isinstance(status, bool)
        or not 100 <= status <= 599
    ):
        raise CaptureError()
    if not isinstance(content_type, str) or not isinstance(body, str):
        raise CaptureError()
    rows = events(body)
    kinds = [(r["payload"] or {}).get("type", r["event"]) for r in rows]
    explicit_error = status >= 400 or any(
        r["event"] == "error" or k in ("error", "response.failed")
        for r, k in zip(rows, kinds)
    )
    malformed = any(not r["valid"] for r in rows)
    completed, usable = False, False
    response_errors = False
    for row, kind in zip(rows, kinds):
        payload = row["payload"] or {}
        if protocol == "messages" and kind == "message_stop":
            completed = True
        if protocol == "responses" and kind == "response.completed":
            completed = True
            response = payload.get("response")
            if isinstance(response, dict):
                response_errors |= (
                    bool(response.get("error")) or response.get("status") == "failed"
                )
                usable |= response.get("status") == "completed" and output_usable(
                    response.get("output")
                )
    explicit_error |= response_errors
    sse = content_type.split(";", 1)[0].strip().lower() == "text/event-stream"
    ok = status == 200 and sse and completed and not explicit_error and not malformed
    return {
        "status": status,
        "event_count": len(rows),
        "explicit_failure": explicit_error,
        "claimed_completion": completed,
        "malformed_events": malformed,
        "usable_output": usable if protocol == "responses" else None,
        "completed_stream": ok,
    }


def analyze(pair, lang="en"):
    if not isinstance(pair, dict):
        raise CaptureError()
    upstream = inspect(pair.get("upstream"), pair.get("upstream_protocol", "messages"))
    downstream = inspect(pair.get("downstream"), "responses")
    if upstream["explicit_failure"] and downstream["claimed_completion"]:
        verdict = "false_success"
    elif upstream["explicit_failure"] and downstream["explicit_failure"]:
        verdict = "preserved"
    elif (
        upstream["completed_stream"]
        and downstream["completed_stream"]
        and downstream["usable_output"]
    ):
        verdict = "healthy"
    else:
        verdict = "inconclusive"
    empty = downstream["claimed_completion"] and not downstream["usable_output"]
    return {
        "verdict": verdict,
        "message": TEXT[lang][verdict],
        "upstream": upstream,
        "downstream": downstream,
        "empty_completion": empty,
        "empty_message": TEXT[lang]["empty"] if empty else None,
        "scope": TEXT[lang]["scope"],
    }


def read_pair(path):
    if path.stat().st_size > 4_100_000:
        raise CaptureError()
    return json.loads(path.read_text(encoding="utf-8"))


HELP = {
    "en": {
        "help": "Show help and exit",
        "usage": "usage",
        "positional": "positional arguments",
        "options": "options",
        "command": "Run a synthetic demo or check saved captures",
        "json": "Print the structured report",
        "language": "Report language",
    },
    "fr": {
        "help": "Afficher l’aide et quitter",
        "usage": "utilisation",
        "positional": "arguments positionnels",
        "options": "options",
        "command": "Exécuter une démo synthétique ou contrôler des captures",
        "json": "Afficher le rapport structuré",
        "language": "Langue du rapport",
    },
    "es": {
        "help": "Mostrar ayuda y salir",
        "usage": "uso",
        "positional": "argumentos posicionales",
        "options": "opciones",
        "command": "Ejecutar una demo sintética o comprobar capturas",
        "json": "Mostrar el informe estructurado",
        "language": "Idioma del informe",
    },
}


def report_language(argv):
    lang = "en"
    for i, value in enumerate(argv):
        if value == "--lang" and i + 1 < len(argv):
            lang = argv[i + 1]
        elif value.startswith("--lang="):
            lang = value.split("=", 1)[1]
    return lang if lang in TEXT else "en"


class Parser(argparse.ArgumentParser):
    def format_help(self):
        return super().format_help().replace("usage:", self.words["usage"] + ":", 1)

    def error(self, message):
        raise CaptureError()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    lang = report_language(argv)
    words = TEXT[lang]
    parser = Parser(description=words["title"], add_help=False)
    parser.words = HELP[lang]
    parser._action_groups[0].title = HELP[lang]["positional"]
    parser._action_groups[1].title = HELP[lang]["options"]
    parser.add_argument("-h", "--help", action="help", help=HELP[lang]["help"])
    parser.add_argument(
        "command", choices=("demo", "check"), help=HELP[lang]["command"]
    )
    parser.add_argument("capture", nargs="?", type=Path, help=words["file"])
    parser.add_argument(
        "--lang", choices=TEXT, default=lang, help=HELP[lang]["language"]
    )
    parser.add_argument("--json", action="store_true", help=HELP[lang]["json"])
    try:
        args = parser.parse_args(argv)
        if args.command == "demo":
            root = Path(__file__).parent / "examples" / "failure-receipt"
            reports = [
                analyze(read_pair(root / name), args.lang)
                for name in ("false-success.json", "preserved.json", "healthy.json")
            ]
            ok = [r["verdict"] for r in reports] == [
                "false_success",
                "preserved",
                "healthy",
            ]
        else:
            if args.capture is None:
                raise CaptureError()
            reports = [analyze(read_pair(args.capture), args.lang)]
            ok = (
                reports[0]["verdict"] in ("preserved", "healthy")
                and not reports[0]["empty_completion"]
            )
        if args.json:
            print(
                json.dumps(
                    {"synthetic_demo": args.command == "demo", "reports": reports},
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(words["title"])
            for report in reports:
                print(report["message"])
                if report["empty_message"]:
                    print(report["empty_message"])
            print(words["scope"])
        if args.command == "demo":
            return 0 if ok else 1
        return (
            0
            if ok
            else 2
            if reports[0]["verdict"] == "false_success"
            or reports[0]["empty_completion"]
            else 3
        )
    except (OSError, UnicodeError, ValueError, TypeError, RecursionError):
        print(words["invalid"], file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
