import time

import requests
import feedparser

# Candidate feeds. Some URLs are from memory and may be dead. That's exactly what this test finds out.
CANDIDATE_FEEDS = {
    "ET Top Stories": "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
    "ET Markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "ET Tech": "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
    "ET Industry": "https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms",
    "ET Economy": "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms",
    "Business Standard Top": "https://www.business-standard.com/rss/home_page_top_stories.rss",
    "Business Standard Economy": "https://www.business-standard.com/rss/economy-policy-102.rss",
    "Mint Companies": "https://www.livemint.com/rss/companies",
    "Mint Technology": "https://www.livemint.com/rss/technology",
    "Mint Markets": "https://www.livemint.com/rss/markets",
    "BusinessLine": "https://www.thehindubusinessline.com/feeder/default.rss",
    "TechCrunch": "https://techcrunch.com/feed/",
    "Moneycontrol Business": "https://www.moneycontrol.com/rss/business.xml",
    "RBI Press Releases": "https://www.rbi.org.in/pressreleases_rss.xml",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JumboNewsBot/0.1)"}


def check_feed(name, url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        if not parsed.entries:
            return f"EMPTY   {name}: reachable but no entries"
        latest = parsed.entries[0].get("published", "no date")
        return f"OK      {name}: {len(parsed.entries)} entries | latest: {latest}"
    except Exception as e:
        return f"FAILED  {name}: {type(e).__name__}: {str(e)[:80]}"


if __name__ == "__main__":
    for feed_name, feed_url in CANDIDATE_FEEDS.items():
        print(check_feed(feed_name, feed_url))
        time.sleep(1)