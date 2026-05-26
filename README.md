# StatRadar (Local MVP)

StatRadar is a **local-first journalist research assistant** for discovering potentially important public-sector signals in Swedish national sources.

It does **not** write finished articles and does **not** make unsupported conclusions. It helps journalists find items worth checking by keeping every flag tied to a URL and source snippet.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open: http://127.0.0.1:5000

## Dev commands

```bash
python app.py crawl      # crawl configured sources
python app.py pipeline   # crawl -> download -> parse -> detect -> rank
python app.py resetdb    # reset sqlite database
python app.py            # run web dashboard
```

## Architecture (simple and modular)

- `app.py`: Flask routes, dashboard, action endpoints, simple CLI entry.
- `config/sources.yaml`: source registry (config-driven crawling).
- `config/signals.yaml`: signal terms, actor lists, source reliability.
- `core/db.py`: SQLite setup and connection helpers.
- `core/models.py`: small DB write/read helpers for documents.
- `core/crawler.py`: source discovery (`html_index`, `rss`, `manual_urls`).
- `core/downloader.py`: downloads pending URLs to local `data/raw/`.
- `core/parser.py`: extracts text from PDF/HTML.
- `core/signals.py`: term and numeric signal detection with snippets.
- `core/scoring.py`: explainable ranking and reason text.
- `core/search.py`: dashboard search helper.
- `templates/`: dashboard + document detail UI.

## Notes and constraints

- SQLite DB at `data/db/statradar.sqlite`.
- Raw files stored in `data/raw/`.
- Duplicate URLs are ignored via unique URL constraint.
- Ranking output is explainable with explicit reason strings.

## TODO (future expansion)

- Migrate DB to Postgres.
- Add scheduled jobs/queue workers.
- Add embeddings-based similarity and semantic search.
- Add source-specific robust crawlers.
- Add stronger named-entity recognition.
- Add anomaly/change-point detection.
- Add an "article idea" helper module (still source-bound and explainable).
