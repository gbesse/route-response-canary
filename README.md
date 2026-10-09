# Route Response Canary

## New: route truth card

**“The provider card was green, but my agent used another model.”** Run `python3 route_truth_card.py demo --lang en` for a five-second synthetic mismatch. With saved evidence, use `python3 route_truth_card.py check --test test.json --route route.json --lang en`. Both JSON objects need `model`, `protocol`, and `config_revision`; the test also needs `config_state: saved`, `outcome: usable`, `tested_at`, while the route needs `served_at` (ISO 8601 with timezone). A draft, missing route field, or future test is inconclusive; an old matching test is stale. This tool reads captures only and cannot discover the actual route itself.

**Related projects:** [Magpie #1395](https://github.com/yetone/magpie/issues/1395) reports one model and protocol being tested while the card appears healthy; [Magpie](https://github.com/yetone/magpie) is the neighboring router. There is no Magpie plugin or affiliation. The integration is a JSON capture exported from a gateway you control.

[Français](README.fr.md) · English · [Español](README.es.md)

## New: check compressed requests

**“My Codex request works uncompressed, but the gateway rejects gzip or zstd.”** [Magpie #1223](https://github.com/yetone/magpie/issues/1223) reports this exact failure on standard `/v1/*` endpoints. This independent probe compares three requests with the same JSON payload and checks whether each returns a usable Responses SSE completion. It does not modify Magpie or identify the backend that served a request.

```sh
python3 -m pip install -r requirements.txt
python3 compression_probe.py demo --lang en
python3 compression_probe.py probe --url http://127.0.0.1:8000/v1/responses --payload request.json --token-env MODEL_TOKEN --lang en
```

The demo starts a local mock and shows identity → usable, gzip/zstd → HTTP 400. `probe` sends **three requests** to an endpoint you control; `request.json` must be a valid Responses payload, usually with `stream: true`. It prints only status and completion checks, never a token or response body. Exit 0 means all three are usable, 2 means at least one is not. An HTTP error alone cannot prove its cause, and backend fallback remains unknown. Python 3.11+; zstandard is the only extra dependency.

**Related projects:** [Magpie #1223](https://github.com/yetone/magpie/issues/1223) supplies the compressed-body reproducer; [Magpie](https://github.com/yetone/magpie) owns the gateway behavior. This tool provides a black-box check for your route, with no claimed affiliation.

**See when a model route returns HTTP 200 but no usable answer.**

## Related projects

- [Magpie issue #1012](https://github.com/yetone/magpie/issues/1012) reports routing groups accepting HTML or empty HTTP 200 responses as success without failing over.
- [Magpie](https://github.com/yetone/magpie) is a neighboring router; this independent tool tests a Responses stream and does not modify Magpie.

## Ten-second demo

```sh
python3 canary.py demo --lang en
```

The demo shows an HTML 200 failure followed by a valid `response.completed` SSE event and exits 0. Run on saved attempts with `python3 canary.py check --attempts attempts.json --json`. The JSON array has `status`, `content_type`, and `body` for each observed attempt. Exit 0 means a fallback was observed in this capture, 1 means it was not.

Probe an endpoint you control with `python3 canary.py probe --url http://localhost:8000/v1/responses --payload request.json --token-env MODEL_TOKEN`. The token stays in the environment. Probe checks the final response only; it cannot prove which backend served it or whether fallback occurred. This is a strict Responses SSE completion check, not a general SSE parser. `canary.py` uses Python 3.11+ and the standard library; `compression_probe.py` also needs zstandard.

Run `python3 -m unittest discover -s tests -q`. MIT license.
