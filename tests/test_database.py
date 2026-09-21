import unittest
from datetime import datetime
from pathlib import Path

from agent.summarizer import Summary
from memory import database as db
from news.parser import IST, Article


def make_article(n, publisher="ET"):
    return Article(
        title=f"Headline {n}", snippet="", url=f"https://example.com/{n}", publisher=publisher,
        source_name=publisher, published=datetime(2026, 9, 21, 12, 0, tzinfo=IST),
        hint="general", kind="news",
    )


SUMMARY = Summary(
    "A headline of decent length", "S" * 300, "Why it matters for India and its businesses.",
    ["Tata Sons"], "article_text",
)


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(Path(":memory:"))
        self.run_id = db.get_or_create_run(self.conn, "2026-09-22")

    def test_one_run_per_date(self):
        self.assertEqual(db.get_or_create_run(self.conn, "2026-09-22"), self.run_id)
        self.assertNotEqual(db.get_or_create_run(self.conn, "2026-09-23"), self.run_id)

    def test_story_with_two_outlets_round_trips(self):
        db.add_story(self.conn, self.run_id, "Business", 4, SUMMARY, [make_article(1, "ET"), make_article(2, "Mint")])
        stories = db.list_stories(self.conn, "2026-09-22")
        self.assertEqual(len(stories), 1)
        self.assertEqual([a["publisher"] for a in stories[0]["articles"]], ["ET", "Mint"])
        self.assertEqual(stories[0]["entities"], ["Tata Sons"])
        self.assertEqual(stories[0]["unverified_numbers"], [])

    def test_known_urls_are_detected(self):
        db.add_story(self.conn, self.run_id, "Business", 4, SUMMARY, [make_article(1)])
        self.assertTrue(db.any_url_known(self.conn, ["https://example.com/1"]))
        self.assertFalse(db.any_url_known(self.conn, ["https://example.com/9"]))

    def test_tokens_accumulate(self):
        db.add_tokens(self.conn, self.run_id, 100, 20)
        db.add_tokens(self.conn, self.run_id, 50, 5)
        row = self.conn.execute("SELECT prompt_tokens, completion_tokens FROM runs").fetchone()
        self.assertEqual((row[0], row[1]), (150, 25))


if __name__ == "__main__":
    unittest.main()