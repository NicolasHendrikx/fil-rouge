import pytest
from fastapi.testclient import TestClient
from starlette.routing import Match

from app.main import app

# Couverture de la spécification : chaque réponse obtenue par un test est notée
# (méthode, chemin du contrat, code). tests/test_contract.py compare ces codes à openapi.yml.
app.state.exercised = set()


class RecordExercisedCodes:
    """Middleware ASGI de test : note le code de chaque réponse, sans rien changer d'autre."""

    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    async def __call__(self, scope, receive, send):
        async def send_and_record(message):
            if message["type"] == "http.response.start":
                for route in app.routes:
                    if route.matches(scope)[0] == Match.FULL:
                        code = str(message["status"])
                        app.state.exercised.add((scope["method"], route.path, code))
                        break
            await send(message)

        if scope["type"] != "http":
            return await self.asgi_app(scope, receive, send)
        await self.asgi_app(scope, receive, send_and_record)


app.add_middleware(RecordExercisedCodes)


def pytest_collection_modifyitems(items):
    """La couverture de la spécification se mesure en dernier, une fois tous les tests passés."""
    items.sort(key=lambda item: item.get_closest_marker("spec_coverage") is not None)


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
