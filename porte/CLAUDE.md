# Écran de porte

Page affichée sur un écran portrait (1080 × 1920) fixé à côté de la porte d'une salle. Elle montre l'état
de la salle à l'instant T : libre ou occupée, par qui et jusqu'à quand, ou la prochaine réservation.
Elle dépend de l'API Salles (`../app`), route `GET /rooms/{room_id}/status?at=…`.

## Commandes

- API : à la racine du dépôt, `uvicorn app.main:app --port 8000`.
- Écran : `python -m http.server 8001 --directory porte`, puis
  http://localhost:8001/?room=1&at=2026-12-01T09:30 (`at` force l'instant ; sans lui, l'heure courante).
- Vérifier l'affichage : avec le serveur MCP Playwright, à la taille de l'écran (1080 × 1920).

## Conventions

- HTML, CSS et JavaScript sans framework ni étape de build : `index.html`, `porte.css`, `porte.js`.
- Textes affichés en français ; code et noms en anglais ; commentaires en français.
- Heures locales sans fuseau, comme l'API (`AAAA-MM-JJTHH:MM:SS`).
- Ne pas modifier l'API depuis ce dossier : une route manquante se spécifie d'abord dans `../openapi.yml`.
