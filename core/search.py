from core.db import get_conn


def search_documents(query: str):
    q = f"%{query}%"
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT d.*, r.total_score, r.explanation
            FROM documents d
            LEFT JOIN rankings r ON r.document_id = d.id
            WHERE d.title LIKE ? OR d.extracted_text LIKE ? OR d.url LIKE ?
            ORDER BY d.id DESC
            """,
            (q, q, q),
        ).fetchall()
