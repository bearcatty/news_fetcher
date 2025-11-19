# Space News Fetcher & Translator

A robust Python-based tool that scrapes space news articles, translates them into Chinese using a local LLM (via LM Studio), and preserves all content structure including images.

## Features

- **Automated Scraping**: Fetches latest news from space.com.
- **Intelligent Translation**: Uses local LLM (LM Studio) to translate content to Chinese.
- **Image Preservation**:
  - Extracts and saves cover images.
  - Preserves inline images in the translated content.
  - Maintains original image placement using Markdown placeholders during translation.
- **Robust Storage**: Uses SQLite (`news.db`) for data persistence and deduplication.
- **Reliability**:
  - Smart text chunking for long articles.
  - Retry mechanisms with exponential backoff for API calls.
  - Content cleaning to remove ads and irrelevant text.
  - Resumable operation (skips already processed articles).

## Prerequisites

- Python 3.8+
- [LM Studio](https://lmstudio.ai/) running locally with a server started (default port 1234).

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/bearcatty/news_fetcher.git
   cd news_fetcher
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Start LM Studio Server**:

   - Open LM Studio.
   - Load a model (e.g., `qwen2.5-7b-instruct`).
   - Start the local server on port `1234`.

2. **Run the Scraper**:

   ```bash
   python run_scraper.py
   ```

   Options:

   - `--retry`: Retry failed translations.
   - `--stats`: Show database statistics without scraping.

## Project Structure

- `run_scraper.py`: Main entry point for scraping and orchestration.
- `scraper.py`: Core scraping logic.
- `translator.py`: Translation logic with chunking and image protection.
- `database.py`: SQLite database manager.
- `mcp_server.py`: Client for LM Studio API.
- `news.db`: SQLite database file (created automatically).

## License

MIT
