"""SQLite storage for Jumbo (Session 3: runs, stories, articles).

A story is one event. It can have several articles (one per outlet). Session 6 will fill in
more articles per story as duplicates are merged. We store only our own summaries, plus titles,
URLs, publishers and times. Article text is never stored."""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from news.parser import IST

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jumbo.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date TEXT NOT NULL UNIQUE,            -- one briefing per IST date
    created_at TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0, -- LLM usage recorded for this run
    completion_tokens INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    category TEXT NOT NULL,
    score INTEGER NOT NULL,
    headline TEXT NOT NULL,
    summary TEXT NOT NULL,
    why_it_matters TEXT NOT NULL,
    source_mode TEXT NOT NULL,                -- article_text or snippet_only
    unverified_numbers TEXT,                  -- JSON list, or NULL when all numbers checked out
    entities TEXT NOT NULL,                   -- JSON list
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER NOT NULL REFERENCES stories(id),
    url TEXT NOT NULL UNIQUE,
    original_title TEXT NOT NULL,
    publisher TEXT NOT NULL,
    published_at TEXT NOT NULL,               -- ISO 8601 with +05:30
    is_lead INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_stories_run ON stories(run_id);
CREATE INDEX IF NOT EXISTS idx_articles_story ON articles(story_id);
"""


def _now():
    return datetime.now(IST).isoformat(timespec="seconds")


def connect(path=DB_PATH):
    if str(path) != ":memory:":
        path.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def get_or_create_run(conn, run_date):
    row = conn.execute("SELECT id FROM runs WHERE run_date = ?", (run_date,)).fetchone()
    if row:
        return row["id"]
    with conn:
        cur = conn.execute("INSERT INTO runs (run_date, created_at) VALUES (?, ?)", (run_date, _now()))
    return cur.lastrowid


def any_url_known(conn, urls):
    """True if any of these article URLs is already saved. This is how re-runs skip finished work."""
    for url in urls:
        if conn.execute("SELECT 1 FROM articles WHERE url = ?", (url,)).fetchone():
            return True
    return False


def add_tokens(conn, run_id, prompt_tokens, completion_tokens):
    with conn:
        conn.execute(
            "UPDATE runs SET prompt_tokens = prompt_tokens + ?, completion_tokens = completion_tokens + ? WHERE id = ?",
            (prompt_tokens, completion_tokens, run_id),
        )


def add_story(conn, run_id, category, score, summary, articles):
    """Saves one story and its article(s) in a single transaction. The first article is the lead."""
    with conn:
        cur = conn.execute(
            "INSERT INTO stories (run_id, category, score, headline, summary, why_it_matters, "
            "source_mode, unverified_numbers, entities, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                run_id, category, score, summary.headline, summary.summary, summary.why_it_matters,
                summary.source_mode,
                json.dumps(summary.unverified_numbers) if summary.unverified_numbers else None,
                json.dumps(summary.entities, ensure_ascii=False),
                _now(),
            ),
        )
        story_id = cur.lastrowid
        for i, a in enumerate(articles):
            conn.execute(
                "INSERT OR IGNORE INTO articles (story_id, url, original_title, publisher, published_at, is_lead) "
                "VALUES (?,?,?,?,?,?)",
                (story_id, a.url, a.title, a.publisher, a.published.isoformat(timespec="seconds"), 1 if i == 0 else 0),
            )
    return story_id


def list_stories(conn, run_date):
    """Everything the dashboard needs for one day's briefing, as plain dicts."""
    rows = conn.execute(
        "SELECT s.* FROM stories s JOIN runs r ON r.id = s.run_id WHERE r.run_date = ? ORDER BY s.score DESC, s.id",
        (run_date,),
    ).fetchall()
    stories = []
    for row in rows:
        story = dict(row)
        story["entities"] = json.loads(story["entities"])
        story["unverified_numbers"] = json.loads(story["unverified_numbers"] or "[]")
        story["articles"] = [
            dict(a)
            for a in conn.execute(
                "SELECT * FROM articles WHERE story_id = ? ORDER BY is_lead DESC, id", (story["id"],)
            )
        ]
        stories.append(story)
    return stories