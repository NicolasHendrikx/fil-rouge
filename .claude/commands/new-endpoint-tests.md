---
description: Dériver les tests d'acceptation d'une route à partir du contrat openapi.yml, sans l'implémenter
argument-hint: <MÉTHODE /chemin>
---

Écris les tests d'acceptation de la route `$ARGUMENTS`, tels que les définit `openapi.yml`.

1. Lis l'opération `$ARGUMENTS` dans `openapi.yml` : corps, paramètres, codes de réponse et leurs
   descriptions. Si elle n'y est pas, arrête-toi et propose de lancer `/new-endpoint-spec`.
2. Lis `tests/conftest.py`, un fichier de tests existant (ex. `tests/test_rooms.py`) et `app/schema.sql` :
   les tests s'appuient sur les fixtures `client` et `db_path` et sur les données de démonstration.
3. Écris `tests/test_<ressource>.py` (ex. `tests/test_bookings.py` pour `/bookings`) :
   - au moins un test par code de réponse déclaré, y compris `422` et `500` ;
   - un test par règle écrite dans les descriptions du contrat (ex. créneaux qui se touchent) ;
   - pour un code d'erreur, vérifier le code et le `detail` exact du contrat ;
   - pour le `500`, la technique de `tests/test_rooms.py` : base vide créée avec `Path(db_path).touch()` ;
   - noms `test_<ce_qui_est_testé>_<résultat_attendu>`, valeurs tirées de `app/schema.sql`.
4. Ne touche ni à `app/` ni à `openapi.yml` : la route n'est pas encore implémentée.
5. Lance `pytest tests/test_<ressource>.py`. Les tests doivent échouer, mais seulement parce que la
   route n'existe pas (404 ou 405 reçu). Une erreur d'import ou de syntaxe est un défaut à corriger.
   Puis lance `ruff format` et `ruff check` sur ce fichier.
6. Termine par un tableau : code de réponse ou règle du contrat → test(s) qui le couvrent.
