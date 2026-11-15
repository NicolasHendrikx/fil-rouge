"""Accès à la base SQLite : le seul module qui contient du SQL et qui connaît sqlite3."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime

from app.calendar import Room


class RepositoryError(Exception):
    """La base est inaccessible ou invalide. Hors de ce module, elle remplace sqlite3.Error."""


@contextmanager
def _sqlite_errors() -> Iterator[None]:
    try:
        yield
    except sqlite3.Error as error:
        raise RepositoryError(str(error)) from error


class Repository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def list_rooms(self) -> list[Room]:
        with _sqlite_errors():
            rows = self._conn.execute("SELECT id, name, capacity FROM rooms ORDER BY id").fetchall()
        return [Room(id=row[0], name=row[1], capacity=row[2]) for row in rows]

    def list_bookings_by_room(self, day: date) -> dict[int, list[tuple[datetime, datetime]]]:
        """Réservations du jour, regroupées par salle : {room_id: [(début, fin), ...]}."""
        with _sqlite_errors():
            rows = self._conn.execute(
                "SELECT room_id, starts_at, ends_at FROM bookings WHERE date(starts_at) = ?",
                (day.isoformat(),),
            ).fetchall()
        bookings: dict[int, list[tuple[datetime, datetime]]] = {}
        for room_id, starts_at, ends_at in rows:
            bookings.setdefault(room_id, []).append(
                (datetime.fromisoformat(starts_at), datetime.fromisoformat(ends_at))
            )
        return bookings
