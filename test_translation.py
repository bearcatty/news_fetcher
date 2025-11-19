from translator import translate_article
import json

def test_translation():
    article = {
        "title": "SpaceX launches Starship",
        "content": "SpaceX has successfully launched its massive Starship rocket from Texas.",
        "url": "http://test.com"
    }
    
    print("Original:", article)
    translated = translate_article(article)
    print("Translated:", json.dumps(translated, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_translation()
