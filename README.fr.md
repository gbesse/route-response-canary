# Route Response Canary

## Nouveau : carte de vérité de la route

**« La carte du fournisseur était verte, mais mon agent a utilisé un autre modèle. »** Lancez `python3 route_truth_card.py demo --lang fr` pour une divergence synthétique en quelques secondes. Avec vos captures, utilisez `python3 route_truth_card.py check --test test.json --route route.json --lang fr`. Les deux objets JSON exigent `model`, `protocol` et `config_revision` ; le test exige aussi `config_state: saved`, `outcome: usable`, `tested_at`, et la route `served_at` (ISO 8601 avec fuseau). Un brouillon, un champ absent ou un test futur reste indéterminé ; un test ancien est périmé. L’outil lit les captures et ne découvre pas lui-même la route réelle.

**Projets voisins :** [Magpie #1395](https://github.com/yetone/magpie/issues/1395) signale qu’une carte verte peut tester un seul modèle et protocole ; [Magpie](https://github.com/yetone/magpie) est le routeur voisin. Aucune extension Magpie ni affiliation n’est revendiquée. L’intégration disponible est une capture JSON d’une passerelle que vous contrôlez.

Français · [English](README.md) · [Español](README.es.md)

## Nouveau : contrôler les requêtes compressées

**« Ma requête Codex fonctionne sans compression, mais la passerelle rejette gzip ou zstd. »** [Magpie #1223](https://github.com/yetone/magpie/issues/1223) rapporte ce cas sur les points d’entrée `/v1/*`. Cette sonde indépendante compare trois requêtes avec le même JSON et vérifie que chacune produit une réponse Responses SSE exploitable. Elle ne modifie pas Magpie et n’identifie pas le backend qui a répondu.

```sh
python3 -m pip install -r requirements.txt
python3 compression_probe.py demo --lang fr
python3 compression_probe.py probe --url http://127.0.0.1:8000/v1/responses --payload request.json --token-env MODEL_TOKEN --lang fr
```

La démo lance un serveur factice local : identity → utilisable, gzip/zstd → HTTP 400. `probe` envoie **trois requêtes** à un point d’entrée que vous contrôlez ; `request.json` doit contenir une requête Responses valide, généralement avec `stream: true`. Le rapport ne montre que le statut et la validité de la réponse, jamais le jeton ou le corps. Code 0 si les trois réponses sont utilisables, 2 sinon. Une erreur HTTP ne prouve pas seule sa cause ; le repli de backend reste inconnu. Python 3.11+ ; zstandard est l’unique dépendance supplémentaire.

**Projets voisins :** [Magpie #1223](https://github.com/yetone/magpie/issues/1223) fournit le reproducteur ; [Magpie](https://github.com/yetone/magpie) gère le comportement de la passerelle. Cet outil vérifie votre route de l’extérieur, sans affiliation revendiquée.

**Repérez les routes de modèle qui renvoient HTTP 200 sans réponse exploitable.**

## Projets voisins

- [Issue Magpie #1012](https://github.com/yetone/magpie/issues/1012) signale des groupes de routage qui acceptent une page HTML ou une réponse vide en HTTP 200 sans repli.
- [Magpie](https://github.com/yetone/magpie) est un routeur voisin ; cet outil indépendant vérifie un flux Responses et ne modifie pas Magpie.

## Démo en dix secondes

```sh
python3 canary.py demo --lang fr
```

La démo montre un échec HTML 200 suivi d’un événement SSE `response.completed` valide et sort avec le code 0. Pour des tentatives capturées : `python3 canary.py check --attempts attempts.json --json`. Le tableau JSON contient `status`, `content_type` et `body` pour chaque tentative observée. Le code 0 signifie qu’un repli apparaît dans cette capture ; le code 1, qu’il n’apparaît pas.

Sondez une route que vous contrôlez avec `python3 canary.py probe --url http://localhost:8000/v1/responses --payload request.json --token-env MODEL_TOKEN`. Le jeton reste dans l’environnement. La sonde ne vérifie que la réponse finale : elle ne peut pas prouver quel backend a répondu ni si un repli a eu lieu. Ce contrôle strict vise Responses SSE, pas tous les flux SSE. `canary.py` utilise Python 3.11+ et la bibliothèque standard ; `compression_probe.py` demande aussi zstandard.

Lancez `python3 -m unittest discover -s tests -q`. Licence MIT.
