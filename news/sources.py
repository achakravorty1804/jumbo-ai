from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    name: str            # unique feed name
    publisher: str       # shown on story cards
    url: str
    hint: str            # rough topic hint, used later by the classifier
    kind: str = "news"   # "news" or "official"
    enabled: bool = True


SOURCES = [
    Source("ET Top Stories", "Economic Times", "https://economictimes.indiatimes.com/rssfeedstopstories.cms", "general"),
    Source("ET Markets", "Economic Times", "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms", "markets"),
    Source("ET Tech", "Economic Times", "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms", "technology"),
    Source("ET Industry", "Economic Times", "https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms", "industry"),
    Source("ET Economy", "Economic Times", "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms", "economy"),
    Source("Mint Companies", "Mint", "https://www.livemint.com/rss/companies", "business"),
    Source("Mint Technology", "Mint", "https://www.livemint.com/rss/technology", "technology"),
    Source("Mint Markets", "Mint", "https://www.livemint.com/rss/markets", "markets"),
    Source("BusinessLine", "The Hindu BusinessLine", "https://www.thehindubusinessline.com/feeder/default.rss", "general"),
    Source("TechCrunch", "TechCrunch", "https://techcrunch.com/feed/", "technology"),
    Source("RBI Press Releases", "Reserve Bank of India", "https://www.rbi.org.in/pressreleases_rss.xml", "economy", kind="official"),
    # Blocked (HTTP 403) when tested from a home connection, so disabled:
    Source("Business Standard Top", "Business Standard", "https://www.business-standard.com/rss/home_page_top_stories.rss", "general", enabled=False),
    Source("Business Standard Economy", "Business Standard", "https://www.business-standard.com/rss/economy-policy-102.rss", "economy", enabled=False),
    Source("Moneycontrol Business", "Moneycontrol", "https://www.moneycontrol.com/rss/business.xml", "business", enabled=False),
]


def enabled_sources():
    return [s for s in SOURCES if s.enabled]