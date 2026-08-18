import os
import json
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

TRUTH_API_KEY = os.environ.get("TRUTH_API_KEY")
TRUTH_API_URL = os.environ.get("TRUTH_API_URL")

EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_TO = os.environ.get("EMAIL_TO")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

TARGET_URL = "https://truthsocial.com/@realDonaldTrump"

TIMEZONE = ZoneInfo("America/Denver")

POSTS_TO_REQUEST = 40


# ============================================================
# VALIDATE CONFIGURATION
# ============================================================

def validate_configuration():

    required = {
        "TRUTH_API_KEY": TRUTH_API_KEY,
        "TRUTH_API_URL": TRUTH_API_URL,
        "EMAIL_ADDRESS": EMAIL_ADDRESS,
        "EMAIL_PASSWORD": EMAIL_PASSWORD,
        "EMAIL_TO": EMAIL_TO,
        "OPENAI_API_KEY": OPENAI_API_KEY,
    }

    missing = [
        name
        for name, value in required.items()
        if not value
    ]

    if missing:

        print("ERROR: Missing required secrets:")

        for name in missing:
            print(" -", name)

        return False

    return True


# ============================================================
# TRUTH SOCIAL API
# ============================================================

def get_truth_social_posts():

    headers = {
        "Authorization": f"Bearer {TRUTH_API_KEY}",
        "Accept": "application/json",
        "User-Agent": "Trump-International-Affairs-Monitor/1.0",
    }

    params = {
        "url": TARGET_URL,
        "limit": POSTS_TO_REQUEST,
    }

    print("Connecting to Truth Social data source...")

    try:

        response = requests.get(
            TRUTH_API_URL,
            headers=headers,
            params=params,
            timeout=30,
        )

        print("HTTP status:", response.status_code)

        response.raise_for_status()

        data = response.json()

        if not data.get("success"):

            print("ERROR: API returned unsuccessful response.")

            print(data)

            return None

        posts = data.get("data", {}).get("posts", [])

        print("Posts retrieved:", len(posts))

        return posts

    except requests.exceptions.Timeout:

        print("ERROR: Truth Social request timed out.")

        return None

    except requests.exceptions.RequestException as e:

        print("ERROR: Truth Social request failed.")

        print(str(e))

        return None

    except ValueError:

        print("ERROR: Truth Social response was not valid JSON.")

        return None


# ============================================================
# DATE PARSING
# ============================================================

def parse_post_time(post):

    possible_fields = [
        "createdAt",
        "created_at",
        "publishedAt",
        "published_at",
        "timestamp",
        "date",
    ]

    value = None

    for field in possible_fields:

        if post.get(field):

            value = post.get(field)

            break

    if not value:

        return None

    try:

        if isinstance(value, (int, float)):

            return datetime.fromtimestamp(
                value,
                tz=timezone.utc,
            )

        value = str(value).strip()

        if value.endswith("Z"):

            value = value[:-1] + "+00:00"

        parsed = datetime.fromisoformat(value)

        if parsed.tzinfo is None:

            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed.astimezone(timezone.utc)

    except Exception:

        return None


# ============================================================
# GET POSTS FROM LAST 24 HOURS
# ============================================================

def get_posts_from_last_24_hours(posts):

    now = datetime.now(timezone.utc)

    cutoff = now - timedelta(hours=24)

    recent_posts = []

    print("--------------------------------")
    print("Current UTC time:", now.isoformat())
    print("24-hour cutoff:", cutoff.isoformat())
    print("--------------------------------")

    for post in posts:

        post_time = parse_post_time(post)

        if post_time is None:

            print(
                "WARNING: Could not determine post time.",
                post.get("id"),
            )

            continue

        if post_time >= cutoff:

            recent_posts.append(post)

    recent_posts.sort(
        key=lambda post: parse_post_time(post) or datetime.min.replace(
            tzinfo=timezone.utc
        )
    )

    print(
        "Posts from previous 24 hours:",
        len(recent_posts)
    )

    return recent_posts


# ============================================================
# CLEAN POST CONTENT
# ============================================================

def clean_content(content):

    if not content:

        return ""

    soup = BeautifulSoup(
        content,
        "html.parser"
    )

    return soup.get_text(
        separator=" ",
        strip=True
    )


# ============================================================
# PREPARE POSTS FOR AI
# ============================================================

def prepare_posts_for_ai(posts):

    prepared = []

    for index, post in enumerate(posts):

        post_id = post.get(
            "id",
            f"unknown-{index}"
        )

        content = clean_content(
            post.get("content", "")
        )

        post_time = parse_post_time(post)

        if post_time:

            timestamp = post_time.astimezone(
                TIMEZONE
            ).strftime(
                "%Y-%m-%d %I:%M %p %Z"
            )

        else:

            timestamp = "Unknown time"

        post_url = post.get("url")

        if not post_url:

            post_url = (
                "https://truthsocial.com/"
                f"@realDonaldTrump/{post_id}"
            )

        prepared.append({
            "id": post_id,
            "time": timestamp,
            "content": content,
            "url": post_url,
        })

    return prepared


# ============================================================
# AI INTERNATIONAL-AFFAIRS CLASSIFICATION
# ============================================================

def classify_posts(posts):

    if not posts:

        return []

    client = OpenAI(
        api_key=OPENAI_API_KEY
    )

    post_text = json.dumps(
        posts,
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
You are an analyst monitoring Donald Trump's public
statements for a national-security and international-affairs
research project.

Below are Trump's Truth Social posts from the previous
24 hours.

Your job is to identify ONLY posts that are meaningfully
related to INTERNATIONAL AFFAIRS.

Include posts involving:

- Foreign countries
- Foreign leaders or governments
- Wars or armed conflicts outside the United States
- NATO
- European security
- Ukraine
- Russia
- China
- Taiwan
- Iran
- Israel
- Gaza
- Middle East conflicts
- Foreign military operations
- U.S. relations with foreign governments
- Diplomacy
- International organizations
- Sanctions
- Foreign aid
- Tariffs when they are clearly connected to foreign relations
- International trade disputes
- Immigration when the post is specifically discussing
  relations with another country or international security
- Nuclear weapons or nuclear deterrence when discussed
  in an international context
- International treaties or agreements

DO NOT include:

- Domestic U.S. politics
- Attacks on domestic political opponents
- U.S. elections
- Campaigning
- Domestic crime
- Domestic economic issues
- Sports
- Celebrity comments
- Personal attacks
- General statements that have no international component

IMPORTANT:

A post should be included only if international affairs
is a meaningful part of what Trump is discussing.

Do not infer an international connection that is not present.

Return ONLY valid JSON in this exact format:

{{
    "international_posts": [
        {{
            "id": "post id",
            "reason": "brief explanation of why this concerns international affairs"
        }}
    ]
}}

Here are the posts:

{post_text}
"""

    try:

        response = client.responses.create(
            model="gpt-5.6",
            input=prompt,
        )

        text = response.output_text.strip()

        result = json.loads(text)

        international_ids = {
            item["id"]: item.get(
                "reason",
                ""
            )
            for item in result.get(
                "international_posts",
                []
            )
        }

        selected = []

        for post in posts:

            post_id = post["id"]

            if post_id in international_ids:

                post_copy = post.copy()

                post_copy["reason"] = (
                    international_ids[post_id]
                )

                selected.append(post_copy)

        print(
            "International-affairs posts:",
            len(selected)
        )

        return selected

    except json.JSONDecodeError as e:

        print(
            "ERROR: AI returned invalid JSON."
        )

        print(str(e))

        return []

    except Exception as e:

        print(
            "ERROR: AI classification failed."
        )

        print(str(e))

        return []


# ============================================================
# CREATE DAILY DIGEST
# ============================================================

def create_daily_digest(posts):

    today = datetime.now(
        TIMEZONE
    ).strftime(
        "%B %d, %Y"
    )

    subject = (
        f"🌎 Trump International Affairs Digest — "
        f"{today}"
    )

    if not posts:

        body = f"""
TRUMP INTERNATIONAL AFFAIRS DAILY DIGEST

{today}

No international-affairs-related Truth Social posts
were identified during the previous 24 hours.

This monitor checks Trump's posts and uses AI to classify
whether each post meaningfully concerns international affairs.
"""

        return subject, body

    sections = []

    for number, post in enumerate(
        posts,
        start=1
    ):

        post_time = post.get(
            "time",
            "Unknown time"
        )

        content = post.get(
            "content",
            ""
        )

        url = post.get(
            "url",
            ""
        )

        reason = post.get(
            "reason",
            ""
        )

        section = f"""
============================================================
POST {number}
============================================================

TIME:
{post_time}

WHY IT WAS INCLUDED:
{reason}

TRUMP'S POST:
{content}

TRUTH SOCIAL:
{url}
"""

        sections.append(section)

    body = f"""
TRUMP INTERNATIONAL AFFAIRS DAILY DIGEST

{today}

The following posts were identified as meaningfully
related to international affairs during the previous
24 hours.

NUMBER OF INTERNATIONAL-AFFAIRS POSTS:
{len(posts)}

"""

    body += "\n".join(sections)

    body += """

============================================================

This digest was generated automatically.
"""

    return subject, body


# ============================================================
# SEND EMAIL
# ============================================================

def send_email(subject, body):

    print("--------------------------------")
    print("Sending daily digest...")
    print("To:", EMAIL_TO)
    print("--------------------------------")

    message = MIMEMultipart()

    message["From"] = EMAIL_ADDRESS
    message["To"] = EMAIL_TO
    message["Subject"] = subject

    message.attach(
        MIMEText(
            body,
            "plain",
            "utf-8"
        )
    )

    try:

        with smtplib.SMTP(
            "smtp.gmail.com",
            587,
            timeout=30,
        ) as server:

            server.starttls()

            server.login(
                EMAIL_ADDRESS,
                EMAIL_PASSWORD,
            )

            server.sendmail(
                EMAIL_ADDRESS,
                EMAIL_TO,
                message.as_string(),
            )

        print("EMAIL SENT SUCCESSFULLY.")

        return True

    except Exception as e:

        print("ERROR: Email failed.")

        print(str(e))

        return False


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("================================================")
    print("TRUMP INTERNATIONAL AFFAIRS DAILY MONITOR")
    print("================================================")

    # --------------------------------------------------------
    # Configuration
    # --------------------------------------------------------

    if not validate_configuration():

        print("MONITOR STOPPED.")

        return

    print("All required configuration detected.")

    # --------------------------------------------------------
    # Get posts
    # --------------------------------------------------------

    posts = get_truth_social_posts()

    if posts is None:

        print("MONITOR FAILED.")

        return

    # --------------------------------------------------------
    # Filter by previous 24 hours
    # --------------------------------------------------------

    recent_posts = get_posts_from_last_24_hours(
        posts
    )

    if not recent_posts:

        print(
            "No posts were found in the previous 24 hours."
        )

        subject, body = create_daily_digest([])

        send_email(
            subject,
            body
        )

        return

    # --------------------------------------------------------
    # Prepare posts
    # --------------------------------------------------------

    prepared_posts = prepare_posts_for_ai(
        recent_posts
    )

    # --------------------------------------------------------
    # AI classification
    # --------------------------------------------------------

    international_posts = classify_posts(
        prepared_posts
    )

    # --------------------------------------------------------
    # Create digest
    # --------------------------------------------------------

    subject, body = create_daily_digest(
        international_posts
    )

    # --------------------------------------------------------
    # Send ONE email
    # --------------------------------------------------------

    success = send_email(
        subject,
        body
    )

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    print("--------------------------------")

    if success:

        print(
            "DAILY DIGEST COMPLETE."
        )

        print(
            "International posts included:",
            len(international_posts)
        )

    else:

        print(
            "DAILY DIGEST FAILED TO SEND."
        )

    print("================================================")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()

    
