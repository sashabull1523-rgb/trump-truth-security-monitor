import os
import requests
from datetime import datetime, timezone


# ============================================================
# TRUTH SOCIAL DATA SOURCE
# ============================================================

TRUTH_API_KEY = os.getenv("TRUTH_API_KEY")

# Put the authorized API endpoint supplied by your data provider here.
TRUTH_API_URL = os.getenv("TRUTH_API_URL")

TRUMP_USERNAME = "realDonaldTrump"


def get_trump_posts():
    """
    Retrieve Trump's latest Truth Social posts from an
    authorized API/data provider.

    This replaces the Playwright browser scraper.
    """

    if not TRUTH_API_KEY:
        print("ERROR: TRUTH_API_KEY is not configured.")
        return []

    if not TRUTH_API_URL:
        print("ERROR: TRUTH_API_URL is not configured.")
        return []

    headers = {
        "Authorization": f"Bearer {TRUTH_API_KEY}",
        "Accept": "application/json",
    }

    params = {
        "username": TRUMP_USERNAME,
    }

    try:
        print("Requesting Trump's Truth Social posts...")

        response = requests.get(
            TRUTH_API_URL,
            headers=headers,
            params=params,
            timeout=30,
        )

        print(f"API status code: {response.status_code}")

        response.raise_for_status()

        data = response.json()

        print("Successfully received data from authorized source.")

        return normalize_posts(data)

    except requests.exceptions.Timeout:
        print("ERROR: Truth Social API request timed out.")
        return []

    except requests.exceptions.HTTPError as e:
        print(f"ERROR: Truth Social API returned HTTP error: {e}")
        print(response.text[:1000])
        return []

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Could not connect to Truth Social API: {e}")
        return []

    except ValueError:
        print("ERROR: API returned invalid JSON.")
        print(response.text[:1000])
        return []


# ============================================================
# NORMALIZE API DATA
# ============================================================

def normalize_posts(data):
    """
    Convert the provider's API response into a simple list
    of posts that the rest of the monitoring system can use.

    The exact field names may need to be adjusted once we know
    the provider's response format.
    """

    if isinstance(data, list):
        raw_posts = data

    elif isinstance(data, dict):
        raw_posts = (
            data.get("posts")
            or data.get("data")
            or data.get("results")
            or []
        )

    else:
        print("ERROR: Unexpected API response format.")
        return []

    posts = []

    for post in raw_posts:

        if not isinstance(post, dict):
            continue

        normalized = {
            "id": (
                post.get("id")
                or post.get("post_id")
                or post.get("uri")
            ),

            "text": (
                post.get("text")
                or post.get("content")
                or post.get("body")
                or ""
            ),

            "created_at": (
                post.get("created_at")
                or post.get("createdAt")
                or post.get("timestamp")
            ),

            "url": (
                post.get("url")
                or post.get("permalink")
                or post.get("link")
            ),

            "username": (
                post.get("username")
                or post.get("account")
                or TRUMP_USERNAME
            ),
        }

        # Don't add completely empty records.
        if normalized["text"]:
            posts.append(normalized)

    print(f"Normalized {len(posts)} posts.")

    return posts


# ============================================================
# DISPLAY POSTS
# ============================================================

def print_posts(posts):

    if not posts:
        print("NO POSTS FOUND")
        return

    print("=" * 60)
    print(f"TOTAL POSTS FOUND: {len(posts)}")
    print("=" * 60)

    for i, post in enumerate(posts, start=1):

        print()
        print(f"POST #{i}")
        print("-" * 60)

        print(f"ID: {post.get('id')}")
        print(f"Created: {post.get('created_at')}")
        print(f"URL: {post.get('url')}")
        print()
        print(post.get("text"))


# ============================================================
# MAIN SCRAPER TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("TRUTH SOCIAL API MONITOR")
    print("=" * 60)

    posts = get_trump_posts()

    print_posts(posts)

    print()
    print("=" * 60)
    print("MONITOR COMPLETE")
    print("=" * 60)
