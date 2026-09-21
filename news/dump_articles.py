"""Saves the last 24h of articles to a text file so we can design filter rules from real data."""
from pathlib import Path
from urllib.parse import urlparse

from news.rss import fetch_all

OUT = Path("scratch") / "articles_dump.txt"


def section(url):
    """First two URL path parts, e.g. /markets/stocks, which is a useful topic hint."""
    parts = [p for p in urlparse(url).path.split("/") if p]
    return "/" + "/".join(parts[:2]) if parts else "/"


if __name__ == "__main__":
    articles, _ = fetch_all()
    articles.sort(key=lambda a: (a.source_name, -a.published.timestamp()))
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for i, a in enumerate(articles, 1):
            f.write(f"{i:03d} | {a.source_name} | {a.title} | {section(a.url)}\n")
    print(f"Saved {len(articles)} articles to {OUT}")