"""Handlers : un par route. Ils consultent le repository et construisent la réponse."""

import sqlite3
from datetime import date

from app import repository
from app.calendar import Calendar, Room, day_slots, is_free


def list_rooms(conn: sqlite3.Connection) -> list[Room]:
    return repository.list_rooms(conn)


def list_available_rooms(conn: sqlite3.Connection, day: date) -> list[Calendar]:
    """Un calendar par salle ayant au moins un quart d'heure libre, avec ses créneaux libres."""
    bookings = repository.list_bookings_by_room(conn, day)
    calendars = []
    for room in repository.list_rooms(conn):
        room_bookings = bookings.get(room.id, [])
        free_slots = [slot for slot in day_slots(day) if is_free(slot, room_bookings)]
        if free_slots:
            calendars.append(Calendar(subject=room, day=day, slots=free_slots))
    return calendars
