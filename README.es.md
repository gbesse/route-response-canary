# Route Response Canary

## Nuevo: ¿un error SSE de origen se convirtió en éxito?

`python3 failure_receipt.py demo --lang es` compara tres pares **sintéticos**: un error de origen no estándar convertido en respuesta completada vacía, un error conservado y un control correcto. Un marcador de finalización solo no demuestra una salida utilizable. El control aborda el límite descrito en [Magpie #1933](https://github.com/yetone/magpie/issues/1933); lee capturas de forma independiente, sin integración con Magpie ni Codex.

```sh
python3 failure_receipt.py check examples/failure-receipt/false-success.json --lang es --json
```

Aportar un objeto JSON con `upstream_protocol` (`messages` o `responses`), `upstream` y `downstream`. Cada lado contiene `status`, `content_type` y el `body` SSE guardado. El emparejamiento es una declaración suya: la herramienta no correlaciona las solicitudes de forma independiente. Reconoce nombres de eventos SSE, datos multilínea, CRLF, errores explícitos, errores HTTP y salidas Responses completadas (texto, rechazo o llamada a función). Un error de origen seguido de `response.completed` en destino es un falso éxito, incluso con salida no vacía. Una respuesta completada sin salida utilizable también falla. Un error seguido de finalización exitosa es contradictorio y falla cuando se empareja con un error de origen.

Códigos de salida: **0** error conservado o control correcto, **2** falso éxito o respuesta completada vacía, **3** resultado indeterminado, **1** entrada no válida. La demo sale con 0 si reproduce los tres veredictos previstos. El JSON se limita a 4,1 MB y cada cuerpo a 2 MB. Los informes solo contienen estados, contadores y controles, sin contenido de los flujos ni mensajes de error. No se verifican los reintentos, la identidad del backend, la causalidad de las solicitudes ni todos los tipos de salida Responses. Correcto significa salida utilizable en estas capturas, no respuesta semánticamente correcta. Python 3.11+, solo biblioteca estándar.

## Nuevo: tarjeta de veracidad de la ruta

**« La tarjeta del proveedor estaba verde, pero mi agente utilizó otro modelo. »** Ejecute `python3 route_truth_card.py demo --lang es` para ver una discrepancia sintética en segundos. Con sus capturas, use `python3 route_truth_card.py check --test test.json --route route.json --lang es`. Ambos objetos JSON requieren `model`, `protocol` y `config_revision`; la prueba también requiere `config_state: saved`, `outcome: usable`, `tested_at`, y la ruta `served_at` (ISO 8601 con zona horaria). Un borrador, un campo ausente o una prueba futura deja el resultado indeterminado; una prueba antigua queda obsoleta. La herramienta solo lee capturas y no descubre por sí misma la ruta real.

**Proyectos relacionados:** [Magpie #1395](https://github.com/yetone/magpie/issues/1395) informa de una tarjeta saludable que solo comprueba un modelo y protocolo; [Magpie](https://github.com/yetone/magpie) es el enrutador vecino. No existe un complemento Magpie ni afiliación. La integración disponible es una captura JSON de una pasarela que usted controla.

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
