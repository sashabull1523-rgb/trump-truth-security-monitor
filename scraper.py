import requests
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime

from config import TRUTH_SOCIAL_USERNAME


def get_trump_posts():

    url = f"https://truthsocial.com/@{TRUTH_SOCIAL_USERNAME}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Could not access Truth Social")
        return []


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    posts = []


    text_blocks = soup.find_all(
        "div"
    )


    for block in text_blocks:

        text = block.get_text(
            " ",
            strip=True
        )


        if len(text) > 50:

            post_id = hashlib.sha256(
                text.encode()
            ).hexdigest()


            posts.append({

                "id": post_id,

                "date":
                datetime.now().isoformat(),

                "text":
                text,

                "url":
                url

            })


    return posts
