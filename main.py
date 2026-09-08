````python
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

# Request a reasonable number per API page.
PAGE_LIMIT = 40

# Safety limit so the workflow cannot accidentally make
# hundreds of API requests.
MAX_PAGES = 10


# ============================================================
# CONFIGURATION CHECK
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
# DATE PARSING
# ============================================================

def parse_post_time(post):

    possible_fields = [
        "created_at",
        "createdAt",
        "published_at",
        "publishedAt",
        "timestamp",
        "date",
    ]

    value = None

    for field in possible_fields:

        if post.get(field) is not None:

            value = post.get(field)

            break

    if value is None:
        return None

    try:

        # Unix timestamp
        if isinstance(value, (int, float)):

            return datetime.fromtimestamp(
                value,
                tz=timezone.utc
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
# API REQUEST
# ============================================================

def request_truth_posts(params):

    headers = {
        "Authorization": f"Bearer {TRUTH_API_KEY}",
        "Accept": "application/json",
        "User-Agent": "Trump-International-Affairs-Monitor/2.0",
    }

    try:

        response = requests.get(
            TRUTH_API_URL,
            headers=headers,
            params=params,
            timeout=30,
        )

        print(
            "API request:",
            response.url
        )

        print(
            "HTTP status:",
            response.status_code
        )

        response.raise_for_status()

        data = response.json()

        if not data.get("success"):

            print("ERROR: API returned unsuccessful response.")
            print(data)

            return None

        posts = data.get(
            "data",
            {}
        ).get(
            "posts",
            []
        )

        return posts

    except requests.exceptions.Timeout:

        print("ERROR: API request timed out.")

        return None

    except requests.exceptions.RequestException as e:

        print("ERROR: API request failed.")
        print(str(e))

        return None

    except ValueError:

        print("ERROR: API response was not valid JSON.")

        return None


# ============================================================
# GET ALL POSTS FROM PREVIOUS 24 HOURS
# ============================================================

def get_truth_social_posts():

    now = datetime.now(timezone.utc)

    cutoff = now - timedelta(hours=24)

    print()
    print("================================================")
    print("TRUTH SOCIAL COLLECTION")
    print("================================================")

    print(
        "Current UTC:",
        now.isoformat()
    )

    print(
        "24-hour cutoff:",
        cutoff.isoformat()
    )

    all_posts = []

    max_id = None

    for page_number in range(
        1,
        MAX_PAGES + 1
    ):

        params = {
            "url": TARGET_URL,
            "limit": PAGE_LIMIT,
        }

        # If the API supports Mastodon-style pagination,
        # max_id retrieves older posts.
        if max_id:

            params["max_id"] = max_id

        print()
        print(
            f"Requesting page {page_number}..."
        )

        posts = request_truth_posts(
            params
        )

        if posts is None:

            return None

        if not posts:

            print(
                "No more posts returned."
            )

            break

        print(
            "Posts returned:",
            len(posts)
        )

        all_posts.extend(posts)

        # ----------------------------------------------------
        # Determine oldest post on this page
        # ----------------------------------------------------

        parsed_times = []

        for post in posts:

            post_time = parse_post_time(
                post
            )

            if post_time:

                parsed_times.append(
                    post_time
                )

        if parsed_times:

            oldest_time = min(
                parsed_times
            )

            newest_time = max(
                parsed_times
            )

            print(
                "Newest post on page:",
                newest_time.isoformat()
            )

            print(
                "Oldest post on page:",
                oldest_time.isoformat()
            )

            # Once the page reaches before the cutoff,
            # we have enough historical posts.
            if oldest_time < cutoff:

                print(
                    "Reached the 24-hour cutoff."
                )

                break

        # ----------------------------------------------------
        # Pagination cursor
        # ----------------------------------------------------

        ids = [
            str(post.get("id"))
            for post in posts
            if post.get("id") is not None
        ]

        if not ids:

            print(
                "No post IDs available for pagination."
            )

            break

        max_id = ids[-1]

        # If fewer posts than requested were returned,
        # there may be no more pages.
        if len(posts) < PAGE_LIMIT:

            print(
                "Returned fewer than page limit; "
                "assuming final page."
            )

            break

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    unique_posts = {}

    for post in all_posts:

        post_id = post.get("id")

        if post_id:

            unique_posts[str(post_id)] = post

    posts = list(
        unique_posts.values()
    )

    print()
    print(
        "Total unique posts collected:",
        len(posts)
    )

    # --------------------------------------------------------
    # Filter previous 24 hours
    # --------------------------------------------------------

    recent_posts = []

    for post in posts:

        post_time = parse_post_time(
            post
        )

        if post_time is None:

            print(
                "WARNING: Could not determine time for:",
                post.get("id")
            )

            continue

        if post_time >= cutoff:

            recent_posts.append(
                post
            )

    recent_posts.sort(
        key=lambda post:
            parse_post_time(post)
            or datetime.min.replace(
                tzinfo=timezone.utc
            )
    )

    print(
        "Posts from previous 24 hours:",
        len(recent_posts)
    )

    print("================================================")

    return recent_posts


# ============================================================
# CLEAN HTML
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
# EXTRACT IMAGE INFORMATION
# ============================================================

def get_media_information(post):

    media = []

    possible_fields = [
        "media_attachments",
        "mediaAttachments",
        "media",
    ]

    attachments = []

    for field in possible_fields:

        if isinstance(
            post.get(field),
            list
        ):

            attachments = post.get(field)

            break

    for attachment in attachments:

        if not isinstance(
            attachment,
            dict
        ):

            continue

        description = (
            attachment.get("description")
            or attachment.get("alt")
            or attachment.get("alt_text")
            or ""
        )

        media_type = (
            attachment.get("type")
            or ""
        )

        if description:

            media.append(
                f"{media_type}: {description}"
            )

        elif media_type:

            media.append(
                f"{media_type} attachment"
            )

    return media


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
            post.get(
                "content",
                ""
            )
        )

        post_time = parse_post_time(
            post
        )

        if post_time:

            timestamp = post_time.astimezone(
                TIMEZONE
            ).strftime(
                "%B %d, %Y at %I:%M %p %Z"
            )

        else:

            timestamp = "Unknown time"

        post_url = post.get("url")

        if not post_url:

            post_url = (
                "https://truthsocial.com/"
                f"@realDonaldTrump/{post_id}"
            )

        media = get_media_information(
            post
        )

        prepared.append({

            "id": str(post_id),

            "time": timestamp,

            "content": content,

            "media": media,

            "url": post_url,

        })

    return prepared


# ============================================================
# AI CLASSIFICATION
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
statements for INTERNATIONAL AFFAIRS and NATIONAL SECURITY.

You are reviewing every Truth Social post from the previous
24 hours.

Your task is to identify posts that meaningfully concern
international affairs.

IMPORTANT:
Be reasonably inclusive.

If a post clearly discusses a foreign country, foreign
government, foreign leader, international conflict,
international security, diplomacy, foreign military activity,
international trade, sanctions, tariffs involving another
country, nuclear weapons in an international context, NATO,
Ukraine, Russia, China, Taiwan, Iran, Israel, Gaza, Europe,
the Middle East, or another international issue, INCLUDE IT.

Also include posts where the international component is
important even if the post contains domestic political
language.

Do NOT require Trump to explicitly say "international
affairs."

Examples that SHOULD generally be included:

- Trump discussing Iran
- Trump discussing Iran's nuclear program
- Trump discussing Iran's military
- Trump discussing Israel or Gaza
- Trump discussing Russia or Ukraine
- Trump discussing NATO
- Trump discussing China or Taiwan
- Trump discussing foreign leaders
- Trump discussing a foreign government
- Trump discussing sanctions
- Trump discussing foreign tariffs or trade
- Trump discussing foreign military operations
- Trump discussing international negotiations
- Trump discussing foreign aid
- Trump discussing international organizations
- Trump discussing nuclear weapons involving another country
- Trump discussing territorial disputes involving another country

Posts that are purely about domestic U.S. politics should NOT
be included.

Posts attacking a domestic political opponent should NOT be
included unless the post also meaningfully discusses an
international issue.

IMPORTANT ABOUT IMAGES:

Some posts contain images or image descriptions.

Use the supplied media descriptions when determining whether
a post concerns international affairs.

If the text is ambiguous but the supplied media description
clearly identifies an international subject, INCLUDE the post.

Do NOT invent facts about an image that are not provided.

For every selected post, provide a short factual explanation.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "international_posts": [
        {{
            "id": "POST_ID",
            "reason": "Why this post meaningfully concerns international affairs"
        }}
    ]
}}

Posts to analyze:

{post_text}
"""

    print()
    print("================================================")
    print("AI CLASSIFICATION")
    print("================================================")

    try:

        response = client.responses.create(
            model="gpt-5.6",
            input=prompt,
        )

        text = response.output_text.strip()

        print(
            "AI response received."
        )

        # ----------------------------------------------------
        # Handle accidental markdown fences
        # ----------------------------------------------------

        if text.startswith("```"):

            text = text.replace(
                "```json",
                "",
                1
            )

            text = text.replace(
                "```",
                "",
            ).strip()

        result = json.loads(
            text
        )

        international_ids = {}

        for item in result.get(
            "international_posts",
            []
        ):

            post_id = item.get(
                "id"
            )

            if post_id:

                international_ids[
                    str(post_id)
                ] = item.get(
                    "reason",
                    "International-affairs relevance identified."
                )

        selected = []

        for post in posts:

            post_id = str(
                post.get("id")
            )

            if post_id in international_ids:

                copy_post = post.copy()

                copy_post["reason"] = (
                    international_ids[
                        post_id
                    ]
                )

                selected.append(
                    copy_post
                )

        print(
            "International-affairs posts:",
            len(selected)
        )

        print("================================================")

        return selected

    except json.JSONDecodeError as e:

        print(
            "ERROR: AI returned invalid JSON."
        )

        print(
            str(e)
        )

        print(
            "Raw AI response:"
        )

        print(
            text
        )

        return []

    except Exception as e:

        print(
            "ERROR: AI classification failed."
        )

        print(
            str(e)
        )

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
        f"Trump International Affairs Daily Digest — "
        f"{today}"
    )

    if not posts:

        body = f"""
TRUMP INTERNATIONAL AFFAIRS DAILY DIGEST

{today}

No international-affairs-related Truth Social posts
were identified during the previous 24 hours.

The monitor reviewed the available Truth Social posts
from the previous 24-hour period and classified them
for international-affairs and national-security relevance.

"""

        return subject, body

    sections = []

    for number, post in enumerate(
        posts,
        start=1
    ):

        section = f"""
============================================================
POST {number}
============================================================

TIME:
{post.get("time", "Unknown time")}

WHY IT WAS INCLUDED:
{post.get("reason", "")}

TRUMP'S POST:
{post.get("content", "")}
"""

        media = post.get(
            "media",
            []
        )

        if media:

            section += "\nMEDIA INFORMATION:\n"

            for item in media:

                section += (
                    f"- {item}\n"
                )

        section += f"""
TRUTH SOCIAL:
{post.get("url", "")}
"""

        sections.append(
            section
        )

    body = f"""
TRUMP INTERNATIONAL AFFAIRS DAILY DIGEST

{today}

This digest contains Trump's Truth Social posts from
the previous 24 hours that were identified as meaningfully
related to international affairs or national security.

NUMBER OF POSTS:
{len(posts)}

"""

    body += "\n".join(
        sections
    )

    body += """

============================================================

This digest was generated automatically.
"""

    return subject, body


# ============================================================
# SEND EMAIL
# ============================================================

def send_email(
    subject,
    body
):

    print()
    print("================================================")
    print("SENDING DAILY DIGEST")
    print("================================================")

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
            timeout=30
        ) as server:

            server.starttls()

            server.login(
                EMAIL_ADDRESS,
                EMAIL_PASSWORD
            )

            server.sendmail(
                EMAIL_ADDRESS,
                EMAIL_TO,
                message.as_string()
            )

        print(
            "EMAIL SENT SUCCESSFULLY."
        )

        print("================================================")

        return True

    except Exception as e:

        print(
            "ERROR: Email failed."
        )

        print(
            str(e)
        )

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
    # Validate configuration
    # --------------------------------------------------------

    if not validate_configuration():

        print(
            "MONITOR STOPPED."
        )

        return

    print(
        "All required configuration detected."
    )

    # --------------------------------------------------------
    # Retrieve posts
    # --------------------------------------------------------

    posts = get_truth_social_posts()

    if posts is None:

        print(
            "MONITOR FAILED: Could not retrieve posts."
        )

        return

    # --------------------------------------------------------
    # Prepare posts
    # --------------------------------------------------------

    prepared_posts = prepare_posts_for_ai(
        posts
    )

    print(
        "Posts prepared for classification:",
        len(prepared_posts)
    )

    # --------------------------------------------------------
    # Classify
    # --------------------------------------------------------

    international_posts = classify_posts(
        prepared_posts
    )

    # --------------------------------------------------------
    # Create ONE daily digest
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
    # Final status
    # --------------------------------------------------------

    print()

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
            "DAILY DIGEST FAILED."
        )

    print(
        "================================================"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
````

    
