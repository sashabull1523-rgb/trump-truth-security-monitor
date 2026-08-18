import os
import json
import smtplib
import requests

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv


load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

TRUTH_API_KEY = os.environ.get("TRUTH_API_KEY")
TRUTH_API_URL = os.environ.get("TRUTH_API_URL")

EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_TO = os.environ.get("EMAIL_TO")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

TARGET_URL = "https://truthsocial.com/@realDonaldTrump"

STATE_FILE = "latest_post.json"


# ============================================================
# STATE MANAGEMENT
# ============================================================

def load_previous_post_id():
    """
    Load the ID of the most recent post we saw during
    the previous GitHub Actions run.
    """

    if not os.path.exists(STATE_FILE):
        return None

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data.get("post_id")

    except Exception as e:
        print("WARNING: Could not read previous post.")
        print(str(e))
        return None


def save_latest_post_id(post_id):
    """
    Save the newest post ID so the next run can determine
    whether a new post appeared.
    """

    data = {
        "post_id": post_id
    }

    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    print("Saved latest post ID:", post_id)


# ============================================================
# EMAIL
# ============================================================

def send_email(subject, body):
    """
    Send an email notification using Gmail SMTP.
    """

    if not EMAIL_ADDRESS:
        print("ERROR: EMAIL_ADDRESS is not configured.")
        return False

    if not EMAIL_PASSWORD:
        print("ERROR: EMAIL_PASSWORD is not configured.")
        return False

    if not EMAIL_TO:
        print("ERROR: EMAIL_TO is not configured.")
        return False

    print("--------------------------------")
    print("Sending email alert...")
    print("From:", EMAIL_ADDRESS)
    print("To:", EMAIL_TO)
    print("--------------------------------")

    message = MIMEMultipart()

    message["From"] = EMAIL_ADDRESS
    message["To"] = EMAIL_TO
    message["Subject"] = subject

    message.attach(
        MIMEText(body, "plain", "utf-8")
    )

    try:

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:

            server.starttls()

            server.login(
                EMAIL_ADDRESS,
                EMAIL_PASSWORD
            )

            server.sendmail(
                EMAIL_ADDRESS,
                EMAIL_TO,
                message.as_string()
            )

        print("EMAIL SENT SUCCESSFULLY.")

        return True

    except Exception as e:

        print("ERROR: Could not send email.")
        print(str(e))

        return False


# ============================================================
# TRUTH SOCIAL API
# ============================================================

def get_truth_social_posts():

    if not TRUTH_API_KEY:
        print("ERROR: TRUTH_API_KEY secret is missing.")
        return None

    if not TRUTH_API_URL:
        print("ERROR: TRUTH_API_URL secret is missing.")
        return None

    headers = {
        "Authorization": f"Bearer {TRUTH_API_KEY}",
        "Accept": "application/json",
        "User-Agent": "Truth-Social-Monitor/1.0"
    }

    params = {
        "url": TARGET_URL
    }

    print("Connecting to authorized Truth Social data source...")

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

            try:
                print("API response:")
                print(response.text[:5000])
            except Exception:
                pass

            return None

        try:

            data = response.json()

        except ValueError:

            print("ERROR: API response was not valid JSON.")
            return None

        if not data.get("success"):

            print("ERROR: API reported an unsuccessful request.")
            print(data)

            return None

        return data

    except requests.exceptions.Timeout:

        print("ERROR: Truth Social API request timed out.")
        return None

    except requests.exceptions.ConnectionError:

        print("ERROR: Could not connect to Truth Social API.")
        return None

    except requests.exceptions.RequestException as e:

        print("ERROR: API request failed.")
        print(str(e))

        return None

    except Exception as e:

        print("UNEXPECTED API ERROR:")
        print(str(e))

        return None


# ============================================================
# FIND NEWEST POST
# ============================================================

def get_newest_post(data):

    try:

        posts = data["data"]["posts"]

        if not posts:

            print("No posts were returned.")
            return None

        newest_post = posts[0]

        return newest_post

    except (KeyError, TypeError):

        print("ERROR: Could not find posts in API response.")
        return None


# ============================================================
# FORMAT EMAIL
# ============================================================

def create_email(post):

    post_id = post.get("id", "Unknown")

    post_url = post.get(
        "url",
        f"https://truthsocial.com/@realDonaldTrump/{post_id}"
    )

    created_at = post.get(
        "createdAt",
        "Unknown time"
    )

    content = post.get(
        "content",
        ""
    )

    # Remove HTML if necessary.
    if "<" in content and ">" in content:

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            content,
            "html.parser"
        )

        content = soup.get_text(
            separator=" ",
            strip=True
        )

    subject = "🚨 New Trump Truth Social Post"

    body = f"""
A new post from Donald Trump was detected on Truth Social.

--------------------------------------------------

POST TIME:
{created_at}

--------------------------------------------------

POST:

{content}

--------------------------------------------------

TRUTH SOCIAL LINK:

{post_url}

--------------------------------------------------

POST ID:

{post_id}

This alert was generated automatically by your
Truth Social monitoring program.
"""

    return subject, body


# ============================================================
# MAIN MONITOR
# ============================================================

def main():

    print()
    print("================================")
    print("TRUTH SOCIAL API MONITOR")
    print("================================")

    # --------------------------------------------------------
    # Check email configuration
    # --------------------------------------------------------

    if not EMAIL_ADDRESS:
        print("WARNING: EMAIL_ADDRESS is not configured.")

    if not EMAIL_PASSWORD:
        print("WARNING: EMAIL_PASSWORD is not configured.")

    if not EMAIL_TO:
        print("WARNING: EMAIL_TO is not configured.")

    # --------------------------------------------------------
    # Check API configuration
    # --------------------------------------------------------

    if not TRUTH_API_KEY:

        print("ERROR: TRUTH_API_KEY secret is missing.")
        return

    if not TRUTH_API_URL:

        print("ERROR: TRUTH_API_URL secret is missing.")
        return

    print("API credentials detected.")

    # --------------------------------------------------------
    # Get Truth Social posts
    # --------------------------------------------------------

    data = get_truth_social_posts()

    if data is None:

        print()
        print("================================")
        print("MONITOR FAILED")
        print("================================")

        return

    print("--------------------------------")
    print("JSON response received successfully.")
    print("--------------------------------")

    try:

        posts = data["data"]["posts"]

        print("Posts retrieved:", len(posts))

    except (KeyError, TypeError):

        print("ERROR: Could not read posts.")
        return

    # --------------------------------------------------------
    # Find newest post
    # --------------------------------------------------------

    newest_post = get_newest_post(data)

    if newest_post is None:
        return

    newest_id = newest_post.get("id")

    newest_time = newest_post.get(
        "createdAt",
        "Unknown time"
    )

    print("--------------------------------")
    print("Newest post ID:", newest_id)
    print("Newest post time:", newest_time)
    print("--------------------------------")

    # --------------------------------------------------------
    # Load previous post
    # --------------------------------------------------------

    previous_id = load_previous_post_id()

    print("Previously recorded post:", previous_id)

    # --------------------------------------------------------
    # FIRST RUN
    # --------------------------------------------------------

    if previous_id is None:

        print("--------------------------------")
        print("FIRST RUN")
        print("--------------------------------")

        print("No previous post has been recorded.")
        print("Saving the current newest post.")

        save_latest_post_id(newest_id)

        print("No email sent on first run.")
        print("This prevents the monitor from emailing you")
        print("about an old post.")

        print("================================")

        return

    # --------------------------------------------------------
    # NO NEW POST
    # --------------------------------------------------------

    if newest_id == previous_id:

        print("--------------------------------")
        print("NO NEW POST")
        print("--------------------------------")

        print("The newest post is the same as the previous run.")
        print("No email will be sent.")

        print("================================")

        return

    # --------------------------------------------------------
    # NEW POST DETECTED
    # --------------------------------------------------------

    print("--------------------------------")
    print("🚨 NEW POST DETECTED")
    print("--------------------------------")

    print("Previous post:", previous_id)
    print("New post:", newest_id)

    # Create email
    subject, body = create_email(newest_post)

    # Send email
    email_sent = send_email(
        subject,
        body
    )

    # Save new post ONLY after processing it
    save_latest_post_id(newest_id)

    print("--------------------------------")

    if email_sent:

        print("New post alert email sent successfully.")

    else:

        print("New post detected, but email was not sent.")

    print("================================")
    print("MONITOR COMPLETE")
    print("================================")


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()
