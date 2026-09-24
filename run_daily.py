"""The one script GitHub Actions runs each day.

Chains:
fetch -> prefilter -> classify -> merge -> summarise -> SQLite -> email
"""

import logging
import sys
from contextlib import closing
from datetime import datetime

from agent import llm
from agent.merge import merge_similar, select_top_stories
from agent.orchestrator import summarise_and_save
from agent.prefilter import prefilter
from agent.classifier import classify_all
from mailer.sender import send_email
from memory import database as db
from news.parser import IST
from news.rss import fetch_all


log = logging.getLogger(__name__)


def build_briefing():
    """Build and save the daily briefing.

    Returns:
        (run_id, story_count, mode)
    """
    articles, fetch_report = fetch_all()
    log.info("Fetched %d articles", len(articles))

    kept, _ = prefilter(articles)
    log.info("Prefilter kept %d", len(kept))

    run_date = datetime.now(IST).date().isoformat()

    with closing(db.connect()) as conn:
        run_id = db.get_or_create_run(conn, run_date)

        # TODO (later): fall back to plain headlines if AI is unavailable.
        classified = classify_all(kept)

        stories = select_top_stories(merge_similar(classified))

        saved, skipped, failed = summarise_and_save(
            stories,
            conn,
            run_id
        )

        log.info(
            "Saved %d, skipped %d already-saved, failed %d",
            saved,
            skipped,
            failed
        )

        return run_id, saved + skipped, "full"


def send_daily_email(story_count: int):
    """Send the short Jumbo daily email."""

    dashboard_url = "https://jumbo-ai-dpdqoyag5ko7krhwt7vrml.streamlit.app/"

    subject = "🐘 Jumbo — Your daily intelligence briefing is ready"

    body = f"""🐘 Hey Akash!

I'm Jumbo, your personal AI news assistant.

I've been keeping track of what's happening around the world and your daily intelligence briefing is ready.

Today's briefing contains {story_count} stories.

OPEN JUMBO:
{dashboard_url}

— Jumbo
"""

    send_email(
        subject=subject,
        body=body,
    )

    log.info("Daily email sent successfully")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s"
    )

    run_id, count, mode = build_briefing()

    print(f"\nRun {run_id}: {count} stories saved, mode={mode}")
    print(f"LLM usage: {llm.usage_totals}")

    send_daily_email(count)