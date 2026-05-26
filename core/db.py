import os
import sqlite3
from contextlib import contextmanager

DB_PATH = "data/db/statradar.sqlite"


def ensure_dirs() -> None:
    os.makedirs("data/db", exist_ok=True)
    os.makedirs("data/raw", exist_ok=True)


@contextmanager
def get_conn():
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT,
                category TEXT,
                url TEXT UNIQUE,
                title TEXT,
                file_type TEXT,
                discovered_at TEXT,
                published_at TEXT,
                status TEXT DEFAULT 'discovered',
                raw_path TEXT,
                extracted_text TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                signal_type TEXT,
                term TEXT,
                snippet TEXT,
                score INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            );

            CREATE TABLE IF NOT EXISTS rankings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER UNIQUE,
                total_score INTEGER,
                explanation TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            );
            """
        )


def reset_db() -> None:
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
