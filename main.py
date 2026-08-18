
import os
import json
import smtplib
import requests

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from bs4 import BeautifulSoup


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

TRUTH_API_KEY = os.environ.get("TRUTH_API_KEY")
TRUTH_API_URL = os.environ.get("TRUTH_API_URL")

EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_TO = os.environ.get("EMAIL_TO")

TARGET_URL = "https://truthsocial.com/@realDonaldTrump"

STATE_FILE = "latest_post.json"


# ============================================================
# STATE MANAGEMENT
# ============================================================

def load_previous_post_id():
    """
    Load the ID of the newest post processed during
    the previous GitHub Actions run.
    """

    if not os.path.exists(STATE_FILE):
        return None

    try:

        with open(STATE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        post_id = data.get("post_id")

        if post_id is None:
            return None

        return str(post_id)

    except Exception as e:

        print("WARNING: Could not read state file.")
        print(str(e))

        return None


def save_latest_post_id(post_id):
    """
    Save the newest processed post ID.
    """

    if post_id is None:
        print("ERROR: Cannot save empty post ID.")
        return False

    data = {
        "post_id": str(post_id)
    }

    try:

        with open(STATE_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

        print("Saved latest post ID:", post_id)

        return True

    except Exception as e:

        print("ERROR: Could not save state file.")
        print(str(e))

        return False


# ============================================================
# EMAIL
# ============================================================

def send_email(subject, body):
    """
    Send an email notification through Gmail SMTP.
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

        with smtplib.SMTP(
            "smtp.gmail.com",
            587,
            timeout=30
        ) as server:

            server.ehlo()

            server.starttls()

            server.ehlo()

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
    """
    Retrieve recent posts from the configured Truth Social
    data source.
    """

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

        if not isinstance(data, dict):

            print("ERROR: API response was not a JSON object.")

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
# GET POSTS
# ============================================================

def get_posts_from_response(data):
    """
    Safely extract posts from the API response.
    """

    try:

        posts = data["data"]["posts"]

        if not isinstance(posts, list):

            print("ERROR: API posts field was not a list.")

            return []

        return posts

    except (KeyError, TypeError):

        print("ERROR: Could not find posts in API response.")

        return []


# ============================================================
# FIND NEWEST POST
# ============================================================

def get_newest_post(posts):
    """
    Find the newest post using the numeric post ID.

    Larger Truth Social/Mastodon-style IDs represent
    newer posts.
    """

    if not posts:

        return None

    valid_posts = []

    for post in posts:

        post_id = post.get("id")

        if post_id is None:
            continue

        try:

            int(post_id)

            valid_posts.append(post)

        except (ValueError, TypeError):

            continue

    if not valid_posts:

        print("ERROR: No posts with valid IDs were found.")

        return None

    newest_post = max(
        valid_posts,
        key=lambda post: int(post["id"])
    )

    return newest_post


# ============================================================
# FIND ALL NEW POSTS
# ============================================================

def get_new_posts(posts, previous_id):
    """
    Return every post newer than the previously recorded post.

    This prevents the monitor from missing posts if multiple
    posts were made between GitHub Actions runs.
    """

    if not posts:

        return []

    if previous_id is None:

        return []

    try:

        previous_id_int = int(previous_id)

    except (ValueError, TypeError):

        print("WARNING: Previous post ID was invalid.")

        return []

    new_posts = []

    for post in posts:

        post_id = post.get("id")

        if post_id is None:
            continue

        try:

            current_id = int(post_id)

        except (ValueError, TypeError):

            continue

        if current_id > previous_id_int:

            new_posts.append(post)

    # Sort from oldest to newest.
    # This means emails arrive in chronological order.

    new_posts.sort(
        key=lambda post: int(post["id"])
    )

    return new_posts


# ============================================================
# CLEAN POST CONTENT
# ============================================================

def clean_post_content(content):
    """
    Remove HTML from Truth Social post content.
    """

    if not content:

        return "(No text content.)"

    try:

        soup = BeautifulSoup(
            content,
            "html.parser"
        )

        cleaned = soup.get_text(
            separator=" ",
            strip=True
        )

        return cleaned

    except Exception:

        return content


# ============================================================
# GET POST URL
# ============================================================

def get_post_url(post):
    """
    Get the direct Truth Social URL for a post.
    """

    post_url = post.get("url")

    if post_url:

        return post_url

    post_id = post.get("id")

    if post_id:

        return (
            f"https://truthsocial.com/"
            f"@realDonaldTrump/{post_id}"
        )

    return TARGET_URL


# ============================================================
# CREATE EMAIL
# ============================================================

def create_email(post):
    """
    Create the email subject and body for a new post.
    """

    post_id = post.get(
        "id",
        "Unknown"
    )

    created_at = post.get(
        "createdAt",
        post.get(
            "created_at",
            "Unknown time"
        )
    )

    content = clean_post_content(
        post.get(
            "content",
            ""
        )
    )

    post_url = get_post_url(post)

    subject = "🚨 New Trump Truth Social Post"

    body = f"""
A new post from Donald Trump was detected on Truth Social.

==================================================

POST TIME:
{created_at}

==================================================

POST:

{content}

==================================================

TRUTH SOCIAL LINK:

{post_url}

==================================================

POST ID:

{post_id}

==================================================

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
    # CHECK CONFIGURATION
    # --------------------------------------------------------

    if not EMAIL_ADDRESS:
        print("WARNING: EMAIL_ADDRESS is not configured.")

    if not EMAIL_PASSWORD:
        print("WARNING: EMAIL_PASSWORD is not configured.")

    if not EMAIL_TO:
        print("WARNING: EMAIL_TO is not configured.")

    if not TRUTH_API_KEY:

        print("ERROR: TRUTH_API_KEY secret is missing.")

        return

    if not TRUTH_API_URL:

        print("ERROR: TRUTH_API_URL secret is missing.")

        return

    print("API credentials detected.")

    # --------------------------------------------------------
    # GET TRUTH SOCIAL POSTS
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

    # --------------------------------------------------------
    # EXTRACT POSTS
    # --------------------------------------------------------

    posts = get_posts_from_response(data)

    print("Posts retrieved:", len(posts))

    if not posts:

        print("No posts available.")

        print("================================")

        return

    # --------------------------------------------------------
    # FIND NEWEST POST
    # --------------------------------------------------------

    newest_post = get_newest_post(posts)

    if newest_post is None:

        print("Could not determine newest post.")

        print("================================")

        return

    newest_id = str(
        newest_post.get("id")
    )

    newest_time = newest_post.get(
        "createdAt",
        newest_post.get(
            "created_at",
            "Unknown time"
        )
    )

    print("--------------------------------")
    print("Newest post ID:", newest_id)
    print("Newest post time:", newest_time)
    print("--------------------------------")

    # --------------------------------------------------------
    # LOAD PREVIOUS STATE
    # --------------------------------------------------------

    previous_id = load_previous_post_id()

    print(
        "Previously recorded post:",
        previous_id
    )

    # ========================================================
    # FIRST RUN
    # ========================================================

    if previous_id is None:

        print("--------------------------------")
        print("FIRST RUN")
        print("--------------------------------")

        print(
            "No previous post has been recorded."
        )

        print(
            "Saving the current newest post."
        )

        save_latest_post_id(
            newest_id
        )

        print(
            "No email sent on first run."
        )

        print(
            "This prevents the monitor from emailing"
        )

        print(
            "you about an old post."
        )

        print("================================")

        return

    # ========================================================
    # FIND NEW POSTS
    # ========================================================

    new_posts = get_new_posts(
        posts,
        previous_id
    )

    # ========================================================
    # NO NEW POSTS
    # ========================================================

    if not new_posts:

        print("--------------------------------")
        print("NO NEW POSTS")
        print("--------------------------------")

        print(
            "The newest post is the same as or older than"
        )

        print(
            "the previously recorded post."
        )

        print(
            "No email will be sent."
        )

        print("================================")

        return

    # ========================================================
    # NEW POSTS FOUND
    # ========================================================

    print("--------------------------------")
    print(
        "🚨 NEW POST(S) DETECTED"
    )
    print("--------------------------------")

    print(
        "Number of new posts:",
        len(new_posts)
    )

    print(
        "Previous post:",
        previous_id
    )

    print(
        "Newest post:",
        newest_id
    )

    # --------------------------------------------------------
    # SEND EMAIL FOR EACH NEW POST
    # --------------------------------------------------------

    successful_emails = 0
    failed_emails = 0

    for post in new_posts:

        post_id = post.get(
            "id",
            "Unknown"
        )

        print("--------------------------------")
        print(
            "Processing new post:",
            post_id
        )
        print("--------------------------------")

        subject, body = create_email(
            post
        )

        email_sent = send_email(
            subject,
            body
        )

        if email_sent:

            successful_emails += 1

            print(
                "Alert sent for post:",
                post_id
            )

        else:

            failed_emails += 1

            print(
                "FAILED to send alert for post:",
                post_id
            )

    # ========================================================
    # UPDATE STATE
    # ========================================================

    # Only move the saved state forward if ALL emails
    # were successfully sent.
    #
    # This prevents the monitor from permanently skipping
    # a post if Gmail temporarily fails.

    if failed_emails == 0:

        save_latest_post_id(
            newest_id
        )

        print("--------------------------------")
        print(
            "State updated successfully."
        )
        print("--------------------------------")

    else:

        print("--------------------------------")
        print(
            "WARNING: Some emails failed."
        )

        print(
            "State was NOT advanced."
        )

        print(
            "The failed posts can be retried"
        )

        print(
            "on the next GitHub Actions run."
        )

        print("--------------------------------")

    # ========================================================
    # FINAL STATUS
    # ========================================================

    print("--------------------------------")
    print("MONITOR SUMMARY")
    print("--------------------------------")

    print(
        "New posts detected:",
        len(new_posts)
    )

    print(
        "Emails sent:",
        successful_emails
    )

    print(
        "Emails failed:",
        failed_emails
    )

    print("================================")
    print("MONITOR COMPLETE")
    print("================================")


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":

    main()
