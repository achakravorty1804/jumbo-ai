"""Downloads every enabled feed and returns fresh, de-duplicated articles."""
import logging
import time
from datetime import datetime, timedelta

import feedparser
import requests

from news.parser import IST, entry_to_article
from news.sources import enabled_sources

log = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JumboNewsBot/0.1)"}
TIMEOUT = 20
RETRIES = 2


def fetch_source(source):
    """Returns (articles, error). Never raises, so one bad feed can't stop the run."""
    error = None
    for attempt in range(RETRIES + 1):
        try:
            response = requests.get(source.url, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
            articles = []
            for entry in parsed.entries:
                try:
                    article = entry_to_article(entry, source)
                except Exception as e:  # one weird entry must not kill the feed
                    log.warning("%s: skipped a bad entry (%s)", source.name, e)
                    continue
                if article:
                    articles.append(article)
            return articles, None
        except requests.HTTPError as e:
            error = f"HTTP {e.response.status_code}"
            if e.response.status_code < 500:
                break  # 403/404 won't fix themselves, so don't retry
        except requests.RequestException as e:
            error = type(e).__name__
        if attempt < RETRIES:
            time.sleep(2 * (attempt + 1))
    log.warning("%s failed: %s", source.name, error)
    return [], error


def fetch_all(hours=24, now=None):
    """Returns (articles, report). Articles are unique by URL, newest first."""
    now = now or datetime.now(IST)
    cutoff = now - timedelta(hours=hours)
    latest_allowed = now + timedelta(minutes=10)  # tolerate small clock differences
    seen_urls = set()
    fresh = []
    report = {}

    for source in enabled_sources():
        articles, error = fetch_source(source)
        in_window = [a for a in articles if cutoff <= a.published <= latest_allowed]
        new = 0
        for article in in_window:
            if article.url in seen_urls:
                continue
            seen_urls.add(article.url)
            fresh.append(article)
            new += 1
        report[source.name] = {
            "fetched": len(articles),
            "in_window": len(in_window),
            "new": new,
            "error": error,
        }
        time.sleep(0.5)  # be polite to the publishers

    fresh.sort(key=lambda a: a.published, reverse=True)
    return fresh, report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    articles, report = fetch_all()
    print("\nPer-source report")
    for name, r in report.items():
        status = f"ERROR: {r['error']}" if r["error"] else "ok"
        print(f"  {name:<22} fetched={r['fetched']:<3} last24h={r['in_window']:<3} new={r['new']:<3} {status}")
    print(f"\nTotal fresh unique articles: {len(articles)}\n")
    for a in articles[:10]:
        print(f"  [{a.published:%d %b %H:%M}] {a.publisher}: {a.title}")