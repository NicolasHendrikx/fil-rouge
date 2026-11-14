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

SCHEMA = Path(__file__).with_name("schema.sql")


def get_db_path() -> str:
    return os.environ.get("SALLES_DB_PATH", "salles.db")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = get_db_path()
    if not Path(db_path).exists():
        with sqlite3.connect(db_path) as conn:
            conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    yield


def get_conn() -> Iterator[sqlite3.Connection]:
    # Une connexion par requête. FastAPI peut l'ouvrir dans un thread et exécuter la route dans un
    # autre : sans check_same_thread=False, des requêtes simultanées échouent en 500.
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()


Conn = Annotated[sqlite3.Connection, Depends(get_conn)]


class ErrorDetail(BaseModel):
    detail: str


# Réponse d'erreur commune, déclarée pour respecter le contrat openapi.yml.
ROOMS_UNAVAILABLE = {500: {"model": ErrorDetail, "description": "rooms unavailable"}}

app = FastAPI(title="Salles", lifespan=lifespan)


@app.get("/rooms", response_model=list[Room], responses=ROOMS_UNAVAILABLE)
def list_rooms(conn: Conn) -> list[Room]:
    try:
        return handlers.list_rooms(conn)
    except sqlite3.Error as error:
        raise HTTPException(status_code=500, detail="rooms unavailable") from error


@app.get("/rooms/available", response_model=list[Calendar], responses=ROOMS_UNAVAILABLE)
def list_available_rooms(day: date, conn: Conn) -> list[Calendar]:
    try:
        return handlers.list_available_rooms(conn, day)
    except sqlite3.Error as error:
        raise HTTPException(status_code=500, detail="rooms unavailable") from error
