from datetime import datetime
import hashlib


def get_trump_posts():

    posts = []

    # TEMPORARY TEST POST
    # This tests the rest of your system
    # before fixing the Truth Social connection

    text = """
    President Trump announces a new NATO defense policy
    involving European allies and military cooperation.
    """

    post_id = hashlib.sha256(
        text.encode()
    ).hexdigest()


    posts.append({

        "id": post_id,

        "date": datetime.now().isoformat(),

        "text": text,

        "url": "test"

    })


    return posts
