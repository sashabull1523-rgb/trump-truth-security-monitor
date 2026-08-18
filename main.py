from scraper import get_trump_posts


print("================================")
print("TRUTH SOCIAL SCRAPER TEST")
print("================================")

posts = get_trump_posts()

print("\n================================")
print(f"TOTAL POSTS FOUND: {len(posts)}")
print("================================")

if len(posts) == 0:

    print("NO POSTS FOUND")

else:

    print("SCRAPER SUCCESSFUL")

    for i, post in enumerate(posts, 1):

        print("\n")
        print(f"POST {i}")
        print("-----------------------------")
        print(post["text"])
        print(f"Date: {post['date']}")
        print(f"URL: {post['url']}")
