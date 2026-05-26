import hashlib
import os

import requests
from core.db import get_conn


def raw_path_for_url(url: str, file_type: str) -> str:
    digest = hashlib.md5(url.encode("utf-8")).hexdigest()  # noqa: S324 for filename only
    ext = ".pdf" if file_type == "pdf" else ".html"
    return os.path.join("data/raw", f"{digest}{ext}")


def download_pending() -> int:
    updated = 0
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, url, file_type FROM documents WHERE status='discovered'"
        ).fetchall()
        for row in rows:
            try:
                res = requests.get(row["url"], timeout=30)
                res.raise_for_status()
                path = raw_path_for_url(row["url"], row["file_type"])
                mode = "wb" if row["file_type"] == "pdf" else "w"
                with open(path, mode, encoding=None if mode == "wb" else "utf-8") as f:
                    f.write(res.content if mode == "wb" else res.text)
                conn.execute(
                    "UPDATE documents SET status='downloaded', raw_path=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (path, row["id"]),
                )
                updated += 1
            except Exception:
                conn.execute(
                    "UPDATE documents SET status='error', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (row["id"],),
                )
    return updated
