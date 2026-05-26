import argparse
import logging

from flask import Flask, redirect, render_template, request, url_for

from core.crawler import run_crawl
from core.db import init_db, reset_db, get_conn
from core.downloader import download_pending
from core.parser import parse_pending
from core.scoring import rebuild_rankings
from core.search import search_documents
from core.signals import detect_signals

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)


@app.route("/")
def dashboard():
    q = request.args.get("q", "")
    with get_conn() as conn:
        docs = search_documents(q) if q else conn.execute(
            """
            SELECT d.*, r.total_score, r.explanation
            FROM documents d LEFT JOIN rankings r ON r.document_id=d.id
            ORDER BY d.id DESC LIMIT 100
            """
        ).fetchall()
        top = conn.execute(
            """
            SELECT d.id, d.title, d.source_name, d.url, r.total_score, r.explanation
            FROM rankings r JOIN documents d ON d.id=r.document_id
            ORDER BY r.total_score DESC, d.id DESC LIMIT 20
            """
        ).fetchall()
    return render_template("dashboard.html", docs=docs, top=top, q=q)


@app.route('/doc/<int:doc_id>')
def doc_detail(doc_id: int):
    with get_conn() as conn:
        doc = conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
        sigs = conn.execute("SELECT * FROM signals WHERE document_id=?", (doc_id,)).fetchall()
        rank = conn.execute("SELECT * FROM rankings WHERE document_id=?", (doc_id,)).fetchone()
    return render_template("doc_detail.html", doc=doc, sigs=sigs, rank=rank)


@app.route('/run/<action>', methods=['POST'])
def run_action(action: str):
    if action == "crawl":
        run_crawl()
    elif action == "download":
        download_pending()
    elif action == "parse":
        parse_pending()
    elif action == "signals":
        detect_signals()
    elif action == "rank":
        rebuild_rankings()
    return redirect(url_for('dashboard'))


def run_pipeline():
    print("Crawled:", run_crawl())
    print("Downloaded:", download_pending())
    print("Parsed:", parse_pending())
    print("Signals:", detect_signals())
    print("Rankings rebuilt")
    rebuild_rankings()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", default="web", choices=["web", "crawl", "pipeline", "resetdb"])
    args = parser.parse_args()

    init_db()
    if args.command == "crawl":
        print("Crawled:", run_crawl())
    elif args.command == "pipeline":
        run_pipeline()
    elif args.command == "resetdb":
        reset_db()
        print("Database reset complete.")
    else:
        app.run(debug=True)
