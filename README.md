# Route Response Canary

[Français](README.fr.md) · English · [Español](README.es.md)

**See when a model route returns HTTP 200 but no usable answer.**

## Related projects

- [Magpie issue #1012](https://github.com/yetone/magpie/issues/1012) reports routing groups accepting HTML or empty HTTP 200 responses as success without failing over.
- [Magpie](https://github.com/yetone/magpie) is a neighboring router; this independent tool tests a Responses stream and does not modify Magpie.

## Ten-second demo

```sh
python3 canary.py demo --lang en
```

The demo shows an HTML 200 failure followed by a valid `response.completed` SSE event and exits 0. Run on saved attempts with `python3 canary.py check --attempts attempts.json --json`. The JSON array has `status`, `content_type`, and `body` for each observed attempt. Exit 0 means a fallback was observed in this capture, 1 means it was not.

Probe an endpoint you control with `python3 canary.py probe --url http://localhost:8000/v1/responses --payload request.json --token-env MODEL_TOKEN`. The token stays in the environment. Probe checks the final response only; it cannot prove which backend served it or whether fallback occurred. This is a strict Responses SSE completion check, not a general SSE parser. Python 3.11+, standard library.

Run `python3 -m unittest discover -s tests -q`. MIT license.
