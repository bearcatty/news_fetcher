import sqlite3
import re

def verify_images():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "news.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT url, title, content, content_zh, cover_image FROM articles WHERE status='COMPLETED'")
    articles = cursor.fetchall()
    
    print(f"Found {len(articles)} completed articles.\n")
    
    for article in articles:
        print(f"Checking: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Cover Image: {article['cover_image']}")
        
        # Check for markdown images in original content
        original_images = re.findall(r'!\[.*?\]\(.*?\)', article['content'])
        print(f"Original Images: {len(original_images)}")
        
        # Check for markdown images in translated content
        translated_images = re.findall(r'!\[.*?\]\(.*?\)', article['content_zh'])
        print(f"Translated Images: {len(translated_images)}")
        
        # Check for placeholders (should be 0)
        placeholders = re.findall(r'\[\[IMG_\d+\]\]', article['content_zh'])
        print(f"Remaining Placeholders: {len(placeholders)}")
        
        if len(original_images) > 0:
            if len(translated_images) == len(original_images):
                print("✅ Image count matches!")
            else:
                print(f"❌ Image count mismatch! Original: {len(original_images)}, Translated: {len(translated_images)}")
                
            # Print first few images to verify
            for i, img in enumerate(translated_images[:3]):
                print(f"  Image {i+1}: {img}")
        else:
            print("ℹ️ No inline images in this article.")
            
        print("-" * 50)
        
    conn.close()

if __name__ == "__main__":
    verify_images()
