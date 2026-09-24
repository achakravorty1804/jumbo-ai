"""🐘 Jumbo's daily briefing dashboard. Read-only: shows the latest saved run from data/jumbo.db.
Run locally with:  streamlit run dashboard.py"""
import json
from contextlib import closing

import streamlit as st

from memory import database as db

CATEGORY_ORDER = [
    "India & Economy", "Business", "AI", "Startups",
    "Technology", "Markets & Finance", "Industries", "Global",
]
CATEGORY_EMOJI = {
    "India & Economy": "🇮🇳", "Business": "💼", "AI": "🤖", "Startups": "🚀",
    "Technology": "💻", "Markets & Finance": "📈", "Industries": "🏭", "Global": "🌍",
}

st.set_page_config(page_title="🐘 Jumbo", page_icon="🐘", layout="centered")


@st.cache_data(ttl=300)
def load_latest_briefing():
    """Returns (run_date, stories) for the most recent run, or (None, []) if the DB is empty."""
    with closing(db.connect()) as conn:
        row = conn.execute("SELECT run_date FROM runs ORDER BY run_date DESC LIMIT 1").fetchone()
        if not row:
            return None, []
        return row["run_date"], db.list_stories(conn, row["run_date"])


def render_story(story):
    flags = []
    if story["source_mode"] != "article_text":
        flags.append("📄 snippet only")
    if story["unverified_numbers"]:
        flags.append("⚠️ figures not fully verified")

    st.markdown(f"#### {story['headline']}")
    if flags:
        st.caption(" · ".join(flags))
    st.write(story["summary"])
    st.markdown(f"**Why it matters:** {story['why_it_matters']}")

    lead = story["articles"][0]
    publishers = ", ".join(sorted({a["publisher"] for a in story["articles"]}))
    when = lead["published_at"][:16].replace("T", " ")
    st.caption(f"{publishers} · {when} IST")
    st.markdown(f"[🔗 Read the full article →]({lead['url']})")
    st.divider()


def main():
    st.title("🐘 Jumbo")
    st.caption("Remembering what matters. Understanding what's happening.")

    run_date, stories = load_latest_briefing()
    if not run_date:
        st.info("No briefing has been generated yet. Check back after the next scheduled run.")
        return

    from datetime import datetime
    pretty_date = datetime.strptime(run_date, "%Y-%m-%d").strftime("%A, %d %B %Y")
    st.markdown(f"### Good morning, Akash. Here's what happened on {pretty_date}.")
    num_categories = len({s["category"] for s in stories})
    st.caption(f"{len(stories)} stories · {num_categories} categories")

    by_category = {}
    for s in stories:
        by_category.setdefault(s["category"], []).append(s)

    for category in CATEGORY_ORDER:
        items = by_category.get(category)
        if not items:
            continue
        with st.expander(f"{CATEGORY_EMOJI.get(category, '')} {category} ({len(items)})", expanded=True):
            for story in sorted(items, key=lambda s: -s["score"]):
                render_story(story)

    shown = {s["category"] for items in by_category.values() for s in items}
    leftover = set(by_category) - set(CATEGORY_ORDER)
    if leftover:
        with st.expander(f"Other ({sum(len(by_category[c]) for c in leftover)})", expanded=True):
            for category in leftover:
                for story in by_category[category]:
                    render_story(story)


if __name__ == "__main__":
    main()