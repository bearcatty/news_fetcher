#!/usr/bin/env python
"""
简化的抓取脚本 - 只运行一次，不使用定时任务
用于测试和手动执行
"""
import requests
from bs4 import BeautifulSoup
import time
import os
import sys

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from datetime import datetime
from translator import translate_article
from database import DatabaseManager

# Configuration
URL = "https://www.space.com/news"

def fetch_article_content(url):
    """
    Fetches the full text content of an article from the given URL.
    Returns a tuple (content, cover_image_url, error_message).
    """
    try:
        # Add a small delay to be polite
        time.sleep(1) 
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract cover image
        cover_image = ""
        og_image = soup.find('meta', property='og:image')
        if og_image:
            cover_image = og_image.get('content', '')
        
        # Find the article body
        article_body = soup.find('div', id='article-body')
        content_parts = []
        
        if not article_body:
            # Fallback: try to find article tag and get all paragraphs
            article = soup.find('article')
            if article:
                paragraphs = article.find_all('p')
                content = "\n\n".join([p.get_text(strip=True) for p in paragraphs])
                return clean_article_content(content), cover_image, None
            return "", cover_image, "Could not find article body or fallback content"
            
        # Iterate through children to preserve order of text and images
        for child in article_body.children:
            if child.name == 'p':
                text = child.get_text(strip=True)
                if text:
                    content_parts.append(text)
            elif child.name == 'figure':
                img = child.find('img')
                if img:
                    src = img.get('src')
                    alt = img.get('alt', '')
                    if src:
                        # Use markdown format for images
                        content_parts.append(f"\n![{alt}]({src})\n")
            elif child.name == 'div' and 'image' in str(child.get('class', '')):
                 # Handle div-wrapped images if any
                 img = child.find('img')
                 if img:
                    src = img.get('src')
                    alt = img.get('alt', '')
                    if src:
                        content_parts.append(f"\n![{alt}]({src})\n")

        content = "\n\n".join(content_parts)
        if not content:
             return "", cover_image, "Extracted content is empty"
             
        return clean_article_content(content), cover_image, None
        
    except Exception as e:
        print(f"Error fetching content for {url}: {e}")
        return "", "", str(e)


def clean_article_content(content):
    """
    清理文章内容，移除广告和不相关的推荐内容
    如果文章主要是营销内容，返回 None
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
        return None
    
    # 需要移除的广告/推广文本模式
    ad_patterns = [
        "Breaking space news, the latest updates on rocket launches, skywatching events and more!",
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
    
    # 分割成段落
    paragraphs = content.split('\n\n')
    cleaned_paragraphs = []
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # 如果是Markdown图片，直接保留
        if para.startswith('![') and '](' in para and para.endswith(')'):
            cleaned_paragraphs.append(para)
            continue

        # 检查是否包含广告模式
        is_ad = False
        for pattern in ad_patterns:
            if pattern.lower() in para.lower():
                is_ad = True
                break
        
        # 过滤掉太短的段落（可能是标题或推广），但保留图片
        # Additional heuristic: very short paragraphs that end with colon often indicate lists/links
        if not is_ad and len(para) < 50 and para.endswith(':'):
             # But be careful of "Note:"
             if "Note:" not in para:
                 is_ad = True

        if not is_ad:
            # Filter out "Buy it if" lines if they missed the global check
            if "Buy it if:" in para or "Don't buy it if:" in para:
                continue
                
            if len(para) > 20:
                cleaned_paragraphs.append(para)
    
    if not cleaned_paragraphs:
        return None
    
    return "\n\n".join(cleaned_paragraphs)


def fetch_and_translate_news(max_articles=10):
    """抓取并翻译新闻，限制数量避免运行太久"""
    print(f"\n{'='*60}")
    print(f"开始抓取新闻 - {datetime.now()}")
    print(f"{'='*60}\n")
    
    # 初始化数据库
    db = DatabaseManager()
    
    # 显示统计信息
    stats = db.get_stats()
    print(f"📊 当前数据库统计: 总计 {stats['total']}, 已翻译 {stats['completed']}, "
          f"失败 {stats['failed']}, 待处理 {stats['pending']}\n")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        print(f"🌐 正在访问 {URL}...")
        response = requests.get(URL, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        articles_processed = 0
        
        # Find all article containers
        listing_results = soup.find_all('div', class_=lambda x: x and 'listingResult' in x)
        
        print(f"📰 找到 {len(listing_results)} 篇文章\n")
        
        for item in listing_results:
            if articles_processed >= max_articles:
                print(f"\n⚠️  已处理 {max_articles} 篇文章，停止抓取")
                break
                
            try:
                # Extract Link
                link_tag = item.find('a', class_='article-link')
                if not link_tag:
                    continue
                link = link_tag.get('href')
                
                # 检查是否已存在于数据库
                if db.article_exists(link):
                    article = db.get_article(link)
                    if article and article['status'] == 'COMPLETED':
                        print(f"⏭️  跳过已存在且已完成: {link}")
                        continue
                    elif article and article['status'] == 'FAILED':
                        print(f"⚠️  发现之前失败的文章，将重试: {link}")
                    else:
                        print(f"ℹ️  更新已存在的文章: {link}")
                
                # Extract Title
                title_tag = item.find('h3', class_='article-name')
                title = title_tag.get_text(strip=True) if title_tag else "No Title"
                
                print(f"\n{'─'*60}")
                print(f"📄 [{articles_processed + 1}] {title}")
                print(f"🔗 {link}")
                
                # Extract Author
                author_tag = item.find('span', class_='by-author')
                author = author_tag.get_text(strip=True).replace('By', '').strip() if author_tag else "Unknown"
                
                # Extract Date
                date_tag = item.find('time')
                published_date = date_tag.get('datetime') if date_tag else None
                if not published_date and date_tag:
                     published_date = date_tag.get_text(strip=True)
                
                # Extract Synopsis
                synopsis_tag = item.find('p', class_='synopsis')
                synopsis = synopsis_tag.get_text(strip=True) if synopsis_tag else ""
                
                # Fetch Full Content and Cover Image
                print(f"📥 正在获取文章内容...")
                content, cover_image, fetch_error = fetch_article_content(link)
                
                if fetch_error:
                    print(f"❌ 获取内容失败: {fetch_error}")
                    article_data = {
                        'title': title,
                        'author': author,
                        'published_date': published_date,
                        'synopsis': synopsis,
                        'content': "",
                        'cover_image': cover_image,
                        'url': link,
                        'fetched_at': datetime.now().isoformat(),
                        'translation_error': f"Fetch Error: {fetch_error}"
                    }
                    db.save_article(article_data)
                    articles_processed += 1
                    continue

                print(f"✓ 内容长度: {len(content)} 字符")
                if cover_image:
                    print(f"✓ 找到封面图")
                
                article_data = {
                    'title': title,
                    'author': author,
                    'published_date': published_date,
                    'synopsis': synopsis,
                    'content': content,
                    'cover_image': cover_image,
                    'url': link,
                    'fetched_at': datetime.now().isoformat()
                }
                
                # 先保存基本信息（状态为PENDING）
                db.save_article(article_data)
                
                # Translate the article
                try:
                    print(f"🔄 正在翻译...")
                    article_data = translate_article(article_data)
                    
                    # 翻译成功，保存完整数据（状态将自动变为COMPLETED）
                    db.save_article(article_data)
                    print(f"✅ 翻译完成并保存到数据库")
                    
                except Exception as e:
                    print(f"❌ 翻译失败: {e}")
                    # 标记为失败
                    article_data['translation_error'] = str(e)
                    db.save_article(article_data)
                
                articles_processed += 1
                
            except Exception as e:
                print(f"❌ 处理文章出错: {e}")
                continue
        
        # 显示最终统计
        print(f"\n{'='*60}")
        stats = db.get_stats()
        print(f"📈 最终统计:")
        print(f"   总计: {stats['total']} 篇")
        print(f"   完成: {stats['completed']} 篇")
        print(f"   失败: {stats['failed']} 篇")
        
        if stats['failed'] > 0:
            print(f"\n⚠️  有 {stats['failed']} 篇文章翻译失败")
            print(f"   运行 'python run_scraper.py --retry' 可重试失败的文章")
        
        print(f"{'='*60}\n")
        
        return articles_processed

    except Exception as e:
        print(f"❌ 抓取新闻出错: {e}")
        import traceback
        traceback.print_exc()
        return 0


def retry_failed():
    """重试所有翻译失败的文章"""
    print("\n🔄 重试翻译失败的文章...\n")
    db = DatabaseManager()
    failed_urls = db.get_failed_articles()
    
    if not failed_urls:
        print("✓ 没有失败的文章需要重试")
        return
    
    print(f"找到 {len(failed_urls)} 篇失败的文章")
    
    # 重新运行抓取（逻辑中会自动处理失败的文章）
    fetch_and_translate_news(max_articles=len(failed_urls) + 5)


def show_stats():
    """显示翻译统计信息"""
    db = DatabaseManager()
    stats = db.get_stats()
    
    print("\n" + "="*60)
    print("📊 数据库统计")
    print("="*60)
    print(f"总计: {stats['total']} 篇文章")
    print(f"已完成: {stats['completed']} 篇")
    print(f"失败: {stats['failed']} 篇")
    print(f"待处理: {stats['pending']} 篇")
    
    if stats['failed'] > 0:
        print(f"\n运行 'python run_scraper.py --retry' 重试失败的文章")
    print("="*60 + "\n")


if __name__ == "__main__":
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == '--retry':
            retry_failed()
        elif sys.argv[1] == '--stats':
            show_stats()
        elif sys.argv[1] == '--help':
            print("\n用法:")
            print("  python run_scraper.py           # 抓取最多10篇新文章")
            print("  python run_scraper.py --retry   # 重试失败的文章")
            print("  python run_scraper.py --stats   # 显示统计信息")
            print()
        else:
            print(f"未知参数: {sys.argv[1]}")
            print("运行 'python run_scraper.py --help' 查看帮助")
    else:
        # 默认抓取最多10篇文章
        fetch_and_translate_news(max_articles=10)
