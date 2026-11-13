"""Accès à la base SQLite : le seul module qui contient du SQL et qui connaît sqlite3."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime

from app.calendar import BookingSummary, Room


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

    def get_room(self, room_id: int) -> Room | None:
        with _sqlite_errors():
            row = self._conn.execute(
                "SELECT id, name, capacity FROM rooms WHERE id = ?", (room_id,)
            ).fetchone()
        return Room(id=row[0], name=row[1], capacity=row[2]) if row else None

    def create_booking_if_free(
        self, room_id: int, organizer: str, start: datetime, end: datetime
    ) -> int | None:
        """Insère la réservation si aucune autre ne la chevauche ; renvoie son id, sinon None.

        La vérification et l'insertion se font dans une même transaction verrouillée en écriture,
        pour que deux demandes simultanées ne puissent pas réserver le même créneau.
        """
        starts_at, ends_at = start.isoformat(), end.isoformat()
        with _sqlite_errors():
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                overlapping = self._conn.execute(
                    "SELECT 1 FROM bookings"
                    " WHERE room_id = ? AND starts_at < ? AND ends_at > ? LIMIT 1",
                    (room_id, ends_at, starts_at),
                ).fetchone()
                if overlapping:
                    self._conn.rollback()
                    return None
                cursor = self._conn.execute(
                    "INSERT INTO bookings (room_id, organizer, starts_at, ends_at)"
                    " VALUES (?, ?, ?, ?)",
                    (room_id, organizer, starts_at, ends_at),
                )
                self._conn.commit()
                return cursor.lastrowid
            except BaseException:
                self._conn.rollback()
                raise

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

    def list_room_bookings(self, room_id: int, day: date) -> list[BookingSummary]:
        """Réservations d'une salle pour un jour, par heure de début croissante."""
        with _sqlite_errors():
            rows = self._conn.execute(
                "SELECT organizer, starts_at, ends_at FROM bookings"
                " WHERE room_id = ? AND date(starts_at) = ? ORDER BY starts_at",
                (room_id, day.isoformat()),
            ).fetchall()
        return [
            BookingSummary(
                organizer=organizer,
                start=datetime.fromisoformat(starts_at),
                end=datetime.fromisoformat(ends_at),
            )
            for organizer, starts_at, ends_at in rows
        ]
