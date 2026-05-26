from bs4 import BeautifulSoup
from pypdf import PdfReader

from core.db import get_conn


def parse_pdf(path: str) -> str:
    reader = PdfReader(path)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def parse_html(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return " ".join(soup.get_text(separator=" ").split())


def parse_pending() -> int:
    count = 0
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, file_type, raw_path FROM documents WHERE status='downloaded'"
        ).fetchall()
        for row in rows:
            try:
                text = parse_pdf(row["raw_path"]) if row["file_type"] == "pdf" else parse_html(row["raw_path"])
                conn.execute(
                    "UPDATE documents SET extracted_text=?, status='parsed', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (text[:1000000], row["id"]),
                )
                count += 1
            except Exception:
                conn.execute("UPDATE documents SET status='error' WHERE id=?", (row["id"],))
    return count
