from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

DAY = "2026-12-01"


def bookings(client, room_id: int = 1, day: str = DAY):
    """Réservations d'une salle pour un jour (AAAA-MM-JJ)."""
    return client.get(f"/rooms/{room_id}/bookings", params={"day": day})


def test_list_room_bookings_returns_sorted_bookings(client):
    response = bookings(client, room_id=1)

    assert response.status_code == 200
    assert response.json() == [
        {"organizer": "Alice", "start": f"{DAY}T09:00:00", "end": f"{DAY}T10:30:00"},
        {"organizer": "Bruno", "start": f"{DAY}T14:00:00", "end": f"{DAY}T15:00:00"},
    ]


def test_list_room_bookings_without_booking_returns_empty_list(client):
    # Amblève n'a aucune réservation
    response = bookings(client, room_id=4)

    assert response.status_code == 200
    assert response.json() == []


def test_list_room_bookings_of_other_day_returns_empty_list(client):
    assert bookings(client, room_id=1, day="2026-12-02").json() == []


def test_list_room_bookings_of_unknown_room_returns_404(client):
    response = bookings(client, room_id=99)

    assert response.status_code == 404
    assert response.json() == {"detail": "room not found"}


@pytest.mark.parametrize("day", ["not-a-date", "2026-12-32", "2026-12-01T09:00:00"])
def test_list_room_bookings_with_invalid_day_returns_422(client, day):
    assert bookings(client, day=day).status_code == 422


def test_list_room_bookings_without_day_returns_422(client):
    assert client.get("/rooms/1/bookings").status_code == 422


def test_list_room_bookings_without_database_returns_500(db_path):
    Path(db_path).touch()  # fichier vide : les tables n'existent pas

    with TestClient(app) as client:
        response = bookings(client, room_id=1)

    assert response.status_code == 500
    assert response.json() == {"detail": "rooms unavailable"}
