# test_send_email.py — temporary, one-off test. Sends ONLY to Akash. Safe to delete after.
from contextlib import closing
from urllib.parse import urlencode

from memory import database as db
from mailer.sender import send_email

dashboard_url = "https://jumbo-ai-dpdqoyag5ko7krhwt7vrml.streamlit.app/"

with closing(db.connect()) as conn:
    row = conn.execute(
        "SELECT run_date FROM runs ORDER BY run_date DESC LIMIT 1"
    ).fetchone()
    run_date = row["run_date"]
    stories = db.list_stories(conn, run_date)

    akash = None
    for user in db.list_users(conn):
        if user["slug"] == "akash":
            akash = user
            break

if not akash:
    raise SystemExit("Could not find a user with slug 'akash' in the DB.")

story_count = len(stories)
personalized_url = f"{dashboard_url}?{urlencode({'user': akash['slug']})}"

subject = "🐘 Jumbo — Your daily intelligence briefing is ready (TEST)"
body = f"""🐘 Hey {akash['name']}!

I'm Jumbo, your personal AI news assistant.

I've been keeping track of what's happening around the world and your daily intelligence briefing is ready.

Today's briefing contains {story_count} stories. (Run date: {run_date})

OPEN JUMBO:
{personalized_url}

— Jumbo
"""

send_email(subject=subject, body=body, recipient=akash["email"])
print(f"Sent to {akash['email']} — {story_count} stories from run_date {run_date}")