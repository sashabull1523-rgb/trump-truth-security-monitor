import os

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-5.5"

# Email
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO")

# Database
DATABASE_PATH = "data/posts.db"

# Truth Social account to monitor
TRUTH_SOCIAL_USERNAME = "realDonaldTrump"
