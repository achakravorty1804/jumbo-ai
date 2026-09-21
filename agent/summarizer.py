"""Session 3: turns one selected story into our own short summary and "why it matters".
The article text is used only as source material and is never stored. Every number in the
summary is checked against the source, so the model can't slip in a figure that isn't there."""
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from agent import llm
from news.article_text import fetch_article_text

log = logging.getLogger(__name__)

PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "summary.txt"
NUMBER_RE = re.compile(r"\d[\d,]*\.?\d*")
LIMITS = {  # (min, max) characters for the summary, by source type
    "article_text": (200, 900),
    "snippet_only": (50, 450),
}


@dataclass
class Summary:
    headline: str
    summary: str
    why_it_matters: str
    entities: list
    source_mode: str  # "article_text" or "snippet_only"
    unverified_numbers: list = field(default_factory=list)  # numbers not found in the source


def _numbers(text):
    """Digit strings in a text with commas removed, e.g. '2,449' -> '2449'.
    A year like 2028 also counts as '28', so 'FY28' matches 'financial year 2028'."""
    found = {n.replace(",", "").rstrip(".") for n in NUMBER_RE.findall(text)}
    found |= {n[2:] for n in found if len(n) == 4 and n.startswith("20")}
    return found

def _tidy(text):
    """Swaps special characters some models emit (non-breaking hyphens and spaces) for plain ones."""
    return (
        str(text or "").replace("\u2011", "-").replace("\u2010", "-")
        .replace("\u202f", " ").replace("\u00a0", " ").strip()
    )

def _check(data, mode):
    """Returns (cleaned dict, problem). problem is None when the reply is usable."""
    if not isinstance(data, dict):
        return None, "the reply was not a JSON object"
    summary = _tidy(data.get("summary"))
    why = _tidy(data.get("why_it_matters"))
    headline = _tidy(data.get("headline"))
    entities = data.get("entities") or []
    if not isinstance(entities, list):
        entities = []
    low, high = LIMITS[mode]
    if not low <= len(summary) <= high:
        return None, f"summary must be {low} to {high} characters (it was {len(summary)})"
    if not 20 <= len(why) <= 300:
        return None, "why_it_matters must be one sentence of 20 to 300 characters"
    if not 10 <= len(headline) <= 140:
        return None, "headline must be 10 to 140 characters"
    entities = [_tidy(e) for e in entities if _tidy(e)][:6]
    return {"headline": headline, "summary": summary, "why_it_matters": why, "entities": entities}, None


def summarize_story(article, text=None, system_prompt=None):
    """Returns a Summary, or None if the story can't be summarised safely. Never raises."""
    if system_prompt is None:
        system_prompt = PROMPT_FILE.read_text(encoding="utf-8")
    mode = "article_text" if text else "snippet_only"
    if not text and len(article.snippet) < 60:
        log.warning("No usable source text for: %s", article.title)
        return None
    body = text if text else article.snippet
    label = "ARTICLE TEXT" if text else "RSS SNIPPET ONLY"
    user = (
        f"Publisher: {article.publisher}\n"
        f"Headline: {article.title}\n"
        f"Published: {article.published:%d %b %Y, %I:%M %p} IST\n"
        f"Source type: {label}\n\n{body}\n\nWrite the JSON now."
    )
    source_numbers = _numbers(f"{article.title} {body}")
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user}]

    fallback = None  # a well-formed summary whose only problem is unverified numbers
    for attempt in range(2):
        reply = ""
        try:
            reply = llm.complete(messages, json_mode=True, max_tokens=1200)
            cleaned, problem = _check(json.loads(reply), mode)
        except llm.LLMError as e:
            log.warning("LLM failed for '%s': %s", article.title[:60], e)
            break
        except ValueError:
            cleaned, problem = None, "the reply was not valid JSON"
        if cleaned:
            missing = sorted(_numbers(cleaned["summary"] + " " + cleaned["why_it_matters"]) - source_numbers)
            if not missing:
                return Summary(**cleaned, source_mode=mode)
            fallback = (cleaned, missing)
            problem = (
                f"these numbers do not appear in the source: {', '.join(missing)}. "
                "Use only numbers from the source and do not calculate new ones"
            )
        log.info("Retrying (%s): %s", problem, article.title[:60])
        messages = messages + [
            {"role": "assistant", "content": reply},
            {"role": "user", "content": f"That reply was rejected: {problem}. Fix it and reply with the JSON object only."},
        ]
    if fallback:
        cleaned, missing = fallback
        return Summary(**cleaned, source_mode=mode, unverified_numbers=missing)
    return None


if __name__ == "__main__":
    from agent.classifier import load_results
    from agent.merge import merge_similar, select_top_stories
    from agent.prefilter import prefilter

    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    results = load_results()
    kept, _ = prefilter([c.article for c in results])
    kept_urls = {a.url for a in kept}
    results = [c for c in results if c.article.url in kept_urls]
    stories = select_top_stories(merge_similar(results))
    step = max(1, len(stories) // count)
    prompt = PROMPT_FILE.read_text(encoding="utf-8")

    for story in stories[::step][:count]:
        article = story.lead.article
        text, status = fetch_article_text(article.url)
        summary = summarize_story(article, text, prompt)
        print("=" * 72)
        print(f"{story.lead.category} | score {story.score} | {article.publisher} | text: {status}")
        print(f"ORIGINAL: {article.title}")
        if not summary:
            print("FAILED: could not summarise this story safely")
            continue
        print(f"HEADLINE: {summary.headline}")
        print(f"SUMMARY:  {summary.summary}")
        print(f"WHY:      {summary.why_it_matters}")
        print(f"ENTITIES: {', '.join(summary.entities)}")
        print(f"MODE: {summary.source_mode} | UNVERIFIED NUMBERS: {summary.unverified_numbers or 'none'}")
        print(f"URL:      {article.url}")
    print("\nLLM usage:", llm.usage_totals)