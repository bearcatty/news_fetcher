import requests
from bs4 import BeautifulSoup

url = "https://www.space.com/entertainment/ryan-gosling-and-rocky-save-life-on-earth-in-new-project-hail-mary-trailer-video"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

# Check for cover image (usually in head or top of article)
og_image = soup.find('meta', property='og:image')
print(f"Cover Image (OG): {og_image['content'] if og_image else 'Not found'}")

# Check article body for images
article_body = soup.find('div', id='article-body')
if article_body:
    print("\n--- Article Body Structure ---")
    # Print first few children to see structure
    for i, child in enumerate(article_body.children):
        if child.name:
            print(f"[{i}] Tag: {child.name}, Class: {child.get('class')}")
            if child.name == 'figure':
                img = child.find('img')
                if img:
                    print(f"    Image found: {img.get('src')}")
                    print(f"    Alt: {img.get('alt')}")
            elif child.name == 'div' and 'image' in str(child.get('class', '')):
                 print(f"    Potential image div: {child}")
