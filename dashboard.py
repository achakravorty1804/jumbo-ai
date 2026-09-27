"""Jumbo's daily briefing dashboard. Read-only: shows the latest saved run from data/jumbo.db.
Run locally with:  streamlit run dashboard.py"""

import time
from contextlib import closing
from datetime import date

import streamlit as st
import streamlit.components.v1 as components

from memory import database as db
from mascot import show_mascot, COLOR_BUBBLE_BG, COLOR_BUBBLE_BORDER, COLOR_TEXT
from theme import (
    apply_theme,
    render_sidebar_brand,
    top_banner,
    render_fact_bubble,
    confirm_exit_dialog,
    PINK_SOFT,
    PINK_BORDER,
    NAVY,
)

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
    slug = st.query_params.get("user") or st.session_state.get("user_slug")

    if not slug:
        st.warning("🐘 Please open your personal Jumbo link to continue.")
        st.stop()

    st.session_state["user_slug"] = slug
    with closing(db.connect()) as conn:
        user = db.get_user_by_slug(conn, slug)

        if user:
            st.query_params["user"] = slug
            return dict(user)

    st.warning("🐘 We couldn't recognize that link. Please check it and try again.")
    st.stop()

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

    return [s for s in items if s.get("headline") and s["headline"].strip()]


def render_message_bubble(message):
    st.markdown(
        f"""
        <div style="
            background: {COLOR_BUBBLE_BG};
            border: 2px solid {COLOR_BUBBLE_BORDER};
            border-radius: 18px;
            padding: 8px 14px;
            margin-bottom: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            display: inline-block;
            max-width: 100%;
        ">
            <p style="
                margin: 0;
                color: {COLOR_TEXT};
                font-size: 13px;
                line-height: 1.45;
            ">{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def _select_story(story):
    st.session_state.stage = "story_detail"
    st.session_state.selected_story = story


def render_story_card(story, key_prefix, index):
    with st.container(key=f"tile_wrap_{key_prefix}_{index}"):
        st.button(
            story["headline"],
            key=f"{key_prefix}_{index}",
            use_container_width=True,
            on_click=_select_story,
            args=(story,),
        )

def render_story_grid(items, key_prefix, cols_per_row=3):
    ordered = sorted(items, key=lambda s: -s["score"])

    with st.container(key="story_tile_stack"):
        for i, story in enumerate(ordered):
            render_story_card(story, key_prefix, i)

def render_story_detail(story, category):
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
        st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
        show_mascot("news", show_bubble=False, size=275, circular=False)
    with ccol:
        if st.button(f"⬅ Back to {category}", key="back_to_category"):
            st.session_state.stage = "category_view"
            st.rerun()

        st.markdown(f"## {story['headline']}")

        if flags:
            st.caption(" · ".join(flags))

        st.write(story["summary"])
        st.markdown(f"**Why it matters:** {story['why_it_matters']}")
        st.caption(f"{publishers} · {when} IST")
        st.markdown(f"[🔗 Read the full article →]({lead['url']})")

def render_about_us(user):
    st.markdown(
        """
        <div style="text-align:center; margin-bottom:4px;">
        <div style="font-size:11px; ...">MEET YOUR NEWS COMPANION</div>
        <h1 style="font-size:26px; font-weight:800; margin:0;">About Jumbo 🐘</h1>
        <p style="font-size:13px; color:#777; margin-top:2px;">
                A smarter, simpler way to stay informed.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    mcol, ccol = st.columns([1, 3])

    with mcol:
        show_mascot("namaste", show_bubble=False, size=280, circular=False)
        render_message_bubble("Hi "+user["name"]+"! I am Jumbo - here is everything you need to know about me.")

    with ccol:
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📰  The Problem", "💡  Why I Was Built", "⚡  What I Can Do", "🛡️  What I Can't Do Yet"]
        )

        with tab1:
            st.markdown(
                """
                <div class="jumbo-info-card">
                    <div class="jumbo-card-title">The news shouldn't feel like homework. 📚</div>
                    <div class="jumbo-item">📰 <b>Old-school news</b><br><span>Newspapers were part of the morning — but who really has time for that anymore?</span></div>
                    <div class="jumbo-item">📱 <b>Too much noise</b><br><span>We're on our phones all day, yet somehow important news still slips right past us.</span></div>
                    <div class="jumbo-item">🗞️ <b>Information overload</b><br><span>Ads, pop-ups and clutter can make even one article exhausting to read.</span></div>
                    <div class="jumbo-item">🤳 <b>Social media isn't enough</b><br><span>It's fast and convenient, but important stories can be difficult to verify.</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with tab2:
            st.markdown(
                """
                <div class="jumbo-info-card">
                    <div class="jumbo-card-title">That's exactly why I exist. 💙</div>
                    <p class="jumbo-big-text">I'm <b>Jumbo</b> — your personalized digital AI news agent.</p>
                    <p>Every morning, I mail you a clean digest of yesterday's most important stories.</p>
                    <div class="jumbo-highlight">✨ No clutter &nbsp;•&nbsp; 🚫 No ads &nbsp;•&nbsp; 🧠 No doomscrolling</div>
                    <p>Just what actually matters, ready when you wake up.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with tab3:
            st.markdown(
                """
                <div class="jumbo-info-card">
                    <div class="jumbo-card-title">Here's what I can do for you. ⚡</div>
                    <div class="jumbo-grid">
                        <div>📧<b>Daily Digest</b><small>Morning stories delivered to you</small></div>
                        <div>🗂️<b>Many Domains</b><small>AI, startups, India, global & more</small></div>
                        <div>🔍<b>Source Checking</b><small>Multiple sources for significance</small></div>
                        <div>🇮🇳<b>India Lens</b><small>Understand the local impact</small></div>
                        <div>💬<b>Ask Jumbo</b><small>Ask about today's news anytime</small></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with tab4:
            st.markdown(
                """
                <div class="jumbo-info-card">
                    <div class="jumbo-card-title">A few things I won't pretend to do. 🛡️</div>
                    <div class="jumbo-item">🎯 <b>No clickbait</b><br><span>If it's not significant, I skip it.</span></div>
                    <div class="jumbo-item">🔮 <b>No future predictions</b><br><span>I report what's happened rather than pretending to know what's next.</span></div>
                    <div class="jumbo-item">📰 <b>Not a replacement for journalism</b><br><span>Think of me as your shortcut to the news worth knowing.</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_contact_info():
    st.markdown(
        """
        <div style="text-align:center; margin-bottom:18px;">
            <div style="font-size:13px; letter-spacing:3px; font-weight:800; color:#E85D9E;">LET'S CONNECT</div>
            <h1 style="font-size:40px; font-weight:800; margin:4px 0;">Contact Jumbo 💌</h1>
            <p style="font-size:16px; color:#777; margin-top:4px;">
                Questions, ideas, feedback — I'd love to hear from you.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    mcol, ccol = st.columns([1, 3])

    with mcol:
        show_mascot("showing", show_bubble=False, size=280, circular=False)

    with ccol:
        st.markdown(
            """
            <div class="contact-card">
                <div class="contact-title">📬 Get in touch</div>
                <p class="contact-subtitle">Whether you have a suggestion or simply want to say hello, here's where you can find me.</p>
                <div class="contact-row">
                    <div class="contact-icon">👤</div>
                    <div><small>NAME</small><strong>Akash Chakravorty</strong></div>
                </div>
                <div class="contact-row">
                    <div class="contact-icon">✉️</div>
                    <div><small>EMAIL</small><strong>achakravorty1804@gmail.com</strong></div>
                </div>
                <div class="contact-row">
                    <div class="contact-icon">📱</div>
                    <div><small>PHONE</small><strong>+91 8617738746</strong></div>
                </div>
                <div class="contact-row">
                    <div class="contact-icon">🔗</div>
                    <div><small>LINKEDIN</small>
                        <a href="https://www.linkedin.com/in/akash-chakravorty-a681212ab/" target="_blank">akash-chakravorty-a681212ab ↗</a>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
def category_button(category, by_category, leftover, key_prefix):
    """One category tile, wrapped in a keyed container so theme.py's
    CSS (targeting the "st-key-ring_..." class) can style ONLY these
    picker buttons — bigger, bolder, decorated — without touching
    Exit, Ask Jumbo, or the story-card buttons elsewhere in the app."""
    items = items_for(category, by_category, leftover)
    emoji = CATEGORY_EMOJI.get(category, "📰")

    safe_key = f"ring_{key_prefix}_{category}".replace(" ", "_").replace("&", "and")

    with st.container(key=safe_key):
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
    points = {"top": [], "left": [], "right": []}
    point_order = ["top", "left", "right", "left", "right"]

    for i, cat in enumerate(cats):
        points[point_order[i % 5]].append(cat)

    if points["top"]:
        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            for cat in points["top"]:
                category_button(cat, by_category, leftover, "ring")

    left_col, center_col, right_col = st.columns([1, 2, 1])

    with left_col:
        for cat in points["left"]:
            category_button(cat, by_category, leftover, "ring")

    with center_col:
        show_mascot(
            "wave",
            f"Hi {user['name']}! What news would you like to view today?",
            size=275,
            circular=False,
        )

    with right_col:
        for cat in points["right"]:
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

    if "want_exit_confirm" not in st.session_state:
        st.session_state.want_exit_confirm = False

    if st.session_state.want_exit_confirm:
        confirm_exit_dialog()

    top_banner()

    if st.session_state.stage is None:
        st.session_state.stage = "intro"

    if st.session_state.stage is None:
        st.session_state.stage = "picker"

    stage = st.session_state.stage

    # "Did you know?" only ever shows on the home picker page — not
    # on intro, thumbsup, category_view, story_detail, clapping, or
    # goodbye.
    if stage == "picker":
        render_fact_bubble(get_daily_fact())

    if stage == "intro":
        show_mascot(
            "namaste",
            f"Welcome back {user['name']}! I am Jumbo, your digital AI news "
            f"assistant, and I'll keep you updated with what's going on in "
            f"the world.",
            circular=False,
            size=300,
        )
        time.sleep(3)
        st.session_state.stage = "picker"
        st.rerun()
        return

    if stage == "goodbye":
        show_mascot(
            "wave",
            f"Goodbye {user['name']}!! Hope to see you again tomorrow.",
            circular=False,
            size=300,
        )
        time.sleep(3)
        st.markdown("### 👋 You're all set — you can close this tab now.")

        components.html("<script>window.close();</script>", height=0)

        st.stop()
        return

    if stage == "about_us":
        render_about_us(user)
        return

    if stage == "contact_info":
        render_contact_info()
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
        show_mascot("thumbsup", "Wow, great choice!", circular=False, size=420)
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
            st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
            show_mascot("showing", show_bubble=False, size=320, circular=False)
            render_message_bubble(
                f"Here's all you need to know about {category} news."
            )

        with ccol:
            if st.button("Back to Home", key="back_to_home"):
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
            size=420,
        )
        time.sleep(3)
        st.session_state.stage = "picker"
        st.rerun()
        return


if __name__ == "__main__":
    main()