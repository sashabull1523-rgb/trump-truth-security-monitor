from scraper import get_trump_posts
from analyzer import analyze_post
from database import create_database, save_post
from email_sender import send_email


def main():

    print("Starting Truth Security Monitor")

    create_database()

    posts = get_trump_posts()

    if not posts:
        print("No Trump posts found.")
        return


    security_posts = []


    for post in posts:

        analysis = analyze_post(
            post["text"]
        )

        if analysis["relevant"]:

            combined_post = {
                **post,
                **analysis
            }

            save_post(
                combined_post
            )

            security_posts.append(
                combined_post
            )


    if not security_posts:

        print(
            "No international security posts found."
        )

        return


    email_body = ""


    for post in security_posts:

        email_body += f"""
--------------------------------

Trump Truth Social Post:

{post['text']}

Topic:
{post['topic']}

Countries:
{', '.join(post['countries'])}

Organizations:
{', '.join(post['organizations'])}

Importance:
{post['importance']}

Summary:
{post['summary']}

Security Reason:
{post['security_reason']}

"""


    send_email(
        "Daily Trump International Security Monitor",
        email_body
    )


    print(
        "Monitor complete"
    )


if __name__ == "__main__":
    main()
