from scraper import get_trump_posts
from analyzer import analyze_post
from database import initialize_database, save_post
from email_sender import send_email


def main():

    print("Starting Truth Security Monitor")

    initialize_database()

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

            security_posts.append(
                combined_post
            )

            save_post(
                combined_post
            )


    if not security_posts:

        print(
            "No international security posts found."
        )

        return


    email_content = ""

    for post in security_posts:

        email_content += f"""
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


Why it matters:
{post['security_reason']}

"""


    send_email(
        "Daily Trump International Security Monitor",
        email_content
    )


    print(
        "Email sent successfully"
    )


if __name__ == "__main__":
    main()
