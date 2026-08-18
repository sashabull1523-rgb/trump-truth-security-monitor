from playwright.sync_api import sync_playwright
import time

from config import TRUTH_USERNAME, TRUTH_PASSWORD


def get_trump_posts():

    posts = []

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page()

        try:

            print("Opening Truth Social...")

            page.goto(
                "https://truthsocial.com",
                wait_until="domcontentloaded",
                timeout=60000
            )

            print("Truth Social opened.")

            # Look for the login button
            page.get_by_text("Log in", exact=True).click()

            time.sleep(3)

            print("Login page opened.")

            # Enter username/email
            page.locator(
                'input[type="text"], input[type="email"]'
            ).first.fill(TRUTH_USERNAME)

            # Enter password
            page.locator(
                'input[type="password"]'
            ).fill(TRUTH_PASSWORD)

            # Submit login
            page.get_by_role(
                "button",
                name="Log in"
            ).click()

            print("Login submitted.")

            time.sleep(8)

            # Go directly to Trump's profile
            page.goto(
                "https://truthsocial.com/@realDonaldTrump",
                wait_until="domcontentloaded",
                timeout=60000
            )

            time.sleep(5)

            print("Trump profile opened.")

            # Find posts on the page
            articles = page.locator("article")

            count = articles.count()

            print(f"Found {count} possible posts.")

            for i in range(count):

                article = articles.nth(i)

                try:

                    text = article.inner_text()

                    if not text.strip():
                        continue

                    posts.append({
                        "id": str(i),
                        "date": "",
                        "text": text,
                        "url": page.url
                    })

                except Exception as error:

                    print(
                        f"Could not read post {i}: {error}"
                    )

        except Exception as error:

            print(
                f"Truth Social scraper error: {error}"
            )

        finally:

            browser.close()

    print(
        f"TOTAL POSTS FOUND: {len(posts)}"
    )

    return posts
