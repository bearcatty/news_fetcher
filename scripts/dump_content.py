import sqlite3
import os
import sys

def dump_content():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "news.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, content FROM articles ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()

    with open("content_dump.txt", "w", encoding="utf-8") as f:
        for row in rows:
            f.write(f"ID: {row['id']}\n")
            f.write(f"Title: {row['title']}\n")
            f.write("=" * 40 + "\n")
            f.write(row['content'] if row['content'] else "[NO CONTENT]")
            f.write("\n" + "=" * 40 + "\n\n")

    print("Dumped content to content_dump.txt")
    conn.close()

if __name__ == "__main__":
    dump_content()
