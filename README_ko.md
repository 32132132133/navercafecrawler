# 네이버 카페 크롤러 (NaverCafeCrawler)

이 프로젝트는 Python을 사용하여 네이버 카페의 게시글을 가져오는 간단한 예제입니다. 카페의 클럽 ID와 게시글 ID를 입력하면 해당 게시글의 제목과 내용을 출력합니다.
**면책 조항:** 이 코드를 사용할 경우 모든 책임은 사용자에게 있습니다. 발생하는 모든 결과는 사용자 본인의 책임입니다.



## 요구 사항
- Python 3.8 이상
- `requirements.txt`에 명시된 패키지

## 설치 방법
아래 명령어로 필요한 패키지를 설치합니다.
```bash
pip install -r requirements.txt
```

## 사용 방법
다음과 같이 클럽 ID와 게시글 ID를 인자로 주어 실행합니다.
```bash
python crawler.py <club_id> <article_id>
```
실행하면 게시글의 제목과 본문이 터미널에 표시됩니다.

## 참고 사항
- 네이버의 서비스 약관을 준수해야 합니다.
- 접근 권한이 없는 게시글을 무단으로 수집하지 마세요.

## 고급 사용법
보다 많은 게시글을 수집하거나 댓글, 이미지 등 추가 정보를 가져오려면 `main.py`를 사용하세요.
환경 설정을 위해 `.env` 파일에 네이버 로그인 정보를 저장할 수 있습니다.

예시:
```bash
python main.py --keyword="예시검색" --max-posts=100 --headless
```
주요 옵션은 다음과 같습니다.
- `--keyword` : 크롤링할 검색 키워드 (여러 개는 쉼표로 구분)
- `--cafe` : 대상 카페의 URL
- `--max-posts` : 최대 수집 게시글 수
- `--max-pages` : 검색 페이지 탐색 범위
- `--no-content` : 게시글 본문을 수집하지 않음
- `--no-comments` : 댓글을 수집하지 않음
- `--with-images` : 이미지 정보를 함께 저장
- `--headless` : 브라우저 창을 띄우지 않고 실행

보다 자세한 설명은 `python main.py --help` 명령으로 확인할 수 있습니다.

## 면책 조항
이 코드를 사용하는 모든 책임은 사용자에게 있습니다. 네이버 서비스 약관 및 관련 법규 준수 여부는 전적으로 사용자 책임이며, 작성자는 그로 인해 발생하는 어떠한 문제에 대해서도 책임을 지지 않습니다.
