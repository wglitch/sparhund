import yaml
from core.db import get_conn


def rebuild_rankings() -> int:
    with open("config/signals.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    reliability = cfg.get("source_reliability", {})

    with get_conn() as conn:
        conn.execute("DELETE FROM rankings")
        docs = conn.execute("SELECT id, source_name, category, extracted_text FROM documents WHERE status='parsed'").fetchall()
        for d in docs:
            sigs = conn.execute("SELECT signal_type, term FROM signals WHERE document_id=?", (d["id"],)).fetchall()
            text = (d["extracted_text"] or "").lower()
            score = 0
            reasons = []

            by_type = {}
            for s in sigs:
                by_type[s["signal_type"]] = by_type.get(s["signal_type"], 0) + 1

            if by_type.get("trend", 0):
                score += 2 * by_type["trend"]
                reasons.append("trend/change language")
            if by_type.get("risk", 0):
                score += 3 * by_type["risk"]
                reasons.append("severity/risk language")
            if by_type.get("numbers", 0):
                score += 2
                reasons.append("concrete numbers/percentages")

            actors = sum(1 for a in cfg.get("named_actors", {}).get("regions", []) if a.lower() in text)
            actors += sum(1 for a in cfg.get("named_actors", {}).get("authorities", []) if a.lower() in text)
            if actors:
                score += min(actors, 5)
                reasons.append(f"mentions {actors} named actors")

            score += reliability.get(d["category"], 1)
            reasons.append(f"source reliability category '{d['category']}'")

            exp = "Flagged because: " + ", ".join(reasons) if reasons else "No strong signals found."
            conn.execute(
                "INSERT INTO rankings (document_id, total_score, explanation) VALUES (?, ?, ?)",
                (d["id"], score, exp),
            )
    return 1
