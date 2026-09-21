"""Simple same-headline merge (Session 3).

Several outlets often run the same wire story with almost identical headlines. This groups
those into ONE story, so the daily cap of 15 counts distinct stories, not copies.

Deliberately conservative: a wrong merge hides a real story, a missed merge only shows a
repeat. When unsure, do NOT merge. Session 6 replaces this with embedding-based event detection.
"""
import re
from dataclasses import dataclass, field

MIN_SHARED_WORDS = 4  # headlines must share at least this many meaningful words
MIN_OVERLAP = 0.7     # ...and those must cover 70% of the shorter headline's words

STOPWORDS = {
    "a", "an", "the", "of", "to", "in", "on", "for", "and", "as", "at", "by", "is", "are",
    "be", "with", "from", "its", "it", "this", "that", "after", "over", "amid", "rs",
}


def tokens(title):
    """Set of meaningful lower-case words. Numbers are normalised (2,449 -> 2449)."""
    text = title.lower()
    text = re.sub(r"(?<=\d),(?=\d)", "", text)  # 2,449 -> 2449
    text = re.sub(r"[’']s\b", "", text)         # India's -> India
    words = ["crore" if w == "cr" else w for w in re.findall(r"[a-z0-9]+", text)]
    return {w for w in words if w not in STOPWORDS}


def _same_story(a, b):
    shared = a & b
    if len(shared) < MIN_SHARED_WORDS:
        return False
    if len(shared) / min(len(a), len(b)) < MIN_OVERLAP:
        return False
    numbers_a = {t for t in a if t.isdigit()}
    numbers_b = {t for t in b if t.isdigit()}
    if numbers_a and numbers_b and not (numbers_a & numbers_b):
        return False  # different amounts usually mean different events
    return True


@dataclass
class Story:
    """One story, possibly reported by several outlets.
    In the database: one row in `stories`, one row per item in `articles`."""

    lead: object                                # best-rated item (has .article, .category, .score)
    others: list = field(default_factory=list)  # the same story from other outlets

    @property
    def score(self):
        return self.lead.score

    @property
    def publishers(self):
        seen = []
        for item in [self.lead, *self.others]:
            if item.article.publisher not in seen:
                seen.append(item.article.publisher)
        return seen


def merge_similar(classified):
    """Groups near-identical headlines. The highest-scored item of each group is its lead."""
    ordered = sorted(classified, key=lambda c: (-c.score, -len(c.article.snippet or "")))
    stories, seeds = [], []
    for item in ordered:
        words = tokens(item.article.title)
        for story, seed_words in zip(stories, seeds):
            # compare with the group's first headline only, so chains of near-matches can't drift
            if _same_story(words, seed_words):
                story.others.append(item)
                break
        else:
            stories.append(Story(lead=item))
            seeds.append(words)
    return stories


def select_top_stories(stories, min_score=4, cap=15):
    picks = [s for s in stories if s.score >= min_score]
    picks.sort(key=lambda s: (-s.score, -s.lead.article.published.timestamp()))
    return picks[:cap]