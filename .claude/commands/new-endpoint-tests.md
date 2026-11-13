---
description: Dériver les tests d'acceptation d'une route à partir du contrat openapi.yml, sans l'implémenter
argument-hint: <MÉTHODE /chemin>
---

## Consigne

Écris les tests d'acceptation de la route $ARGUMENTS, d'après `openapi.yml`.

- Où lire la route : l'opération $ARGUMENTS dans `openapi.yml` (corps, paramètres, codes de réponse et
  leurs descriptions). Si elle n'y est pas, arrête-toi et propose `/new-endpoint-spec`.
- Où écrire les tests : `tests/test_<ressource>.py` (ex. `tests/test_bookings.py` pour `/bookings`).

## Règles

- Couverture : au moins un test par code de réponse déclaré, `422` et `500` compris, et un test par
  règle écrite dans les descriptions du contrat. Pour une erreur, vérifier le code et le `detail` exact.
- Interdits : ne toucher ni à `app/` ni à `openapi.yml` ; la route n'est pas encore implémentée.
- Données : les fixtures `client` et `db_path` de `tests/conftest.py` et les données de `app/schema.sql`.
  Pour le `500`, la technique de `tests/test_rooms.py` (base vide avec `Path(db_path).touch()`).

## Validation

- Lance `pytest tests/test_<ressource>.py` : les tests doivent échouer, mais seulement parce que la route
  n'existe pas (404 ou 405 reçu). Une erreur d'import ou de syntaxe est un défaut à corriger.
  Puis `ruff format` et `ruff check` sur ce fichier.
- Termine par un tableau : code de réponse ou règle du contrat → test(s) qui le couvrent.
