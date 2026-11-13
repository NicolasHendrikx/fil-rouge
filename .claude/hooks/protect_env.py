"""Hook PreToolUse (Read|Edit|Write) : bloque tout accès aux fichiers `.env`.

Bloqués : `.env` et ses variantes (`.env.local`, `.env.production`...).
Autorisé : `.env.example`, qui ne contient pas de secrets.
Code de sortie 2 = appel refusé, la raison (stderr) est renvoyée à Claude.
"""

import json
import sys
from pathlib import PurePath

ALLOWED = {".env.example"}


def is_protected(file_path: str) -> bool:
    """Vrai si le chemin désigne un fichier `.env` (ou une variante) non autorisé."""
    name = PurePath(file_path.replace("\\", "/")).name.lower()
    if name in ALLOWED:
        return False
    return name == ".env" or name.startswith(".env.")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Entrée illisible : on ne bloque pas, ce n'est pas le rôle de ce hook.
        return 0
    file_path = (payload.get("tool_input") or {}).get("file_path") or ""
    if not is_protected(file_path):
        return 0
    tool = payload.get("tool_name", "this tool")
    print(
        f"Access denied: {tool} on '{file_path}' is blocked by the project's "
        "protect_env hook. .env files hold secrets and must never be read or "
        "modified. Use .env.example to learn which variables exist, or ask the "
        "user for the value you need.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
