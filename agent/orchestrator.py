"""Pipeline tail: rated articles -> chosen stories -> summaries -> SQLite.
Safe to re-run: stories already saved are skipped, so a repeated or crashed run costs no extra tokens."""
import logging
import sys
import time
from contextlib import closing
from datetime import datetime

from agent import llm
from agent.classifier import load_results
from agent.merge import merge_similar, select_top_stories
from agent.prefilter import prefilter
from agent.summarizer import PROMPT_FILE, summarize_story
from memory import database as db
from memory import dedup
from news.article_text import fetch_article_text
from news.parser import IST

log = logging.getLogger(__name__)


def choose_stories(results):
    """Applies the current pre-filter rules to saved ratings, merges copies, keeps the top stories."""
    kept, _ = prefilter([c.article for c in results])
    kept_urls = {a.url for a in kept}
    return select_top_stories(merge_similar([c for c in results if c.article.url in kept_urls]))


def summarise_and_save(stories, conn, run_id):
    prompt = PROMPT_FILE.read_text(encoding="utf-8")
    saved = skipped = failed = 0
    for n, story in enumerate(stories, 1):
        articles = [story.lead.article] + [o.article for o in story.others]
        if db.any_url_known(conn, [a.url for a in articles]):
            skipped += 1
            continue
        lead = articles[0]
        text, status = fetch_article_text(lead.url)
        time.sleep(1.5)  # be polite to the publisher's server
        before = dict(llm.usage_totals)
        summary = summarize_story(lead, text, prompt)
        db.add_tokens(
            conn,
            run_id,
            llm.usage_totals["prompt_tokens"] - before["prompt_tokens"],
            llm.usage_totals["completion_tokens"] - before["completion_tokens"],
        )
        if not summary:
            failed += 1
            log.warning("Could not summarise: %s", lead.title)
            continue
        embedding = dedup.embed(summary.headline, summary.summary)
        match_id, similarity = dedup.find_best_match(conn, embedding, exclude_run_id=run_id)
        duplicate_of = match_id if similarity >= dedup.SIMILARITY_THRESHOLD else None
        db.add_story(conn, run_id, story.lead.category, story.score, summary, articles,
                      embedding=embedding, duplicate_of=duplicate_of,
                      source_count=len(story.publishers))
        if duplicate_of:
            db.increment_source_count(conn, duplicate_of, by=len(story.publishers))
        saved += 1
        dup_note = f" [duplicate of story {duplicate_of}, sim={similarity:.2f}]" if duplicate_of else ""
        log.info("Saved %d of %d (%s, page: %s)%s", n, len(stories), summary.source_mode, status, dup_note)
    return saved, skipped, failed


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    stories = choose_stories(load_results())
    run_date = datetime.now(IST).date().isoformat()
    with closing(db.connect()) as conn:
        run_id = db.get_or_create_run(conn, run_date)
        saved, skipped, failed = summarise_and_save(stories, conn, run_id)
        print(f"\nStories chosen: {len(stories)} | saved now: {saved} | already saved: {skipped} | failed: {failed}")
        print(f"Tokens this session: {llm.usage_totals}\n")
        for s in db.list_stories(conn, run_date):
            note = "" if s["source_mode"] == "article_text" else "  [snippet only]"
            if s["unverified_numbers"]:
                note += f"  [unverified numbers: {s['unverified_numbers']}]"
            print(f"{s['score']} | {s['category']:<17} | {s['headline']}{note}")