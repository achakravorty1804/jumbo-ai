"""Session 6's threshold was calibrated on one test pair (same-event ~0.79,
unrelated ~0.23). This locks that calibration in so a model/library upgrade
that quietly shifts scores gets caught instead of silently breaking dedup."""
import unittest

from memory import dedup


class DedupTests(unittest.TestCase):
    def test_same_event_reworded_scores_above_threshold(self):
        emb_a = dedup.embed(
            "RBI cuts repo rate by 25 basis points to 6.25%",
            "The Reserve Bank of India lowered its key repo rate by a quarter "
            "point, citing easing inflation and a need to support growth.",
        )
        emb_b = dedup.embed(
            "Reserve Bank trims repo rate 25 bps to 6.25 per cent",
            "India's central bank cut the benchmark repo rate by 25 basis "
            "points to 6.25%, pointing to cooling inflation.",
        )
        sim = dedup.cosine_similarity(dedup._to_vector(emb_a), dedup._to_vector(emb_b))
        self.assertGreaterEqual(sim, dedup.SIMILARITY_THRESHOLD)

    def test_unrelated_stories_score_below_threshold(self):
        emb_a = dedup.embed(
            "RBI cuts repo rate by 25 basis points to 6.25%",
            "The Reserve Bank of India lowered its key repo rate.",
        )
        emb_b = dedup.embed(
            "Startup raises $40 million in Series B funding round",
            "A Bengaluru-based fintech startup closed a $40 million round "
            "led by a US venture capital firm.",
        )
        sim = dedup.cosine_similarity(dedup._to_vector(emb_a), dedup._to_vector(emb_b))
        self.assertLess(sim, dedup.SIMILARITY_THRESHOLD)


if __name__ == "__main__":
    unittest.main()