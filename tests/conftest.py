import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def db_path(tmp_path, monkeypatch) -> str:
    """Chemin d'une base SQLite temporaire, propre à chaque test."""
    path = str(tmp_path / "test.db")
    monkeypatch.setenv("SALLES_DB_PATH", path)
    return path


@pytest.fixture
def client(db_path):
    """Client HTTP ; la base est créée avec les données de démonstration au démarrage."""
    with TestClient(app) as test_client:
        yield test_client
