# Disclaimer: use at your own risk. The authors take no responsibility for misuse.
import os
import time
import pandas as pd
from datetime import datetime
import re
from typing import Union

def create_output_directory(output_dir):
    """출력 디렉토리 생성"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"출력 디렉토리 생성: {output_dir}")

def clean_text(text):
    """텍스트 정리 (불필요한 공백, 특수문자 제거)"""
    if not text:
        return ""
    
    # 여러 공백을 하나로 변환
    text = re.sub(r'\s+', ' ', text)
    # 앞뒤 공백 제거
    text = text.strip()
    # 특수문자 일부 제거 (필요에 따라 수정)
    text = re.sub(r'[^\w\s가-힣ㄱ-ㅎㅏ-ㅣ.,!?()[\]-]', '', text)
    
    return text

def save_to_excel(posts_data, filename):
    """수집된 데이터를 엑셀 파일로 저장"""
    try:
        df = pd.DataFrame(posts_data)
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"데이터 저장 완료: {filename}")
        print(f"총 {len(posts_data)}개의 게시글 저장됨")
        return True
    except Exception as e:
        print(f"엑셀 저장 중 오류 발생: {e}")
        return False

def get_timestamp():
    """현재 시간을 문자열로 반환"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def print_progress(current, total, message=""):
    """진행상황 출력"""
    percentage = (current / total) * 100
    print(f"진행률: {current}/{total} ({percentage:.1f}%) {message}")

def safe_wait(driver, delay: Union[int, float] = 2):
    """안전한 대기 (너무 빠른 요청 방지)"""
    time.sleep(delay)

def extract_post_number(url):
    """URL에서 게시글 번호 추출"""
    try:
        # 네이버 카페 게시글 URL 패턴에서 번호 추출
        match = re.search(r'articleid=(\d+)', url)
        if match:
            return match.group(1)
        return None
    except:
        return None

def validate_cafe_url(url):
    """카페 URL 유효성 검사"""
    cafe_patterns = [
        r'https://cafe\.naver\.com/[a-zA-Z0-9_-]+',
        r'https://cafe\.naver\.com/ArticleList\.nhn\?search\.clubid=\d+',
    ]
    
    for pattern in cafe_patterns:
        if re.match(pattern, url):
            return True
    return False 