from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

DAY = "2026-12-01"


def calendars_by_room(client, day: str = DAY) -> dict[str, dict]:
    response = client.get("/rooms/available", params={"day": day})
    assert response.status_code == 200
    return {calendar["subject"]["name"]: calendar for calendar in response.json()}


def test_fully_booked_room_is_omitted(client):
    assert "Meuse" not in calendars_by_room(client)


def test_calendar_has_room_subject_day_and_quarter_hour_granularity(client):
    calendar = calendars_by_room(client)["Ourthe"]

    assert calendar["subject"] == {"id": 1, "name": "Ourthe", "capacity": 8}
    assert calendar["day"] == DAY
    assert calendar["granularity_minutes"] == 15


def test_calendar_lists_only_free_quarter_hours(client):
    starts = [slot["start"] for slot in calendars_by_room(client)["Ourthe"]["slots"]]

    assert len(starts) == 40 - 6 - 4  # 8 h – 18 h, moins 9 h – 10 h 30 et 14 h – 15 h
    assert f"{DAY}T08:45:00" in starts
    assert f"{DAY}T09:00:00" not in starts
    assert f"{DAY}T10:30:00" in starts


def test_partially_booked_quarter_hour_is_not_free(client):
    starts = [slot["start"] for slot in calendars_by_room(client)["Vesdre"]["slots"]]

    assert f"{DAY}T10:00:00" in starts
    assert f"{DAY}T10:15:00" not in starts  # réservé de 10 h 15 à 11 h
    assert len(starts) == 37


def test_day_without_bookings_returns_every_room_fully_free(client):
    calendars = calendars_by_room(client, "2026-12-02")

    assert len(calendars) == 4
    assert all(len(calendar["slots"]) == 40 for calendar in calendars.values())


def test_invalid_day_returns_422(client):
    assert client.get("/rooms/available", params={"day": "demain"}).status_code == 422


def test_available_rooms_without_database_returns_500(db_path):
    Path(db_path).touch()

    with TestClient(app) as client:
        response = client.get("/rooms/available", params={"day": DAY})

    assert response.status_code == 500
    assert response.json() == {"detail": "rooms unavailable"}
