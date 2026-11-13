"""Objet calendar : sujet = une salle, portée = une journée, granularité = le quart d'heure."""

from datetime import date, datetime, time, timedelta

from pydantic import BaseModel

DAY_START = time(8)
DAY_END = time(18)
GRANULARITY = timedelta(minutes=15)


class Room(BaseModel):
    id: int
    name: str
    capacity: int


class Slot(BaseModel):
    start: datetime
    end: datetime


class Calendar(BaseModel):
    subject: Room
    day: date
    granularity_minutes: int = int(GRANULARITY.total_seconds() // 60)
    slots: list[Slot]


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
