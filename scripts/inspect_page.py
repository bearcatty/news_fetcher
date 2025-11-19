import requests
from bs4 import BeautifulSoup

def inspect():
    url = "https://www.space.com/space-exploration/launches-spacecraft/spacex-starlink-launch-group-6-94-asog"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to find the main article content
        article = soup.find('article')
        
        if article:
            print("\n--- Article Found ---")
            
            # Check for article-body
            body = article.find('div', id='article-body')
            if body:
                print("Found div with id='article-body'")
                paragraphs = body.find_all('p')
                print(f"Found {len(paragraphs)} paragraphs in article-body.")
                for i, p in enumerate(paragraphs[:3]):
                    print(f"P{i}: {p.get_text(strip=True)}")
            else:
                print("Did not find div with id='article-body'. Searching for all p tags in article.")
                paragraphs = article.find_all('p')
                print(f"Found {len(paragraphs)} paragraphs in article.")
                for i, p in enumerate(paragraphs[:3]):
                    print(f"P{i}: {p.get_text(strip=True)}")
        else:
            print("Could not find article tag.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect()
