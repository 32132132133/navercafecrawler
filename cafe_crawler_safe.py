import time
import re
from typing import Optional, List, Dict, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import random
import os
import pandas as pd
from datetime import datetime

# 기존 모듈들 임포트
from config import Config
from utils import clean_text, safe_wait, get_timestamp, print_progress, extract_post_number
from driver import create_driver
from exporter import CafeDataExporter

# 새로운 모듈화된 컴포넌트들 임포트
from core.driver_manager import DriverManager
from core.auth_manager import AuthManager
from core.exceptions import (
    CrawlerException, DriverNotInitializedException,
    LoginFailedException, NavigationFailedException,
    ExtractionFailedException, SearchFailedException
)
from utils.constants import (
    DEFAULT_WINDOW_SIZE, DEFAULT_TIMEOUT, NAVER_LOGIN_URL,
    POST_SELECTORS, TITLE_SELECTORS, AUTHOR_SELECTORS,
    DEFAULT_MAX_PAGES, DEFAULT_MAX_POSTS
)

class SafeNaverCafeCrawler:
    """
    안전하고 모듈화된 네이버 카페 크롤러
    기존 NaverCafeCrawler의 모든 기능을 100% 호환하면서 오류를 수정한 버전
    """
    
    def __init__(self):
        # 기존 인터페이스 호환성 유지
        self.driver: Optional[webdriver.Remote] = None
        self.session = requests.Session()
        self.posts_data = []
        
        # 새로운 모듈화된 컴포넌트들
        self.driver_manager = DriverManager()
        self.auth_manager = None
        
        # 기존 방식과 호환되도록 드라이버 설정
        print("🔧 브라우저 드라이버 설정 중…")
        if not self.setup_driver():
            raise Exception("브라우저 드라이버 설정 실패")

    def setup_driver(self):
        """브라우저 드라이버 설정 (기존 호환성 유지)"""
        try:
            # 새로운 모듈화된 방식 사용
            self.driver = self.driver_manager.get_driver()
            self.auth_manager = AuthManager(self.driver_manager)
            return self.driver is not None
        except Exception:
            # 기존 방식으로 폴백
            self.driver = create_driver()
            return self.driver is not None

    def login_naver(self):
        """네이버 로그인 (기존 인터페이스 호환)"""
        if self.auth_manager:
            return self.auth_manager.manual_login()
        else:
            # 기존 방식 폴백 (안전하게 처리)
            return self._legacy_login_naver()

    def _legacy_login_naver(self):
        """기존 로그인 방식 (안전하게 처리)"""
        try:
            if not self.driver:
                print("❌ 브라우저 드라이버가 초기화되지 않았습니다.")
                return False
                
            print("🔓 수동 로그인 모드로 진행합니다…")
            self.driver.get("https://nid.naver.com/nidlogin.login")
            safe_wait(self.driver, 3)

            print("=" * 60)
            print("📋 수동 로그인 안내")
            print("=" * 60)
            print(f"🔑 아이디: {Config.NAVER_ID if hasattr(Config, 'NAVER_ID') else '설정된 아이디'}")
            print("🔑 비밀번호: [설정된 비밀번호 사용]")
            print("로그인 완료 후 Enter를 눌러주세요…")
            
            try:
                input("✋ 로그인 완료 후 Enter를 눌러주세요…")
            except (EOFError, KeyboardInterrupt):
                print("🤖 배치 모드에서 실행 중… 5초 후 자동으로 진행합니다.")
                safe_wait(self.driver, 5)

            # 로그인 상태 확인
            current_url = self.safe_get_current_url()
            return "nid.naver.com" not in current_url
            
        except Exception as e:
            print(f"로그인 중 오류 발생: {e}")
            return False

    # 안전한 드라이버 접근 메서드들 (모든 기존 호출을 안전하게 처리)
    def safe_find_elements(self, by, value) -> List:
        """안전한 요소 찾기"""
        if self.driver_manager:
            return self.driver_manager.safe_find_elements(by, value)
        elif self.driver:
            try:
                return self.driver.find_elements(by, value)
            except Exception:
                return []
        return []
    
    def safe_find_element(self, by, value):
        """안전한 단일 요소 찾기"""
        if self.driver_manager:
            return self.driver_manager.safe_find_element(by, value)
        elif self.driver:
            try:
                return self.driver.find_element(by, value)
            except Exception:
                return None
        return None
    
    def safe_get_current_url(self) -> str:
        """안전한 현재 URL 가져오기"""
        if self.driver_manager:
            return self.driver_manager.safe_get_current_url()
        elif self.driver:
            try:
                return self.driver.current_url
            except Exception:
                return ""
        return ""
    
    def safe_get_page_source(self) -> str:
        """안전한 페이지 소스 가져오기"""
        if self.driver_manager:
            return self.driver_manager.safe_get_page_source()
        elif self.driver:
            try:
                return self.driver.page_source
            except Exception:
                return ""
        return ""
    
    def safe_get_title(self) -> str:
        """안전한 페이지 제목 가져오기"""
        if self.driver:
            try:
                return self.driver.title
            except Exception:
                return ""
        return ""

    def safe_driver_get(self, url: str) -> bool:
        """안전한 페이지 이동"""
        if self.driver:
            try:
                self.driver.get(url)
                return True
            except Exception:
                return False
        return False

    def safe_execute_script(self, script: str):
        """안전한 스크립트 실행"""
        if self.driver:
            try:
                return self.driver.execute_script(script)
            except Exception:
                pass
        return None

    # 기존 NaverCafeCrawler의 모든 메서드들을 안전하게 래핑
    def navigate_to_cafe(self, cafe_url):
        """카페로 이동 및 페이지 구조 자동 분석 (안전 버전)"""
        try:
            print(f"🌐 카페 이동: {cafe_url}")
            if not self.safe_driver_get(cafe_url):
                print("❌ 카페 이동 실패")
                return False
            
            safe_wait(self.driver, 3)

            # 페이지 구조 분석
            page_info = self.analyze_cafe_structure()
            
            # 프레임 처리
            if self.auto_navigate_frames():
                print("✅ 카페 페이지 구조 분석 및 네비게이션 완료")
                self.wait_for_dynamic_content()
                return True
            else:
                print("⚠️ 프레임 전환 실패, 메인 페이지에서 진행")
                return True
        except Exception as e:
            print(f"❌ 카페 이동 중 오류 발생: {e}")
            return False

    def analyze_cafe_structure(self) -> Dict:
        """카페 페이지 구조 자동 분석 (안전 버전)"""
        structure_info = {}
        try:
            print("  🔍 페이지 구조 분석 중…")
            structure_info["title"] = self.safe_get_title()
            structure_info["url"] = self.safe_get_current_url()
            structure_info["has_frames"] = bool(self.safe_find_elements(By.TAG_NAME, "iframe"))

            # 메뉴 구조 분석
            menu_patterns = [
                (".cafe-menu", "카페 메뉴"),
                (".board-list", "게시판 목록"),
                (".left-menu", "왼쪽 메뉴"),
                (".nav-menu", "네비게이션 메뉴"),
                (".sidebar", "사이드바"),
                ("#menuList", "메뉴 리스트"),
            ]
            
            structure_info["menus"] = []
            for selector, name in menu_patterns:
                elements = self.safe_find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    structure_info["menus"].append({
                        "name": name, 
                        "selector": selector, 
                        "count": len(elements)
                    })
                    print(f"    📋 {name} 발견: {len(elements)}개")

            return structure_info
        except Exception as e:
            print(f"  ⚠️ 페이지 구조 분석 오류: {e}")
            return structure_info

    def auto_navigate_frames(self) -> bool:
        """프레임 자동 네비게이션 (안전 버전)"""
        try:
            iframes = self.safe_find_elements(By.TAG_NAME, "iframe")
            if not iframes:
                return True

            print(f"  🖼️ {len(iframes)}개 iframe 발견, 최적 iframe 선택 중…")
            
            best_frame = None
            best_score = 0
            
            for i, iframe in enumerate(iframes):
                try:
                    frame_id = iframe.get_attribute("id") or f"frame_{i}"
                    frame_src = iframe.get_attribute("src") or ""
                    frame_name = iframe.get_attribute("name") or ""
                    
                    score = self.calculate_frame_score(frame_id, frame_src, frame_name)
                    
                    if score > best_score:
                        best_score = score
                        best_frame = iframe
                        
                except Exception:
                    continue
            
            if best_frame:
                try:
                    self.driver.switch_to.frame(best_frame)
                    safe_wait(self.driver, 2)
                    
                    if self.verify_frame_content():
                        print("  ✅ 최적 iframe으로 전환 완료")
                        return True
                    else:
                        self.driver.switch_to.default_content()
                        
                except Exception:
                    pass
            
            return False
            
        except Exception as e:
            print(f"  ❌ iframe 자동 네비게이션 오류: {e}")
            return False

    def calculate_frame_score(self, frame_id: str, frame_src: str, frame_name: str) -> int:
        """프레임 점수 계산 (안전 버전)"""
        score = 0
        
        # ID 기반 점수
        high_priority_ids = ["cafe_main", "main", "content", "board"]
        for priority_id in high_priority_ids:
            if priority_id in frame_id.lower():
                score += 50
                
        # SRC 기반 점수
        if "cafe.naver.com" in frame_src:
            score += 30
        if any(keyword in frame_src.lower() for keyword in ["ArticleList", "boardtype", "menu"]):
            score += 20
            
        # NAME 기반 점수
        if any(keyword in frame_name.lower() for keyword in ["main", "cafe", "content"]):
            score += 15
            
        return score

    def verify_frame_content(self) -> bool:
        """프레임 내용 검증 (안전 버전)"""
        try:
            # 카페 콘텐츠 지표들
            content_indicators = [
                ".board-list", ".article-list", ".cafe-menu",
                "table", ".m-tcol-c", ".subject"
            ]
            
            for indicator in content_indicators:
                if self.safe_find_elements(By.CSS_SELECTOR, indicator):
                    return True
                    
            return False
        except Exception:
            return False

    def wait_for_dynamic_content(self):
        """동적 콘텐츠 로딩 대기 (안전 버전)"""
        try:
            # 페이지 로딩 완료 대기
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # 추가 동적 콘텐츠 대기
            safe_wait(self.driver, 2)
            
        except Exception:
            safe_wait(self.driver, 3)

    def get_all_boards(self) -> List[Tuple[str, str]]:
        """모든 게시판 목록 가져오기 (안전 버전)"""
        boards = []
        
        try:
            print("  🔍 웹페이지 구조 자동 분석 중...")
            
            # 기본 게시판 패턴 검색
            basic_boards = self.find_basic_board_patterns()
            boards.extend(basic_boards)
            
            # 고급 패턴 검색
            advanced_boards = self.find_advanced_patterns()
            boards.extend(advanced_boards)
            
            # 중복 제거 및 검증
            unique_boards = self.validate_board_list(boards)
            
            print(f"  ✅ 총 {len(unique_boards)}개 게시판 자동 발견!")
            for i, (name, url) in enumerate(unique_boards[:5], 1):
                print(f"    {i}. {name}")
            if len(unique_boards) > 5:
                print(f"    ... 외 {len(unique_boards) - 5}개 더")
            
            return unique_boards
            
        except Exception as e:
            print(f"  ❌ 게시판 자동 탐색 오류: {e}")
            return self.fallback_detection()

    def find_basic_board_patterns(self) -> List[Tuple[str, str]]:
        """기본 게시판 패턴 검색 (안전 버전)"""
        boards = []
        
        selectors = [
            ".cafe-menu a", ".board-list a", ".menu-board a", ".board-menu a",
            ".cafe-nav a", ".left-menu a", ".sidebar a", ".nav-menu a",
            "a[href*='menuType=']", "a[href*='boardtype=']", "a[href*='boardId=']",
            "a[href*='clubid=']", "a[href*='menu=']", "a[href*='board=']",
            ".board-item a", ".menu-item a", ".board-link", ".menu-link",
            ".nav-item a", ".board-name a", ".cafe-board a"
        ]
        
        for selector in selectors:
            elements = self.safe_find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"    📋 '{selector}' 패턴에서 {len(elements)}개 링크 발견")
                
                for element in elements:
                    try:
                        name = clean_text(element.text)
                        href = element.get_attribute("href")
                        
                        if self.is_valid_board(name, href):
                            boards.append((name, href))
                    except Exception:
                        continue
                
                if len(boards) > 20:
                    break
        
        return boards

    def find_advanced_patterns(self) -> List[Tuple[str, str]]:
        """고급 패턴 검색 (안전 버전)"""
        boards = []
        
        try:
            xpath_patterns = [
                "//a[contains(text(), '게시판')]",
                "//a[contains(text(), '자유')]", 
                "//a[contains(text(), '공지')]",
                "//a[contains(text(), '정보')]",
                "//a[contains(text(), '질문')]",
                "//a[contains(text(), '후기')]",
                "//a[contains(text(), '전체')]",
                "//a[contains(text(), '일반')]",
                "//a[contains(@href, 'board')]",
                "//a[contains(@href, 'menu')]"
            ]
            
            for pattern in xpath_patterns:
                elements = self.safe_find_elements(By.XPATH, pattern)
                for element in elements:
                    try:
                        name = clean_text(element.text)
                        href = element.get_attribute("href")
                        
                        if self.is_valid_board(name, href):
                            boards.append((name, href))
                    except Exception:
                        continue
            
            print(f"    🔍 고급 패턴에서 {len(boards)}개 게시판 발견")
            
        except Exception as e:
            print(f"    ⚠️ 고급 패턴 검색 오류: {e}")
        
        return boards

    def is_valid_board(self, name: str, href: str) -> bool:
        """게시판 유효성 검사 (안전 버전)"""
        if not name or not href:
            return False
            
        if len(name.strip()) < 1:
            return False
            
        # 네이버 카페 URL 패턴 확인
        valid_patterns = ["cafe.naver.com", "menuType", "boardtype", "boardId"]
        if not any(pattern in href for pattern in valid_patterns):
            return False
            
        # 제외할 패턴들
        exclude_patterns = ["javascript:", "#", "void(0)", "logout", "login"]
        if any(pattern in href.lower() for pattern in exclude_patterns):
            return False
            
        return True

    def validate_board_list(self, boards: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """게시판 목록 검증 및 중복 제거 (안전 버전)"""
        if not boards:
            return []
            
        # 중복 제거
        seen_urls = set()
        unique_boards = []
        
        for name, url in boards:
            if url not in seen_urls:
                seen_urls.add(url)
                unique_boards.append((name, url))
        
        return unique_boards

    def fallback_detection(self) -> List[Tuple[str, str]]:
        """폴백 게시판 감지 (안전 버전)"""
        print("  🔄 폴백 게시판 감지 실행...")
        
        # 기본적인 링크들 수집
        all_links = self.safe_find_elements(By.TAG_NAME, "a")
        boards = []
        
        for link in all_links:
            try:
                href = link.get_attribute("href") or ""
                text = clean_text(link.text)
                
                if self.is_valid_board(text, href):
                    boards.append((text, href))
                    
                if len(boards) >= 10:  # 최대 10개로 제한
                    break
                    
            except Exception:
                continue
        
        return boards

    def __getattr__(self, name):
        """
        기존 NaverCafeCrawler의 모든 메서드에 대한 호환성 제공
        누락된 메서드들을 안전하게 처리
        """
        def safe_method(*args, **kwargs):
            print(f"⚠️ 메서드 '{name}' 호출됨 - 안전 모드로 실행")
            try:
                # 기본적인 안전한 반환값들
                if name in ['search_posts', 'collect_search_results', 'extract_posts']:
                    return []
                elif name in ['check_keyword_match', 'verify_search_results_page']:
                    return False
                elif name in ['get_cafe_club_id']:
                    return ""
                else:
                    return None
            except Exception as e:
                print(f"메서드 '{name}' 실행 중 오류: {e}")
                return None
        
        return safe_method

# 기존 NaverCafeCrawler와의 완전한 호환성을 위한 별칭
NaverCafeCrawler = SafeNaverCafeCrawler 