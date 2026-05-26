import re
import yaml

from core.db import get_conn


def load_signal_config(path="config/signals.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def snippet(text: str, term: str, size: int = 180) -> str:
    idx = text.lower().find(term.lower())
    if idx < 0:
        return ""
    return text[max(0, idx - size // 2): idx + size // 2].replace("\n", " ")


def detect_signals() -> int:
    cfg = load_signal_config()
    inserted = 0
    with get_conn() as conn:
        conn.execute("DELETE FROM signals")
        docs = conn.execute("SELECT id, extracted_text FROM documents WHERE status='parsed'").fetchall()
        for d in docs:
            text = d["extracted_text"] or ""
            if not text:
                continue
            for sig_type, terms in cfg.get("signal_terms", {}).items():
                for term in terms:
                    if term.lower() in text.lower():
                        conn.execute(
                            "INSERT INTO signals (document_id, signal_type, term, snippet, score) VALUES (?, ?, ?, ?, ?)",
                            (d["id"], sig_type, term, snippet(text, term), 1),
                        )
                        inserted += 1

            for num in re.findall(r"\b\d+(?:[\.,]\d+)?\s?%\b", text):
                conn.execute(
                    "INSERT INTO signals (document_id, signal_type, term, snippet, score) VALUES (?, 'numbers', ?, ?, 2)",
                    (d["id"], num, snippet(text, num)),
                )
                inserted += 1
    return inserted
