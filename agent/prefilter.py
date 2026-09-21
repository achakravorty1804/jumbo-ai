"""Layer 1 filter: cheap rules that drop only near-certain junk.
Everything else goes to the AI. When unsure, do NOT add a rule."""
import re
from collections import Counter
from dataclasses import dataclass
from urllib.parse import urlparse

from news.rss import fetch_all


@dataclass(frozen=True)
class Rule:
    name: str
    source: str | None = None  # exact source_name, or None for any source
    title: str | None = None   # regex on the title (case-insensitive)
    path: str | None = None    # regex on the URL path


RULES = [
    Rule("company press release", source="BusinessLine", path=r"^/brandhub/"),
    Rule("sports section", source="BusinessLine", path=r"^/news/sports"),
    Rule("science trivia section", source="BusinessLine", path=r"^/news/science"),
    Rule("viral/trivia section", source="ET Top Stories", path=r"^/news/new-updates"),
    Rule("auto-generated stock page", title=r"share price live updates"),
    Rule("IPO GMP/allotment tracker", title=r"allotment (status|likely)|check GMP|GMP compared"),
    Rule("stock tip", title=r"target price|stop[- ]loss|stocks? to buy"),
    Rule("upper-circuit chatter", title=r"upper circuit"),
    Rule("daily RBI data table", source="RBI Press Releases", title=r"^Money Market Operations as on"),
    Rule("daily price listing", title=r"^gold rate today"),
    Rule("event ticket promo", source="TechCrunch", title=r"\d+ days? left|save up to"),
]


def _matches(rule, article):
    if not (rule.title or rule.path):
        return False  # a rule with no pattern must never match everything
    if rule.source and article.source_name != rule.source:
        return False
    if rule.title and not re.search(rule.title, article.title, re.IGNORECASE):
        return False
    if rule.path and not re.search(rule.path, urlparse(article.url).path, re.IGNORECASE):
        return False
    return True


def prefilter(articles):
    """Returns (kept, dropped). dropped is a list of (rule_name, article)."""
    kept, dropped = [], []
    for article in articles:
        rule = next((r for r in RULES if _matches(r, article)), None)
        if rule:
            dropped.append((rule.name, article))
        else:
            kept.append(article)
    return kept, dropped


if __name__ == "__main__":
    articles, _ = fetch_all()
    kept, dropped = prefilter(articles)
    print(f"Fetched {len(articles)} | kept {len(kept)} | dropped {len(dropped)}\n")
    for name, n in Counter(name for name, _ in dropped).most_common():
        print(f"  {n:>3}  {name}")
    print("\nDropped articles (look for anything that should NOT be here):")
    for name, a in sorted(dropped, key=lambda x: x[0]):
        print(f"  [{name}] {a.source_name}: {a.title}")