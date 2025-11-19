import requests
from bs4 import BeautifulSoup
import schedule
import time
import os
from datetime import datetime

# Configuration
import json
from translator import translate_article
from progress_tracker import TranslationProgress, TranslationStatus

# Configuration
URL = "https://www.space.com/news"
JSON_FILE = "space_news.json"

def fetch_article_content(url):
    """
    Fetches the full text content of an article from the given URL.
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
        
        # Find the article body
        article_body = soup.find('div', id='article-body')
        if not article_body:
            # Fallback: try to find article tag and get all paragraphs
            article = soup.find('article')
            if article:
                paragraphs = article.find_all('p')
                return "\n\n".join([p.get_text(strip=True) for p in paragraphs])
            return ""
            
        paragraphs = article_body.find_all('p')
        content = "\n\n".join([p.get_text(strip=True) for p in paragraphs])
        return content
        
    except Exception as e:
        print(f"Error fetching content for {url}: {e}")
        return ""

def fetch_latest_news(progress: TranslationProgress = None):
    print(f"[{datetime.now()}] Fetching news from {URL}...")
    
    # 初始化进度跟踪器
    if progress is None:
        progress = TranslationProgress()
    
    # 显示统计信息
    stats = progress.get_statistics()
    print(f"翻译进度: 已完成 {stats['completed']}, 失败 {stats['failed']}, "
          f"进行中 {stats['translating']}, 待处理 {stats['pending']}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        articles = []
        seen_urls = set()
        
        # Find all article containers
        # Based on inspection: div.listingResult
        listing_results = soup.find_all('div', class_=lambda x: x and 'listingResult' in x)
        
        print(f"Found {len(listing_results)} articles on the page.")
        
        for item in listing_results:
            try:
                # Extract Link
                link_tag = item.find('a', class_='article-link')
                if not link_tag:
                    continue
                link = link_tag.get('href')
                
                if link in seen_urls:
                    continue
                seen_urls.add(link)
                
                # 检查是否已完成翻译
                if progress.is_completed(link):
                    print(f"跳过已翻译文章: {link}")
                    continue
                
                # Extract Title
                title_tag = item.find('h3', class_='article-name')
                title = title_tag.get_text(strip=True) if title_tag else "No Title"
                
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
                
                # Fetch Full Content
                print(f"Fetching content for: {title}")
                content = fetch_article_content(link)
                
                article_data = {
                    'title': title,
                    'author': author,
                    'published_date': published_date,
                    'synopsis': synopsis,
                    'content': content,
                    'url': link,
                    'fetched_at': datetime.now().isoformat()
                }
                
                # 标记为翻译中
                progress.set_status(link, TranslationStatus.TRANSLATING)
                
                # Translate the article
                try:
                    print(f"Translating article...")
                    article_data = translate_article(article_data)
                    
                    # 翻译成功，标记为完成
                    progress.set_status(link, TranslationStatus.COMPLETED)
                    print(f"✓ 翻译完成: {title}")
                    
                except Exception as e:
                    print(f"✗ 翻译失败: {e}")
                    # 标记为失败，但继续处理其他文章
                    progress.set_status(link, TranslationStatus.FAILED, str(e))
                    article_data['title_zh'] = ""
                    article_data['content_zh'] = ""
                    article_data['translation_error'] = str(e)
                
                articles.append(article_data)
                
                # 立即保存这篇文章到JSON（增量保存）
                save_single_article(article_data)
                
            except Exception as e:
                print(f"Error parsing article item: {e}")
                continue
                
        return articles

    except Exception as e:
        print(f"Error fetching news: {e}")
        return []

def save_single_article(article):
    """
    立即保存单篇文章到JSON文件（增量保存）
    避免批量保存导致的数据丢失风险
    """
    if not article:
        return
    
    existing_articles = []
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                existing_articles = json.load(f)
        except Exception as e:
            print(f"Error reading existing JSON: {e}")
            existing_articles = []
    
    # 检查是否已存在（基于URL去重）
    existing_urls = {a['url'] for a in existing_articles}
    
    if article['url'] not in existing_urls:
        existing_articles.append(article)
        try:
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(existing_articles, f, indent=4, ensure_ascii=False)
            print(f"✓ 已保存文章到 {JSON_FILE}")
        except Exception as e:
            print(f"✗ 保存文章失败: {e}")
    else:
        # 更新现有文章
        for i, existing in enumerate(existing_articles):
            if existing['url'] == article['url']:
                existing_articles[i] = article
                break
        try:
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(existing_articles, f, indent=4, ensure_ascii=False)
            print(f"✓ 已更新文章到 {JSON_FILE}")
        except Exception as e:
            print(f"✗ 更新文章失败: {e}")


def update_json(new_articles):
    """批量更新JSON（向后兼容，但现在推荐使用save_single_article）"""
    if not new_articles:
        print("No articles to save.")
        return

    existing_articles = []
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                existing_articles = json.load(f)
        except Exception as e:
            print(f"Error reading existing JSON: {e}")
            # If error, we might start fresh or backup. For now, start fresh but warn.
            print("Starting with empty list due to read error.")

    # Deduplicate based on URL
    existing_urls = {article['url'] for article in existing_articles}
    articles_to_add = [a for a in new_articles if a['url'] not in existing_urls]
    
    if articles_to_add:
        updated_articles = existing_articles + articles_to_add
        try:
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(updated_articles, f, indent=4, ensure_ascii=False)
            print(f"Added {len(articles_to_add)} new articles to {JSON_FILE}.")
        except Exception as e:
            print(f"Error saving JSON: {e}")
    else:
        print("No new articles found (all duplicates).")

def job():
    print("Starting scheduled job...")
    progress = TranslationProgress()
    
    # 显示失败文章统计
    failed = progress.get_failed_articles()
    if failed:
        print(f"⚠️  有 {len(failed)} 篇文章翻译失败，可以运行 'python scraper.py --retry' 重试")
    
    articles = fetch_latest_news(progress)
    # 注意：现在每篇文章都是增量保存的，这里不需要再批量保存
    print(f"Job finished. Processed {len(articles)} articles.\\n")
    
    # 显示最终统计
    stats = progress.get_statistics()
    print(f"最终统计: 总计 {stats['total']}, 完成 {stats['completed']}, "
          f"失败 {stats['failed']}, 待处理 {stats['pending']}")


def retry_failed():
    """重试所有翻译失败的文章"""
    print("重试翻译失败的文章...")
    progress = TranslationProgress()
    failed_urls = progress.get_failed_articles()
    
    if not failed_urls:
        print("没有失败的文章需要重试")
        return
    
    print(f"找到 {len(failed_urls)} 篇失败的文章")
    progress.reset_failed()
    
    # 重新运行抓取（会跳过已完成的，只处理失败的）
    job()


def show_stats():
    """显示翻译统计信息"""
    progress = TranslationProgress()
    stats = progress.get_statistics()
    
    print("\n=== 翻译统计 ===")
    print(f"总计: {stats['total']} 篇文章")
    print(f"已完成: {stats['completed']} 篇")
    print(f"失败: {stats['failed']} 篇")
    print(f"进行中: {stats['translating']} 篇")
    print(f"待处理: {stats['pending']} 篇")
    
    if stats['failed'] > 0:
        print(f"\n运行 'python scraper.py --retry' 重试失败的文章")
    print()


def main():
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == '--retry':
            retry_failed()
            return
        elif sys.argv[1] == '--stats':
            show_stats()
            return
        elif sys.argv[1] == '--help':
            print("用法:")
            print("  python scraper.py          # 正常运行")
            print("  python scraper.py --retry  # 重试失败的文章")
            print("  python scraper.py --stats  # 显示统计信息")
            return
    
    # Run once immediately
    job()
    
    # Schedule to run every day at a specific time, or for demo purposes, every minute?
    # The user asked for "daily", but for verification I should probably leave it running or just show it works.
    # I'll set it to run every day at 09:00, but also keep the script alive.
    
    schedule.every().day.at("09:00").do(job)
    # schedule.every(1).minutes.do(job) # Uncomment for testing
    
    print("Scheduler started. Press Ctrl+C to exit.")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()

