import re

def clean_article_content(content):
    """
    Refined cleaning logic for testing.
    Returns None if the article should be discarded.
    """
    if not content:
        return None
    
    # 1. Check for "Deal/Review" specific markers that indicate the WHOLE article is marketing
    marketing_markers = [
        "Price history:",
        "Price comparison:",
        "Reviews consensus:",
        "✅ Buy it if:",
        "❌ Don't buy it if:",
        "Best Black Friday",
        "streaming deal",
    ]
    
    marker_count = sum(1 for m in marketing_markers if m in content)
    if marker_count >= 2:
        print(f"Discarding article due to marketing markers: {marker_count}")
        return None

    # 2. Line-by-line cleaning
    ad_patterns = [
        "Breaking space news, the latest updates on rocket launches",
        "Get the Space.com Newsletter",
        "Sign up for our newsletter",
        "Join our Space Forums",
        "Follow us on",
        "Subscribe to",
        "Related:",
        "More:",
        "Read more:",
        "Editor's note:",
        "This article was updated",
        "Check out our other guides",
        "Featured in guides:",
        "use a VPN",
        "NordVPN",
        "ExpressVPN",
        "Save over",
        "on sale right now",
        "coupon",
        "promo code",
        "visit our",
        "See our",
    ]
    
    paragraphs = content.split('\n\n')
    cleaned_paragraphs = []
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # Keep images
        if para.startswith('![') and '](' in para and para.endswith(')'):
            cleaned_paragraphs.append(para)
            continue

        # Check for ad patterns
        is_ad = False
        for pattern in ad_patterns:
            if pattern.lower() in para.lower():
                is_ad = True
                break
        
        # Additional heuristic: very short paragraphs that end with colon often indicate lists/links
        if len(para) < 50 and para.endswith(':'):
             # But be careful of "Note:"
             pass

        if not is_ad:
            # Filter out "Buy it if" lines if they missed the global check
            if "Buy it if:" in para or "Don't buy it if:" in para:
                continue
                
            cleaned_paragraphs.append(para)
    
    if not cleaned_paragraphs:
        return None
        
    return "\n\n".join(cleaned_paragraphs)

def test_cleaning():
    # Read from the dump file
    try:
        with open("content_dump.txt", "r", encoding="utf-8") as f:
            raw_data = f.read()
    except FileNotFoundError:
        print("content_dump.txt not found.")
        return

    # Split by ID (rough parsing)
    articles = raw_data.split("ID: ")
    
    for art in articles:
        if not art.strip():
            continue
            
        lines = art.split('\n')
        id_line = lines[0]
        title = ""
        content_start = 0
        
        for i, line in enumerate(lines):
            if line.startswith("Title: "):
                title = line[7:]
            if line.startswith("=====") and i > 1:
                content_start = i + 1
                break
        
        content = "\n".join(lines[content_start:]).split("=====")[0].strip()
        
        if content == "[NO CONTENT]":
            continue
            
        print(f"Testing Article ID: {id_line} - {title[:50]}...")
        cleaned = clean_article_content(content)
        
        if cleaned is None:
            print(">>> RESULT: DISCARDED (Marketing/Empty)")
        else:
            print(f">>> RESULT: KEPT ({len(cleaned)} chars)")
            # Print last few lines to check for footer ads
            print("--- Tail ---")
            print(cleaned[-200:])
        print("-" * 40)

if __name__ == "__main__":
    test_cleaning()
