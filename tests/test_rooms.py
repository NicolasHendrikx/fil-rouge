from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_list_rooms_returns_seeded_rooms(client):
    response = client.get("/rooms")

    assert response.status_code == 200
    assert [room["name"] for room in response.json()] == ["Ourthe", "Meuse", "Vesdre", "Amblève"]


def test_rooms_have_id_name_and_capacity(client):
    room = client.get("/rooms").json()[0]

    assert room == {"id": 1, "name": "Ourthe", "capacity": 8}


def test_list_rooms_without_database_returns_500(db_path):
    Path(db_path).touch()  # fichier vide : la table rooms n'existe pas

    with TestClient(app) as client:
        response = client.get("/rooms")

    assert response.status_code == 500
    assert response.json() == {"detail": "rooms unavailable"}


def test_simultaneous_requests_all_succeed(client):
    """Non-régression : des requêtes simultanées ne doivent pas échouer en 500 (connexion SQLite
    ouverte dans un thread et utilisée dans un autre, corrigé dans get_conn)."""
    with ThreadPoolExecutor(max_workers=16) as pool:
        codes = list(pool.map(lambda _: client.get("/rooms").status_code, range(80)))

    assert codes == [200] * 80
