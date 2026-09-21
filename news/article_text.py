"""Fetches the readable text of an article page, ONLY as source material for our own summary.
The text is used in memory and never saved or shown to readers. We respect robots.txt,
identify ourselves honestly, and fall back to the RSS snippet when a page can't be read."""
import logging
import os
import re
import sys
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
import trafilatura
from dotenv import load_dotenv

log = logging.getLogger(__name__)
load_dotenv()
RESPECT_PAYWALL_FLAG = os.getenv("RESPECT_PAYWALL_FLAG", "false").lower() == "true"

ROBOT_AGENT = "JumboNewsBot"
HEADERS = {"User-Agent": f"Mozilla/5.0 (compatible; {ROBOT_AGENT}/0.1)"}
TIMEOUT = 20
MIN_CHARS = 600   # shorter than this is probably a paywall stub or a failed extraction
MAX_CHARS = 4000  # the start of an article is enough to summarise it
BOILERPLATE_RE = re.compile(r"^\s*Listen to this article in summarized format\s*", re.IGNORECASE)
PAYWALL_RE = re.compile(
    r'isAccessibleForFree["\']?\s*:\s*["\']?(?:https?://schema\.org/)?(true|false)', re.IGNORECASE
)
_robots = {}  # one robots.txt per site, fetched once per run


def _allowed(url):
    parts = urlparse(url)
    site = f"{parts.scheme}://{parts.netloc}"
    if site not in _robots:
        parser = RobotFileParser()
        try:
            response = requests.get(f"{site}/robots.txt", headers=HEADERS, timeout=10)
        except requests.RequestException:
            parser.disallow_all = True  # can't check the rules, so don't fetch
        else:
            if response.status_code == 200:
                parser.parse(response.text.splitlines())
            elif response.status_code in (401, 403) or response.status_code >= 500:
                parser.disallow_all = True
            else:
                parser.allow_all = True  # no robots.txt means no restrictions
        _robots[site] = parser
    return _robots[site].can_fetch(ROBOT_AGENT, url)

def declared_free(html):
    """None if the page doesn't say. False if any part is declared not free. True if all are free."""
    values = [v.lower() for v in PAYWALL_RE.findall(html)]
    if not values:
        return None
    return all(v == "true" for v in values)

def fetch_article_text(url):
    """Returns (text, status). text is None when the page can't be used. Never raises."""
    try:
        if not _allowed(url):
            return None, "robots.txt disallows"
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        if RESPECT_PAYWALL_FLAG and declared_free(response.text) is False:
            return None, "paywalled (declared by the page)"
        text = trafilatura.extract(response.content, include_comments=False, include_tables=False)
    except requests.HTTPError as e:
        return None, f"HTTP {e.response.status_code}"
    except Exception as e:  # this function must never crash the daily run
        return None, f"error: {type(e).__name__}"
    if text:
          text = BOILERPLATE_RE.sub("", text)
    if not text or len(text) < MIN_CHARS:
        return None, f"too short ({len(text or '')} chars)"
    return text[:MAX_CHARS], "ok"


if __name__ == "__main__":
    from agent.classifier import load_results
    from agent.merge import merge_similar, select_top_stories
    from agent.prefilter import prefilter

    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    results = load_results()
    kept, _ = prefilter([c.article for c in results])  # new rules apply to saved ratings too
    kept_urls = {a.url for a in kept}
    results = [c for c in results if c.article.url in kept_urls]
    stories = select_top_stories(merge_similar(results))

    ok = 0
    for story in stories:
        article = story.lead.article
        text, status = fetch_article_text(article.url)
        ok += text is not None
        print(f"{status:<30} {len(text or ''):>5} | {article.publisher:<22} | {article.title[:55]}")
        if text:
            print("      starts:", text[:90].replace("\n", " "))
        time.sleep(1.5)
    print(f"\n{ok} of {len(stories)} stories have usable article text")