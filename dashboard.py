"""Jumbo's daily briefing dashboard. Read-only: shows the latest saved run from data/jumbo.db.
Run locally with:  streamlit run dashboard.py"""

import time
from contextlib import closing
from datetime import date

import streamlit as st

from memory import database as db
from mascot import show_mascot, COLOR_BUBBLE_BG, COLOR_BUBBLE_BORDER, COLOR_TEXT
from theme import apply_theme, render_sidebar_brand, top_banner, PINK_SOFT, PINK_BORDER, NAVY

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

ELEPHANT_FACTS = [
    "An elephant's trunk has no bones — it's made of over 40,000 muscles, more than the entire human body has.",
    "Elephants can recognize themselves in a mirror, a rare sign of self-awareness shared with humans, apes and dolphins.",
    "A herd of elephants is led by the oldest female, called the matriarch, who guides the group using decades of memory.",
    "Elephants can communicate over long distances using low-frequency rumbles that travel through the ground.",
    "An elephant's memory is so strong that they can recognize other elephants and humans even after many years apart.",
    "Elephants are the only mammals that can't jump — but they can swim for hours using their trunk as a snorkel.",
    "A baby elephant may suck its trunk for comfort, just like a human baby sucks its thumb.",
    "Elephants show empathy — they've been seen comforting distressed herd members by touching them with their trunks.",
]

st.set_page_config(
    page_title="🐘 Jumbo",
    page_icon="🐘",
    layout="wide",
)


def get_daily_fact():
    index = date.today().toordinal() % len(ELEPHANT_FACTS)
    return ELEPHANT_FACTS[index]


@st.cache_data(ttl=300)
def load_latest_briefing():
    with closing(db.connect()) as conn:
        row = conn.execute(
            "SELECT run_date FROM runs ORDER BY run_date DESC LIMIT 1"
        ).fetchone()

        if not row:
            return None, []

        return row["run_date"], db.list_stories(conn, row["run_date"])


def get_current_user():
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
        "id": None,
        "name": "Akash",
        "slug": "akash",
        "has_seen_intro": 0,
    }


def group_by_category(stories):
    by_category = {}

    for story in stories:
        by_category.setdefault(story["category"], []).append(story)

    return by_category


def display_categories(by_category):
    cats = [c for c in CATEGORY_ORDER if by_category.get(c)]
    leftover = sorted(set(by_category) - set(CATEGORY_ORDER))

    if leftover:
        cats.append("Other")

    return cats, leftover


def items_for(category, by_category, leftover):
    if category == "Other":
        items = []

        for cat in leftover:
            items.extend(by_category.get(cat, []))

    else:
        items = by_category.get(category, [])

    # Defensive filter: skip any story with a missing/blank headline
    # (e.g. from a failed/partial LLM generation) so it doesn't show
    # up as an empty tile in the grid.
    return [s for s in items if s.get("headline") and s["headline"].strip()]


def render_message_bubble(message):
    """A small pink-bordered speech-bubble box for page content
    (used next to Jumbo in category_view), independent of the
    mascot component's own bubble."""
    st.markdown(
        f"""
        <div style="
            background: {COLOR_BUBBLE_BG};
            border: 2px solid {COLOR_BUBBLE_BORDER};
            border-radius: 18px;
            padding: 14px 20px;
            margin-bottom: 18px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            display: inline-block;
            max-width: 100%;
        ">
            <p style="
                margin: 0;
                color: {COLOR_TEXT};
                font-size: 16px;
                line-height: 1.45;
            ">{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _select_story(story):
    """on_click callback: change state to open this story's detail
    page. Using on_click (rather than checking the button's return
    value and calling st.rerun() ourselves afterward) is the more
    reliable pattern for state changes triggered by a button inside
    a loop."""
    st.session_state.stage = "story_detail"
    st.session_state.selected_story = story


def render_story_card(story, key_prefix, index):
    """One story as a small, wide, pink clickable tile showing only
    the headline. Clicking it opens Jumbo's own in-app detail page
    for that story (does NOT redirect to the external article)."""
    st.button(
        story["headline"],
        key=f"{key_prefix}_{index}",
        use_container_width=True,
        on_click=_select_story,
        args=(story,),
    )


def render_story_grid(items, key_prefix, cols_per_row=3):
    ordered = sorted(items, key=lambda s: -s["score"])

    for row_start in range(0, len(ordered), cols_per_row):
        row_items = ordered[row_start:row_start + cols_per_row]
        cols = st.columns(cols_per_row)

        for col, story in zip(cols, row_items):
            with col:
                render_story_card(story, key_prefix, row_start + row_items.index(story))


def render_story_detail(story, category):
    """Jumbo-branded full detail page for a single story: headline,
    flags, summary, why it matters, source/date, and the ONLY link
    to the external article, at the bottom."""
    flags = []

    if story.get("source_count", 1) > 1:
        flags.append(f"✓ {story['source_count']} sources")

    if story.get("duplicate_of"):
        flags.append("🔄 update to earlier story")

    if story["source_mode"] != "article_text":
        flags.append("📄 snippet only")

    if story["unverified_numbers"]:
        flags.append("⚠️ figures not fully verified")

    lead = story["articles"][0]
    publishers = ", ".join(sorted({a["publisher"] for a in story["articles"]}))
    when = lead["published_at"][:16].replace("T", " ")

    mcol, ccol = st.columns([1, 3])

    with mcol:
        show_mascot("thinking", show_bubble=False, size=260, circular=False)

    with ccol:
        if st.button(f"⬅ Back to {category}"):
            st.session_state.stage = "category_view"
            st.rerun()

        st.markdown(f"## {story['headline']}")

        if flags:
            st.caption(" · ".join(flags))

        st.write(story["summary"])
        st.markdown(f"**Why it matters:** {story['why_it_matters']}")
        st.caption(f"{publishers} · {when} IST")
        st.markdown(f"[🔗 Read the full article →]({lead['url']})")


def category_button(category, by_category, leftover, key_prefix):
    items = items_for(category, by_category, leftover)
    emoji = CATEGORY_EMOJI.get(category, "📰")

    clicked = st.button(
        f"{emoji}\n{category}\n{len(items)} stories",
        use_container_width=True,
        key=f"{key_prefix}_{category}",
    )

    if clicked:
        st.session_state.stage = "thumbsup"
        st.session_state.chosen_category = category
        st.rerun()


def render_picker_ring(cats, by_category, leftover, user):
    """Jumbo centered, categories arranged top / sides / bottom."""
    top_row = cats[0:3]
    side_left = cats[3:4]
    side_right = cats[4:5]
    bottom_row = cats[5:8]
    extra = cats[8:]

    if top_row:
        cols = st.columns(len(top_row))
        for col, cat in zip(cols, top_row):
            with col:
                category_button(cat, by_category, leftover, "ring")

    mid_cols = st.columns([1, 2, 1])

    with mid_cols[0]:
        for cat in side_left:
            category_button(cat, by_category, leftover, "ring")

    with mid_cols[1]:
        show_mascot(
            "wave",
            f"Hi {user['name']}! What news would you like to view today?",
            size=200,
            circular=False,
        )

    with mid_cols[2]:
        for cat in side_right:
            category_button(cat, by_category, leftover, "ring")

    if bottom_row:
        cols = st.columns(len(bottom_row))
        for col, cat in zip(cols, bottom_row):
            with col:
                category_button(cat, by_category, leftover, "ring")

    if extra:
        cols = st.columns(len(extra))
        for col, cat in zip(cols, extra):
            with col:
                category_button(cat, by_category, leftover, "ring")


def main():
    apply_theme()
    render_sidebar_brand()

    user = get_current_user()

    if "stage" not in st.session_state:
        st.session_state.stage = None

    if "chosen_category" not in st.session_state:
        st.session_state.chosen_category = None

    if "selected_story" not in st.session_state:
        st.session_state.selected_story = None

    top_banner(get_daily_fact())

    if not user.get("has_seen_intro", 0) and st.session_state.stage is None:
        st.session_state.stage = "intro"

    if st.session_state.stage is None:
        st.session_state.stage = "picker"

    stage = st.session_state.stage

    if stage == "intro":
        show_mascot(
            "wave",
            f"Hi {user['name']}! Did you know? {get_daily_fact()}",
            circular=False,
        )

        if st.button("Got it — let's go!", type="primary"):
            if user.get("id") is not None:
                with closing(db.connect()) as conn:
                    db.mark_intro_seen(conn, user["id"])

            st.session_state.stage = "picker"
            st.rerun()

        return

    if stage == "goodbye":
        show_mascot(
            "wave",
            f"Goodbye {user['name']}!! Hope to see you again tomorrow.",
            circular=False,
        )
        time.sleep(3)
        st.markdown("### 👋 You're all set — you can close this tab now.")
        st.stop()
        return

    run_date, stories = load_latest_briefing()

    if not run_date:
        st.info(
            "No briefing has been generated yet. "
            "Check back after the next scheduled run."
        )
        return

    by_category = group_by_category(stories)
    cats, leftover = display_categories(by_category)

    if stage == "picker":
        render_picker_ring(cats, by_category, leftover, user)
        return

    if stage == "thumbsup":
        show_mascot("thumbsup", "Wow, great choice!", circular=False)
        time.sleep(3)
        st.session_state.stage = "category_view"
        st.rerun()
        return

    if stage == "category_view":
        category = st.session_state.chosen_category
        items = items_for(category, by_category, leftover)
        emoji = CATEGORY_EMOJI.get(category, "📰")

        mcol, ccol = st.columns([1, 3])

        with mcol:
            show_mascot("showing", show_bubble=False, size=260, circular=False)

        with ccol:
            render_message_bubble(
                f"Here's all you need to know about {category} news."
            )

            if st.button("⬅ Exit"):
                st.session_state.stage = "clapping"
                st.rerun()

            st.markdown(f"### {emoji} {category}")

            render_story_grid(items, key_prefix="card")

        return

    if stage == "story_detail":
        story = st.session_state.selected_story
        category = st.session_state.chosen_category

        if not story:
            st.session_state.stage = "category_view"
            st.rerun()
            return

        render_story_detail(story, category)
        return

    if stage == "clapping":
        category = st.session_state.chosen_category

        show_mascot(
            "clapping",
            f"Congrats on reading the {category} news!",
            circular=False,
        )
        time.sleep(3)
        st.session_state.stage = "picker"
        st.rerun()
        return


if __name__ == "__main__":
    main()