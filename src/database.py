import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.path.join(BASE_DIR, "data", "news.db")

class DatabaseManager:
    def __init__(self, db_file: str = DB_FILE):
        self.db_file = db_file
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_file)

    def init_db(self):
        """Initialize the database with the articles table."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                content TEXT,
                title_zh TEXT,
                content_zh TEXT,
                author TEXT,
                published_date TEXT,
                fetched_at TEXT,
                synopsis TEXT,
                cover_image TEXT,
                status TEXT DEFAULT 'PENDING',
                translation_error TEXT
            )
        ''')
        
        # Check if cover_image column exists (for migration)
        cursor.execute("PRAGMA table_info(articles)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'cover_image' not in columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN cover_image TEXT")
            
        conn.commit()
        conn.close()

    def article_exists(self, url: str) -> bool:
        """Check if an article with the given URL already exists."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM articles WHERE url = ?', (url,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def save_article(self, article_data: Dict[str, Any]):
        """Save or update an article in the database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Prepare data for insertion/update
        url = article_data.get('url')
        if not url:
            return

        # Check if status needs to be updated based on translation
        status = 'PENDING'
        if article_data.get('content_zh'):
            status = 'COMPLETED'
        elif article_data.get('translation_error'):
            status = 'FAILED'
        
        # Use upsert logic
        cursor.execute('''
            INSERT OR REPLACE INTO articles (
                url, title, content, title_zh, content_zh, 
                author, published_date, fetched_at, synopsis, 
                cover_image, status, translation_error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            url,
            article_data.get('title'),
            article_data.get('content'),
            article_data.get('title_zh'),
            article_data.get('content_zh'),
            article_data.get('author'),
            article_data.get('published_date'),
            article_data.get('fetched_at') or datetime.now().isoformat(),
            article_data.get('synopsis'),
            article_data.get('cover_image'),
            status,
            article_data.get('translation_error')
        ))
        
        conn.commit()
        conn.close()

    def get_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Retrieve an article by URL."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM articles WHERE url = ?', (url,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about articles in the database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM articles')
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE status = 'COMPLETED'")
        completed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE status = 'FAILED'")
        failed = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total': total,
            'completed': completed,
            'failed': failed,
            'pending': total - completed - failed
        }

    def get_failed_articles(self) -> List[str]:
        """Get URLs of failed articles."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM articles WHERE status = 'FAILED'")
        urls = [row[0] for row in cursor.fetchall()]
        conn.close()
        return urls
