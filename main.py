from scraper import get_trump_posts


print("Starting Truth Social scraper test")

posts = get_trump_posts()

print("\n================================")
print(f"TOTAL POSTS FOUND: {len(posts)}")
print("================================")

for i, post in enumerate(posts, 1):

    print(f"\nPOST {i}")
    print("----------------------------")
    print(post["text"])    
