"""
Utils 패키지
네이버 카페 크롤러에서 사용하는 유틸리티 모듈들을 포함합니다.
"""

# 주요 유틸리티 함수들 import
from .constants import *

# utils.py의 함수들을 직접 정의
import time
import re
from selenium.webdriver.support.wait import WebDriverWait

def safe_wait(driver, seconds):
    """안전한 대기"""
    time.sleep(seconds)

def clean_text(text):
    """텍스트 정리"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip())

def get_timestamp():
    """현재 타임스탬프 반환"""
    import datetime
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def print_progress(current, total, message=""):
    """진행률 출력"""
    if total > 0:
        percentage = (current / total) * 100
        print(f"진행률: {current}/{total} ({percentage:.1f}%) {message}")

def extract_post_number(url):
    """URL에서 게시글 번호 추출"""
    if not url:
        return None
    match = re.search(r'articleid=(\d+)', url)
    return match.group(1) if match else None

__version__ = "1.0.0"
__all__ = [
    "DEFAULT_WINDOW_SIZE",
    "DEFAULT_TIMEOUT", 
    "NAVER_LOGIN_URL",
    "POST_SELECTORS",
    "TITLE_SELECTORS",
    "AUTHOR_SELECTORS",
    "DATE_SELECTORS",
    "SEARCH_SCOPES",
    "SORT_METHODS",
    "safe_wait",
    "clean_text",
    "get_timestamp",
    "print_progress",
    "extract_post_number"
] 