# Space News Scraper Implementation Plan

## Goal Description
Build a Python-based scraper to extract news articles from space.com (or similar sites). The scraper will:
1.  Fetch the latest news articles.
2.  Extract details: Title, Publication Date, Author, Content, URL.
3.  Save data to a CSV file (`space_news.csv`).
4.  Run periodically (e.g., daily) to append new articles without duplicates.

## User Review Required
- **Target Site**: Defaulting to `space.com/news`.
- **Frequency**: Defaulting to daily checks.
- **Storage**: Local CSV file.

## Proposed Changes

### Project Structure
- `scraper.py`: Main script containing scraping logic, CSV handling, and scheduling.
- `requirements.txt`: Dependencies (requests, beautifulsoup4, schedule, pandas).

### Scraper Logic (`scraper.py`)
- **Dependencies**: `requests` for HTTP, `BeautifulSoup` for parsing, `pandas` for CSV handling (easier deduplication), `schedule` for timing.
- **Functions**:
    - `fetch_latest_news()`: Scrapes the news listing page.
    - `parse_article(url)`: Extracts full content from an article page.
    - `update_csv(new_data)`: Reads existing CSV, checks for duplicates based on URL, appends new rows.
    - `job()`: The function to run on schedule.
    - `main()`: Entry point to start the scheduler.

## Verification Plan

### Automated Tests
- Run the scraper function once to verify it fetches data.
- Check if `space_news.csv` is created and contains valid data.
- Run the scheduler for a short interval (e.g., every minute for testing) to verify it triggers.

### Manual Verification
- Inspect the generated CSV file for correct encoding and content.
