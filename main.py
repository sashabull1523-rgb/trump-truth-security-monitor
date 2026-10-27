
import os
import re
import smtplib
import requests
import xml.etree.ElementTree as ET

from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser


# ============================================================
# CONFIGURATION
# ============================================================

RSS_URL = "https://www.trumpstruth.org/feed"
POST_LIMIT = 100
HOURS_TO_CHECK = 24

EMAIL_ADDRESS = os.environ["EMAIL_ADDRESS"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
EMAIL_TO = os.environ["EMAIL_TO"]


# ============================================================
# KEYWORDS
# ============================================================

KEYWORDS = [
    # Foreign policy and diplomacy
    "foreign policy", "diplomacy", "diplomatic", "ambassador",
    "embassy", "state department", "secretary of state",
    "foreign minister", "summit", "treaty", "bilateral",

    # Alliances and international organizations
    "nato", "united nations", "security council", "alliance",
    "allies", "g7", "g20", "brics", "european union",

    # Countries and regions
    "ukraine", "russia", "china", "taiwan", "iran", "israel",
    "gaza", "palestine", "hamas", "hezbollah", "lebanon",
    "syria", "iraq", "yemen", "north korea", "south korea",
    "venezuela", "cuba", "mexico", "canada", "afghanistan",
    "pakistan", "india", "greenland", "africa", "japan",
    "saudi arabia", "united kingdom", "britain", "france",
    "germany", "australia", "colombia", "brazil",

    # Military and national security
    "national security", "military", "defense", "defence",
    "pentagon", "armed forces", "troops", "missile", "nuclear",
    "terrorism", "terrorist", "intelligence", "cybersecurity",
    "cyber attack", "ceasefire", "invasion", "airstrike",
    "air strike", "weapons", "warfare", "peace deal",
    "peace agreement", "hostage", "military operation",

    # Trade and economic statecraft
    "tariff", "tariffs", "trade agreement", "trade deal",
    "foreign aid", "sanctions", "export controls", "oil prices",
    "world bank", "international monetary fund", "imf",
]


# ============================================================
# HTML CLEANING
# ============================================================

class TextExtractor(HTMLParser):
    """Convert HTML content into readable text."""

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self):
        return " ".join(self.parts)


def clean_text(value):
    value = unescape(value or "")
    parser = TextExtractor()

    try:
        parser.feed(value)
        value = parser.get_text()
    except Exception:
        pass

    return re.sub(r"\s+", " ", value).strip()


# ============================================================
# FETCH POSTS
# ============================================================

def fetch_posts(limit=POST_LIMIT):
    """Fetch posts from the public RSS feed."""

    print("Connecting to the public posts feed...")

    response = requests.get(
        RSS_URL,
        params={"limit": min(max(int(limit), 1), 500)},
        headers={
            "User-Agent": "Trump-International-Affairs-Monitor/1.0"
        },
        timeout=30,
    )

    print("Feed HTTP status:", response.status_code)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    posts = []

    for item in root.findall(".//item"):
        title = clean_text(item.findtext("title", default=""))
        description = clean_text(
            item.findtext("description", default="")
        )
        link = item.findtext("link", default="").strip()
        pub_date = item.findtext("pubDate", default="").strip()

        text = description or title

        if not text:
            continue

        published = None

        if pub_date:
            try:
                published = parsedate_to_datetime(pub_date)

                if published.tzinfo is None:
                    published = published.replace(
                        tzinfo=timezone.utc
                    )

                published = published.astimezone(timezone.utc)

            except (TypeError, ValueError, OverflowError):
                published = None

        posts.append({
            "id": link or title,
            "text": text,
            "url": link,
            "created_at": published,
        })

    # Avoid duplicate posts when the feed repeats an entry.
    unique_posts = []
    seen = set()

    for post in posts:
        key = post["url"] or post["text"]

        if key not in seen:
            seen.add(key)
            unique_posts.append(post)

    print(f"Retrieved {len(unique_posts)} unique posts.")
    return unique_posts


# ============================================================
# FILTER THE LAST 24 HOURS
# ============================================================

def get_recent_posts(posts):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=HOURS_TO_CHECK)

    recent = []
    missing_dates = 0

    for post in posts:
        published = post["created_at"]

        if published is None:
            missing_dates += 1
            continue

        if cutoff <= published <= now:
            recent.append(post)

    print(f"Posts in the last {HOURS_TO_CHECK} hours: {len(recent)}")

    if missing_dates:
        print(
            f"Warning: skipped {missing_dates} posts "
            "with unrecognized publication dates."
        )

    return recent


# ============================================================
# CLASSIFY POSTS WITHOUT OPENAI
# ============================================================

def analyze_posts(posts):
    """
    Identify likely international affairs and national security posts
    using keyword matching. This function makes no paid API calls.
    """

    relevant_posts = []

    for post in posts:
        text = post["text"].lower()

        matches = [
            keyword
            for keyword in KEYWORDS
            if re.search(
                r"(?<!\w)" + re.escape(keyword) + r"(?!\w)",
                text
            )
        ]

        if matches:
            result = dict(post)
            result["matched_keywords"] = matches
            result["reason"] = (
                "Matched keywords: " + ", ".join(matches[:6])
            )
            relevant_posts.append(result)

    return relevant_posts


# ============================================================
# SEND EMAIL
# ============================================================

def send_email(posts):
    """Send the digest through Gmail SMTP."""

    today = datetime.now().astimezone().strftime("%B %d, %Y")

    message = EmailMessage()
    message["From"] = EMAIL_ADDRESS
    message["To"] = EMAIL_TO

    if posts:
        message["Subject"] = (
            f"Trump International Affairs Monitor — {today} "
            f"({len(posts)} relevant posts)"
        )

        sections = [
            "TRUMP INTERNATIONAL AFFAIRS & NATIONAL SECURITY MONITOR",
            f"Daily digest: {today}",
            f"Relevant posts found: {len(posts)}",
            "Filtering method: keyword matching (no OpenAI API used)",
            "",
            "=" * 60,
        ]

        for index, post in enumerate(posts, start=1):
            published = post["created_at"]

            date_text = (
                published.strftime("%Y-%m-%d %H:%M UTC")
                if published else "Date unavailable"
            )

            sections.extend([
                "",
                f"{index}. {date_text}",
                f"Matched topics: {post['reason']}",
                "",
                post["text"],
                "",
                f"Original post: {post['url'] or 'URL unavailable'}",
                "-" * 60,
            ])

        sections.extend([
            "",
            "Note: Keyword matches are not a guarantee of relevance.",
            "Some relevant posts may be missed, and some matches may "
            "be unrelated to international affairs.",
            "",
            f"Source: {RSS_URL}",
        ])

        message.set_content("\n".join(sections))

    else:
        message["Subject"] = (
            f"Trump International Affairs Monitor — {today}: "
            "No matching posts"
        )

        message.set_content(
            f"No posts matching the monitor's keywords were found "
            f"among the posts published in the last {HOURS_TO_CHECK} "
            "hours that were available in the feed.\n\n"
            "This does not prove that no relevant posts were published. "
            "The feed may be delayed or incomplete, and keyword filtering "
            "can miss relevant content.\n\n"
            f"Source: {RSS_URL}"
        )

    print(f"Sending email to {EMAIL_TO}...")

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(message)

    print("Email sent successfully.")


# ============================================================
# MAIN WORKFLOW
# ============================================================

def main():
    print("=" * 60)
    print("TRUMP INTERNATIONAL AFFAIRS MONITOR")
    print("Keyword-based mode — no OpenAI API required")
    print("=" * 60)

    try:
        print("\n1. Fetching posts...")
        posts = fetch_posts()

        if not posts:
            raise RuntimeError(
                "The feed returned no posts. Check the feed URL "
                "before trusting an empty digest."
            )

        print("\n2. Filtering posts by publication date...")
        recent_posts = get_recent_posts(posts)

        print("\n3. Identifying international affairs posts...")
        relevant_posts = analyze_posts(recent_posts)

        print(
            f"Identified {len(relevant_posts)} posts "
            "matching the keyword filter."
        )

        print("\n4. Sending email digest...")
        send_email(relevant_posts)

        print("\nMONITOR COMPLETED SUCCESSFULLY.")

    except Exception as error:
        print(
            f"\nMONITOR FAILED: {type(error).__name__}: {error}"
        )
        raise


if __name__ == "__main__":
    main()

 

     

