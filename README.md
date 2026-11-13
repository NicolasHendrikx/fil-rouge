# Salles — réservation de salles de réunion

Application fil rouge de la formation « Introduction au développement agentique avec Claude Code ».

## Installation

```bash
python -m venv .venv
# Windows : .venv\Scripts\activate   —   macOS/Linux : source .venv/bin/activate
pip install -e ".[dev]"
```

## Commandes

| Action | Commande |
| --- | --- |
| Lancer l'application | `uvicorn app.main:app --reload` puis http://127.0.0.1:8000/rooms |
| Tests | `pytest` |
| Formater | `ruff format .` |
| Linter | `ruff check .` |

Documentation interactive de l'API : http://127.0.0.1:8000/docs

La base SQLite (`salles.db`, ou `SALLES_DB_PATH`) est créée au premier démarrage à partir de
`app/schema.sql`, avec des salles et des réservations de démonstration (1er décembre 2026).

## Branches

- `main` : point de départ de la journée.
- `correction-s1` … `correction-s5` : une solution possible pour chaque séquence pratique ;
  chaque séquence part de la correction de la précédente.
