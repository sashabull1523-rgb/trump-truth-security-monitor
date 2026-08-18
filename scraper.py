import requests
from bs4 import BeautifulSoup
from datetime import datetime
import hashlib


TRUMP_ACCOUNT_ID = "107780257626128497"

TRUTH_API_URL = (
    f"https://truthsocial.com/api/v1/accounts/"
    f"{TRUMP_ACCOUNT_ID}/statuses"
)


def get_trump_posts():

    print("Starting Truth Social API scraper...")
    print(f"Requesting: {TRUTH_API_URL}")

    posts = []

    try:

        response = requests.get(
            TRUTH_API_URL,
            params={
                "limit": 20
            },
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=30
        )

        print(f"HTTP STATUS: {response.status_code}")

        response.raise_for_status()

        data = response.json()

        print(f"POSTS RECEIVED: {len(data)}")

        for status in data:

            html = status.get("content", "")

            soup = BeautifulSoup(
                html,
                "html.parser"
            )

            text = soup.get_text(
                " ",
                strip=True
            )

            if not text:
                continue

            post_id = status.get("id")

            created_at = status.get(
                "created_at"
            )

            post_url = status.get(
                "url"
            )

            posts.append({

                "id": post_id,

                "date": created_at,

                "text": text,

                "url": post_url

            })

            print("\n-----------------------------")
            print("TRUMP POST")
            print("-----------------------------")
            print(text)
            print(f"DATE: {created_at}")
            print(f"URL: {post_url}")

    except Exception as error:

        print(
            f"Truth Social API error: {error}"
        )

    return posts
