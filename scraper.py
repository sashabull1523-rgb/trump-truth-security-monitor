from playwright.sync_api import sync_playwright
from config import TRUTH_SOCIAL_USERNAME


def test_scraper():

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

            page.wait_for_timeout(10000)

            print("PAGE TITLE:")
            print(page.title())

            print("\nNUMBER OF ARTICLES:")
            print(page.locator("article").count())

            print("\nPAGE TEXT SAMPLE:")
            print(page.inner_text("body")[:2000])

        except Exception as error:
            print("ERROR:")
            print(error)

        browser.close()


if __name__ == "__main__":
    test_scraper()
