"""Accès à la base SQLite : le seul module qui contient du SQL."""

import sqlite3
from datetime import date, datetime

from app.calendar import Room


def list_rooms(conn: sqlite3.Connection) -> list[Room]:
    rows = conn.execute("SELECT id, name, capacity FROM rooms ORDER BY id").fetchall()
    return [Room(id=row[0], name=row[1], capacity=row[2]) for row in rows]


def list_bookings_by_room(
    conn: sqlite3.Connection, day: date
) -> dict[int, list[tuple[datetime, datetime]]]:
    """Réservations du jour, regroupées par salle : {room_id: [(début, fin), ...]}."""
    rows = conn.execute(
        "SELECT room_id, starts_at, ends_at FROM bookings WHERE date(starts_at) = ?",
        (day.isoformat(),),
    ).fetchall()
    bookings: dict[int, list[tuple[datetime, datetime]]] = {}
    for room_id, starts_at, ends_at in rows:
        bookings.setdefault(room_id, []).append(
            (datetime.fromisoformat(starts_at), datetime.fromisoformat(ends_at))
        )
    return bookings
