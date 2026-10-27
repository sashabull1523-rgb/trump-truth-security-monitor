
import requests
import xml.etree.ElementTree as ET
from html import unescape
from datetime import datetime, timezone

FEED_URL = "https://www.trumpstruth.org/feed"


def fetch_posts(limit=100):
    """Fetch recent public Trump posts from the RSS archive."""
    response = requests.get(
        FEED_URL,
        params={"limit": min(max(int(limit), 1), 500)},
        headers={"User-Agent": "Trump-International-Affairs-Monitor/1.0"},
        timeout=30,
    )
    response.raise_for_status()

    root = ET.fromstring(response.content)
    posts = []

    for item in root.findall(".//item"):
        title = item.findtext("title", default="")
        description = item.findtext("description", default="")
        link = item.findtext("link", default="")
        pub_date = item.findtext("pubDate", default="")

        text = unescape(description or title).strip()
        if not text:
            continue

        posts.append({
            "id": link or title,
            "text": text,
            "url": link,
            "created_at": pub_date,
        })

    return posts


if __name__ == "__main__":
    try:
        posts = fetch_posts()
        print(f"Retrieved {len(posts)} posts.")

        for post in posts[:5]:
            print("\n", post["created_at"])
            print(post["text"][:300])
            print(post["url"])

    except (requests.RequestException, ET.ParseError, ValueError) as error:
        print(f"Could not retrieve posts: {error}")
        raise

