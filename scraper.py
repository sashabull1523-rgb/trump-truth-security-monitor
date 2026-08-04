mport requests
from datetime import datetime
import hashlib

from config import TRUTH_SOCIAL_USERNAME


def get_trump_posts():

    posts = []

    # Truth Social account
    username = TRUTH_SOCIAL_USERNAME

    # Public feed endpoint attempt
    url = f"https://truthsocial.com/@{username}.rss"

    try:

        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=30
        )

        response.raise_for_status()

        text = response.text

        if len(text) < 100:
            print("No RSS data returned.")
            return posts


        # Basic RSS extraction
        items = text.split("<item>")[1:]


        for item in items[:10]:

            if "<description>" in item:

                post_text = (
                    item
                    .split("<description>")[1]
                    .split("</description>")[0]
                )

                post_text = (
                    post_text
                    .replace("<![CDATA[", "")
                    .replace("]]>", "")
                )


                post_id = hashlib.sha256(
                    post_text.encode()
                ).hexdigest()


                posts.append({

                    "id": post_id,

                    "date":
                    datetime.now().isoformat(),

                    "text":
                    post_text,

                    "url":
                    f"https://truthsocial.com/@{username}"

                })


        print(
            f"Found {len(posts)} Trump posts"
        )


    except Exception as error:

        print(
            "Truth Social scraper error:",
            error
        )


    return posts
