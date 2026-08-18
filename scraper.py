
from playwright.sync_api import sync_playwright
from datetime import datetime
import hashlib
import os

from config import TRUTH_SOCIAL_USERNAME


TRUTH_SOCIAL_PASSWORD = os.getenv("TRUTH_SOCIAL_PASSWORD")


def get_trump_posts():

    posts = []

    username = TRUTH_SOCIAL_USERNAME

    if not TRUTH_SOCIAL_PASSWORD:
        print("ERROR: TRUTH_SOCIAL_PASSWORD is not configured.")
        return posts

    profile_url = f"https://truthsocial.com/@{username}"

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        context = browser.new_context()

        page = context.new_page()

        try:

            print("Opening Truth Social...")

            page.goto(
                "https://truthsocial.com/",
                wait_until="domcontentloaded",
                timeout=60000
            )

            print("Truth Social opened.")

            # Look for login controls
            page.wait_for_timeout(5000)

            print("Page title:", page.title())

            # Try to find a login button
            login_button = page.get_by_text(
                "Log in",
                exact=True
            )

            if login_button.count() > 0:

                print("Login button found.")

                login_button.first.click()

                page.wait_for_timeout(3000)

            else:

                print("Login button not found.")

            # Look for username/email field
            username_field = page.locator(
                'input[type="email"], input[name="email"], input[name="username"]'
            )

            if username_field.count() == 0:

                print("Username/email field not found.")
                print("Current URL:", page.url)

                browser.close()
                return posts

            username_field.first.fill(
                username
            )

            password_field = page.locator(
                'input[type="password"]'
            )

            if password_field.count() == 0:

                print("Password field not found.")

                browser.close()
                return posts

            password_field.first.fill(
                TRUTH_SOCIAL_PASSWORD
            )

            print("Login information entered.")

            # Find submit/login button
            submit_button = page.locator(
                'button[type="submit"]'
            )

            if submit_button.count() > 0:

                submit_button.first.click()

            else:

                page.get_by_text(
                    "Log in",
                    exact=True
                ).last.click()

            print("Login submitted.")

            page.wait_for_timeout(8000)

            print("Current URL after login:", page.url)

            # Go directly to Trump's profile
            page.goto(
                profile_url,
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_timeout(8000)

            print("Trump profile opened.")

            print("Profile URL:", page.url)

            articles = page.locator(
                "article"
            )

            count = articles.count()

            print(
                "Articles found:",
                count
            )

            for i in range(
                min(count, 20)
            ):

                try:

                    text = articles.nth(i).inner_text()

                    if len(text.strip()) < 30:
                        continue

                    post_id = hashlib.sha256(
                        text.encode("utf-8")
                    ).hexdigest()

                    posts.append({

                        "id": post_id,

                        "date":
                        datetime.now().isoformat(),

                        "text":
                        text.strip(),

                        "url":
                        profile_url

                    })

                except Exception as error:

                    print(
                        "Could not read post:",
                        error
                    )

            print(
                "Posts collected:",
                len(posts)
            )

        except Exception as error:

            print(
                "Truth Social Playwright error:",
                error
            )

        finally:

            browser.close()

    return posts
