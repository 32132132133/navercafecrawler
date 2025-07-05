"""
프로젝트 상수 정의
모든 모듈에서 공통으로 사용하는 상수들을 정의합니다.
"""
# Disclaimer: use at your own risk. The authors take no responsibility for misuse.

# 브라우저 설정
DEFAULT_WINDOW_SIZE = (1920, 1080)
DEFAULT_TIMEOUT = 10
LOGIN_TIMEOUT = 300

# 네이버 URL 상수
NAVER_LOGIN_URL = "https://nid.naver.com/nidlogin.login"
NAVER_LOGOUT_URL = "https://nid.naver.com/nidlogout.logout"
NAVER_MAIN_URL = "https://www.naver.com"

# 크롤링 설정
DEFAULT_MAX_PAGES = 5
DEFAULT_MAX_POSTS = 50
DEFAULT_DELAY_RANGE = (1, 3)

# CSS 선렉터 상수
POST_SELECTORS = [
    ".article-board tbody tr",
    ".board-list tbody tr", 
    ".list-table tbody tr",
    "[class*='article'] tr",
    "[class*='list'] tr",
    "tr[class*='board']"
]

TITLE_SELECTORS = [
    ".article-head",
    ".title a",
    ".subject a", 
    "[class*='title'] a",
    "[class*='subject'] a"
]

AUTHOR_SELECTORS = [
    ".p-nick a",
    ".author",
    ".writer",
    "[class*='nick'] a",
    "[class*='author']",
    "[class*='writer']"
]

DATE_SELECTORS = [
    ".date",
    ".time", 
    "[class*='date']",
    "[class*='time']"
]

# 검색 관련 상수
SEARCH_SCOPES = {
    'all': 1,      # 전체
    'title': 2,    # 제목
    'content': 3,  # 내용
    'author': 4,   # 작성자
    'comment': 5   # 댓글
}

SORT_METHODS = {
    'date': 'date',
    'sim': 'sim',    # 정확도
    'count': 'count' # 댓글수
}

# 파일 경로 상수
OUTPUT_DIR = "output"
EXCEL_EXTENSION = ".xlsx"
DEFAULT_FILENAME_PREFIX = "naver_cafe_posts"

# 디버그 설정
DEBUG_MODE = False
VERBOSE_LOGGING = False

# 성능 설정
MAX_RETRY_ATTEMPTS = 3
ELEMENT_WAIT_TIMEOUT = 5
PAGE_LOAD_TIMEOUT = 30 