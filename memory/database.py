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
    published_at TEXT NOT NULL,
    is_lead INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_stories_run ON stories(run_id);
CREATE INDEX IF NOT EXISTS idx_articles_story ON articles(story_id);
CREATE TABLE IF NOT EXISTS chat_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,   -- groups messages into one chat session
    role TEXT NOT NULL,              -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chat_log_conv ON chat_log(conversation_id);
"""


def _now():
    return datetime.now(IST).isoformat(timespec="seconds")


def connect(path=DB_PATH):
    if str(path) != ":memory:":
        path.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    # Old day-grouped chat_log schema from early testing; drop it before running
    # the current SCHEMA, since it lacks the conversation_id column the new
    # schema's index requires. Only ever contained test data, safe to replace.
    existing = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='chat_log'"
    ).fetchone()
    if existing:
        chat_cols = {row["name"] for row in conn.execute("PRAGMA table_info(chat_log)")}
        if "conversation_id" not in chat_cols:
            conn.execute("DROP TABLE chat_log")

    conn.executescript(SCHEMA)
    _migrate(conn)
    return conn

def _migrate(conn):
    cols = {row["name"] for row in conn.execute("PRAGMA table_info(stories)")}
    if "embedding" not in cols:
        conn.execute("ALTER TABLE stories ADD COLUMN embedding BLOB")
    if "duplicate_of" not in cols:
        conn.execute("ALTER TABLE stories ADD COLUMN duplicate_of INTEGER REFERENCES stories(id)")
    if "source_count" not in cols:
        conn.execute("ALTER TABLE stories ADD COLUMN source_count INTEGER NOT NULL DEFAULT 1")

    conn.commit()

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


def increment_source_count(conn, story_id, by=1):
    """Called when a later report is found to be an update of an earlier story (cross-day dedup)."""
    with conn:
        conn.execute(
            "UPDATE stories SET source_count = source_count + ? WHERE id = ?",
            (by, story_id),
        )


def add_story(conn, run_id, category, score, summary, articles, embedding=None, duplicate_of=None, source_count=1):
    """Saves one story and its article(s) in a single transaction. The first article is the lead."""
    with conn:
        cur = conn.execute(
            "INSERT INTO stories (run_id, category, score, headline, summary, why_it_matters, "
            "source_mode, unverified_numbers, entities, created_at, embedding, duplicate_of, source_count) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                run_id, category, score, summary.headline, summary.summary, summary.why_it_matters,
                summary.source_mode,
                json.dumps(summary.unverified_numbers) if summary.unverified_numbers else None,
                json.dumps(summary.entities, ensure_ascii=False),
                _now(), embedding, duplicate_of, source_count,
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

def add_chat_message(conn, conversation_id, role, content):
    with conn:
        conn.execute(
            "INSERT INTO chat_log (conversation_id, role, content, created_at) VALUES (?,?,?,?)",
            (conversation_id, role, content, _now()),
        )


def get_chat_history(conn, conversation_id):
    rows = conn.execute(
        "SELECT role, content FROM chat_log WHERE conversation_id = ? ORDER BY id", (conversation_id,)
    ).fetchall()
    return [(row["role"], row["content"]) for row in rows]


def list_conversations(conn):
    """One row per conversation: its id, a title (first user message), and last activity time."""
    rows = conn.execute(
        """
        SELECT conversation_id,
               MIN(CASE WHEN role = 'user' THEN content END) AS title,
               MAX(created_at) AS last_active
        FROM chat_log
        GROUP BY conversation_id
        ORDER BY last_active DESC
        """
    ).fetchall()
    return [dict(row) for row in rows]