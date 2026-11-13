---
description: Spécifier une nouvelle route dans le contrat openapi.yml, sans écrire de code
argument-hint: <MÉTHODE /chemin> <ce que fait la route>
---

Spécifie la route suivante dans `openapi.yml` : $ARGUMENTS

1. Lis `openapi.yml` et `app/schema.sql` pour connaître les routes, les schémas et les données existants.
2. Ajoute l'opération sous `paths`, dans le style des opérations existantes :
   - `operationId` en snake_case, `summary` en français ;
   - paramètres ou `requestBody` avec leurs types et formats (dates en ISO 8601) ;
   - une réponse par code : le succès, `422` si la route reçoit des données, chaque erreur métier
     (ex. `404`, `409`) avec un `detail` explicite, et `500` via `#/components/responses/RoomsUnavailable` ;
   - les schémas nouveaux sous `components/schemas` ; réutilise `Room`, `Calendar`, `ErrorDetail`.
3. Ne modifie que `openapi.yml` : ni code, ni tests, ni opération existante.
4. Vérifie que le fichier reste valide : `python -c "import yaml; yaml.safe_load(open('openapi.yml', encoding='utf-8'))"`.
5. Termine par :
   - un résumé de la route spécifiée (méthode, chemin, corps, codes de réponse) ;
   - la liste des choix que la demande ne dictait pas, à faire valider.

`tests/test_contract.py` échouera tant que la route n'est pas implémentée : c'est attendu.
