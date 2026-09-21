import itertools
import unittest
from datetime import datetime
from types import SimpleNamespace

from agent.merge import merge_similar, select_top_stories, tokens
from news.parser import IST, Article

_ids = itertools.count(1)


def item(title, publisher="Test", score=4, snippet="", minute=0):
    """A stand-in for a classified article."""
    article = Article(
        title=title,
        snippet=snippet,
        url=f"https://example.com/{next(_ids)}",
        publisher=publisher,
        source_name=publisher,
        published=datetime(2026, 9, 21, 12, minute, tzinfo=IST),
        hint="general",
        kind="news",
    )
    return SimpleNamespace(article=article, category="Business", score=score, reason="")


COAL_BL = "Nearly 40% of coal power plants face critically low fuel stocks"
COAL_ET = "Nearly 40% of India's coal power plants running critically low on fuel, data show"
CHIP_ET = "India needs to move beyond chip manufacturing, use Indian chips in products designed and made locally: Report"
CHIP_BL = "India needs to move beyond chip manufacturing, use Indian chips in locally made products: Report"
IOCL_BL = "Indian Oil to invest ₹2,449 crore for Kochi-Thoothukudi natural gas pipeline"
IOCL_ET = "IOCL to plug Rs 2,449 cr for natural gas pipeline"
TATA_1 = "Tata Trusts rejects board's claim on Chandrasekaran vote, cites governing rules"
TATA_2 = "Noel Tata challenges legality of N. Chandrasekaran’s reappointment as Tata Sons Chairman"
STARBUCKS_1 = "Starbucks to set up its first India GCC in Chennai"
STARBUCKS_2 = "Starbucks plans Chennai GCC with 800 new jobs"


class MergeTests(unittest.TestCase):
    def test_tokens_normalise_numbers_and_possessives(self):
        self.assertEqual(tokens("India's ₹2,449 crore"), {"india", "2449", "crore"})

    def test_wire_copy_with_light_rewording_merges(self):
        stories = merge_similar([item(COAL_BL, "BusinessLine"), item(COAL_ET, "ET")])
        self.assertEqual(len(stories), 1)
        self.assertEqual(set(stories[0].publishers), {"BusinessLine", "ET"})

    def test_abbreviated_headline_merges(self):
        stories = merge_similar([item(IOCL_BL, "BusinessLine"), item(IOCL_ET, "ET")])
        self.assertEqual(len(stories), 1)

    def test_three_outlets_become_one_story(self):
        stories = merge_similar(
            [item(CHIP_ET, "ET"), item(CHIP_ET, "Mint"), item(CHIP_BL, "BusinessLine")]
        )
        self.assertEqual(len(stories), 1)
        self.assertEqual(len(stories[0].others), 2)

    def test_related_but_different_stories_stay_separate(self):
        self.assertEqual(len(merge_similar([item(TATA_1), item(TATA_2)])), 2)

    def test_different_amounts_do_not_merge(self):
        stories = merge_similar(
            [item("HDFC Bank raises ₹5,000 crore via bonds"), item("HDFC Bank raises ₹3,000 crore via bonds")]
        )
        self.assertEqual(len(stories), 2)

    def test_known_limit_same_event_reworded_is_not_merged(self):
        # Session 6 (embeddings) should catch this. Until then a repeat beats a wrong merge.
        self.assertEqual(len(merge_similar([item(STARBUCKS_1), item(STARBUCKS_2)])), 2)

    def test_story_takes_the_best_score_and_lead(self):
        stories = merge_similar(
            [item(COAL_BL, "BusinessLine", score=3), item(COAL_ET, "ET", score=4)]
        )
        self.assertEqual(stories[0].score, 4)
        self.assertEqual(stories[0].lead.article.publisher, "ET")

    def test_cap_counts_distinct_stories(self):
        items = [
            item(CHIP_ET, "ET", 5),
            item(CHIP_ET, "Mint", 5),
            item(CHIP_BL, "BusinessLine", 5),
            item("Chalet Hotels in advanced talks to buy Six Senses Vana for Rs 600 crore", score=4, minute=1),
            item("Inox Clean Energy set to buy Actis-owned Athena Renewables for Rs 2,500 crore", score=4, minute=2),
            item("Welspun Corp bags Rs 2,000 crore order from Saudi Aramco", score=4, minute=3),
        ]
        picks = select_top_stories(merge_similar(items), min_score=4, cap=3)
        self.assertEqual(len(picks), 3)
        self.assertTrue(picks[0].lead.article.title.startswith("India needs to move"))
        self.assertEqual(len({p.lead.article.title for p in picks}), 3)


if __name__ == "__main__":
    unittest.main()