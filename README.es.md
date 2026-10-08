# Route Response Canary

[Français](README.fr.md) · [English](README.md) · Español

## Nuevo: comprobar solicitudes comprimidas

**« Mi solicitud de Codex funciona sin compresión, pero la pasarela rechaza gzip o zstd. »** [Magpie #1223](https://github.com/yetone/magpie/issues/1223) describe este fallo en los endpoints `/v1/*`. Esta sonda independiente compara tres solicitudes con el mismo JSON y comprueba que cada una produzca una respuesta Responses SSE utilizable. No modifica Magpie ni identifica el backend que respondió.

```sh
python3 -m pip install -r requirements.txt
python3 compression_probe.py demo --lang es
python3 compression_probe.py probe --url http://127.0.0.1:8000/v1/responses --payload request.json --token-env MODEL_TOKEN --lang es
```

La demo inicia un servidor ficticio local: identity → utilizable, gzip/zstd → HTTP 400. `probe` envía **tres solicitudes** a un endpoint bajo su control; `request.json` debe contener una solicitud Responses válida, normalmente con `stream: true`. El informe solo muestra el estado y la validez de la respuesta, nunca el token ni el cuerpo. Código 0 si las tres respuestas son utilizables, 2 en caso contrario. Un error HTTP no demuestra por sí solo su causa; el cambio de backend sigue sin conocerse. Python 3.11+; zstandard es la única dependencia adicional.

**Proyectos relacionados:** [Magpie #1223](https://github.com/yetone/magpie/issues/1223) aporta el caso reproducible; [Magpie](https://github.com/yetone/magpie) controla el comportamiento de la pasarela. Esta herramienta comprueba su ruta desde fuera, sin afiliación declarada.

**Detecte rutas de modelos que devuelven HTTP 200 sin una respuesta utilizable.**

## Proyectos relacionados

- [Issue de Magpie #1012](https://github.com/yetone/magpie/issues/1012) informa de grupos de rutas que aceptan HTML o respuestas vacías con HTTP 200 sin cambiar de proveedor.
- [Magpie](https://github.com/yetone/magpie) es un router vecino; esta herramienta independiente comprueba un flujo Responses y no modifica Magpie.

## Demo en diez segundos

```sh
python3 canary.py demo --lang es
```

La demo muestra un fallo HTML 200 seguido de un evento SSE `response.completed` válido y sale con código 0. Para intentos capturados: `python3 canary.py check --attempts attempts.json --json`. La lista JSON incluye `status`, `content_type` y `body` para cada intento observado. El código 0 indica un cambio de proveedor observado en esta captura; el código 1, que no aparece.

Sondee una ruta bajo su control con `python3 canary.py probe --url http://localhost:8000/v1/responses --payload request.json --token-env MODEL_TOKEN`. El token permanece en el entorno. La sonda solo valida la respuesta final: no puede probar qué backend respondió ni si hubo cambio. La comprobación estricta está diseñada para Responses SSE, no para cualquier SSE. `canary.py` usa Python 3.11+ y la biblioteca estándar; `compression_probe.py` también necesita zstandard.

Ejecute `python3 -m unittest discover -s tests -q`. Licencia MIT.
