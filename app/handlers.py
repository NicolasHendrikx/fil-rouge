"""Handlers : un par route. Ils consultent le repository et retournent une réponse ou une erreur.

Un handler ne connaît ni sqlite3 ni FastAPI : c'est la route qui traduit son résultat en HTTP.
"""

from dataclasses import dataclass
from datetime import date
from enum import Enum

from app.calendar import Calendar, Room, day_slots, is_free
from app.repository import Repository, RepositoryError


class ErrorKind(Enum):
    STORAGE_UNAVAILABLE = "storage unavailable"


@dataclass(frozen=True)
class Error:
    kind: ErrorKind


@dataclass(frozen=True)
class RoomsResponse:
    rooms: list[Room]


@dataclass(frozen=True)
class AvailableRoomsResponse:
    calendars: list[Calendar]


def list_rooms(repository: Repository) -> RoomsResponse | Error:
    try:
        return RoomsResponse(rooms=repository.list_rooms())
    except RepositoryError:
        return Error(ErrorKind.STORAGE_UNAVAILABLE)


def list_available_rooms(repository: Repository, day: date) -> AvailableRoomsResponse | Error:
    """Un calendar par salle ayant au moins un quart d'heure libre, avec ses créneaux libres."""
    try:
        bookings = repository.list_bookings_by_room(day)
        rooms = repository.list_rooms()
    except RepositoryError:
        return Error(ErrorKind.STORAGE_UNAVAILABLE)
    calendars = []
    for room in rooms:
        room_bookings = bookings.get(room.id, [])
        free_slots = [slot for slot in day_slots(day) if is_free(slot, room_bookings)]
        if free_slots:
            calendars.append(Calendar(subject=room, day=day, slots=free_slots))
    return AvailableRoomsResponse(calendars=calendars)
