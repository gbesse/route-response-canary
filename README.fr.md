# Route Response Canary

## Nouveau : une erreur SSE amont est-elle devenue un succès ?

`python3 failure_receipt.py demo --lang fr` compare trois paires **synthétiques** : une erreur amont non standard transformée en réponse terminée vide, une erreur préservée en aval et un témoin sain. Un simple marqueur de fin ne suffit pas à établir une sortie exploitable. Ce contrôle traite la frontière signalée dans [Magpie #1933](https://github.com/yetone/magpie/issues/1933) ; il lit des captures indépendamment, sans intégration à Magpie ou Codex.

```sh
python3 failure_receipt.py check examples/failure-receipt/false-success.json --lang fr --json
```

Fournir un objet JSON avec `upstream_protocol` (`messages` ou `responses`), `upstream` et `downstream`. Chaque côté contient `status`, `content_type` et le `body` SSE enregistré. L’appariement est votre déclaration : l’outil ne corrèle pas les requêtes indépendamment. Il reconnaît les noms d’événements SSE, les données multilignes, CRLF, les erreurs explicites, les erreurs HTTP et les sorties Responses terminées (texte, refus ou appel de fonction). Une erreur amont suivie de `response.completed` en aval constitue un faux succès, même avec une sortie non vide. Une réponse terminée sans sortie exploitable échoue aussi. Une erreur suivie d’une fin réussie est contradictoire et échoue si elle est appariée à une erreur amont.

Codes de sortie : **0** erreur préservée ou témoin sain, **2** faux succès ou réponse terminée vide, **3** résultat indéterminé, **1** entrée invalide. La démo sort avec 0 si les trois verdicts attendus sont reproduits. Le JSON est limité à 4,1 Mo, chaque corps à 2 Mo. Les rapports ne contiennent que statuts, compteurs et contrôles, sans contenu des flux ni messages d’erreur. Les reprises, l’identité du backend, la causalité des requêtes et tous les types de sortie Responses ne sont pas vérifiés. Sain signifie une sortie exploitable dans ces captures, pas une réponse sémantiquement correcte. Python 3.11+, bibliothèque standard uniquement.

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
