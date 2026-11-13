"""Hook PostToolUse (Edit|Write) : `ruff format` puis `ruff check` sur le fichier Python édité.

Si `ruff check` échoue, sa sortie part sur stderr et le hook sort avec le code 2 :
Claude reçoit les erreurs de lint et doit les corriger.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_ruff(project_dir: Path) -> list[str] | None:
    """Commande ruff : celle du venv `.venv` du projet, sinon celle du PATH."""
    for candidate in (
        project_dir / ".venv" / "Scripts" / "ruff.exe",
        project_dir / ".venv" / "bin" / "ruff",
    ):
        if candidate.is_file():
            return [str(candidate)]
    found = shutil.which("ruff")
    return [found] if found else None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    file_path = (payload.get("tool_input") or {}).get("file_path") or ""
    if not file_path.endswith((".py", ".pyi")) or not Path(file_path).is_file():
        return 0

    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".")
    ruff = find_ruff(project_dir)
    if ruff is None:
        # Non bloquant (code 1) : l'outil manque, le fichier n'est pas en cause.
        print("ruff_after_edit: ruff not found (.venv or PATH)", file=sys.stderr)
        return 1

    # cwd = racine du projet, pour que ruff applique la config de pyproject.toml.
    subprocess.run([*ruff, "format", "--quiet", file_path], cwd=project_dir)
    check = subprocess.run(
        [*ruff, "check", "--no-fix", file_path],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    if check.returncode != 0:
        print(check.stdout + check.stderr, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
