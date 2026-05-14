"""SQLite logger for emotion detection sessions."""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            emotion   TEXT NOT NULL,
            song      TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_session(emotion: str, song: str = None):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO sessions (timestamp, emotion, song) VALUES (?, ?, ?)",
        (datetime.now().isoformat(), emotion, os.path.basename(song) if song else None)
    )
    conn.commit()
    conn.close()


def get_history(limit: int = 50) -> list[tuple]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT timestamp, emotion, song FROM sessions ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return rows
