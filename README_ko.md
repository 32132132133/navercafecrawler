# 네이버 카페 크롤러 (NaverCafeCrawler)

이 프로젝트는 Python을 사용하여 네이버 카페의 게시글을 가져오는 간단한 예제입니다. 카페의 클럽 ID와 게시글 ID를 입력하면 해당 게시글의 제목과 내용을 출력합니다.

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
