# Route Response Canary

Français · [English](README.md) · [Español](README.es.md)

**Repérez les routes de modèle qui renvoient HTTP 200 sans réponse exploitable.**

## Projets voisins

- [Issue Magpie #1012](https://github.com/yetone/magpie/issues/1012) signale des groupes de routage qui acceptent une page HTML ou une réponse vide en HTTP 200 sans repli.
- [Magpie](https://github.com/yetone/magpie) est un routeur voisin ; cet outil indépendant vérifie un flux Responses et ne modifie pas Magpie.

## Démo en dix secondes

```sh
python3 canary.py demo --lang fr
```

La démo montre un échec HTML 200 suivi d’un événement SSE `response.completed` valide et sort avec le code 0. Pour des tentatives capturées : `python3 canary.py check --attempts attempts.json --json`. Le tableau JSON contient `status`, `content_type` et `body` pour chaque tentative observée. Le code 0 signifie qu’un repli apparaît dans cette capture ; le code 1, qu’il n’apparaît pas.

Sondez une route que vous contrôlez avec `python3 canary.py probe --url http://localhost:8000/v1/responses --payload request.json --token-env MODEL_TOKEN`. Le jeton reste dans l’environnement. La sonde ne vérifie que la réponse finale : elle ne peut pas prouver quel backend a répondu ni si un repli a eu lieu. Ce contrôle strict vise Responses SSE, pas tous les flux SSE. Python 3.11+, bibliothèque standard.

Lancez `python3 -m unittest discover -s tests -q`. Licence MIT.
