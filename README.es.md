# Route Response Canary

[Français](README.fr.md) · [English](README.md) · Español

**Detecte rutas de modelos que devuelven HTTP 200 sin una respuesta utilizable.**

## Proyectos relacionados

- [Issue de Magpie #1012](https://github.com/yetone/magpie/issues/1012) informa de grupos de rutas que aceptan HTML o respuestas vacías con HTTP 200 sin cambiar de proveedor.
- [Magpie](https://github.com/yetone/magpie) es un router vecino; esta herramienta independiente comprueba un flujo Responses y no modifica Magpie.

## Demo en diez segundos

```sh
python3 canary.py demo --lang es
```

La demo muestra un fallo HTML 200 seguido de un evento SSE `response.completed` válido y sale con código 0. Para intentos capturados: `python3 canary.py check --attempts attempts.json --json`. La lista JSON incluye `status`, `content_type` y `body` para cada intento observado. El código 0 indica un cambio de proveedor observado en esta captura; el código 1, que no aparece.

Sondee una ruta bajo su control con `python3 canary.py probe --url http://localhost:8000/v1/responses --payload request.json --token-env MODEL_TOKEN`. El token permanece en el entorno. La sonda solo valida la respuesta final: no puede probar qué backend respondió ni si hubo cambio. La comprobación estricta está diseñada para Responses SSE, no para cualquier SSE. Python 3.11+, biblioteca estándar.

Ejecute `python3 -m unittest discover -s tests -q`. Licencia MIT.
