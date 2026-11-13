---
paths:
  - "tests/**"
---
# Conventions de tests

- Un fichier de tests par ressource de l'API : `tests/test_<ressource>.py`.
- Nom d'un test : `test_<ce_qui_est_testé>_<résultat_attendu>`, par exemple `test_list_rooms_returns_seeded_rooms`.
- Utiliser les fixtures de `conftest.py` (`db_path`, `client`) : chaque test a sa base SQLite temporaire.
- Les données de démonstration de `app/schema.sql` servent de jeu de test : ne pas les dupliquer dans les tests.
- Tester chaque code de réponse d'une route, erreurs comprises (500 avec son `detail`).
