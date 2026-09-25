"""Confirms classify_all's circuit breaker trips after 2 consecutive fully-failed
batches (so a Groq outage degrades safely instead of hammering a dead API), and
that ai_unavailable is only True when the breaker actually tripped."""
import unittest
from datetime import datetime
from unittest.mock import patch

from agent import classifier
from news.parser import IST, Article


def make_article(n):
    return Article(
        title=f"Headline {n}", snippet="", url=f"https://example.com/{n}",
        publisher="Test", source_name="Test",
        published=datetime(2026, 9, 21, 12, 0, tzinfo=IST),
        hint="general", kind="news",
    )


class ClassifierCircuitBreakerTests(unittest.TestCase):
    def test_llm_down_trips_breaker_and_flags_ai_unavailable(self):
        articles = [make_article(i) for i in range(50)]  # spans multiple batches of 20
        with patch("agent.llm.complete", side_effect=classifier.llm.LLMError("simulated outage")):
            results, ai_unavailable = classifier.classify_all(articles, batch_size=20)

        self.assertTrue(ai_unavailable)
        self.assertEqual(len(results), 50)  # every article still gets a result, just unrated
        self.assertTrue(all(c.score == 0 for c in results))

    def test_healthy_llm_never_trips_breaker(self):
        articles = [make_article(i) for i in range(20)]
        good_reply = (
            '{"results": ['
            + ",".join(f'{{"id": {i+1}, "category": "AI", "score": 3, "reason": "ok"}}' for i in range(20))
            + "]}"
        )
        with patch("agent.llm.complete", return_value=good_reply):
            results, ai_unavailable = classifier.classify_all(articles, batch_size=20)

        self.assertFalse(ai_unavailable)
        self.assertEqual(len(results), 20)
        self.assertTrue(all(c.score == 3 for c in results))


if __name__ == "__main__":
    unittest.main()