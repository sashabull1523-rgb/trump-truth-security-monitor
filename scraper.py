from playwright.sync_api import sync_playwright
from datetime import datetime
import hashlib

from config import TRUTH_SOCIAL_USERNAME


def get_trump_posts():

    posts = []

    url = f"https://truthsocial.com/@{TRUTH_SOCIAL_USERNAME}"


    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page()


        try:

            page.goto(
                url,
                timeout=60000
            )


            page.wait_for_timeout(
                5000
            )


            articles = page.locator(
                "article"
            )


            count = articles.count()


            for i in range(min(count, 10)):

                text = articles.nth(i).inner_text()


                if len(text) > 30:


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


        except Exception as error:

            print(
                "Scraper error:",
                error
            )


        browser.close()


    return posts
