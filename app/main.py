"""Application « Salles » : réservation de salles de réunion."""

import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException

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


app = FastAPI(title="Salles", lifespan=lifespan)


@app.get("/rooms")
def list_rooms() -> list[dict]:
    try:
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT id, name, capacity FROM rooms ORDER BY id").fetchall()
        conn.close()
    except sqlite3.Error as error:
        raise HTTPException(status_code=500, detail="rooms unavailable") from error
    return [dict(row) for row in rows]
