from playwright.sync_api import sync_playwright
from config import TRUTH_SOCIAL_USERNAME


def get_trump_posts():

    url = f"https://truthsocial.com/@{TRUTH_SOCIAL_USERNAME}"

    print("Starting Truth Social scraper...")
    print(f"Opening: {url}")

    posts = []

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page()

        try:

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_timeout(10000)

            print("PAGE TITLE:")
            print(page.title())

            print("\nPAGE URL:")
            print(page.url)

            print("\nPAGE TEXT:")
            print(page.locator("body").inner_text()[:3000])

            articles = page.locator("article")

            count = articles.count()

            print(f"\nNUMBER OF ARTICLES: {count}")

            for i in range(min(count, 10)):

                text = articles.nth(i).inner_text().strip()

                if text:

                    print("\n--- POST ---")
                    print(text)

                    posts.append({
                        "text": text,
                        "url": url
                    })

        except Exception as error:

            print(
                f"Truth Social scraper error: {error}"
            )

        finally:

            browser.close()

    return posts
