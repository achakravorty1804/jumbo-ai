"""Prints the latest saved briefing so you can read it and spot-check it.
  python -m memory.show_briefing             (all stories)
  python -m memory.show_briefing welspun     (only stories with that word in the headline)"""
import sys
from contextlib import closing

from memory import database as db

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    word = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    with closing(db.connect()) as conn:
        row = conn.execute("SELECT run_date FROM runs ORDER BY run_date DESC LIMIT 1").fetchone()
        if not row:
            sys.exit("No briefing saved yet")
        print(f"Briefing for {row['run_date']}")
        for s in db.list_stories(conn, row["run_date"]):
            if word and word not in s["headline"].lower():
                continue
            print("=" * 72)
            print(f"{s['category']} | score {s['score']} | {s['source_mode']}")
            print(s["headline"])
            print(s["summary"])
            print("WHY:", s["why_it_matters"])
            print("UNVERIFIED NUMBERS:", s["unverified_numbers"] or "none")
            for a in s["articles"]:
                print(f"  {a['publisher']}: {a['url']}")