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

class RefactoredNaverCafeCrawler:
    """
    리팩토링된 네이버 카페 크롤러
    기존 NaverCafeCrawler의 모든 기능을 100% 호환하면서 오류를 수정하고 구조를 개선한 버전
    """

    def __init__(self):
        self.driver: Optional[webdriver.Remote] = None
        self.session = requests.Session()
        self.posts_data = []
        self.current_cafe_id = None
        self.current_cafe_url = None

        # 브라우저 드라이버 자동 설정
        print("🔧 브라우저 드라이버 설정 중…")
        if not self.setup_driver():
            raise Exception("브라우저 드라이버 설정 실패")

    def setup_driver(self):
        """브라우저 드라이버 설정 및 초기화"""
        try:
            self.driver = create_driver()
            return self.driver is not None
        except Exception as e:
            print(f"드라이버 설정 오류: {e}")
            return False

    # 안전한 드라이버 접근 메서드들
    def safe_find_elements(self, by, value) -> List:
        """안전한 요소 찾기"""
        if not self.driver:
            return []
        try:
            return self.driver.find_elements(by, value)
        except Exception:
            return []

    def safe_find_element(self, by, value):
        """안전한 단일 요소 찾기"""
        if not self.driver:
            return None
        try:
            return self.driver.find_element(by, value)
        except Exception:
            return None

    def safe_get_current_url(self) -> str:
        """안전한 현재 URL 가져오기"""
        if not self.driver:
            return ""
        try:
            return self.driver.current_url
        except Exception:
            return ""

    def safe_get_page_source(self) -> str:
        """안전한 페이지 소스 가져오기"""
        if not self.driver:
            return ""
        try:
            return self.driver.page_source
        except Exception:
            return ""

    def safe_get_title(self) -> str:
        """안전한 페이지 제목 가져오기"""
        if not self.driver:
            return ""
        try:
            return self.driver.title
        except Exception:
            return ""

    def safe_driver_get(self, url: str) -> bool:
        """안전한 페이지 이동"""
        if not self.driver:
            return False
        try:
            self.driver.get(url)
            return True
        except Exception:
            return False

    def safe_execute_script(self, script: str):
        """안전한 스크립트 실행"""
        if not self.driver:
            return None
        try:
            return self.driver.execute_script(script)
        except Exception:
            return None

    def login_naver(self):
        """네이버 수동 로그인 (안전 버전)"""
        try:
            if not self.driver:
                print("❌ 브라우저 드라이버가 초기화되지 않았습니다.")
                return False

            print("🔐 수동 로그인 모드로 진행합니다...")
            self.safe_driver_get("https://nid.naver.com/nidlogin.login")
            safe_wait(self.driver, 3)

            print("=" * 60)
            print("🔐 수동 로그인 안내")
            print("=" * 60)
            print(f"🔑 아이디: {Config.NAVER_ID if hasattr(Config, 'NAVER_ID') else '설정된 아이디'}")
            print("🔑 비밀번호: [설정된 비밀번호 사용]")
            print("로그인 완료 후 Enter를 눌러주세요...")

            try:
                input("✅ 로그인 완료 후 Enter를 눌러주세요...")
            except (EOFError, KeyboardInterrupt):
                print("🤖 배치 모드에서 실행 중… 5초 후 자동으로 진행합니다.")
                safe_wait(self.driver, 5)

            # 로그인 상태 확인
            current_url = self.safe_get_current_url()
            if "nid.naver.com" not in current_url:
                print("✅ 로그인 성공!")
                return True

            # 추가 확인
            try:
                self.safe_driver_get("https://www.naver.com")
                safe_wait(self.driver, 3)
                login_indicators = [".MyView-module__my_area___HUbS_", ".link_name"]
                for indicator in login_indicators:
                    if self.safe_find_element(By.CSS_SELECTOR, indicator):
                        print("✅ 로그인 상태 확인 완료!")
                        return True
            except Exception:
                pass

            print("❌ 로그인이 완료되지 않았습니다.")
            return False

        except Exception as e:
            print(f"로그인 중 오류 발생: {e}")
            return False

    def navigate_to_cafe(self, cafe_url):
        """카페로 이동 및 페이지 구조 자동 분석"""
        try:
            if not self.driver:
                print("❌ 브라우저 드라이버가 초기화되지 않았습니다.")
                return False

            print(f"🌐 카페 이동: {cafe_url}")
            if not self.safe_driver_get(cafe_url):
                return False
            
            self.current_cafe_url = cafe_url
            safe_wait(self.driver, 3)

            # 카페 ID 추출
            self.extract_cafe_id(cafe_url)

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

    def extract_cafe_id(self, cafe_url: str):
        """카페 URL에서 카페 ID 추출"""
        try:
            # URL 패턴에서 카페 ID 추출
            import re
            patterns = [
                r'cafe\.naver\.com/([^/?]+)',
                r'clubid=(\d+)',
                r'cafe\.naver\.com/\w+/(\d+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, cafe_url)
                if match:
                    self.current_cafe_id = match.group(1)
                    print(f"  📝 카페 ID 추출: {self.current_cafe_id}")
                    return
            
            print("  ⚠️ 카페 ID 추출 실패")
        except Exception as e:
            print(f"  ❌ 카페 ID 추출 오류: {e}")

    def analyze_cafe_structure(self) -> Dict:
        """카페 페이지 구조 자동 분석"""
        structure_info = {}
        try:
            print("  🔍 페이지 구조 분석 중...")
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
        """프레임 자동 네비게이션"""
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

            if best_frame and self.driver:
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
        """Calculate frame score for best frame selection"""
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
        """Verify frame content for correct navigation"""
        try:
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
        """동적 콘텐츠 로딩 대기"""
        try:
            if self.driver:
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
            safe_wait(self.driver, 2)
        except Exception:
            safe_wait(self.driver, 3)

    def get_all_boards(self) -> List[Tuple[str, str]]:
        """Get all board lists from cafe"""
        boards = []

        try:
            print("  🔍 웹페이지 구조 자동 분석 중...")

            # 기본 게시판 패턴 검색
            basic_boards = self.find_basic_board_patterns()
            if isinstance(basic_boards, list):
                boards.extend(basic_boards)

            # 고급 패턴 검색
            advanced_boards = self.find_advanced_patterns()
            if isinstance(advanced_boards, list):
                boards.extend(advanced_boards)

            # 중복 제거 및 검증
            unique_boards = self.validate_board_list(boards)

            if isinstance(unique_boards, list) and unique_boards:
                print(f"  ✅ 총 {len(unique_boards)}개 게시판 자동 발견!")
                for i, (name, url) in enumerate(unique_boards[:5], 1):
                    print(f"    {i}. {name}")
                if len(unique_boards) > 5:
                    print(f"    ... and {len(unique_boards) - 5} more")

                return unique_boards

        except Exception as e:
            print(f"  ❌ 게시판 자동 탐색 오류: {e}")

        # 폴백으로 빈 리스트 반환
        return []

    def find_basic_board_patterns(self) -> List[Tuple[str, str]]:
        """Find basic board patterns"""
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
            try:
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
            except Exception:
                continue

        return boards

    def find_advanced_patterns(self) -> List[Tuple[str, str]]:
        """Find advanced board patterns using XPath"""
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
                try:
                    elements = self.safe_find_elements(By.XPATH, pattern)
                    for element in elements:
                        try:
                            name = clean_text(element.text)
                            href = element.get_attribute("href")

                            if self.is_valid_board(name, href):
                                boards.append((name, href))
                        except Exception:
                            continue
                except Exception:
                    continue

            print(f"    🔍 고급 패턴에서 {len(boards)}개 게시판 발견")

        except Exception as e:
            print(f"    ⚠️ 고급 패턴 검색 오류: {e}")

        return boards

    def is_valid_board(self, name: str, href: str) -> bool:
        """Validate board link"""
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
        """Validate and deduplicate board list"""
        if not boards or not isinstance(boards, list):
            return []

        # 중복 제거
        seen_urls = set()
        unique_boards = []

        for name, url in boards:
            if url not in seen_urls:
                seen_urls.add(url)
                unique_boards.append((name, url))

        return unique_boards

    def search_posts(self, keyword: str, max_pages: int = 5) -> List[Dict]:
        """키워드로 게시글 검색 (안전 버전)"""
        try:
            print(f"🔍 키워드 '{keyword}' 검색 시작...")

            # 검색 실행
            posts = self.search_with_cafe_function(keyword, max_pages)

            print(f"✅ 총 {len(posts)}개 게시글 검색 완료")
            return posts

        except Exception as e:
            print(f"❌ 검색 중 오류: {e}")
            return []

    def search_with_cafe_function(self, keyword: str, max_pages: int) -> List[Dict]:
        """카페 검색 기능을 이용한 검색 (안전 버전)"""
        posts = []

        try:
            # 다양한 검색 전략 시도
            if hasattr(Config, 'SEARCH_ALL_BOARDS') and Config.SEARCH_ALL_BOARDS:
                boards = self.get_all_boards()
                if isinstance(boards, list) and boards:
                    print(f"  {len(boards)}개 게시판에서 검색합니다.")

                    for board_name, board_url in boards:
                        try:
                            if self.safe_driver_get(board_url):
                                safe_wait(self.driver, 2)
                                board_posts = self.search_in_current_board(keyword, max_pages // len(boards) + 1)
                                if isinstance(board_posts, list):
                                    posts.extend(board_posts)
                                    print(f"    '{board_name}'에서 {len(board_posts)}개 게시글 수집")
                        except Exception as e:
                            print(f"    '{board_name}' 게시판 검색 오류: {e}")
                            continue
            else:
                # 현재 게시판에서만 검색
                posts = self.search_in_current_board(keyword, max_pages)

        except Exception as e:
            print(f"검색 중 오류: {e}")

        return posts if isinstance(posts, list) else []

    def search_in_current_board(self, keyword: str, max_pages: int) -> List[Dict]:
        """현재 게시판에서 키워드 검색 (안전 버전)"""
        posts = []

        try:
            # 검색 실행 시도
            for page in range(max_pages):
                try:
                    page_posts = self.extract_posts_from_page(keyword)
                    if isinstance(page_posts, list):
                        posts.extend(page_posts)

                    # 다음 페이지로 이동
                    if not self.go_to_next_page():
                        break

                except Exception as e:
                    print(f"페이지 {page+1} 처리 오류: {e}")
                    break

        except Exception as e:
            print(f"게시판 검색 오류: {e}")

        return posts

    def extract_posts_from_page(self, keyword: Optional[str] = None) -> List[Dict]:
        """페이지에서 게시글 추출 (안전 버전)"""
        posts = []

        try:
            # 게시글 요소 찾기
            post_elements = self.find_post_elements()

            for i, element in enumerate(post_elements):
                try:
                    post_info = self.extract_single_post_info(element, i)
                    if post_info and isinstance(post_info, dict):
                        # 키워드 매칭 확인
                        if keyword:
                            title = post_info.get('title', '')
                            if keyword.lower() in title.lower():
                                post_info['keyword_matched'] = keyword
                                posts.append(post_info)
                        else:
                            posts.append(post_info)
                except Exception as e:
                    print(f"게시글 {i+1} 추출 오류: {e}")
                    continue

        except Exception as e:
            print(f"페이지 게시글 추출 오류: {e}")

        return posts

    def find_post_elements(self) -> List:
        """게시글 요소 찾기 (안전 버전)"""
        patterns = [
            ".board-list tbody tr",
            ".article-board tbody tr",
            "table.board-list tbody tr",
            "tbody tr[align]",
            "tbody tr",
            ".article-list li",
            ".post-item",
            "tr"
        ]

        for pattern in patterns:
            elements = self.safe_find_elements(By.CSS_SELECTOR, pattern)
            if elements and len(elements) > 1:  # 헤더 제외
                return elements[1:]  # 첫번째 요소(헤더) 제외

        return []

    def extract_single_post_info(self, element, index: int) -> Optional[Dict]:
        """단일 게시글 정보 추출 (안전 버전)"""
        try:
            post_info = {
                'index': index + 1,
                'title': '',
                'url': '',
                'author': '',
                'date': '',
                'views': '',
                'likes': ''
            }

            # 제목과 URL 추출
            title_url = self.extract_title_and_url(element)
            if title_url:
                post_info.update(title_url)

            # 기타 정보 추출
            post_info['author'] = self.extract_author(element)
            post_info['date'] = self.extract_date(element)
            post_info['views'] = self.extract_views(element)
            post_info['likes'] = self.extract_likes(element)

            return post_info if post_info['title'] and post_info['url'] else None

        except Exception as e:
            print(f"게시글 정보 추출 오류: {e}")
            return None

    def extract_title_and_url(self, element) -> Optional[Dict]:
        """제목과 URL 추출 (안전 버전)"""
        try:
            link_patterns = [
                ".m-tcol-c a", ".subject a", ".title a", "td a", "a"
            ]

            for pattern in link_patterns:
                try:
                    link = element.find_element(By.CSS_SELECTOR, pattern)
                    if link:
                        title = clean_text(link.text)
                        url = link.get_attribute("href")

                        if title and url and "read" in url:
                            return {'title': title, 'url': url}
                except Exception:
                    continue

        except Exception:
            pass

        return None

    def extract_author(self, element) -> str:
        """작성자 추출 (안전 버전)"""
        try:
            author_patterns = [
                ".m-tcol-c.writer", ".author", ".writer",
                "td[class*='writer']", "td[class*='author']"
            ]

            for pattern in author_patterns:
                try:
                    author_elem = element.find_element(By.CSS_SELECTOR, pattern)
                    if author_elem:
                        return clean_text(author_elem.text)
                except Exception:
                    continue
        except Exception:
            pass
        return ""

    def extract_date(self, element) -> str:
        """날짜 추출 (안전 버전)"""
        try:
            date_patterns = [
                ".m-tcol-c.date", ".date", "td[class*='date']"
            ]

            for pattern in date_patterns:
                try:
                    date_elem = element.find_element(By.CSS_SELECTOR, pattern)
                    if date_elem:
                        return clean_text(date_elem.text)
                except Exception:
                    continue
        except Exception:
            pass
        return ""

    def extract_views(self, element) -> str:
        """조회수 추출 (안전 버전)"""
        try:
            view_patterns = [
                ".m-tcol-c.view", ".views", "td[class*='view']"
            ]

            for pattern in view_patterns:
                try:
                    view_elem = element.find_element(By.CSS_SELECTOR, pattern)
                    if view_elem:
                        return clean_text(view_elem.text)
                except Exception:
                    continue
        except Exception:
            pass
        return ""

    def extract_likes(self, element) -> str:
        """좋아요수 추출 (안전 버전)"""
        try:
            like_patterns = [
                ".m-tcol-c.like", ".likes", "td[class*='like']"
            ]

            for pattern in like_patterns:
                try:
                    like_elem = element.find_element(By.CSS_SELECTOR, pattern)
                    if like_elem:
                        return clean_text(like_elem.text)
                except Exception:
                    continue
        except Exception:
            pass
        return ""

    def go_to_next_page(self) -> bool:
        """다음 페이지로 이동 (안전 버전)"""
        try:
            next_patterns = [
                ".pgR a", ".next a", "a[title='다음']", ".pagination .next"
            ]

            for pattern in next_patterns:
                next_button = self.safe_find_element(By.CSS_SELECTOR, pattern)
                if next_button and next_button.is_enabled():
                    next_button.click()
                    safe_wait(self.driver, 2)
                    return True
        except Exception:
            pass
        return False

    def save_to_excel(self, filename: Optional[str] = None):
        """Excel 파일로 저장 (안전 버전)"""
        try:
            if not self.posts_data:
                print("저장할 데이터가 없습니다.")
                return

            if not filename:
                filename = f"cafe_crawl_data_{get_timestamp()}.xlsx"

            df = pd.DataFrame(self.posts_data)
            df.to_excel(filename, index=False)
            print(f"✅ 데이터가 '{filename}' 파일로 저장되었습니다.")

        except Exception as e:
            print(f"❌ 저장 중 오류: {e}")

    def crawl_cafe(self, cafe_url: str, keywords: Optional[List[str]] = None) -> Dict:
        """카페 크롤링 메인 메서드 (안전 버전)"""
        results = {
            'cafe_url': cafe_url,
            'keywords': keywords or [],
            'posts': [],
            'success': False
        }

        try:
            # 카페 이동
            if not self.navigate_to_cafe(cafe_url):
                return results

            # 키워드별 검색
            if keywords:
                for keyword in keywords:
                    print(f"\n🔍 키워드 '{keyword}' 검색 중...")
                    posts = self.search_posts(keyword)
                    results['posts'].extend(posts)
            else:
                # 전체 게시글 수집
                posts = self.extract_posts_from_page()
                results['posts'].extend(posts)

            # 데이터 저장
            self.posts_data = results['posts']
            results['success'] = True
            print(f"\n✅ 크롤링 완료: 총 {len(results['posts'])}개 게시글 수집")

        except Exception as e:
            print(f"❌ 크롤링 중 오류: {e}")

        return results

    def __del__(self):
        """소멸자 - 드라이버 정리"""
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass

# 기존 호환성을 위한 별칭
NaverCafeCrawler = RefactoredNaverCafeCrawler
