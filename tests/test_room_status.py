from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

DAY = "2026-12-01"
OURTHE = {"id": 1, "name": "Ourthe", "capacity": 8}


def status(client, room_id: int = 1, at: str = "09:30"):
    """État d'une salle le 1er décembre 2026 à l'heure `at` (HH:MM)."""
    return client.get(f"/rooms/{room_id}/status", params={"at": f"{DAY}T{at}:00"})


def summary(organizer: str, start: str, end: str) -> dict:
    """Réservation attendue le 1er décembre 2026 (heures au format HH:MM)."""
    return {"organizer": organizer, "start": f"{DAY}T{start}:00", "end": f"{DAY}T{end}:00"}


ALICE = summary("Alice", "09:00", "10:30")
BRUNO = summary("Bruno", "14:00", "15:00")


def test_room_status_during_booking_returns_occupied(client):
    response = status(client, room_id=1, at="09:30")

    assert response.status_code == 200
    assert response.json() == {
        "room": OURTHE,
        "at": f"{DAY}T09:30:00",
        "state": "occupied",
        "current": ALICE,
        "next": None,
    }


def test_room_status_at_booking_start_returns_occupied(client):
    # start <= at : à l'instant du début, la réservation est en cours
    body = status(client, room_id=1, at="09:00").json()

    assert body["state"] == "occupied"
    assert body["current"] == ALICE


def test_room_status_at_booking_end_returns_free(client):
    # at < end : à l'instant de sa fin, la salle est libre
    body = status(client, room_id=1, at="10:30").json()

    assert body["state"] == "free"
    assert body["current"] is None
    assert body["next"] == BRUNO


def test_room_status_when_occupied_has_no_next(client):
    # Alice occupe Ourthe ; Bruno vient après, mais une salle occupée n'annonce pas de next
    body = status(client, room_id=1, at="09:15").json()

    assert body["state"] == "occupied"
    assert body["next"] is None


def test_room_status_when_free_returns_first_next_booking(client):
    # avant 9 h, Alice et Bruno sont à venir : next est la première
    response = status(client, room_id=1, at="08:00")

    assert response.status_code == 200
    assert response.json() == {
        "room": OURTHE,
        "at": f"{DAY}T08:00:00",
        "state": "free",
        "current": None,
        "next": ALICE,
    }


def test_room_status_after_last_booking_has_no_next(client):
    body = status(client, room_id=1, at="15:00").json()

    assert body["state"] == "free"
    assert body["current"] is None
    assert body["next"] is None


def test_room_status_next_is_limited_to_same_day(client):
    # la veille au soir, la réservation d'Alice du lendemain n'est pas « next »
    body = client.get("/rooms/1/status", params={"at": "2026-11-30T20:00:00"}).json()

    assert body["state"] == "free"
    assert body["next"] is None


def test_room_status_without_any_booking_returns_free(client):
    # Amblève n'a aucune réservation
    body = status(client, room_id=4, at="10:00").json()

    assert body["room"] == {"id": 4, "name": "Amblève", "capacity": 2}
    assert body["state"] == "free"
    assert body["current"] is None
    assert body["next"] is None


@pytest.mark.parametrize(("at", "state"), [("17:45", "occupied"), ("18:00", "free")])
def test_room_status_of_full_day_booking_ends_at_18(client, at, state):
    # Chloé occupe Meuse de 8 h à 18 h
    assert status(client, room_id=2, at=at).json()["state"] == state


def test_room_status_of_unknown_room_returns_404(client):
    response = status(client, room_id=99)

    assert response.status_code == 404
    assert response.json() == {"detail": "room not found"}


def test_room_status_without_at_returns_422(client):
    assert client.get("/rooms/1/status").status_code == 422


@pytest.mark.parametrize("at", ["not-a-date", "2026-12-32T09:00:00", "09:30"])
def test_room_status_with_invalid_at_returns_422(client, at):
    assert client.get("/rooms/1/status", params={"at": at}).status_code == 422


def test_room_status_with_non_integer_room_id_returns_422(client):
    response = client.get("/rooms/ourthe/status", params={"at": f"{DAY}T09:30:00"})

    assert response.status_code == 422


def test_room_status_without_database_returns_500(db_path):
    Path(db_path).touch()  # fichier vide : les tables n'existent pas

    with TestClient(app) as client:
        response = status(client, room_id=1)

    assert response.status_code == 500
    assert response.json() == {"detail": "rooms unavailable"}
