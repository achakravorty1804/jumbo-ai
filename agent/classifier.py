"""Layer 2: AI triage. Sends articles to the LLM in small batches and gets back
a category and a 1-5 importance score for each one."""
import dataclasses
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from agent import llm
from agent.merge import merge_similar, select_top_stories
from agent.prefilter import prefilter
from news.parser import Article
from news.rss import fetch_all
log = logging.getLogger(__name__)

CATEGORIES = {
    "India & Economy", "Business", "AI", "Startups", "Technology",
    "Markets & Finance", "Industries", "Global", "Excluded",
}
PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "classification.txt"
SNIPPET_CHARS = 200
BATCH_SIZE = 20
CACHE_FILE = Path(__file__).resolve().parent.parent / "scratch" / "classified_latest.json"

@dataclass
class Classified:
    article: object
    category: str
    score: int  # 1-5, or 0 if the AI could not rate it
    reason: str

def url_section(url):
      parts = [p for p in urlparse(url).path.split("/") if p][:2]
      parts = [p for p in parts if len(p) <= 25 and not any(ch.isdigit() for ch in p)]
      return "/" + "/".join(parts) if parts else "-"

def format_batch(batch):
      return "\n".join(
          f"{i} | {a.publisher} | {url_section(a.url)} | {a.title} | {a.snippet[:SNIPPET_CHARS]}"
          for i, a in enumerate(batch, 1)
      )

def _parse(reply, expected):
    """Returns {id: (category, score, reason)} for every valid item in the reply."""
    try:
        items = json.loads(reply)["results"]
    except (ValueError, KeyError, TypeError):
        return {}
    out = {}
    for item in items:
        try:
            i, category, score = int(item["id"]), item["category"], int(item["score"])
        except (KeyError, TypeError, ValueError):
            continue
        if 1 <= i <= expected and category in CATEGORIES and 1 <= score <= 5:
            out.setdefault(i, (category, score, str(item.get("reason", ""))[:120]))
    return out


def classify_batch(batch, system_prompt):
    """Returns one Classified per article, in order. Splits the batch if the reply is incomplete."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Rate these news items. Reply in JSON.\n\n" + format_batch(batch)},
    ]
    try:
        reply = llm.complete(messages, json_mode=True, max_tokens=3000)
    except llm.LLMError as e:
        log.warning("LLM call failed for a batch of %d: %s", len(batch), e)
        return [Classified(a, "Unrated", 0, "LLM call failed") for a in batch]

    parsed = _parse(reply, len(batch))
    if len(parsed) == len(batch):
        return [Classified(a, *parsed[i]) for i, a in enumerate(batch, 1)]
    if len(batch) == 1:
        log.warning("Could not rate: %s", batch[0].title)
        return [Classified(batch[0], "Unrated", 0, "invalid AI reply")]
    log.info("Incomplete reply (%d of %d rated); splitting the batch", len(parsed), len(batch))
    mid = len(batch) // 2
    return classify_batch(batch[:mid], system_prompt) + classify_batch(batch[mid:], system_prompt)


def classify_all(articles, batch_size=BATCH_SIZE):
    system_prompt = PROMPT_FILE.read_text(encoding="utf-8")
    results, failures = [], 0
    ai_unavailable = False
    for start in range(0, len(articles), batch_size):
        batch = articles[start:start + batch_size]
        if failures >= 2:  # the LLM is clearly unavailable; don't keep hammering it
            results += [Classified(a, "Unrated", 0, "skipped: LLM unavailable") for a in batch]
            ai_unavailable = True
            continue
        rated = classify_batch(batch, system_prompt)
        results += rated
        failures = failures + 1 if all(c.score == 0 for c in rated) else 0
        log.info("Rated %d of %d", min(start + batch_size, len(articles)), len(articles))
    return results, ai_unavailable

def save_results(results, path=CACHE_FILE):
    """Saves ratings to a local file (scratch/ is gitignored) so later steps can be tested for free."""
    path.parent.mkdir(exist_ok=True)
    rows = []
    for c in results:
        article = dataclasses.asdict(c.article)
        article["published"] = c.article.published.isoformat()
        rows.append({"article": article, "category": c.category, "score": c.score, "reason": c.reason})
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")


def load_results(path=CACHE_FILE):
    rows = json.loads(path.read_text(encoding="utf-8"))
    results = []
    for row in rows:
        article = dict(row["article"])
        article["published"] = datetime.fromisoformat(article["published"])
        results.append(Classified(Article(**article), row["category"], row["score"], row["reason"]))
    return results


def select_top(classified, min_score=4, cap=15):
    picks = [c for c in classified if c.score >= min_score]
    picks.sort(key=lambda c: (-c.score, -c.article.published.timestamp()))
    return picks[:cap]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    mode = sys.argv[1] if len(sys.argv) > 1 else "20"
    articles, _ = fetch_all()
    kept, _ = prefilter(articles)
    if mode != "all":
        n = int(mode)
        step = max(1, len(kept) // n)
        kept = kept[::step][:n]  # a spread across all sources, not just the newest
    print(f"Rating {len(kept)} articles...\n")
    results, ai_unavailable = classify_all(kept)
    if ai_unavailable:
        print("NOTE: circuit breaker tripped — the LLM looked unavailable partway through\n")
    for c in sorted(results, key=lambda c: -c.score):
        print(f"{c.score} | {c.category:<17} | {c.article.source_name:<14} | {c.article.title[:85]} | {c.reason}")
    stories = merge_similar(results)
    strong = sum(1 for c in results if c.score >= 4)
    distinct = sum(1 for s in stories if s.score >= 4)
    print(f"\nArticles scored 4+: {strong}")
    print(f"Distinct stories scoring 4+ after merging same-headline copies: {distinct}")
    print("\nTop stories for the briefing (cap 15):")
    for s in select_top_stories(stories):
        print(f"  {s.score} | {' + '.join(s.publishers):<34} | {s.lead.article.title[:80]}")
    print(f"\nLLM usage: {llm.usage_totals}")
    if mode == "all":  # only cache a full run, so a small test can't overwrite it
        save_results(results)
        print(f"Saved ratings to {CACHE_FILE}")