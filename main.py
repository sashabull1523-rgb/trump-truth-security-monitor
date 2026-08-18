from playwright.sync_api import sync_playwright
import os
import time


TRUTH_USERNAME = os.environ.get("TRUTH_USERNAME")
TRUTH_PASSWORD = os.environ.get("TRUTH_PASSWORD")


def main():

    print("================================")
    print("TRUTH SOCIAL PLAYWRIGHT TEST")
    print("================================")

    if not TRUTH_USERNAME:
        print("ERROR: TRUTH_USERNAME secret is missing")
        return

    if not TRUTH_PASSWORD:
        print("ERROR: TRUTH_PASSWORD secret is missing")
        return

    print("Truth Social credentials detected.")
    print("Opening Truth Social...")

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page(
            viewport={
                "width": 1280,
                "height": 900
            }
        )

        try:

            page.goto(
                "https://truthsocial.com",
                wait_until="domcontentloaded",
                timeout=60000
            )

            print("Truth Social opened.")

            time.sleep(5)

            print("Current URL:")
            print(page.url)

            print("Page title:")
            print(page.title())

            print("Looking at visible page text...")

            text = page.locator("body").inner_text(
                timeout=30000
            )

            print("--------------------------------")
            print(text[:10000])
            print("--------------------------------")

            print("Looking for login elements...")

            links = page.locator("a").all_inner_texts()

            print("LINKS:")
            for link in links[:100]:
                print(repr(link))

            buttons = page.locator("button").all_inner_texts()

            print("BUTTONS:")
            for button in buttons[:100]:
                print(repr(button))

            print("================================")
            print("PAGE INSPECTION COMPLETE")
            print("================================")

        except Exception as e:

            print("ERROR:")
            print(str(e))

        finally:

            browser.close()


if __name__ == "__main__":
    main()
