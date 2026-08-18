import os
import json
import smtplib
import requests

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv


# ============================================
# LOAD ENVIRONMENT VARIABLES
# ============================================

load_dotenv()


TRUTH_API_KEY = os.environ.get("TRUTH_API_KEY")
TRUTH_API_URL = os.environ.get("TRUTH_API_URL")

EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
ALERT_EMAIL = os.environ.get("ALERT_EMAIL")

TARGET_URL = "https://truthsocial.com/@realDonaldTrump"

STATE_FILE = "last_post.json"


# ============================================
# LOAD LAST POST
# ============================================

def load_last_post():

    if not os.path.exists(STATE_FILE):
        return None

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data.get("post_id")

    except Exception as e:

        print("WARNING: Could not read previous post state.")
        print(str(e))

        return None


# ============================================
# SAVE LAST POST
# ============================================

def save_last_post(post_id):

    try:

        with open(STATE_FILE, "w", encoding="utf-8") as file:

            json.dump(
                {
                    "post_id": str(post_id)
                },
                file,
                indent=2
            )

        print("Saved latest post ID:", post_id)

    except Exception as e:

        print("WARNING: Could not save post state.")
        print(str(e))


# ============================================
# SEND EMAIL
# ============================================

def send_email(subject, body):

    if not EMAIL_ADDRESS:
        print("ERROR: EMAIL_ADDRESS secret is missing.")
        return False

    if not EMAIL_PASSWORD:
        print("ERROR: EMAIL_PASSWORD secret is missing.")
        return False

    if not ALERT_EMAIL:
        print("ERROR: ALERT_EMAIL secret is missing.")
        return False

    try:

        message = MIMEMultipart()

        message["From"] = EMAIL_ADDRESS
        message["To"] = ALERT_EMAIL
        message["Subject"] = subject

        message.attach(
            MIMEText(body, "plain", "utf-8")
        )

        print("Connecting to email server...")

        # Gmail SMTP
        with smtplib.SMTP(
            "smtp.gmail.com",
            587,
            timeout=30
        ) as server:

            server.starttls()

            server.login(
                EMAIL_ADDRESS,
                EMAIL_PASSWORD
            )

            server.sendmail(
                EMAIL_ADDRESS,
                ALERT_EMAIL,
                message.as_string()
            )

        print("EMAIL SENT SUCCESSFULLY.")

        return True

    except Exception as e:

        print("ERROR: Could not send email.")
        print(str(e))

        return False


# ============================================
# GET TRUTH SOCIAL POSTS
# ============================================

def get_truth_posts():

    if not TRUTH_API_KEY:

        print("ERROR: TRUTH_API_KEY secret is missing.")

        return None

    if not TRUTH_API_URL:

        print("ERROR: TRUTH_API_URL secret is missing.")

        return None

    print("API credentials detected.")

    print(
        "Connecting to authorized Truth Social data source..."
    )

    headers = {

        "Authorization":
            f"Bearer {TRUTH_API_KEY}",

        "Accept":
            "application/json",

        "User-Agent":
            "Truth-Social-Monitor/1.0"
    }

    params = {

        "url": TARGET_URL
    }

    try:

        response = requests.get(

            TRUTH_API_URL,

            headers=headers,

            params=params,

            timeout=30
        )

        print("--------------------------------")
        print("HTTP status:", response.status_code)
        print("--------------------------------")

        if response.status_code >= 400:

            print("API REQUEST FAILED")
            print("Status code:", response.status_code)

            print("API response:")
            print(response.text[:5000])

            return None

        try:

            data = response.json()

        except ValueError:

            print(
                "ERROR: API response was not valid JSON."
            )

            return None

        print("JSON response received successfully.")

        return data

    except requests.exceptions.Timeout:

        print("ERROR: API request timed out.")

        return None

    except requests.exceptions.ConnectionError:

        print("ERROR: Could not connect to API.")

        return None

    except requests.exceptions.RequestException as e:

        print("ERROR: API request failed.")

        print(str(e))

        return None


# ============================================
# EXTRACT POSTS
# ============================================

def extract_posts(data):

    try:

        posts = data["data"]["posts"]

        if not isinstance(posts, list):

            print("ERROR: Posts were not returned as a list.")

            return []

        return posts

    except (KeyError, TypeError):

        print(
            "ERROR: Could not find posts in API response."
        )

        return []


# ============================================
# GET POST INFORMATION
# ============================================

def get_post_text(post):

    return (
        post.get("content")
        or post.get("text")
        or "(No text available)"
    )


def get_post_id(post):

    return post.get("id")


def get_post_url(post):

    return (
        post.get("url")
        or post.get("uri")
        or TARGET_URL
    )


def get_post_time(post):

    return (
        post.get("created_at")
        or post.get("createdAt")
        or "Unknown time"
    )


# ============================================
# MAIN MONITOR
# ============================================

def main():

    print("================================")
    print("TRUTH SOCIAL API MONITOR")
    print("================================")

    # -----------------------------------------
    # Check email configuration
    # -----------------------------------------

    if not EMAIL_ADDRESS:

        print(
            "WARNING: EMAIL_ADDRESS is not configured."
        )

    if not EMAIL_PASSWORD:

        print(
            "WARNING: EMAIL_PASSWORD is not configured."
        )

    if not ALERT_EMAIL:

        print(
            "WARNING: ALERT_EMAIL is not configured."
        )

    # -----------------------------------------
    # Get Truth Social data
    # -----------------------------------------

    data = get_truth_posts()

    if data is None:

        print("Could not retrieve Truth Social data.")

        return

    # -----------------------------------------
    # Extract posts
    # -----------------------------------------

    posts = extract_posts(data)

    print("--------------------------------")
    print("Posts retrieved:", len(posts))
    print("--------------------------------")

    if not posts:

        print("No posts were returned.")

        return

    # -----------------------------------------
    # Find newest post
    # -----------------------------------------

    newest_post = posts[0]

    newest_post_id = get_post_id(newest_post)

    if not newest_post_id:

        print(
            "ERROR: Newest post does not have an ID."
        )

        return

    newest_post_id = str(newest_post_id)

    newest_text = get_post_text(newest_post)

    newest_url = get_post_url(newest_post)

    newest_time = get_post_time(newest_post)

    print("Newest post ID:", newest_post_id)
    print("Newest post time:", newest_time)

    # -----------------------------------------
    # Load previous state
    # -----------------------------------------

    last_post_id = load_last_post()

    print("Previously recorded post:", last_post_id)

    # -----------------------------------------
    # FIRST RUN
    # -----------------------------------------

    if last_post_id is None:

        print("--------------------------------")
        print("FIRST RUN")
        print("--------------------------------")

        print(
            "No previous post has been recorded."
        )

        print(
            "Saving the current newest post."
        )

        save_last_post(newest_post_id)

        print(
            "No email sent on first run."
        )

        print(
            "This prevents the monitor from "
            "emailing you about an old post."
        )

        print("================================")

        return

    # -----------------------------------------
    # NO NEW POST
    # -----------------------------------------

    if newest_post_id == last_post_id:

        print("--------------------------------")
        print("NO NEW POSTS")
        print("--------------------------------")

        print(
            "The newest post is the same as "
            "the previous check."
        )

        print("================================")

        return

    # -----------------------------------------
    # NEW POST FOUND
    # -----------------------------------------

    print("--------------------------------")
    print("NEW POST DETECTED")
    print("--------------------------------")

    print("Post ID:", newest_post_id)
    print("Posted:", newest_time)

    print()
    print("POST:")
    print(newest_text)

    print()
    print("URL:")
    print(newest_url)

    # -----------------------------------------
    # Email
    # -----------------------------------------

    email_subject = (
        "🚨 New Donald Trump Truth Social Post"
    )

    email_body = f"""
NEW DONALD TRUMP TRUTH SOCIAL POST

Posted:
{newest_time}

--------------------------------

POST:

{newest_text}

--------------------------------

VIEW POST:

{newest_url}

--------------------------------

This alert was generated automatically
by the Truth Social Monitor.
"""

    email_sent = send_email(
        email_subject,
        email_body
    )

    # -----------------------------------------
    # Save new post after processing
    # -----------------------------------------

    if email_sent:

        save_last_post(newest_post_id)

    else:

        print(
            "Email was not sent."
        )

        print(
            "The previous post ID was NOT updated "
            "so the program can try again next run."
        )

    print("================================")
    print("MONITOR COMPLETE")
    print("================================")


# ============================================
# START PROGRAM
# ============================================

if __name__ == "__main__":

    main()
