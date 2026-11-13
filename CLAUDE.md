# Salles — réservation de salles de réunion

API FastAPI + SQLite. Une solution possible de la séquence S1.

## Commandes

- Installer : `pip install -e ".[dev]"` dans le venv `.venv`
- Lancer : `uvicorn app.main:app --reload` (http://127.0.0.1:8000, API sur `/docs`)
- Tests : `pytest` — à lancer après toute modification de code
- Qualité : `ruff format .` puis `ruff check .` — doivent passer avant de rendre la main

## Architecture

Une requête traverse trois couches, toujours dans cet ordre : route → handler → repository.

- `app/main.py` : les routes. Une route ne fait que trois choses : lire ses paramètres, appeler
  son handler, convertir `sqlite3.Error` en HTTP 500 `{"detail": "rooms unavailable"}`.
- `app/handlers.py` : un handler par route, du même nom que la fonction de route. Le handler
  obtient les données en appelant le repository, jamais en ouvrant la base lui-même.
- `app/repository.py` : le SEUL module qui contient du SQL. Requêtes paramétrées (`?`).
- `app/calendar.py` : l'objet `Calendar` renvoyé par toute route qui parle de disponibilités.
  Son sujet est une salle (`subject`), sa portée une journée (`day`), sa granularité le quart
  d'heure (`granularity_minutes: 15`) ; `slots` liste des créneaux `{start, end}` de 15 min.
  Les heures de la journée (8 h – 18 h) sont `DAY_START` et `DAY_END` : ne pas les recopier ailleurs.
- `app/schema.sql` : schéma et données de démonstration, chargés au premier démarrage.
- `openapi.yml` : le contrat de l'API. Une nouvelle route y est décrite d'abord, puis implémentée.
  `tests/test_contract.py` exige que l'app expose exactement ses routes et ses codes de réponse :
  une route déclare ses codes d'erreur avec `responses=` (ex. `ROOMS_UNAVAILABLE`).

## Conventions

- Code et noms en anglais ; commentaires, docstrings et messages en français.
- Dates en ISO 8601 (`AAAA-MM-JJ`, `AAAA-MM-JJTHH:MM:SS`), heure locale, sans fuseau.
- Toute nouvelle route a un test par code de réponse (200, 422, 500).

## Interdits

- Pas de SQL ni de `sqlite3.connect` en dehors de `repository.py` et de `main.py` (connexion).
- Ne pas modifier les données de démonstration de `app/schema.sql` : les tests en dépendent.
- Pas de nouvelle dépendance dans `pyproject.toml` sans le demander d'abord.
- Ne jamais lire ni modifier `.env`.
