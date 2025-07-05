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

## Advanced Usage
For crawling many articles or collecting comments and images, run `main.py`.
You can store your login details in a `.env` file and pass additional options:

```bash
python main.py --keyword="example" --max-posts=100 --headless
```
Run `python main.py --help` for the full list of command-line arguments.
