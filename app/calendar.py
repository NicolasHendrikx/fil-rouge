"""Objet calendar : sujet = une salle, portée = une journée, granularité = le quart d'heure."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Literal

DAY_START = time(8)
DAY_END = time(18)
GRANULARITY = timedelta(minutes=15)


@dataclass(frozen=True)
class Room:
    id: int
    name: str
    capacity: int


@dataclass(frozen=True)
class Slot:
    start: datetime
    end: datetime


@dataclass(frozen=True)
class Calendar:
    subject: Room
    day: date
    slots: list[Slot]
    granularity_minutes: int = int(GRANULARITY.total_seconds() // 60)


@dataclass(frozen=True)
class Booking:
    id: int
    room: Room
    organizer: str
    start: datetime
    end: datetime


@dataclass(frozen=True)
class BookingSummary:
    """Réservation telle qu'affichée sur l'écran de porte."""

    organizer: str
    start: datetime
    end: datetime


@dataclass(frozen=True)
class RoomStatus:
    """État d'une salle à l'instant `at` : occupée (`current`) ou libre (`next`)."""

    room: Room
    at: datetime
    state: Literal["free", "occupied"]
    current: BookingSummary | None
    next: BookingSummary | None


def slot_problem(start: datetime, end: datetime) -> str | None:
    """Pourquoi le créneau demandé est refusé, ou None s'il est valable.

    Un créneau valable est en heure locale, sur un seul jour, dans la journée, aligné sur la
    granularité.
    """
    if start.tzinfo is not None or end.tzinfo is not None:
        return "start and end must be local times without timezone"
    if end <= start:
        return "end must be after start"
    if start.date() != end.date():
        return "start and end must be on the same day"
    if start.time() < DAY_START or end.time() > DAY_END:
        return f"slot must be between {DAY_START} and {DAY_END}"
    if not (is_aligned(start) and is_aligned(end)):
        return "start and end must fall on a quarter of an hour"
    return None


def is_aligned(moment: datetime) -> bool:
    """Vrai si l'instant tombe pile sur un multiple de la granularité depuis minuit."""
    since_midnight = moment - datetime.combine(moment.date(), time())
    return since_midnight % GRANULARITY == timedelta(0)


def day_slots(day: date) -> list[Slot]:
    """Tous les quarts d'heure de la journée, de DAY_START à DAY_END."""
    slots = []
    start = datetime.combine(day, DAY_START)
    end_of_day = datetime.combine(day, DAY_END)
    while start < end_of_day:
        slots.append(Slot(start=start, end=start + GRANULARITY))
        start += GRANULARITY
    return slots


def is_free(slot: Slot, bookings: list[tuple[datetime, datetime]]) -> bool:
    """Un quart d'heure est libre si aucune réservation ne le chevauche, même en partie."""
    return all(ends_at <= slot.start or starts_at >= slot.end for starts_at, ends_at in bookings)
