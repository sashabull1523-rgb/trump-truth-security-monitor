from scraper import get_trump_posts
from analyzer import analyze_post
from database import (
    create_database,
    save_post,
    get_unemailed_posts,
    mark_as_emailed
)
from email_sender import send_email


def run_monitor():

    print("Starting Truth Security Monitor")


    # Create database if it does not exist
    create_database()


    # Get new Truth Social posts
    posts = get_trump_posts()


    security_posts = []


    for post in posts:

        analysis = analyze_post(
            post["text"]
        )


        if analysis["relevant"]:


            post.update({

                "topic":
                analysis["topic"],

                "countries":
                ", ".join(
                    analysis["countries"]
                ),

                "organizations":
                ", ".join(
                    analysis["organizations"]
                ),

                "summary":
                analysis["summary"],

                "importance":
                analysis["importance"],

                "security_reason":
                analysis["security_reason"]

            })


            save_post(post)


            security_posts.append(post)



    if len(security_posts) > 0:


        report = build_report(
            security_posts
        )


        send_email(
            "Trump International Security Report",
            report
        )


        for post in security_posts:

            mark_as_emailed(
                post["id"]
            )


    else:

        print(
            "No international security posts found."
        )



def build_report(posts):

    report = ""

    report += "Trump International Security Report\n\n"


    for index, post in enumerate(posts):

        report += f"""
POST {index + 1}

Topic:
{post['topic']}

Summary:
{post['summary']}

Countries:
{post['countries']}

Organizations:
{post['organizations']}

Importance:
{post['importance']}

Why it matters:
{post['security_reason']}


Original Post:
{post['text']}


----------------------------

"""


    return report



if __name__ == "__main__":

    run_monitor()
