import sqlite3
import os

DATABASE_PATH = "data/posts.db"


def create_database():
    os.makedirs("data", exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id TEXT PRIMARY KEY,
        date TEXT,
        text TEXT,
        url TEXT,
        topic TEXT,
        countries TEXT,
        organizations TEXT,
        summary TEXT,
        importance TEXT,
        security_reason TEXT,
        emailed INTEGER DEFAULT 0
    )
    """)

    connection.commit()
    connection.close()


def save_post(post):
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO posts
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        post["id"],
        post["date"],
        post["text"],
        post["url"],
        post["topic"],
        post["countries"],
        post["organizations"],
        post["summary"],
        post["importance"],
        post["security_reason"],
        0
    ))

    connection.commit()
    connection.close()


def get_unemailed_posts():
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
    SELECT *
    FROM posts
    WHERE emailed = 0
    """)

    results = cursor.fetchall()

    connection.close()

    return results


def mark_as_emailed(post_id):
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
    UPDATE posts
    SET emailed = 1
    WHERE id = ?
    """, (post_id,))

    connection.commit()
    connection.close()
