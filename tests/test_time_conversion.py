import sys
import os

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from translator import translate_article
import json

def test_time_conversion():
    """测试时间转换功能"""
    article = {
        "title": "SpaceX Falcon 9 rocket launches at 7:12 p.m. EST on Tuesday",
        "content": "SpaceX launched its Falcon 9 rocket from Cape Canaveral Space Force Station on Tuesday at 7:12 p.m. EST (0012 GMT on Nov. 19). The rocket successfully deployed 29 Starlink satellites into low Earth orbit.",
        "url": "http://test.com"
    }
    
    print("原文:", article["title"])
    print("\n原文内容:", article["content"])
    print("\n开始翻译...")
    
    translated = translate_article(article)
    
    print("\n" + "="*60)
    print("翻译结果:")
    print("="*60)
    print("中文标题:", translated.get('title_zh', 'N/A'))
    print("\n中文内容:", translated.get('content_zh', 'N/A'))

if __name__ == "__main__":
    test_time_conversion()
