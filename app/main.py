"""Application « Salles » : réservation de salles de réunion."""

import os
import sqlite3
from collections.abc import Iterator
from contextlib import asynccontextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

from app import handlers
from app.calendar import Booking, Calendar, Room, RoomStatus, slot_problem
from app.handlers import Error, ErrorKind
from app.repository import Repository

SCHEMA = Path(__file__).with_name("schema.sql")


def get_db_path() -> str:
    return os.environ.get("SALLES_DB_PATH", "salles.db")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = get_db_path()
    if not Path(db_path).exists():
        conn = sqlite3.connect(db_path)
        try:
            conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        finally:
            conn.close()
    yield


def get_repository() -> Iterator[Repository]:
    # Une connexion par requête. FastAPI peut l'ouvrir dans un thread et exécuter la route dans un
    # autre : sans check_same_thread=False, des requêtes simultanées échouent en 500.
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    try:
        yield Repository(conn)
    finally:
        conn.close()


Repo = Annotated[Repository, Depends(get_repository)]


class ErrorDetail(BaseModel):
    detail: str


# Réponse d'erreur commune, déclarée pour respecter le contrat openapi.yml.
ROOMS_UNAVAILABLE = {500: {"model": ErrorDetail, "description": "rooms unavailable"}}
ROOM_NOT_FOUND = {404: {"model": ErrorDetail, "description": "room not found"}}
SLOT_ALREADY_BOOKED = {409: {"model": ErrorDetail, "description": "slot already booked"}}

# La route choisit le code HTTP et le contenu de chaque erreur retournée par un handler.
HTTP_ERRORS = {
    ErrorKind.STORAGE_UNAVAILABLE: (500, "rooms unavailable"),
    ErrorKind.ROOM_NOT_FOUND: (404, "room not found"),
    ErrorKind.SLOT_ALREADY_BOOKED: (409, "slot already booked"),
    ErrorKind.TIME_WITH_TIMEZONE: (422, "at must be a local time without timezone"),
}


def http_error(error: Error) -> HTTPException:
    status_code, detail = HTTP_ERRORS[error.kind]
    return HTTPException(status_code=status_code, detail=detail)


class BookingRequest(BaseModel):
    """Corps de POST /bookings. Un créneau refusé par slot_problem donne un 422."""

    room_id: int
    organizer: str = Field(min_length=1)
    start: datetime
    end: datetime

    @model_validator(mode="after")
    def check_slot(self) -> "BookingRequest":
        problem = slot_problem(self.start, self.end)
        if problem is not None:
            raise ValueError(problem)
        return self


app = FastAPI(title="Salles", lifespan=lifespan)

# L'écran de porte (porte/) est servi sur le port 8001 : il appelle l'API depuis le navigateur.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8001", "http://127.0.0.1:8001"],
    allow_methods=["GET"],
)


@app.get("/rooms", response_model=list[Room], responses=ROOMS_UNAVAILABLE)
def list_rooms(repository: Repo) -> list[Room]:
    result = handlers.list_rooms(repository)
    if isinstance(result, Error):
        raise http_error(result)
    return result.rooms


@app.get("/rooms/available", response_model=list[Calendar], responses=ROOMS_UNAVAILABLE)
def list_available_rooms(day: date, repository: Repo) -> list[Calendar]:
    result = handlers.list_available_rooms(repository, day)
    if isinstance(result, Error):
        raise http_error(result)
    return result.calendars


@app.get(
    "/rooms/{room_id}/status",
    response_model=RoomStatus,
    responses=ROOM_NOT_FOUND | ROOMS_UNAVAILABLE,
)
def get_room_status(room_id: int, at: datetime, repository: Repo) -> RoomStatus:
    result = handlers.get_room_status(repository, room_id, at)
    if isinstance(result, Error):
        raise http_error(result)
    return result.status


@app.post(
    "/bookings",
    status_code=201,
    response_model=Booking,
    responses=ROOM_NOT_FOUND | SLOT_ALREADY_BOOKED | ROOMS_UNAVAILABLE,
)
def create_booking(request: BookingRequest, repository: Repo) -> Booking:
    result = handlers.create_booking(
        repository, request.room_id, request.organizer, request.start, request.end
    )
    if isinstance(result, Error):
        raise http_error(result)
    return result.booking
