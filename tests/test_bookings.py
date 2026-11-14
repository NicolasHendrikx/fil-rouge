from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

DAY = "2026-12-01"


def booking_request(room_id: int = 4, start: str = "10:30", end: str = "11:00") -> dict:
    """Corps d'une demande de réservation le 1er décembre 2026 (heures au format HH:MM)."""
    return {
        "room_id": room_id,
        "organizer": "Emma",
        "start": f"{DAY}T{start}:00",
        "end": f"{DAY}T{end}:00",
    }


def book(client, room_id: int = 4, start: str = "10:30", end: str = "11:00"):
    return client.post("/bookings", json=booking_request(room_id, start, end))


def test_create_booking_returns_201_with_booked_room(client):
    response = book(client, room_id=1, start="10:30", end="11:00")

    assert response.status_code == 201
    booking = response.json()
    assert isinstance(booking["id"], int)
    assert booking["room"] == {"id": 1, "name": "Ourthe", "capacity": 8}
    assert booking["organizer"] == "Emma"
    assert booking["start"] == f"{DAY}T10:30:00"
    assert booking["end"] == f"{DAY}T11:00:00"


def test_created_booking_is_no_longer_available(client):
    book(client, room_id=4, start="11:00", end="11:30")

    calendars = client.get("/rooms/available", params={"day": DAY}).json()
    calendar = next(c for c in calendars if c["subject"]["id"] == 4)
    starts = [slot["start"] for slot in calendar["slots"]]
    assert f"{DAY}T11:00:00" not in starts
    assert f"{DAY}T11:15:00" not in starts
    assert f"{DAY}T11:30:00" in starts


def test_booking_ending_when_existing_starts_returns_201(client):
    # Alice occupe Ourthe de 9 h à 10 h 30 : des créneaux qui se touchent ne se chevauchent pas
    assert book(client, room_id=1, start="08:00", end="09:00").status_code == 201


def test_booking_starting_when_existing_ends_returns_201(client):
    assert book(client, room_id=1, start="10:30", end="11:00").status_code == 201


def test_booking_covering_whole_day_returns_201(client):
    # bornes de la journée incluses : 8 h – 18 h ; Amblève n'a aucune réservation
    assert book(client, room_id=4, start="08:00", end="18:00").status_code == 201


def test_same_slot_in_another_room_returns_201(client):
    # Ourthe est réservée de 9 h à 10 h 30, pas Amblève
    assert book(client, room_id=4, start="09:00", end="10:30").status_code == 201


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("10:00", "11:00"),  # chevauche la fin de la réservation d'Alice
        ("08:30", "09:15"),  # chevauche son début
        ("09:30", "10:00"),  # contenu dans la réservation
        ("08:00", "12:00"),  # contient la réservation
        ("09:00", "10:30"),  # exactement le même créneau
    ],
)
def test_overlapping_booking_returns_409(client, start, end):
    response = book(client, room_id=1, start=start, end=end)

    assert response.status_code == 409
    assert response.json() == {"detail": "slot already booked"}


def test_booking_same_slot_twice_returns_409(client):
    assert book(client, room_id=4, start="16:00", end="17:00").status_code == 201

    response = book(client, room_id=4, start="16:00", end="17:00")

    assert response.status_code == 409
    assert response.json() == {"detail": "slot already booked"}


def test_unknown_room_returns_404(client):
    response = book(client, room_id=99)

    assert response.status_code == 404
    assert response.json() == {"detail": "room not found"}


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("11:00", "10:30"),  # fin avant le début
        ("11:00", "11:00"),  # fin égale au début
        ("07:45", "08:30"),  # commence avant 8 h
        ("17:30", "18:15"),  # finit après 18 h
        ("10:10", "11:00"),  # début hors quart d'heure
        ("10:30", "11:05"),  # fin hors quart d'heure
    ],
)
def test_invalid_slot_returns_422(client, start, end):
    assert book(client, start=start, end=end).status_code == 422


def test_slot_spanning_two_days_returns_422(client):
    body = booking_request() | {"end": "2026-12-02T11:00:00"}

    assert client.post("/bookings", json=body).status_code == 422


def test_start_with_seconds_returns_422(client):
    body = booking_request() | {"start": f"{DAY}T10:30:30"}

    assert client.post("/bookings", json=body).status_code == 422


def test_invalid_datetime_returns_422(client):
    body = booking_request() | {"start": "demain"}

    assert client.post("/bookings", json=body).status_code == 422


def test_empty_organizer_returns_422(client):
    body = booking_request() | {"organizer": ""}

    assert client.post("/bookings", json=body).status_code == 422


@pytest.mark.parametrize("field", ["room_id", "organizer", "start", "end"])
def test_missing_field_returns_422(client, field):
    body = booking_request()
    del body[field]

    assert client.post("/bookings", json=body).status_code == 422


def test_create_booking_without_database_returns_500(db_path):
    Path(db_path).touch()  # fichier vide : les tables n'existent pas

    with TestClient(app) as client:
        response = book(client)

    assert response.status_code == 500
    assert response.json() == {"detail": "rooms unavailable"}


# DELETE /bookings/{booking_id} — réservations de démonstration : 1 Alice (Ourthe, 9 h – 10 h 30),
# 2 Bruno (Ourthe, 14 h – 15 h), 3 Chloé (Meuse, 8 h – 18 h), 4 David (Vesdre, 10 h 15 – 11 h).


def free_starts(client, room_id: int) -> list[str]:
    """Débuts des quarts d'heure libres de la salle le 1er décembre 2026 ([] si salle complète)."""
    calendars = client.get("/rooms/available", params={"day": DAY}).json()
    calendar = next((c for c in calendars if c["subject"]["id"] == room_id), None)
    return [slot["start"] for slot in calendar["slots"]] if calendar else []


def test_delete_booking_returns_204_without_body(client):
    response = client.delete("/bookings/1")

    assert response.status_code == 204
    assert response.content == b""


def test_deleted_booking_slot_becomes_free_again(client):
    assert f"{DAY}T09:00:00" not in free_starts(client, room_id=1)

    client.delete("/bookings/1")

    starts = free_starts(client, room_id=1)
    assert f"{DAY}T09:00:00" in starts
    assert f"{DAY}T10:15:00" in starts


def test_deleted_booking_slot_can_be_booked_again(client):
    client.delete("/bookings/1")

    assert book(client, room_id=1, start="09:00", end="10:30").status_code == 201


def test_delete_booking_keeps_other_bookings(client):
    client.delete("/bookings/1")

    # Bruno (14 h – 15 h, Ourthe) et Chloé (Meuse, toute la journée) restent réservés
    assert f"{DAY}T14:00:00" not in free_starts(client, room_id=1)
    assert free_starts(client, room_id=2) == []
    assert book(client, room_id=1, start="14:00", end="15:00").status_code == 409


def test_delete_booking_twice_returns_404(client):
    assert client.delete("/bookings/1").status_code == 204

    response = client.delete("/bookings/1")

    assert response.status_code == 404
    assert response.json() == {"detail": "booking not found"}


def test_delete_unknown_booking_returns_404(client):
    response = client.delete("/bookings/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "booking not found"}


def test_delete_booking_with_non_integer_id_returns_422(client):
    assert client.delete("/bookings/abc").status_code == 422


def test_delete_booking_without_database_returns_500(db_path):
    Path(db_path).touch()  # fichier vide : la table bookings n'existe pas

    with TestClient(app) as client:
        response = client.delete("/bookings/1")

    assert response.status_code == 500
    assert response.json() == {"detail": "rooms unavailable"}
