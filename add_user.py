"""Add a new person who can access Jumbo. Run once per new user.

Usage:
    python add_user.py "Full Name" "email@gmail.com"

Generates a slug from the name (lowercase, first name only, deduped if
already taken), inserts into the users table, and prints the link they'll
get in their email. No further wiring needed — run_daily.py already loops
over db.list_users() for every send, and the dashboard/Ask Jumbo already
work for any slug in the table.
"""
import sys
import re
from memory import database as db


def make_slug(name, conn):
    base = re.sub(r"[^a-z]", "", name.strip().split()[0].lower())
    if not base:
        raise ValueError("Couldn't derive a slug from that name.")
    slug = base
    i = 2
    while db.get_user_by_slug(conn, slug):
        slug = f"{base}{i}"
        i += 1
    return slug


def main():
    if len(sys.argv) != 3:
        print('Usage: python add_user.py "Full Name" "email@gmail.com"')
        sys.exit(1)

    name, email = sys.argv[1], sys.argv[2]
    conn = db.connect()

    slug = make_slug(name, conn)
    try:
        db.add_user(conn, name, email, slug)
    except Exception as e:
        print(f"❌ Couldn't add user: {e}")
        sys.exit(1)

    print(f"✅ Added {name} <{email}> with slug '{slug}'")
    print(f"   They'll get tomorrow's email with a link like: ...?user={slug}")


if __name__ == "__main__":
    main()