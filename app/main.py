"""Application « Salles » : réservation de salles de réunion."""

import os
import sqlite3
from collections.abc import Iterator
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from app import handlers
from app.calendar import Calendar, Room
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

# La route choisit le code HTTP et le contenu de chaque erreur retournée par un handler.
HTTP_ERRORS = {
    ErrorKind.STORAGE_UNAVAILABLE: (500, "rooms unavailable"),
}


def http_error(error: Error) -> HTTPException:
    status_code, detail = HTTP_ERRORS[error.kind]
    return HTTPException(status_code=status_code, detail=detail)


app = FastAPI(title="Salles", lifespan=lifespan)


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
