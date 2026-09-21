"""Turns raw feed entries into one clean, standard Article format."""
import html
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from news.sources import Source

# Fixed offset, so we don't depend on Windows timezone databases.
IST = timezone(timedelta(hours=5, minutes=30))

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


@dataclass
class Article:
    title: str
    snippet: str
    url: str
    publisher: str
    source_name: str
    published: datetime  # timezone-aware, in IST
    hint: str
    kind: str


def clean_text(raw, max_len=None):
    text = html.unescape(raw or "")
    text = TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = SPACE_RE.sub(" ", text).strip()
    if max_len and len(text) > max_len:
        text = text[: max_len - 3].rstrip() + "..."
    return text


def clean_url(url):
    parts = urlparse((url or "").strip())
    if parts.scheme not in ("http", "https"):
        return ""
    query = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not k.lower().startswith("utm_") and k.lower() not in ("fbclid", "gclid")
    ]
    return urlunparse(parts._replace(query=urlencode(query), fragment=""))


def parse_published(entry):
    """Returns an IST datetime, or None if the entry has no usable date."""
    raw = entry.get("published") or entry.get("updated") or ""
    if raw:
        dt = None
        try:
            dt = parsedate_to_datetime(raw)
        except (TypeError, ValueError):
            try:
                dt = datetime.fromisoformat(raw.strip())
            except ValueError:
                dt = None
        if dt is not None:
            if dt.tzinfo is None:
                return dt.replace(tzinfo=IST)  # no timezone given (e.g. RBI): assume IST
            return dt.astimezone(IST)
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        return datetime(*parsed[:6], tzinfo=timezone.utc).astimezone(IST)
    return None


def entry_to_article(entry, source: Source):
    """Returns an Article, or None if the entry is missing a title, link or date."""
    title = clean_text(entry.get("title"))
    url = clean_url(entry.get("link"))
    published = parse_published(entry)
    if not (title and url and published):
        return None
    snippet = clean_text(entry.get("summary") or entry.get("description"), max_len=600)
    return Article(
        title=title,
        snippet=snippet,
        url=url,
        publisher=source.publisher,
        source_name=source.name,
        published=published,
        hint=source.hint,
        kind=source.kind,
    )