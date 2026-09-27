# send_today_to_family.py — one-off manual send, TODAY's briefing only, to Tapas and Debjani.
from contextlib import closing
from urllib.parse import urlencode

from memory import database as db
from mailer.sender import send_email

dashboard_url = "https://jumbo-ai-dpdqoyag5ko7krhwt7vrml.streamlit.app/"
TARGET_SLUGS = {"tapas", "debjani", "akash", "babu", "adrija2"}

with closing(db.connect()) as conn:
    row = conn.execute(
        "SELECT run_date FROM runs ORDER BY run_date DESC LIMIT 1"
    ).fetchone()
    run_date = row["run_date"]
    stories = db.list_stories(conn, run_date)
    story_count = len(stories)

    all_users = db.list_users(conn)

targets = [u for u in all_users if u["slug"] in TARGET_SLUGS]

if not targets:
    raise SystemExit(f"No users found matching slugs {TARGET_SLUGS}")

subject = "🐘 Jumbo — Your daily intelligence briefing is ready"

for user in targets:
    personalized_url = f"{dashboard_url}?{urlencode({'user': user['slug']})}"
    body = f"""🐘 Hey {user['name']}!

I'm Jumbo, your personal AI news assistant.

I've been keeping track of what's happening around the world and your daily intelligence briefing is ready.

Today's briefing contains {story_count} stories. (Run date: {run_date})

OPEN JUMBO:
{personalized_url}

— Jumbo
"""
    send_email(subject=subject, body=body, recipient=user["email"])
    print(f"Sent to {user['name']} <{user['email']}>")

print(f"\nDone. {len(targets)} email(s) sent for run_date {run_date}.")