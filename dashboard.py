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
    "India & Economy": "🇮🇳",
    "Business": "💼",
    "AI": "🤖",
    "Startups": "🚀",
    "Technology": "💻",
    "Markets & Finance": "📈",
    "Industries": "🏭",
    "Global": "🌍",
}

st.set_page_config(
    page_title="🐘 Jumbo",
    page_icon="🐘",
    layout="centered",
)


@st.cache_data(ttl=300)
def load_latest_briefing():
    """Returns (run_date, stories) for the most recent run."""
    with closing(db.connect()) as conn:
        row = conn.execute(
            "SELECT run_date FROM runs ORDER BY run_date DESC LIMIT 1"
        ).fetchone()

        if not row:
            return None, []

        return row["run_date"], db.list_stories(conn, row["run_date"])


def get_current_user():
    """Return the user matching ?user=slug, falling back to the owner."""
    slug = st.query_params.get("user")

    if not slug:
        slug = "akash"

    with closing(db.connect()) as conn:
        user = db.get_user_by_slug(conn, slug)

        if user:
            return dict(user)

        owner = db.get_user_by_slug(conn, "akash")

        if owner:
            return dict(owner)

    return {
        "name": "Akash",
        "slug": "akash",
        "has_seen_intro": 0,
    }


def handle_intro(user):
    """Show the first-open intro once for each user."""
    if user.get("has_seen_intro", 0):
        return

    st.info(
        "💡 **Did you know?** Jumbo remembers what matters and turns "
        "the day's important news into a focused briefing for you."
    )

    if st.button("Got it — let's go", type="primary"):
        with closing(db.connect()) as conn:
            db.mark_intro_seen(conn, user["id"])

        st.rerun()


def render_story(story):
    flags = []

    if story.get("source_count", 1) > 1:
        flags.append(f"✓ {story['source_count']} sources")

    if story.get("duplicate_of"):
        flags.append("🔄 update to earlier story")

    if story["source_mode"] != "article_text":
        flags.append("📄 snippet only")

    if story["unverified_numbers"]:
        flags.append("⚠️ figures not fully verified")

    st.markdown(f"#### {story['headline']}")

    if flags:
        st.caption(" · ".join(flags))

    st.write(story["summary"])

    st.markdown(
        f"**Why it matters:** {story['why_it_matters']}"
    )

    lead = story["articles"][0]

    publishers = ", ".join(
        sorted({a["publisher"] for a in story["articles"]})
    )

    when = lead["published_at"][:16].replace("T", " ")

    st.caption(f"{publishers} · {when} IST")

    st.markdown(
        f"[🔗 Read the full article →]({lead['url']})"
    )

    st.divider()


def main():
    user = get_current_user()

    st.title("🐘 Jumbo")
    st.caption(
        "Remembering what matters. Understanding what's happening."
    )

    handle_intro(user)

    run_date, stories = load_latest_briefing()

    if not run_date:
        st.info(
            "No briefing has been generated yet. "
            "Check back after the next scheduled run."
        )
        return

    st.markdown(
        f"### Good morning, {user['name']}. "
        "Here's what's going on around the World."
    )

    num_categories = len({s["category"] for s in stories})

    st.caption(
        f"{len(stories)} stories · {num_categories} categories"
    )

    by_category = {}

    for story in stories:
        by_category.setdefault(
            story["category"], []
        ).append(story)

    for category in CATEGORY_ORDER:
        items = by_category.get(category)

        if not items:
            continue

        with st.expander(
            f"{CATEGORY_EMOJI.get(category, '')} "
            f"{category} ({len(items)})",
            expanded=True,
        ):
            for story in sorted(
                items,
                key=lambda s: -s["score"],
            ):
                render_story(story)

    leftover = set(by_category) - set(CATEGORY_ORDER)

    if leftover:
        with st.expander(
            f"Other ({sum(len(by_category[c]) for c in leftover)})",
            expanded=True,
        ):
            for category in leftover:
                for story in by_category[category]:
                    render_story(story)


if __name__ == "__main__":
    main()