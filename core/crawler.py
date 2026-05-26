import logging
from datetime import datetime
from urllib.parse import urljoin

import requests
import yaml
from bs4 import BeautifulSoup
from xml.etree import ElementTree

from core.models import upsert_document

log = logging.getLogger(__name__)


def load_sources(path: str = "config/sources.yaml") -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f).get("sources", [])


def detect_file_type(url: str) -> str:
    if ".pdf" in url.lower():
        return "pdf"
    return "html"


def discover_from_html(source: dict):
    for entry in source.get("entry_urls", []):
        try:
            res = requests.get(entry, timeout=20)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.select(source.get("selectors", {}).get("link_selector", "a")):
                href = a.get("href")
                if not href:
                    continue
                url = urljoin(source.get("base_url"), href)
                title = (a.get_text() or "").strip()[:300]
                yield {"url": url, "title": title or url}
        except Exception as exc:
            log.warning("HTML crawl failed for %s: %s", entry, exc)


def discover_from_rss(source: dict):
    for entry in source.get("entry_urls", []):
        try:
            res = requests.get(entry, timeout=20)
            res.raise_for_status()
            root = ElementTree.fromstring(res.content)
            for item in root.findall(".//item"):
                link = item.findtext("link")
                title = item.findtext("title") or link
                pub_date = item.findtext("pubDate")
                if link:
                    yield {"url": link, "title": title, "published_at": pub_date}
        except Exception as exc:
            log.warning("RSS crawl failed for %s: %s", entry, exc)


def run_crawl() -> int:
    count = 0
    for src in load_sources():
        if not src.get("enabled", False):
            continue
        crawl_type = src.get("crawl_type")
        if crawl_type == "html_index":
            items = discover_from_html(src)
        elif crawl_type == "rss":
            items = discover_from_rss(src)
        elif crawl_type in {"manual_urls", "direct_pdf_list"}:
            items = ({"url": u, "title": u} for u in src.get("entry_urls", []))
        else:
            continue

        for item in items:
            url = item["url"]
            if not url.startswith("http"):
                continue
            if not any(x in url.lower() for x in ["pdf", "press", "dokument", "rapport", "sou", "utred"]):
                continue
            upsert_document(
                {
                    "source_name": src["name"],
                    "category": src["category"],
                    "url": url,
                    "title": item.get("title", url),
                    "file_type": detect_file_type(url),
                    "discovered_at": datetime.utcnow().isoformat(),
                    "published_at": item.get("published_at"),
                    "status": "discovered",
                }
            )
            count += 1
    return count
