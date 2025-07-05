# NaverCafeCrawler
For a detailed explanation in Korean, see [README_ko.md](README_ko.md).
This project provides a simple example for scraping articles from Naver Cafe using Python.

## Requirements

- Python 3.8 or later
- Packages listed in `requirements.txt`

## Setup

```bash
pip install -r requirements.txt
```

## Usage

Run the crawler with the cafe club ID and article ID:

```bash
python crawler.py <club_id> <article_id>
```

This will print the article title and content to standard output.

**Note**: Only crawl content you are permitted to access and be sure to comply with Naver's terms of service.
