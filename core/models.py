from datetime import datetime
from core.db import get_conn


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def upsert_document(item: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO documents (source_name, category, url, title, file_type, discovered_at, published_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                title=excluded.title,
                category=excluded.category,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                item.get("source_name"),
                item.get("category"),
                item.get("url"),
                item.get("title"),
                item.get("file_type"),
                item.get("discovered_at", now_iso()),
                item.get("published_at"),
                item.get("status", "discovered"),
            ),
        )


def list_documents(limit: int = 100):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM documents ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
