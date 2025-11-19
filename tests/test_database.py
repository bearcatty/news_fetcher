import unittest
import os
import sys
import sqlite3

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from database import DatabaseManager

TEST_DB = "test_news.db"

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        # Use a separate test database
        self.db = DatabaseManager(TEST_DB)

    def tearDown(self):
        # Clean up test database
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_init_db(self):
        """Test if the table is created correctly."""
        conn = sqlite3.connect(TEST_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
        self.assertIsNotNone(cursor.fetchone())
        conn.close()

    def test_save_and_get_article(self):
        """Test saving and retrieving an article."""
        article_data = {
            'url': 'http://example.com/1',
            'title': 'Test Article',
            'content': 'Test Content',
            'author': 'Tester',
            'published_date': '2023-01-01'
        }
        self.db.save_article(article_data)
        
        retrieved = self.db.get_article('http://example.com/1')
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['title'], 'Test Article')
        self.assertEqual(retrieved['status'], 'PENDING') # Default status

    def test_article_exists(self):
        """Test existence check."""
        url = 'http://example.com/exists'
        self.assertFalse(self.db.article_exists(url))
        
        self.db.save_article({'url': url, 'title': 'Exists'})
        self.assertTrue(self.db.article_exists(url))

    def test_deduplication(self):
        """Test that saving the same URL updates instead of duplicates."""
        url = 'http://example.com/dup'
        
        # First save
        self.db.save_article({'url': url, 'title': 'Version 1'})
        
        # Second save with different title
        self.db.save_article({'url': url, 'title': 'Version 2'})
        
        stats = self.db.get_stats()
        self.assertEqual(stats['total'], 1)
        
        retrieved = self.db.get_article(url)
        self.assertEqual(retrieved['title'], 'Version 2')

    def test_status_update(self):
        """Test status update logic."""
        url = 'http://example.com/status'
        
        # Save with translation
        self.db.save_article({
            'url': url, 
            'title': 'En', 
            'title_zh': 'Zh', 
            'content_zh': 'Content Zh'
        })
        
        retrieved = self.db.get_article(url)
        self.assertEqual(retrieved['status'], 'COMPLETED')

if __name__ == '__main__':
    unittest.main()
