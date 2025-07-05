import sys
import requests
from bs4 import BeautifulSoup


def fetch_article(club_id: str, article_id: str) -> dict:
    """Fetch an article from Naver Cafe using club_id and article_id.

    Parameters
    ----------
    club_id : str
        Naver Cafe club ID.
    article_id : str
        Article ID within the cafe.

    Returns
    -------
    dict
        A dictionary containing the article URL, title, and text content.
    """
    url = (
        "https://cafe.naver.com/ArticleRead.nhn?"
        f"clubid={club_id}&articleid={article_id}"
    )
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    title_elem = soup.select_one("div.tit-box span.b")
    content_elem = soup.select_one("#tbody")

    return {
        "url": url,
        "title": title_elem.get_text(strip=True) if title_elem else "",
        "content": content_elem.get_text(strip=True) if content_elem else "",
    }


def main(argv: list[str]) -> None:
    if len(argv) != 3:
        print("Usage: python crawler.py <club_id> <article_id>")
        raise SystemExit(1)

    club_id, article_id = argv[1], argv[2]
    article = fetch_article(club_id, article_id)
    print(article["title"])
    print(article["content"])


if __name__ == "__main__":
    main(sys.argv)
