"""Handlers : un par route. Ils consultent le repository et retournent une réponse ou une erreur.

Un handler ne connaît ni sqlite3 ni FastAPI : c'est la route qui traduit son résultat en HTTP.
"""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from app.calendar import Booking, Calendar, Room, RoomStatus, day_slots, is_free
from app.repository import Repository, RepositoryError


class ErrorKind(Enum):
    STORAGE_UNAVAILABLE = "storage unavailable"
    ROOM_NOT_FOUND = "room not found"
    SLOT_ALREADY_BOOKED = "slot already booked"
    TIME_WITH_TIMEZONE = "time with timezone"
    BOOKING_NOT_FOUND = "booking not found"


@dataclass(frozen=True)
class Error:
    kind: ErrorKind


@dataclass(frozen=True)
class RoomsResponse:
    rooms: list[Room]


@dataclass(frozen=True)
class AvailableRoomsResponse:
    calendars: list[Calendar]


@dataclass(frozen=True)
class BookingResponse:
    booking: Booking


@dataclass(frozen=True)
class DeletedBookingResponse:
    booking_id: int


@dataclass(frozen=True)
class RoomStatusResponse:
    status: RoomStatus


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


def create_booking(
    repository: Repository, room_id: int, organizer: str, start: datetime, end: datetime
) -> BookingResponse | Error:
    """Réserve la salle si elle existe et si le créneau ne chevauche aucune réservation."""
    try:
        room = repository.get_room(room_id)
        if room is None:
            return Error(ErrorKind.ROOM_NOT_FOUND)
        booking_id = repository.create_booking_if_free(room.id, organizer, start, end)
    except RepositoryError:
        return Error(ErrorKind.STORAGE_UNAVAILABLE)
    if booking_id is None:
        return Error(ErrorKind.SLOT_ALREADY_BOOKED)
    booking = Booking(id=booking_id, room=room, organizer=organizer, start=start, end=end)
    return BookingResponse(booking=booking)


def delete_booking(repository: Repository, booking_id: int) -> DeletedBookingResponse | Error:
    """Annule la réservation : son créneau redevient libre."""
    try:
        deleted = repository.delete_booking(booking_id)
    except RepositoryError:
        return Error(ErrorKind.STORAGE_UNAVAILABLE)
    if not deleted:
        return Error(ErrorKind.BOOKING_NOT_FOUND)
    return DeletedBookingResponse(booking_id=booking_id)


def get_room_status(
    repository: Repository, room_id: int, at: datetime
) -> RoomStatusResponse | Error:
    """Occupée si une réservation vérifie start <= at < end ; sinon libre, avec la suivante."""
    if at.tzinfo is not None:
        return Error(ErrorKind.TIME_WITH_TIMEZONE)
    try:
        room = repository.get_room(room_id)
        if room is None:
            return Error(ErrorKind.ROOM_NOT_FOUND)
        bookings = repository.list_room_bookings(room.id, at.date())
    except RepositoryError:
        return Error(ErrorKind.STORAGE_UNAVAILABLE)
    current = next((b for b in bookings if b.start <= at < b.end), None)
    if current is not None:
        status = RoomStatus(room=room, at=at, state="occupied", current=current, next=None)
    else:
        upcoming = next((b for b in bookings if b.start > at), None)
        status = RoomStatus(room=room, at=at, state="free", current=None, next=upcoming)
    return RoomStatusResponse(status=status)
