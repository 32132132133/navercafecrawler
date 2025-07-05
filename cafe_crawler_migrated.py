"""
네이버 카페 크롤러 - 점진적 마이그레이션 버전
기존 인터페이스를 100% 호환하면서 새로운 모듈화된 구조를 사용
"""
# Disclaimer: use at your own risk. The authors take no responsibility for misuse.

import time
import re
from typing import Optional, List, Dict, Any, Tuple
import os
import pandas as pd
from datetime import datetime
import random

# 기존 imports ?��?
from config import Config
from utils import clean_text, safe_wait, get_timestamp, print_progress, extract_post_number
from exporter import CafeDataExporter

# ?�로??모듈??import
try:
    from core.exceptions import (
        CrawlerException, DriverNotInitializedException,
        LoginFailedException, NavigationFailedException,
        ExtractionFailedException, SearchFailedException
    )
    from core.driver_manager import DriverManager
    from core.auth_manager import AuthManager
    from utils.constants import (
        DEFAULT_WINDOW_SIZE, DEFAULT_TIMEOUT, NAVER_LOGIN_URL,
        POST_SELECTORS, TITLE_SELECTORS, AUTHOR_SELECTORS
    )
    NEW_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"?�️ ?�로??모듈??찾을 ???�습?�다: {e}")
    print("기존 모듈�??�용?�여 ?�작?�니??")
    NEW_MODULES_AVAILABLE = False

    # 기존 selenium imports
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.wait import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException


class CafeCrawlerMigrated:
    """
    ?�진??마이그레?�션??카페 ?�롤??    - 기존 ?�터?�이??100% ?�환
    - ?�로??모듈???�으�??�용, ?�으�?기존 방식?�로 fallback
    - ?�전?�과 ?��?보수???�상
    """

    def __init__(self):
        """크롤러 초기화 - 기존과 동일한 인터페이스"""
        # 기존 ?�환?�을 ?�한 ?�성??        self.driver: Optional[Any] = None
        self.posts_data = []
        self.current_cafe_url = ""
        self.search_results = []

        if NEW_MODULES_AVAILABLE:
            # ?�로??모듈 매니?�??            self._driver_manager: Optional[DriverManager] = None
            self._auth_manager: Optional[AuthManager] = None

        # ?��? ?�태 관�?        self._is_logged_in = False
        self._current_cafe_id = None
        self._cafe_metadata = {}

        print("??CafeCrawler (Migration Version) 초기???�료")

    def setup_driver(self):
        """Driver setup - maintains existing interface, improves internal implementation"""
        try:
            if NEW_MODULES_AVAILABLE:
                # 새로운 드라이버 매니저 사용
                self._driver_manager = DriverManager()
                if self._driver_manager.create_driver():
                    self.driver = self._driver_manager.driver
                self._auth_manager = AuthManager(self._driver_manager)
            else:
                # 기존 방식 fallback
                from driver import create_driver
                self.driver = create_driver()

            print("✅ 드라이버 설정 완료")
            return True

        except Exception as e:
            print(f"❌ 드라이버 설정 실패: {e}")
            if NEW_MODULES_AVAILABLE:
                raise DriverNotInitializedException(f"드라이버 초기화 실패: {e}")
            else:
                raise Exception(f"드라이버 초기화 실패: {e}")

    def login_naver(self):
        """네이버 로그인 - 향상된 안전성"""
        try:
            if not self.driver:
                self.setup_driver()

            print("🔐 네이버 로그인을 진행합니다...")

            if NEW_MODULES_AVAILABLE and self._auth_manager:
                # 새로운 인증 매니저 사용
                login_success = self._auth_manager.login_naver()

                if login_success:
                    self._is_logged_in = True
                    print("??로그???�공")
                    return True
                else:
                    raise LoginFailedException("로그???�패")
            else:
                # 기존 방식 fallback
                return self._legacy_login()

        except Exception as e:
            print(f"??로그???�패: {e}")
            return False

    def _legacy_login(self):
        """기존 로그??방식 (fallback)"""
        try:
            # ?�이�?로그???�이지�??�동
            self.driver.get("https://nid.naver.com/nidlogin.login")

            print("?�� ?�동 로그?�을 진행?�주?�요...")
            print("로그???�료 ???�무 ?�나 ?�르?�요...")
            input()

            # 로그???�공 ?�인
            current_url = self.driver.current_url
            if "naver.com" in current_url and "login" not in current_url:
                self._is_logged_in = True
                print("??로그???�공")
                return True
            else:
                print("??로그???�패")
                return False

        except Exception as e:
            print(f"??기존 로그??방식 ?�패: {e}")
            return False

    def navigate_to_cafe(self, cafe_url: str):
        """카페 이동 - 향상된 안전성과 구조 분석"""
        try:
            if not self.driver:
                if NEW_MODULES_AVAILABLE:
                    raise DriverNotInitializedException("드라이버가 초기화되지 않았습니다")
                else:
                    raise Exception("드라이버가 초기화되지 않았습니다")

            print(f"?�� 카페�??�동 �? {cafe_url}")

            # ?�전???�이지 ?�동
            if NEW_MODULES_AVAILABLE and self._driver_manager:
                self._driver_manager.driver.get(cafe_url)
            else:
                self.driver.get(cafe_url)

            self.current_cafe_url = cafe_url
            safe_wait(self.driver, 3)

            # 카페 구조 분석
            self._analyze_cafe_structure()

            print("??카페 ?�동 ?�료")
            return True

        except Exception as e:
            print(f"??카페 ?�동 ?�패: {e}")
            if NEW_MODULES_AVAILABLE:
                raise NavigationFailedException(f"카페 ?�동 ?�패: {e}")
            else:
                raise Exception(f"카페 ?�동 ?�패: {e}")

    def search_posts(self, keyword: str, max_pages: int = 5) -> List[Dict]:
        """게시글 검색 - 향상된 검색 전략"""
        try:
            if not self.driver:
                if NEW_MODULES_AVAILABLE:
                    raise DriverNotInitializedException("드라이버가 초기화되지 않았습니다")
                else:
                    raise Exception("드라이버가 초기화되지 않았습니다")

            print(f"?�� ?�워??'{keyword}' 검???�작 (최�? {max_pages}?�이지)")

            # 검???�략 ?�택
            if NEW_MODULES_AVAILABLE:
                search_results = self._perform_enhanced_search(keyword, max_pages)
                self.search_results = self._convert_to_legacy_format(search_results)
            else:
                self.search_results = self._legacy_search(keyword, max_pages)

            print(f"??검???�료: {len(self.search_results)}�?게시글 발견")
            return self.search_results

        except Exception as e:
            print(f"??검???�패: {e}")
            if NEW_MODULES_AVAILABLE:
                raise SearchFailedException(f"검???�패: {e}")
            else:
                raise Exception(f"검???�패: {e}")

    def _legacy_search(self, keyword: str, max_pages: int) -> List[Dict]:
        """기존 검??방식 (fallback)"""
        try:
            search_results = []

            # 기본?�인 검???�도
            search_strategies = [
                self._try_cafe_search_function,
                self._try_direct_search_url,
                self._try_basic_navigation
            ]

            for strategy in search_strategies:
                try:
                    results = strategy(keyword, max_pages)
                    if results:
                        search_results.extend(results)
                        break
                except Exception as e:
                    print(f"  ?�️ 검???�략 ?�패: {e}")
                    continue

            return search_results

        except Exception as e:
            print(f"??기존 검??방식 ?�패: {e}")
            return []

    def _try_cafe_search_function(self, keyword: str, max_pages: int) -> List[Dict]:
        """카페 고장 검색 기능 테스트"""
        try:
            # 검?�창 찾기
            search_selectors = [
                "input[placeholder*='검??]",
                "input[name*='search']",
                ".search-input input",
                "#cafe-search input"
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if search_input.is_displayed():
                        break
                except:
                    continue

            if search_input:
                search_input.clear()
                search_input.send_keys(keyword)

                # 검??버튼 ?�릭
                search_button_selectors = [
                    "button[type='submit']",
                    ".search-btn",
                    ".btn-search",
                    "input[type='submit']"
                ]

                for selector in search_button_selectors:
                    try:
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if button.is_displayed():
                            button.click()
                            break
                    except:
                        continue

                safe_wait(self.driver, 3)
                return self._extract_search_results(max_pages)

            return []

        except Exception as e:
            print(f"??카페 검??기능 ?�패: {e}")
            return []

    def _try_direct_search_url(self, keyword: str, max_pages: int) -> List[Dict]:
        """직접 검색 URL 구성 시도"""
        try:
            if self._current_cafe_id:
                search_url = f"https://cafe.naver.com/ArticleSearchList.nhn?search.clubid={self._current_cafe_id}&search.searchBy=0&search.query={keyword}"
                self.driver.get(search_url)
                safe_wait(self.driver, 3)
                return self._extract_search_results(max_pages)

            return []

        except Exception as e:
            print(f"??직접 URL 검???�패: {e}")
            return []

    def _try_basic_navigation(self, keyword: str, max_pages: int) -> List[Dict]:
        """기본 네비게이션 시도"""
        try:
            # 기본?�인 게시글 목록?�서 ?�워??매칭
            post_results = []

            # 게시글 링크??찾기
            post_selectors = [
                "a[href*='ArticleRead']",
                ".article-board a",
                ".board-list a",
                "a[href*='/article/']"
            ]

            for selector in post_selectors:
                try:
                    post_links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for link in post_links[:20]:  # 최�? 20개만 체크
                        try:
                            title = clean_text(link.text or link.get_attribute("title") or "")
                            if keyword.lower() in title.lower():
                                post_data = {
                                    'title': title,
                                    'url': link.get_attribute("href"),
                                    'author': '',
                                    'date': '',
                                    'views': 0,
                                    'likes': 0,
                                    'content': ''
                                }
                                post_results.append(post_data)
                        except:
                            continue

                    if post_results:
                        break

                except:
                    continue

            return post_results

        except Exception as e:
            print(f"??기본 ?�비게이???�패: {e}")
            return []

    def _extract_search_results(self, max_pages: int) -> List[Dict]:
        """검??결과 추출"""
        try:
            results = []

            for page in range(max_pages):
                print(f"  ?�� {page + 1}/{max_pages} ?�이지 처리 �?..")

                # ?�재 ?�이지??게시글 추출
                page_results = self._extract_posts_from_current_page()
                results.extend(page_results)

                # ?�음 ?�이지�??�동
                if page < max_pages - 1:
                    if not self._go_to_next_page():
                        print("  ?�️ ???�상 ?�이지가 ?�습?�다")
                        break

                safe_wait(self.driver, 2)

            return results

        except Exception as e:
            print(f"??검??결과 추출 ?�패: {e}")
            return []

    def _extract_posts_from_current_page(self) -> List[Dict]:
        """현재 페이지에서 게시글 추출"""
        try:
            posts = []

            # 게시글 ?�소??찾기
            post_selectors = [
                ".article-board tr",
                ".board-list tr",
                ".list-item",
                ".post-item"
            ]

            for selector in post_selectors:
                try:
                    post_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for element in post_elements:
                        try:
                            post_data = self._extract_single_post_data(element)
                            if post_data and post_data.get('title'):
                                posts.append(post_data)
                        except:
                            continue

                    if posts:
                        break

                except:
                    continue

            return posts

        except Exception as e:
            print(f"???�이지 게시글 추출 ?�패: {e}")
            return []

    def _extract_single_post_data(self, element) -> Optional[Dict]:
        """단일 게시글 데이터 추출"""
        try:
            post_data = {
                'title': '',
                'url': '',
                'author': '',
                'date': '',
                'views': 0,
                'likes': 0,
                'content': ''
            }

            # ?�목�?URL 추출
            title_selectors = ["a[href*='Article']", ".title a", "a.article", "td a"]
            for selector in title_selectors:
                try:
                    title_element = element.find_element(By.CSS_SELECTOR, selector)
                    post_data['title'] = clean_text(title_element.text)
                    post_data['url'] = title_element.get_attribute("href")
                    break
                except:
                    continue

            # ?�성??추출
            author_selectors = [".author", ".writer", ".name", "td:nth-child(3)"]
            for selector in author_selectors:
                try:
                    author_element = element.find_element(By.CSS_SELECTOR, selector)
                    post_data['author'] = clean_text(author_element.text)
                    break
                except:
                    continue

            # ?�짜 추출
            date_selectors = [".date", ".time", "td:nth-child(4)"]
            for selector in date_selectors:
                try:
                    date_element = element.find_element(By.CSS_SELECTOR, selector)
                    post_data['date'] = clean_text(date_element.text)
                    break
                except:
                    continue

            return post_data if post_data['title'] else None

        except Exception as e:
            return None

    def _go_to_next_page(self) -> bool:
        """다음 페이지로 이동"""
        try:
            # 다양한 "다음 페이지" 패턴들
            next_patterns = [
                # ?�반?�인 ?�턴
                ".next", ".page-next", ".btn-next",
                "a[title*='?�음']", "a[title*='next']",

                # ?�스??기반
                "//a[contains(text(), '?�음')]",
                "//a[contains(text(), 'next')]",
                "//a[contains(text(), '>')]",

                # ?�이지 번호 기반 (?�재 ?�이지 + 1)
                ".pagination a", ".paging a", ".page-link"
            ]

            # 1. 직접?�인 "?�음" 버튼 찾기
            for pattern in next_patterns[:5]:  # 처음 5�??�턴�??�도
                try:
                    if pattern.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, pattern)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, pattern)

                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # ?�릭 가?�한지 ?�인
                            if 'disabled' not in element.get_attribute('class').lower():
                                element.click()
                                print(f"        ?�️ ?�음 ?�이지 ?�동 ?�공: {pattern}")
                                self.safe_wait(self.driver, 2)
                                return True
                except:
                    continue

            # 2. ?�이지 번호�??�동 ?�도
            try:
                # ?�재 ?�성 ?�이지 찾기
                active_selectors = [
                    ".current", ".active", ".selected",
                    ".page-current", ".page-active"
                ]

                current_page = None
                for selector in active_selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        current_page = int(element.text)
                        break
                    except:
                        continue

                if current_page:
                    # ?�음 ?�이지 번호 ?�릭 ?�도
                    next_page = current_page + 1
                    page_selectors = [
                        f"a[href*='page={next_page}']",
                        f"//a[text()='{next_page}']",
                        f".pagination a:contains('{next_page}')"
                    ]

                    for selector in page_selectors:
                        try:
                            if selector.startswith("//"):
                                element = self.driver.find_element(By.XPATH, selector)
                            else:
                                element = self.driver.find_element(By.CSS_SELECTOR, selector)

                            if element.is_displayed():
                                element.click()
                                print(f"        ?�️ ?�이지 {next_page}�??�동 ?�공")
                                self.safe_wait(self.driver, 2)
                                return True
                        except:
                            pass
            except:
                pass

            print("        ?�️ ?�음 ?�이지�?찾을 ???�음")
            return False

        except Exception as e:
            print(f"        ???�음 ?�이지 ?�동 ?�류: {e}")
            return False

    def get_post_content(self, post_url):
        """게시글 세부 내용 및 댓글 추출 (향상된 버전)"""
        if not post_url or 'cafe.naver.com' not in post_url or not self.driver:
            return {"content": "", "comments": []}

        try:
            print(f"      ?�� 게시글 ?�용 ?�집: {post_url[:60]}...")

            # ?�재 ?�레???�태 ?�??            current_frame = None
            try:
                current_frame = self.driver.current_frame
            except:
                pass

            # 게시글 ?�이지�??�동
            self.driver.get(post_url)
            self.safe_wait(self.driver, 2)

            # iframe 처리 (게시글 ?�세 ?�이지??iframe 구조?????�음)
            self.handle_post_detail_iframe()

            # 게시글 ?�용 추출
            content = self.extract_post_content()

            # ?��? 추출 (?�정???�라)
            comments = []
            extract_comments = getattr(Config, 'EXTRACT_COMMENTS', True)
            include_comments = getattr(Config, 'INCLUDE_COMMENTS', True)
            if extract_comments and include_comments:
                comments = self.extract_comments()

            print(f"        📄 내용: {len(content)}자, 댓글: {len(comments)}개")

            extract_images = getattr(Config, 'EXTRACT_IMAGES', False)
            extract_attachments = getattr(Config, 'EXTRACT_ATTACHMENTS', False)

            return {
                "content": content,
                "comments": comments,
                "images": self.extract_images() if extract_images else [],
                "attachments": self.extract_attachments() if extract_attachments else []
            }

        except Exception as e:
            print(f"        ??게시글 ?�용 ?�집 ?�류: {e}")
            return {"content": "", "comments": []}

        finally:
            # ?�래 ?�레?�으�?복�? ?�도
            try:
                if current_frame and self.driver:
                    self.driver.switch_to.frame(current_frame)
                elif self.driver:
                    self.driver.switch_to.default_content()
            except:
                pass

    def handle_post_detail_iframe(self):
        """게시글 세부 페이지의 iframe 처리"""
        if not self.driver:
            return False

        try:
            current_url = self.driver.current_url

            if 'iframe_url=' in current_url or 'ArticleRead' in current_url:
                # iframe 찾기 �??�환
                iframe_selectors = [
                    '#cafe_main',
                    'iframe[name="cafe_main"]',
                    'iframe[src*="ArticleRead"]',
                    'iframe[src*="read"]',
                    'iframe'
                ]

                for selector in iframe_selectors:
                    try:
                        iframes = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for iframe in iframes:
                            if iframe.is_displayed():
                                self.driver.switch_to.frame(iframe)
                                self.safe_wait(self.driver, 1)

                                # iframe ?�용 ?�인
                                if self.verify_post_detail_page():
                                    return True
                                else:
                                    self.driver.switch_to.default_content()
                    except:
                        pass

            return False

        except Exception as e:
            return False

    def verify_post_detail_page(self):
        """게시글 ?�세 ?�이지?��? ?�인"""
        if not self.driver:
            return False

        try:
            # 게시글 ?�세 ?�이지 지?�들
            indicators = [
                '.se-main-container',  # ?�마?�에?�터
                '.article_container',
                '.post-content',
                '.se-component',
                'div[class*="article"]',
                'div[class*="post"]'
            ]

            for indicator in indicators:
                if self.driver.find_elements(By.CSS_SELECTOR, indicator):
                    return True

            # ?�스??기반 ?�인
            page_source = self.driver.page_source
            if any(text in page_source for text in ['게시글', '작성자', '댓글', '추천']):
                return True

            return False

        except:
            return False

    def extract_post_content(self):
        """게시글 본문 ?�용 추출"""
        if not self.driver:
            return ""

        try:
            content_selectors = [
                # ?�이�?카페 ?�마?�에?�터 ?�턴??                '.se-main-container .se-component .se-text',
                '.se-main-container',
                '.article_container .article_viewer',
                '.post-content',
                '.se-component',

                # ?�반?�인 게시글 ?�용 ?�턴??                '.article-content',
                '.post_content',
                '.content',
                'div[class*="content"]',
                'div[class*="article"]',

                # ?�이�?기반 ?�턴
                'td.article',
                'td[class*="content"]',

                # 백업 ?�턴 (???��? 범위)
                'div',
                'td'
            ]

            content_parts = []

            for selector in content_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 10:  # 최소 10???�상
                            # 중복 ?�거 (?��? 추�????�용?��? ?�인)
                            if not any(text[:50] in part for part in content_parts):
                                content_parts.append(text)

                    # 충분???�용??찾았?�면 중단
                    if content_parts and sum(len(part) for part in content_parts) > 100:
                        break

                except Exception as e:
                    continue

            # ?�용 ?�치�?�??�리
            full_content = '\\n\\n'.join(content_parts)

            # ?�무 길면 ?�약 (10000???�한)
            if len(full_content) > 10000:
                full_content = full_content[:10000] + "... (?�용 ?�략)"

            return self.clean_text(full_content) if full_content else ""

        except Exception as e:
            print(f"        ?�️ 게시글 ?�용 추출 ?�류: {e}")
            return ""

    def extract_comments(self):
        """?��? 추출 (1000�??��? ?�집 최적??"""
        if not self.driver:
            return []

        try:
            # ?�체 ?��? ?�집 추적
            total_comments_collected = getattr(self, '_total_comments_collected', 0)

            # ?�체 ?��? ?�한 ?�인 (기본�??�정)
            max_total_comments = getattr(Config, 'MAX_TOTAL_COMMENTS', 1000)
            if total_comments_collected >= max_total_comments:
                print(f"        ?�️ ?�체 ?��? ?�집 ?�한 ({max_total_comments}�? ?�달")
                return []

            print(f"        ?�� ?��? ?�집 �?.. (?�재: {total_comments_collected}/{max_total_comments})")
            comments = []

            # 다양한 네이버 카페 댓글 패턴들
            comment_selectors = [
                '.comment_area .comment_box',
                '.cmt_area .comment_item',
                '.reply_area .reply_item',
                'div[class*="comment"]',
                'li[class*="comment"]',
                '.CommentItem',
                '.comment-item',
                '.comment_list li',
                '.comment-list .item',
                '[class*="CommentBox"]',
                '[class*="ReplyBox"]',
                '.comment_wrap .comment',
                '.board_comment .comment'
            ]

            # ?�집 가?�한 ?��? ??계산
            max_comments_per_post = getattr(Config, 'MAX_COMMENTS_PER_POST', 50)
            remaining_quota = max_total_comments - total_comments_collected
            max_collect = min(max_comments_per_post, remaining_quota)

            for selector in comment_selectors:
                try:
                    comment_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    if comment_elements and len(comment_elements) > 0:
                        print(f"        ?�� ?��? ?�턴 발견: '{selector}' ({len(comment_elements)}�?")

                        collected_this_round = 0
                        for i, comment_elem in enumerate(comment_elements):
                            if collected_this_round >= max_collect:
                                break

                            comment_data = self.extract_single_comment_enhanced(comment_elem, total_comments_collected + i + 1)
                            if comment_data:
                                # 최소 길이 ?�인
                                min_length = getattr(Config, 'COMMENT_CONTENT_MIN_LENGTH', 5)
                                if len(comment_data.get('content', '')) >= min_length:
                                    comments.append(comment_data)
                                    collected_this_round += 1

                        # ?��???찾았?�면 중단
                        if comments:
                            break

                except Exception as e:
                    continue

            # ?�?��? ?�집 (?�정???�성?�된 경우)
            collect_replies = getattr(Config, 'COLLECT_COMMENT_REPLIES', True)
            if collect_replies and comments and len(comments) < max_collect:
                replies = self.extract_comment_replies_enhanced(max_collect - len(comments))
                comments.extend(replies)

            # ?�체 ?��? 카운???�데?�트
            self._total_comments_collected = getattr(self, '_total_comments_collected', 0) + len(comments)

            print(f"        ??�?{len(comments)}�??��? ?�집 ?�료 (?�체: {self._total_comments_collected}/{max_total_comments})")
            return comments

        except Exception as e:
            print(f"        ???��? 추출 ?�류: {e}")
            return []

    def extract_single_comment_enhanced(self, comment_element, comment_id):
        """개별 ?��? ?�보 추출 (1000�??�집 최적??"""
        try:
            comment_data = {
                'comment_id': comment_id,
                'author': '',
                'content': '',
                'date': '',
                'like_count': 0,
                'depth': 1,
                'parent_id': None
            }

            # ?��? ?�성??추출 (?�장???�택??
            author_selectors = [
                '.comment_nick a', '.comment_author', '.nick',
                '.user_nick', '.author', 'strong', '.name',
                '.nickname', '.user-name', '.author-name',
                '[class*="nick"]', '[class*="author"]',
                '.writer', '.userid'
            ]

            for selector in author_selectors:
                try:
                    author_elem = comment_element.find_element(By.CSS_SELECTOR, selector)
                    author_text = self.clean_text(author_elem.text)
                    if author_text and len(author_text) > 0:
                        comment_data['author'] = author_text
                        break
                except:
                    continue

            # ?��? ?�용 추출 (?�장???�택??
            content_selectors = [
                '.comment_text', '.comment_content', '.text',
                '.content', 'span', 'div', 'p',
                '.comment-text', '.comment-content',
                '[class*="content"]', '[class*="text"]',
                '.message', '.body'
            ]

            for selector in content_selectors:
                try:
                    content_elem = comment_element.find_element(By.CSS_SELECTOR, selector)
                    content_text = self.clean_text(content_elem.text)
                    min_length = getattr(Config, 'COMMENT_CONTENT_MIN_LENGTH', 5)
                    if content_text and len(content_text) >= min_length:
                        comment_data['content'] = content_text
                        break
                except:
                    continue

            # ?��? ?�짜 추출 (?�장???�택??
            date_selectors = [
                '.comment_date', '.date', '.time', '.created_time',
                '.comment-date', '.comment-time', '.timestamp',
                '[class*="date"]', '[class*="time"]',
                '.regdate', '.writedate'
            ]

            for selector in date_selectors:
                try:
                    date_elem = comment_element.find_element(By.CSS_SELECTOR, selector)
                    date_text = self.clean_text(date_elem.text)
                    if date_text:
                        comment_data['date'] = date_text
                        break
                except:
                    continue

            # 좋아????추출
            like_selectors = [
                '.like_count', '.like-count', '.thumbup',
                '[class*="like"]', '[class*="thumb"]',
                '.recommend', '.good'
            ]

            for selector in like_selectors:
                try:
                    like_elem = comment_element.find_element(By.CSS_SELECTOR, selector)
                    like_text = self.clean_text(like_elem.text)
                    if like_text:
                        # ?�자�?추출
                        like_numbers = ''.join(filter(str.isdigit, like_text))
                        comment_data['like_count'] = int(like_numbers) if like_numbers else 0
                        break
                except:
                    continue

            # ?��? 깊이 ?�인 (?�?��??��?)
            class_name = comment_element.get_attribute('class').lower()
            if any(keyword in class_name for keyword in ['re-comment', 'reply', 'sub-comment', 'child']):
                comment_data['depth'] = 2

            # ?�효???��??��? ?�인
            min_length = getattr(Config, 'COMMENT_CONTENT_MIN_LENGTH', 5)
            if comment_data.get('content') and len(comment_data['content']) >= min_length:
                # 기본�??�정
                comment_data.setdefault('author', '?�명')
                comment_data.setdefault('date', '?�짜 ?�음')

                return comment_data

            return None

        except Exception as e:
            return None

    def extract_comment_replies_enhanced(self, max_replies):
        """?�?��? ?�집 (1000�??��? ?�집 최적??"""
        try:
            collect_replies = getattr(Config, 'COLLECT_COMMENT_REPLIES', True)
            if not collect_replies:
                return []

            replies = []

            # 답글 선택자 패턴들
            reply_selectors = [
                '.re-comment', '.reply', '.comment-reply',
                '.sub-comment', '.child-comment', '.reply-item',
                '[class*="reply"]', '[class*="re-comment"]',
                '.comment_reply', '.comment-child'
            ]

            for selector in reply_selectors:
                try:
                    reply_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    if reply_elements:
                        for i, reply_elem in enumerate(reply_elements):
                            if len(replies) >= max_replies:
                                break

                            reply_data = self.extract_single_reply(reply_elem, i + 1)
                            if reply_data:
                                replies.append(reply_data)

                        # ?�?��???찾았?�면 중단
                        if replies:
                            break

                except Exception as e:
                    continue

            return replies

        except Exception as e:
            return []

    def extract_single_reply(self, reply_element, reply_index):
        """개별 ?�?��? ?�보 추출"""
        try:
            reply_data = {
                'comment_id': f"reply_{reply_index}",
                'author': '',
                'content': '',
                'date': '',
                'like_count': 0,
                'depth': 2,
                'parent_id': None
            }

            # 답글 작성자 선택자
            author_selectors = [
                '.nick', '.author', '.user_nick', '.name',
                '[class*="nick"]', '[class*="author"]'
            ]

            for selector in author_selectors:
                try:
                    author_elem = reply_element.find_element(By.CSS_SELECTOR, selector)
                    author_text = self.clean_text(author_elem.text)
                    if author_text:
                        reply_data['author'] = author_text
                        break
                except:
                    continue

            # ?�?��? ?�용
            content_selectors = [
                '.content', '.comment_content', '.text', '[class*="content"]'
            ]

            for selector in content_selectors:
                try:
                    content_elem = reply_element.find_element(By.CSS_SELECTOR, selector)
                    content_text = self.clean_text(content_elem.text)
                    min_length = getattr(Config, 'COMMENT_CONTENT_MIN_LENGTH', 5)
                    if content_text and len(content_text) >= min_length:
                        reply_data['content'] = content_text
                        break
                except:
                    continue

            # ?�?��? ?�짜
            date_selectors = ['.date', '.time', '[class*="date"]', '[class*="time"]']

            for selector in date_selectors:
                try:
                    date_elem = reply_element.find_element(By.CSS_SELECTOR, selector)
                    date_text = self.clean_text(date_elem.text)
                    if date_text:
                        reply_data['date'] = date_text
                        break
                except:
                    continue

            # ?�효???�?��??��? ?�인
            min_length = getattr(Config, 'COMMENT_CONTENT_MIN_LENGTH', 5)
            if reply_data.get('content') and len(reply_data['content']) >= min_length:
                reply_data.setdefault('author', '?�명')
                reply_data.setdefault('date', '?�짜 ?�음')
                return reply_data

            return None

        except Exception as e:
            return None

    def extract_images(self):
        """게시글 ???��?지 URL 추출"""
        if not self.driver:
            return []

        try:
            images = []
            img_elements = self.driver.find_elements(By.TAG_NAME, "img")

            for img in img_elements:
                src = img.get_attribute("src")
                alt = img.get_attribute("alt") or ""

                if src and 'http' in src:
                    images.append({
                        'url': src,
                        'alt': self.clean_text(alt),
                        'size': f"{img.size['width']}x{img.size['height']}"
                    })

            return images[:10]  # 최�? 10개까지

        except:
            return []

    def extract_attachments(self):
        """첨�??�일 ?�보 추출"""
        if not self.driver:
            return []

        try:
            attachments = []

            # 첨�??�일 링크 ?�턴??            attachment_selectors = [
                'a[href*="attachment"]', 'a[href*="download"]',
                'a[href*="file"]', '.attachment', '.file'
            ]

            for selector in attachment_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        href = elem.get_attribute("href")
                        text = self.clean_text(elem.text)

                        if href and text:
                            attachments.append({
                                'name': text,
                                'url': href
                            })
                except:
                    continue

            return attachments[:5]  # 최�? 5개까지

        except:
            return []

    # =====================================================================
    # Phase 4: 고급 ?�이??추출 ?�스??(??번째 그룹 - 게시글 ?�용 �?구조 분석)
    # =====================================================================

    def enhance_posts_with_details(self, posts, keyword):
        """게시글 ?�세 ?�보 강화 (?�용, ?��?, ?��?지 ??"""
        try:
            print(f"    ?�� ?�세 ?�보 ?�집 �?.. (�?{len(posts)}�?")
            enhanced_posts = []
            max_total_posts = getattr(Config, 'MAX_TOTAL_POSTS', 100)

            for i, post in enumerate(posts[:max_total_posts], 1):
                try:
                    print(f"      ?�� 게시글 {i}/{min(len(posts), max_total_posts)} 처리 �?..")

                    # ?�세 ?�용 ?�집
                    extract_full_content = getattr(Config, 'EXTRACT_FULL_CONTENT', False)
                    extract_comments = getattr(Config, 'EXTRACT_COMMENTS', False)

                    if extract_full_content or extract_comments:
                        post_url = post.get('url', '')
                        if post_url:
                            detail_data = self.get_post_content(post_url)

                            # ?�세 ?�보 ?�합
                            if detail_data.get('content'):
                                post['full_content'] = detail_data['content']

                            if detail_data.get('comments'):
                                post['comments'] = detail_data['comments']
                                post['comment_count'] = len(detail_data['comments'])

                            if detail_data.get('images'):
                                post['images'] = detail_data['images']

                            if detail_data.get('attachments'):
                                post['attachments'] = detail_data['attachments']

                    # 추�? 메�??�이??                    post['keyword'] = keyword
                    post['collection_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    post['enhanced'] = True

                    enhanced_posts.append(post)

                    # 진행�??�시
                    if i % 10 == 0:
                        print(f"      ?�� 진행�? {i}/{min(len(posts), max_total_posts)} ({i/min(len(posts), max_total_posts)*100:.1f}%)")

                except Exception as e:
                    print(f"      ??게시글 {i} 처리 ?�류: {e}")
                    # 기본 ?�보?�도 ?��?
                    post['keyword'] = keyword
                    post['collection_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    post['enhanced'] = False
                    enhanced_posts.append(post)
                    continue

            print(f"    ???�세 ?�보 ?�집 ?�료: {len(enhanced_posts)}�?)
            return enhanced_posts

        except Exception as e:
            print(f"    ???�세 ?�보 ?�집 ?�류: {e}")
            return posts

    def get_posts_data(self):
        """?�집??게시글 ?�이??반환"""
        return getattr(self, 'posts_data', [])

    def analyze_page_structure_for_posts(self):
        """게시글 추출???�한 ?�이지 구조 분석"""
        structure = {}

        try:
            # ?�이�?기반 구조 ?�인
            tables = self.driver.find_elements(By.CSS_SELECTOR, "table")
            structure['table_count'] = len(tables)

            # 리스??기반 구조 ?�인
            lists = self.driver.find_elements(By.CSS_SELECTOR, "ul, ol")
            structure['list_count'] = len(lists)

            # div 기반 구조 ?�인
            divs = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='article'], div[class*='post'], div[class*='board']")
            structure['div_count'] = len(divs)

            # 링크 ?�소 ?�인
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='read']")
            structure['link_count'] = len(links)

            print(f"      ?�� ?�이지 구조: ?�이�?{structure['table_count']}, 리스??{structure['list_count']}, div {structure['div_count']}, 링크 {structure['link_count']}")

            return structure

        except Exception as e:
            print(f"      ?�️ ?�이지 구조 분석 ?�류: {e}")
            return {}

    # =====================================================================
    # Phase 6: 구조 분석 �??�색 ?�스??(�?번째 그룹 - 기본 분석)
    # =====================================================================

    def analyze_current_page(self):
        """?�재 ?�이지 ?�태 분석"""
        analysis = {}

        try:
            # ?�이지 ?�??감�?
            page_indicators = {
                'board_list': ['.article-board', '.post-list', '.board-content'],
                'search_result': ['.search-result', '.search-list'],
                'main_page': ['.cafe-main', '.main-content'],
                'single_post': ['.post-view', '.article-view']
            }

            analysis['page_type'] = 'unknown'
            for page_type, selectors in page_indicators.items():
                for selector in selectors:
                    try:
                        if self.driver.find_elements(By.CSS_SELECTOR, selector):
                            analysis['page_type'] = page_type
                            break
                    except:
                        continue
                if analysis['page_type'] != 'unknown':
                    break

            # 게시글 ??계산
            post_selectors = [
                '.article-board tbody tr',
                '.post-item',
                '.board-item'
            ]

            analysis['post_count'] = 0
            for selector in post_selectors:
                try:
                    posts = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    analysis['post_count'] = len(posts)
                    if analysis['post_count'] > 0:
                        break
                except:
                    continue

            print(f"      ?�� ?�이지 분석: ?�??{analysis['page_type']}, 게시글??{analysis['post_count']}")

            return analysis

        except Exception as e:
            print(f"      ?�️ ?�이지 분석 ?�류: {e}")
            return {'page_type': 'unknown', 'post_count': 0}

    def debug_page_structure(self):
        """?�이지 구조 ?�버�?""
        try:
            print("      ?�� ?�이지 구조 ?�버�?�?..")

            # ?�재 URL�??�목
            current_url = self.driver.current_url
            page_title = self.driver.title
            print(f"        URL: {current_url}")
            print(f"        ?�목: {page_title}")

            # 주요 ?�소??개수 ?�인
            elements_info = {
                "?�이�?: len(self.driver.find_elements(By.TAG_NAME, "table")),
                "??tr)": len(self.driver.find_elements(By.TAG_NAME, "tr")),
                "링크(a)": len(self.driver.find_elements(By.TAG_NAME, "a")),
                "리스??li)": len(self.driver.find_elements(By.TAG_NAME, "li")),
                "div": len(self.driver.find_elements(By.TAG_NAME, "div"))
            }

            for name, count in elements_info.items():
                print(f"        {name}: {count}�?)

            # 링크 ?�플 ?�인
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href]")[:10]
            print(f"        링크 ?�플 (처음 10�?:")
            for i, link in enumerate(links):
                try:
                    text = link.text.strip()[:30] if link.text else "(?�스???�음)"
                    href = link.get_attribute("href")[:50] if link.get_attribute("href") else "(href ?�음)"
                    print(f"          {i+1}. {text} -> {href}")
                except:
                    print(f"          {i+1}. (?�류)")

        except Exception as e:
            print(f"        ???�버�??�류: {e}")

    # =====================================================================
    # Phase 6: 구조 분석 �??�색 ?�스??(??번째 그룹 - ?�전 ?�색)
    # =====================================================================

    def explore_cafe_completely(self, cafe_url, keywords=None):
        """?�� ?�이�?카페 ?�전 ?�색 ?�스??""
        print(f"\n?? ?�이�?카페 ?�전 ?�색 ?�작!")
        print(f"?�� ?�??카페: {cafe_url}")
        print(f"?�� ?�색 모드: ?�체 검??기능 + 모든 게시??)
        print("=" * 80)

        exploration_results = {
            'cafe_metadata': {},
            'all_boards': [],
            'search_results': {},
            'statistics': {},
            'total_posts': 0,
            'total_comments': 0
        }

        try:
            # 1?�계: 카페 ?�속 �?기본 분석
            print(f"?�� 1?�계: 카페 ?�속 �?구조 분석")
            self.driver.get(cafe_url)
            self.safe_wait(self.driver, 3)

            # 로그???�인
            if not self.check_login_status():
                print("??로그?�이 ?�요?�니??")
                return exploration_results

            # 2?�계: 카페 메�??�이???�집
            if getattr(Config, 'COLLECT_CAFE_METADATA', True):
                print(f"?�� 2?�계: 카페 메�??�이???�집")
                exploration_results['cafe_metadata'] = self.collect_cafe_metadata()

            # 3?�계: 모든 게시??발견 �?분석
            if getattr(Config, 'EXPLORE_ALL_BOARDS', True):
                print(f"?���?3?�계: 모든 게시??발견 �?분석")
                exploration_results['all_boards'] = self.discover_all_boards()

            # 4?�계: ?�이�?카페 ?��? 검??기능 ?�전 ?�용
            if keywords:
                print(f"?�� 4?�계: ?��? 검??기능 ?�전 ?�용")
                exploration_results['search_results'] = self.comprehensive_search_exploration(keywords)

            # 5?�계: 모든 게시?�별 ?�색
            print(f"?�� 5?�계: 모든 게시??개별 ?�색")
            board_results = self.explore_all_boards_individually(exploration_results['all_boards'])
            exploration_results.update(board_results)

            # 6?�계: ?�계 �?분석
            print(f"?�� 6?�계: 종합 ?�계 ?�성")
            exploration_results['statistics'] = self.generate_exploration_statistics(exploration_results)

            print(f"\n?�� ?�전 ?�색 ?�료!")
            print(f"?�� 발견??게시?? {len(exploration_results['all_boards'])}�?)
            print(f"?�� ?�집??게시글: {exploration_results['total_posts']}�?)
            print(f"?�� ?�집???��?: {exploration_results['total_comments']}�?)

            return exploration_results

        except Exception as e:
            print(f"???�전 ?�색 �??�류: {e}")
            return exploration_results

    def collect_cafe_metadata(self):
        """카페 메�??�이???�집"""
        try:
            print(f"    ?�� 카페 기본 ?�보 ?�집 �?..")
            metadata = {
                'cafe_name': '',
                'cafe_url': '',
                'member_count': 0,
                'category': '',
                'description': '',
                'creation_date': '',
                'cafe_level': '',
                'cafe_type': '',
                'rules': [],
                'admin_info': {},
                'activity_stats': {}
            }

            # 카페 ?�름 추출
            cafe_name_selectors = [
                '.cafe-name', '.cafe_name', 'h1', '.title',
                '[class*="cafe"]', '[class*="title"]'
            ]

            for selector in cafe_name_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    cafe_name = self.clean_text(element.text)
                    if cafe_name and len(cafe_name) > 2:
                        metadata['cafe_name'] = cafe_name
                        break
                except:
                    continue

            # 멤버 ??추출
            member_selectors = [
                '[class*="member"]', '[class*="count"]',
                '.member-count', '.cafe-member'
            ]

            for selector in member_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text
                        numbers = ''.join(filter(str.isdigit, text))
                        if numbers and int(numbers) > 10:  # ?�제 멤버 ?�로 보이??경우
                            metadata['member_count'] = int(numbers)
                            break
                    if metadata['member_count'] > 0:
                        break
                except:
                    continue

            # ?�재 URL ?�??            metadata['cafe_url'] = self.driver.current_url

            # 카페 ?�명 추출
            description_selectors = [
                '.cafe-description', '.description',
                '[class*="intro"]', '[class*="desc"]'
            ]

            for selector in description_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    desc_text = self.clean_text(element.text)
                    if desc_text and len(desc_text) > 10:
                        metadata['description'] = desc_text[:500]  # 최�? 500??                        break
                except:
                    continue

            print(f"        ??카페�? {metadata['cafe_name']}")
            print(f"        ?�� 멤버?? {metadata['member_count']:,}�?)
            print(f"        ?�� ?�명: {metadata['description'][:50]}..." if metadata['description'] else "        ?�� ?�명: ?�음")

            return metadata

        except Exception as e:
            print(f"        ??메�??�이???�집 ?�류: {e}")
            return {}

    def comprehensive_search_exploration(self, keywords):
        """?�� ?�이�?카페 ?��? 검??기능 ?�전 ?�용"""
        try:
            print(f"    ?�� ?�워?? {keywords}")
            search_results = {
                'total_searches': 0,
                'successful_searches': 0,
                'failed_searches': 0,
                'all_posts': [],
                'search_strategies': {}
            }

            # ?�워?��? 문자?�인 경우 리스?�로 변??            if isinstance(keywords, str):
                keyword_list = [keywords]
            else:
                keyword_list = keywords

            for keyword in keyword_list:
                print(f"        ?�� '{keyword}' 검???�작...")

                # 1. ?�합 검??                if getattr(Config, 'USE_INTEGRATED_SEARCH', True):
                    result = self.perform_integrated_search(keyword)
                    search_results['search_strategies']['integrated'] = result
                    search_results['total_searches'] += 1
                    if result.get('posts'):
                        search_results['successful_searches'] += 1
                        search_results['all_posts'].extend(result['posts'])

                # 2. ?�중 범위 검??(?�목, ?�용, ?�성????
                if hasattr(Config, 'COMPREHENSIVE_SEARCH_SCOPES'):
                    for scope in Config.COMPREHENSIVE_SEARCH_SCOPES:
                        result = self.perform_scope_specific_search(keyword, scope)
                        search_results['search_strategies'][f'scope_{scope}'] = result
                        search_results['total_searches'] += 1
                        if result.get('posts'):
                            search_results['successful_searches'] += 1
                            search_results['all_posts'].extend(result['posts'])

                # 3. ?�중 ?�렬 검??                if hasattr(Config, 'COMPREHENSIVE_SORT_METHODS'):
                    for sort_method in Config.COMPREHENSIVE_SORT_METHODS:
                        result = self.perform_sort_specific_search(keyword, sort_method)
                        search_results['search_strategies'][f'sort_{sort_method}'] = result
                        search_results['total_searches'] += 1
                        if result.get('posts'):
                            search_results['successful_searches'] += 1
                            search_results['all_posts'].extend(result['posts'])

                # 4. 기간�?검??                if hasattr(Config, 'COMPREHENSIVE_DATE_FILTERS'):
                    for date_filter in Config.COMPREHENSIVE_DATE_FILTERS:
                        result = self.perform_date_specific_search(keyword, date_filter)
                        search_results['search_strategies'][f'date_{date_filter}'] = result
                        search_results['total_searches'] += 1
                        if result.get('posts'):
                            search_results['successful_searches'] += 1
                            search_results['all_posts'].extend(result['posts'])

            # 중복 ?�거
            search_results['all_posts'] = self.deduplicate_posts(search_results['all_posts'])
            search_results['failed_searches'] = search_results['total_searches'] - search_results['successful_searches']

            print(f"        ??검???�료: {len(search_results['all_posts'])}�?게시글 발견")
            return search_results

        except Exception as e:
            print(f"        ??종합 검???�류: {e}")
            return {'all_posts': [], 'search_strategies': {}}

    # =====================================================================
    # Phase 6: 구조 분석 �??�색 ?�스??(??번째 그룹 - 개별 게시???�색)
    # =====================================================================

    def explore_all_boards_individually(self, boards):
        """모든 게시??개별 ?�색"""
        try:
            print(f"    ?�� 개별 게시???�색 �?.. ({len(boards)}�?")

            board_results = {
                'board_results': {},
                'active_boards': [],
                'inactive_boards': [],
                'total_posts': 0,
                'total_comments': 0
            }

            for i, board in enumerate(boards):
                try:
                    board_name = board.get('name', f'Board_{i+1}')
                    board_url = board.get('url', '')

                    print(f"        ?�� {i+1}/{len(boards)}: {board_name}")

                    if not board_url:
                        print(f"            ?�️ URL ?�음, 건너?�기")
                        continue

                    # 게시?�으�??�동
                    self.driver.get(board_url)
                    self.safe_wait(self.driver, 2)

                    # 게시글 추출
                    board_posts = self.extract_board_posts(board)

                    # ?�계 계산
                    board_info = {
                        'board_info': board,
                        'posts': board_posts,
                        'post_count': len(board_posts),
                        'comment_count': sum(len(post.get('comments', [])) for post in board_posts),
                        'last_activity': self.get_board_last_activity(board_posts),
                        'activity_score': self.calculate_board_activity_score(board_posts)
                    }

                    board_results['board_results'][board_name] = board_info

                    # ?�동??분류
                    if board_info['activity_score'] > 10:
                        board_results['active_boards'].append(board)
                    else:
                        board_results['inactive_boards'].append(board)

                    # ?�체 ?�계 ?�데?�트
                    board_results['total_posts'] += board_info['post_count']
                    board_results['total_comments'] += board_info['comment_count']

                    print(f"            ??게시글: {board_info['post_count']}�? ?��?: {board_info['comment_count']}�?)

                    # ?�무 빠른 ?�청 방�?
                    self.adaptive_delay()

                except Exception as e:
                    print(f"            ??게시???�색 ?�류: {e}")
                    continue

            print(f"    ??개별 게시???�색 ?�료")
            print(f"        ?�성 게시?? {len(board_results['active_boards'])}�?)
            print(f"        비활??게시?? {len(board_results['inactive_boards'])}�?)

            return board_results

        except Exception as e:
            print(f"    ??개별 게시???�색 ?�류: {e}")
            return {'board_results': {}, 'total_posts': 0, 'total_comments': 0}

    def extract_board_posts(self, board):
        """게시?�에??게시글 추출"""
        try:
            # 기존 extract_posts 메서???�용
            posts = self.extract_posts()

            # 게시???�보 추�?
            for post in posts:
                post['board_name'] = board.get('name', '')
                post['board_type'] = board.get('board_type', 'unknown')
                post['board_url'] = board.get('url', '')

            return posts

        except Exception as e:
            return []

    def get_board_last_activity(self, posts):
        """게시??최근 ?�동 ?�간 계산"""
        try:
            if not posts:
                return ""

            # 가??최근 게시글???�성?�간 반환
            latest_date = ""
            for post in posts:
                post_date = post.get('date', '')
                if post_date and (not latest_date or post_date > latest_date):
                    latest_date = post_date

            return latest_date

        except Exception as e:
            return ""

    def calculate_board_activity_score(self, posts):
        """게시???�동???�수 계산"""
        try:
            if not posts:
                return 0

            # 기본 ?�수: 게시글 ??            score = len(posts)

            # ?��? ??가?�점
            total_comments = sum(len(post.get('comments', [])) for post in posts)
            score += total_comments * 0.5

            # 조회??가?�점
            total_views = sum(post.get('views', 0) for post in posts)
            score += total_views * 0.001

            # 최근 ?�동 가?�점 (최근 ?�동?�수�??��? ?�수)
            recent_posts = sum(1 for post in posts if self.is_recent_post(post))
            score += recent_posts * 2

            return round(score, 2)

        except Exception as e:
            return 0

    def is_recent_post(self, post):
        """최근 게시글?��? ?�인 (7???�내)"""
        try:
            from datetime import datetime, timedelta

            post_date_str = post.get('date', '')
            if not post_date_str:
                return False

            # ?�짜 ?�식 ?�싱 ?�도
            try:
                # ?�양???�짜 ?�식 처리
                for date_format in ['%Y.%m.%d', '%Y-%m-%d', '%m.%d', '%m-%d']:
                    try:
                        post_date = datetime.strptime(post_date_str, date_format)
                        if date_format in ['%m.%d', '%m-%d']:  # ?�도가 ?�는 경우 ?�재 ?�도 ?�용
                            post_date = post_date.replace(year=datetime.now().year)
                        break
                    except:
                        continue
                else:
                    return False

                # 7???�내?��? ?�인
                week_ago = datetime.now() - timedelta(days=7)
                return post_date >= week_ago

            except:
                return False

        except Exception as e:
            return False

    def generate_exploration_statistics(self, exploration_results):
        """?�색 ?�계 ?�성"""
        try:
            print(f"    ?�� ?�계 분석 �?..")

            stats = {
                'exploration_summary': {},
                'board_statistics': {},
                'content_statistics': {},
                'activity_analysis': {},
                'top_boards': [],
                'content_distribution': {}
            }

            # 기본 ?�계
            total_boards = len(exploration_results.get('all_boards', []))
            total_posts = exploration_results.get('total_posts', 0)
            total_comments = exploration_results.get('total_comments', 0)

            stats['exploration_summary'] = {
                'total_boards_discovered': total_boards,
                'total_posts_collected': total_posts,
                'total_comments_collected': total_comments,
                'active_boards_count': len(exploration_results.get('active_boards', [])),
                'inactive_boards_count': len(exploration_results.get('inactive_boards', [])),
                'search_strategies_used': len(exploration_results.get('search_results', {}).get('search_strategies', {})),
                'cafe_metadata_collected': bool(exploration_results.get('cafe_metadata', {}))
            }

            # 게시???�계
            board_results = exploration_results.get('board_results', {})
            if board_results:
                board_stats = []
                for board_name, board_data in board_results.items():
                    board_stats.append({
                        'name': board_name,
                        'post_count': board_data.get('post_count', 0),
                        'comment_count': board_data.get('comment_count', 0),
                        'activity_score': board_data.get('activity_score', 0),
                        'board_type': board_data.get('board_info', {}).get('board_type', 'unknown')
                    })

                # ?�동?????�렬
                board_stats.sort(key=lambda x: x['activity_score'], reverse=True)
                stats['top_boards'] = board_stats[:10]  # ?�위 10�?게시??
                # 게시???�형�?분포
                board_type_dist = {}
                for board_stat in board_stats:
                    board_type = board_stat['board_type']
                    if board_type not in board_type_dist:
                        board_type_dist[board_type] = 0
                    board_type_dist[board_type] += 1

                stats['board_statistics'] = {
                    'total_boards_with_content': len(board_stats),
                    'board_type_distribution': board_type_dist,
                    'average_posts_per_board': round(total_posts / len(board_stats), 2) if board_stats else 0,
                    'average_comments_per_board': round(total_comments / len(board_stats), 2) if board_stats else 0
                }

            # 검??결과 ?�계
            search_results = exploration_results.get('search_results', {})
            if search_results:
                stats['content_statistics'] = {
                    'total_searches_performed': search_results.get('total_searches', 0),
                    'successful_searches': search_results.get('successful_searches', 0),
                    'failed_searches': search_results.get('failed_searches', 0),
                    'search_success_rate': round((search_results.get('successful_searches', 0) / max(search_results.get('total_searches', 1), 1)) * 100, 2),
                    'unique_posts_from_search': len(search_results.get('all_posts', []))
                }

            print(f"        ???�계 ?�성 ?�료")
            return stats

        except Exception as e:
            print(f"        ???�계 ?�성 ?�류: {e}")
            return {}

    # =====================================================================
    # CRITICAL MISSING METHODS - Phase 1: iframe 처리 ?�스??    # =====================================================================

    def auto_navigate_frames(self):
        """?�레??구조 ?�동 감�? �?최적 ?�레?�으�??�환"""
        try:
            if not self.driver:
                return False
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            if not iframes:
                print("  ?�� ?�일 ?�이지 구조 (iframe ?�음)")
                return True

            print(f"  ?���?{len(iframes)}�?iframe 발견, 최적 ?�레??찾는 중�?)
            best_frame, best_score = None, 0
            for i, iframe in enumerate(iframes):
                try:
                    frame_id = iframe.get_attribute("id") or f"frame_{i}"
                    frame_src = iframe.get_attribute("src") or ""
                    frame_name = iframe.get_attribute("name") or ""

                    score = self.calculate_frame_score(frame_id, frame_src, frame_name)
                    if score > best_score:
                        best_score = score
                        best_frame = iframe
                except:
                    continue

            if best_frame:
                try:
                    self.driver.switch_to.frame(best_frame)
                    if self.verify_frame_content():
                        print(f"  ??최적 ?�레?�으�??�환 ?�료 (?�수: {best_score})")
                        return True
                    else:
                        self.driver.switch_to.default_content()
                except:
                    self.driver.switch_to.default_content()

            print(f"  ?�� 메인 ?�이지?�서 계속 진행")
            return True
        except Exception as e:
            print(f"  ???�레???�비게이???�류: {e}")
            return False

    def calculate_frame_score(self, frame_id, frame_src, frame_name):
        """?�레???�선?�위 ?�수 계산"""
        score = 0
        # 카페 관???�워?�로 ?�수 부??        cafe_keywords = ['cafe', 'main', 'content', 'board', 'article']
        for keyword in cafe_keywords:
            if keyword in frame_id.lower() or keyword in frame_src.lower() or keyword in frame_name.lower():
                score += 10

        # 메인 ?�레???�선
        if 'main' in frame_id.lower() or 'main' in frame_name.lower():
            score += 20

        return score

    def verify_frame_content(self):
        """?�재 ?�레?�에 ?�용??콘텐츠�? ?�는지 ?�인"""
        try:
            # 게시글 목록 ?�소 ?�인
            post_indicators = ['.article-board', '.post-list', '.board-list', 'table', '.cafe-content']
            for indicator in post_indicators:
                if self.driver.find_elements(By.CSS_SELECTOR, indicator):
                    return True
            return False
        except:
            return False

    def handle_search_iframe(self):
        """검??결과 ?�이지??iframe 처리"""
        try:
            search_iframes = self.driver.find_elements(By.CSS_SELECTOR, "iframe[src*='search'], iframe[name*='search']")
            if search_iframes:
                self.driver.switch_to.frame(search_iframes[0])
                return True
            return self.auto_navigate_frames()
        except:
            return False

    def navigate_to_all_posts_iframe(self):
        """?�체글보기 iframe?�로 ?�동"""
        try:
            all_post_iframes = self.driver.find_elements(By.CSS_SELECTOR, "iframe[src*='ArticleList'], iframe[name*='cafe_main']")
            if all_post_iframes:
                self.driver.switch_to.frame(all_post_iframes[0])
                return True
            return self.auto_navigate_frames()
        except:
            return False

    # =====================================================================
    # CRITICAL MISSING METHODS - Phase 2: 고급 검???�스???�심 메서?�들
    # =====================================================================

    def search_with_cafe_function(self, keyword, max_pages):
        """카페 ??검??기능???�용??고급 검??""
        try:
            if not self.driver:
                return []
            print(f"  ?�� ?�이�?카페 고급 검??기능?�로 '{keyword}' 검??..")

            # 1. 직접 검??URL 구성 방식 ?�도
            search_url_found = self.try_direct_search_url(keyword)
            if search_url_found:
                return self.collect_search_results(keyword, max_pages)

            # 2. 카페 ??검??기능 ?�용
            if self.use_cafe_search_interface(keyword):
                return self.collect_search_results(keyword, max_pages)

            return []
        except Exception as e:
            print(f"  ??카페 검??기능 ?�류: {e}")
            return []

    def try_direct_search_url(self, keyword):
        """직접 검??URL 구성"""
        try:
            club_id = self.get_cafe_club_id()
            if club_id:
                search_url = f"https://cafe.naver.com/ArticleSearchList.nhn?search.clubid={club_id}&search.query={keyword}"
                self.driver.get(search_url)
                self.safe_wait(self.driver, 2)
                return True
            return False
        except:
            return False

    def use_cafe_search_interface(self, keyword):
        """카페 검???�터?�이???�용"""
        try:
            search_selectors = ['.search-box input', '#search-input', '[name=\"query\"]', '.cafe-search input']
            for selector in search_selectors:
                try:
                    search_box = self.driver.find_element(By.CSS_SELECTOR, selector)
                    search_box.clear()
                    search_box.send_keys(keyword)
                    search_box.send_keys(Keys.RETURN)
                    self.safe_wait(self.driver, 2)
                    return True
                except:
                    continue
            return False
        except:
            return False

    def collect_search_results(self, keyword, max_pages):
        """검??결과 ?�집"""
        try:
            all_posts = []
            for page in range(max_pages):
                posts = self.extract_search_result_posts(keyword)
                if not posts:
                    break
                all_posts.extend(posts)
                if not self._go_to_next_page():
                    break
            return all_posts
        except:
            return []

    def get_cafe_club_id(self):
        """카페 Club ID 추출"""
        try:
            url = self.driver.current_url
            if 'cafe.naver.com' in url:
                # URL?�서 카페�?추출 ??Club ID 조회
                cafe_name = url.split('cafe.naver.com/')[-1].split('/')[0]
                return cafe_name
            return None
        except:
            return None

    def extract_search_result_posts(self, keyword=None):
        """검??결과?�서 게시글 추출"""
        try:
            return self._extract_posts_from_current_page()
        except:
            return []

    # =====================================================================
    # CRITICAL MISSING METHODS - Phase 3: 게시???��? ?�스??    # =====================================================================

    def get_all_boards(self):
        """카페??모든 게시??목록 ?�동 분석 �??�집"""
        boards = []
        try:
            print("  ?�� ?�페?��? 구조 ?�동 분석 �?..")

            # 1. 기본 게시???�턴 검??            basic_boards = self.find_basic_board_patterns()
            boards.extend(basic_boards)

            # 2. 고급 ?�턴 검??            advanced_boards = self.find_advanced_patterns()
            boards.extend(advanced_boards)

            # 3. 중복 ?�거 �?검�?            unique_boards = self.validate_board_list(boards)

            print(f"  ??�?{len(unique_boards)}�?게시??발견")
            return unique_boards

        except Exception as e:
            print(f"  ??게시??분석 ?�류: {e}")
            return []

    def find_basic_board_patterns(self):
        """기본 게시???�턴 찾기"""
        boards = []
        try:
            basic_selectors = [
                'a[href*=\"menuType=1\"]',  # 게시??메뉴
                'a[href*=\"boardtype\"]',   # 게시???�??                '.menu-list a', '.board-menu a',  # 메뉴 링크
                'nav a', '.navigation a'  # ?�비게이??링크
            ]

            for selector in basic_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        name = element.text.strip()
                        href = element.get_attribute('href')
                        if self.is_valid_board(name, href):
                            boards.append((name, href))
                except:
                    continue
            return boards
        except:
            return []

    def find_advanced_patterns(self):
        """고급 게시???�턴 찾기"""
        boards = []
        try:
            # ?�스??기반 링크 검??            all_links = self.driver.find_elements(By.TAG_NAME, 'a')
            for link in all_links:
                try:
                    text = link.text.strip()
                    href = link.get_attribute('href')
                    # 게시??관???�워???�터�?                    board_keywords = ['게시??, '?�유', '?�보', '질문', '?�기', '공�?', '?�벤??]
                    if any(keyword in text for keyword in board_keywords) and self.is_valid_board(text, href):
                        boards.append((text, href))
                except:
                    continue
            return boards
        except:
            return []

    def is_valid_board(self, name, href):
        """?�효??게시?�인지 ?�인"""
        if not name or not href or len(name) < 2:
            return False
        if 'cafe.naver.com' not in href:
            return False
        if any(word in name.lower() for word in ['로그??, 'login', '?�원가??, '?�정']):
            return False
        return True

    def validate_board_list(self, boards):
        """게시??목록 검�?�?중복 ?�거"""
        try:
            unique_boards = []
            seen_urls = set()
            seen_names = set()

            for name, url in boards:
                if url not in seen_urls and name not in seen_names:
                    unique_boards.append({'name': name, 'url': url})
                    seen_urls.add(url)
                    seen_names.add(name)

            return unique_boards
        except:
            return []

    # =====================================================================
    # CRITICAL MISSING METHODS - Phase 5: ?�이지 ?�비게이???�스??    # =====================================================================

    def navigate_to_all_posts(self):
        """?�체글보기 ?�이지�??�동"""
        try:
            all_post_selectors = [
                'a[href*=\"ArticleList\"]',
                'a[title*=\"?�체글\"]',
                'a[title*=\"?�체\"]',
                '.all-posts', '.board-all'
            ]

            for selector in all_post_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    element.click()
                    self.safe_wait(self.driver, 2)
                    self.auto_navigate_frames()
                    return True
                except:
                    continue
            return False
        except:
            return False

    def smart_page_navigation(self, target_type="all_posts"):
        """?�마???�이지 ?�비게이??""
        try:
            if target_type == "all_posts":
                return self.navigate_to_all_posts()
            return False
        except:
            return False

    def wait_for_dynamic_content(self):
        """?�적 컨텐�?로딩 ?��?""
        try:
            # JavaScript 로딩 ?�료 ?��?            self.safe_wait(self.driver, 2)

            # jQuery ?�료 ?��?(?�는 경우)
            try:
                WebDriverWait(self.driver, 3).until(
                    lambda driver: driver.execute_script("return jQuery.active == 0") if
                    driver.execute_script("return typeof jQuery !== 'undefined'") else True
                )
            except:
                pass

            return True
        except:
            return False

    def adaptive_delay(self):
        """?�응???�레??(?�버 부??고려)"""
        try:
            base_delay = 1.0  # 기본 ?�레??
            # ?�이지 로딩 ?�간 측정
            start_time = time.time()
            self.wait_for_page_load()
            load_time = time.time() - start_time

            # 로딩 ?�간???�른 ?�응???�레??            if load_time > 3:
                # 로딩???�래 걸리�???�??�레??                delay = base_delay * 1.5
            elif load_time < 1:
                # 로딩??빠르�?기본 ?�레??                delay = base_delay
            else:
                # 중간 ?�도�??�간 �??�레??                delay = base_delay * 1.2

            time.sleep(delay)

        except Exception as e:
            # ?�류 ??기본 ?�레??            time.sleep(1.0)

    def safe_find_elements(self, by, value):
        """?�전???�소 찾기"""
        try:
            return self.driver.find_elements(by, value)
        except:
            return []

    def safe_get_page_source(self):
        """?�전???�이지 ?�스 가?�오�?""
        try:
            return self.driver.page_source
        except:
            return ""

    def safe_get_current_url(self):
        """?�전???�재 URL 가?�오�?""
        try:
            return self.driver.current_url
        except:
            return ""

    def safe_get_title(self):
        """?�전???�이지 ?�목 가?�오�?""
        try:
            return self.driver.title
        except:
            return ""

    def safe_driver_get(self, url):
        """?�전???�이지 ?�동"""
        try:
            self.driver.get(url)
            return True
        except:
            return False

    def safe_execute_script(self, script):
        """?�전???�크립트 ?�행"""
        try:
            return self.driver.execute_script(script)
        except:
            return None

    # =====================================================================
    # Phase 7A: 카페 구조 분석 �?기본 ?�비게이??메서??    # =====================================================================

    def analyze_cafe_structure(self):
        """카페 ?�이지 구조 ?�동 분석"""
        structure_info = {}
        try:
            if not self.driver:
                return {}

            print("  ?�� ?�이지 구조 분석 중�?)
            structure_info["title"] = self.driver.title
            structure_info["url"] = self.driver.current_url
            structure_info["has_frames"] = bool(self.driver.find_elements(By.TAG_NAME, "iframe"))

            # 메뉴 구조 분석
            menu_patterns = [
                (".cafe-menu", "카페 메뉴"),
                (".board-list", "게시??목록"),
                (".left-menu", "?�쪽 메뉴"),
                (".nav-menu", "?�비게이??메뉴"),
                (".sidebar", "?�이?�바"),
                ("#menuList", "메뉴 리스??),
            ]
            structure_info["menus"] = []
            for selector, name in menu_patterns:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        structure_info["menus"].append({"name": name, "selector": selector, "count": len(elements)})
                        print(f"    ?�� {name} 발견: {len(elements)}�?)
                except Exception:
                    continue

            # 컨텐�??�역 분석
            content_patterns = [
                (".content", "메인 컨텐�?),
                (".article-board", "게시??),
                (".post-list", "게시글 목록"),
                (".board-content", "게시??컨텐�?),
            ]
            structure_info["content_areas"] = []
            for selector, name in content_patterns:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        structure_info["content_areas"].append({"name": name, "selector": selector, "count": len(elements)})
                except Exception:
                    continue
            print(
                f"    ??구조 분석 ?�료: {len(structure_info['menus'])}�?메뉴, "
                f"{len(structure_info['content_areas'])}�?컨텐�??�역"
            )
            return structure_info
        except Exception as e:
            print(f"    ?�️ 구조 분석 ?�류: {e}")
            return structure_info

    def optimize_view_mode(self):
        """최적??보기 모드�??�환"""
        try:
            print("      ?�� 최적 보기 모드 ?�정 �?..")

            # 리스??보기�??�환 (???�태가 ?�롤링하�?좋음)
            list_view_selectors = [
                ".list-view", ".table-view", ".board-view",
                "a[href*='listStyle=list']",
                "button[data-view='list']"
            ]

            for selector in list_view_selectors:
                try:
                    view_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if view_btn.is_displayed():
                        view_btn.click()
                        time.sleep(1)
                        print(f"        ??리스??보기�??�환: {selector}")
                        break
                except:
                    continue

            # ?�이지???�시 개수 최�???            items_per_page_selectors = [
                "select[name='listStyle']",
                ".items-per-page select",
                "select[name='pageSize']"
            ]

            for selector in items_per_page_selectors:
                try:
                    select_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    # 가????�??�택 (보통 50 ?�는 100)
                    from selenium.webdriver.support.ui import Select
                    select = Select(select_element)

                    # ?�션 �?가?????�자 찾기
                    options = select.options
                    max_value = 0
                    max_option = None

                    for option in options:
                        try:
                            value = int(option.get_attribute('value'))
                            if value > max_value:
                                max_value = value
                                max_option = option
                        except:
                            continue

                    if max_option:
                        select.select_by_value(str(max_value))
                        print(f"        ???�이지???�시 개수: {max_value}개로 ?�정")
                        time.sleep(2)
                        break

                except:
                    pass

        except Exception as e:
            print(f"      ?�️ 보기 모드 최적???�류: {e}")

    def wait_for_page_load(self):
        """?�이지 로딩 ?�료 ?��?(?�상??버전)"""
        try:
            # 1. 기본 로딩 ?��?            time.sleep(1)

            # 2. JavaScript ?�행 ?�료 ?��?            try:
                WebDriverWait(self.driver, 5).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
            except:
                pass

            # 3. Ajax ?�청 ?�료 ?��?(jQuery가 ?�는 경우)
            try:
                WebDriverWait(self.driver, 3).until(
                    lambda driver: driver.execute_script("return jQuery.active == 0") if
                    driver.execute_script("return typeof jQuery !== 'undefined'") else True
                )
            except:
                pass

            # 4. ?�정 로딩 ?�소?�이 ?�라�??�까지 ?��?            loading_indicators = [
                '.loading', '.spinner', '.ajax-loading',
                '[style*="loading"]', '.progress-bar'
            ]

            for indicator in loading_indicators:
                try:
                    WebDriverWait(self.driver, 2).until_not(
                        EC.presence_of_element_located((By.CSS_SELECTOR, indicator))
                    )
                except:
                    continue

        except Exception as e:
            pass  # 로딩 ?��??�류??무시?�고 진행

    def smart_next_page(self):
        """?�마???�음 ?�이지 ?�동"""
        try:
            # ?�양??"?�음 ?�이지" ?�턴??            next_patterns = [
                # ?�반?�인 ?�턴
                ".next", ".page-next", ".btn-next",
                "a[title*='?�음']", "a[title*='next']",

                # ?�스??기반
                "//a[contains(text(), '?�음')]",
                "//a[contains(text(), 'next')]",
                "//a[contains(text(), '>')]",

                # ?�이지 번호 기반 (?�재 ?�이지 + 1)
                ".pagination a", ".paging a", ".page-link"
            ]

            # 1. 직접?�인 "?�음" 버튼 찾기
            for pattern in next_patterns[:5]:  # 처음 5�??�턴�??�도
                try:
                    if pattern.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, pattern)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, pattern)

                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # ?�릭 가?�한지 ?�인
                            if 'disabled' not in element.get_attribute('class').lower():
                                element.click()
                                print(f"        ?�️ ?�음 ?�이지 ?�동 ?�공: {pattern}")
                                time.sleep(2)
                                return True
                except:
                    continue

            # 2. ?�이지 번호�??�동 ?�도
            try:
                # ?�재 ?�성 ?�이지 찾기
                active_selectors = [
                    ".current", ".active", ".selected",
                    ".page-current", ".page-active"
                ]

                current_page = None
                for selector in active_selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        current_page = int(element.text)
                        break
                    except:
                        continue

                if current_page:
                    # ?�음 ?�이지 번호 ?�릭 ?�도
                    next_page = current_page + 1
                    page_selectors = [
                        f"a[href*='page={next_page}']",
                        f"//a[text()='{next_page}']",
                        f".pagination a:contains('{next_page}')"
                    ]

                    for selector in page_selectors:
                        try:
                            if selector.startswith("//"):
                                element = self.driver.find_element(By.XPATH, selector)
                            else:
                                element = self.driver.find_element(By.CSS_SELECTOR, selector)

                            if element.is_displayed():
                                element.click()
                                print(f"        ?�️ ?�이지 {next_page}�??�동 ?�공")
                                time.sleep(2)
                                return True
                        except:
                            pass
            except:
                pass

            print("        ?�️ ?�음 ?�이지�?찾을 ???�음")
            return False

        except Exception as e:
            print(f"        ???�음 ?�이지 ?�동 ?�류: {e}")
            return False

    def go_to_next_page(self):
        """?�음 ?�이지�??�동"""
        try:
            return self.smart_next_page()
        except Exception as e:
            print(f"?�음 ?�이지 ?�동 ?�패: {e}")
            return False

    # =====================================================================
    # Phase 7C: 게시글 ?�세 ?�보 추출 메서??(7�?
    # =====================================================================

    def extract_title_and_url(self, element):
        """?�목�?URL 추출"""
        if not element:
            return None

        title_patterns = [
            # ?�반?�인 ?�턴
            ".article a", ".title a", ".subject a",
            "a[href*='read']", "a[href*='article']",

            # ?�이�?기반
            "td a", ".td_article a", ".td_subject a",

            # div 기반
            ".post-title a", ".board-title a",

            # ?�순 ?�턴
            "a"
        ]

        for pattern in title_patterns:
            try:
                title_element = element.find_element(By.CSS_SELECTOR, pattern)
                title = clean_text(title_element.text)
                url = title_element.get_attribute("href")

                # ?�효???�목�?URL?��? ?�인
                if title and url and len(title.strip()) > 0:
                    if 'read' in url or 'article' in url or 'cafe.naver.com' in url:
                        return {'title': title, 'url': url}

            except Exception:
                continue

        return None

    def extract_author(self, element):
        """?�성??추출"""
        if not element:
            return "?????�음"

        author_patterns = [
            ".p-nick a", ".author a", ".writer a",
            ".td_name a", ".name a", ".nickname a",
            "td:nth-child(3) a", "td:nth-child(4) a"
        ]

        for pattern in author_patterns:
            try:
                author_element = element.find_element(By.CSS_SELECTOR, pattern)
                author = clean_text(author_element.text)
                if author and len(author.strip()) > 0:
                    return author
            except Exception:
                continue

        return "?????�음"

    def extract_date(self, element):
        """?�성??추출"""
        if not element:
            return "?????�음"

        date_patterns = [
            ".td_date", ".date", ".time", ".created",
            "td:last-child", "td:nth-last-child(2)",
            "td:nth-child(5)", "td:nth-child(6)"
        ]

        for pattern in date_patterns:
            try:
                date_element = element.find_element(By.CSS_SELECTOR, pattern)
                date = clean_text(date_element.text)
                if date and len(date.strip()) > 0:
                    # ?�짜 ?�식?��? 간단???�인
                    if any(char.isdigit() for char in date):
                        return date
            except Exception:
                continue

        return "?????�음"

    def extract_views(self, element):
        """조회??추출"""
        if not element:
            return "0"

        view_patterns = [
            ".td_view", ".view", ".views", ".hit",
            "td:nth-last-child(1)", "td:nth-last-child(2)"
        ]

        for pattern in view_patterns:
            try:
                view_element = element.find_element(By.CSS_SELECTOR, pattern)
                views = clean_text(view_element.text)
                if views and views.isdigit():
                    return views
            except Exception:
                continue

        return "0"

    def extract_likes(self, element):
        """추천??추출"""
        if not element:
            return "0"

        like_patterns = [
            ".td_good", ".like", ".likes", ".recommend",
            ".good", ".thumb"
        ]

        for pattern in like_patterns:
            try:
                like_element = element.find_element(By.CSS_SELECTOR, pattern)
                likes = clean_text(like_element.text)
                if likes and likes.isdigit():
                    return likes
            except Exception:
                continue

        return "0"

    def debug_page_structure(self):
        """?�이지 구조 ?�버�?""
        try:
            print("      ?�� ?�이지 구조 ?�버�?�?..")

            # ?�재 URL�??�목
            current_url = self.safe_get_current_url()
            page_title = self.safe_get_title()
            print(f"        URL: {current_url}")
            print(f"        ?�목: {page_title}")

            # 주요 ?�소??개수 ?�인
            elements_info = {
                "?�이�?: len(self.safe_find_elements(By.TAG_NAME, "table")),
                "??tr)": len(self.safe_find_elements(By.TAG_NAME, "tr")),
                "링크(a)": len(self.safe_find_elements(By.TAG_NAME, "a")),
                "리스??li)": len(self.safe_find_elements(By.TAG_NAME, "li")),
                "div": len(self.safe_find_elements(By.TAG_NAME, "div"))
            }

            for name, count in elements_info.items():
                print(f"        {name}: {count}�?)

            # 링크 ?�플 ?�인
            links = self.safe_find_elements(By.CSS_SELECTOR, "a[href]")[:10]
            print(f"        링크 ?�플 (처음 10�?:")
            for i, link in enumerate(links):
                try:
                    text = link.text.strip()[:30] if link.text else "(?�스???�음)"
                    href = link.get_attribute("href")[:50] if link.get_attribute("href") else "(href ?�음)"
                    print(f"          {i+1}. {text} -> {href}")
                except Exception:
                    print(f"          {i+1}. (?�류)")

        except Exception as e:
            print(f"        ???�버�??�류: {e}")

    def save_to_excel(self, filename=None):
        """CafeDataExporter�??�임?�여 ?��? ?�??""
        try:
            if hasattr(self, 'posts_data') and self.posts_data:
                return CafeDataExporter.save_all(self.posts_data, filename)
            else:
                print("?�️ ?�?�할 ?�이?��? ?�습?�다.")
                return False
        except Exception as e:
            print(f"???��? ?�???�류: {e}")
            return False

    # =====================================================================
    # Phase 7D: 검??�??�워??처리 메서??(10�?
    # =====================================================================

    def check_keyword_match(self, title, content, keyword):
        """?�워??매칭 ?�인 (?�상??버전)"""
        try:
            if not keyword or not title:
                return False

            # ?�스???�규??            title_clean = clean_text(title).lower()
            keyword_clean = keyword.lower().strip()

            # ?�버�??�보 (가?�씩�?출력)
            if random.randint(1, 10) == 1:  # 10% ?�률�??�버�?출력
                print(f"        ?�� ?�워??매칭 ?�버�?")
                print(f"          ?�목: '{title_clean[:50]}...'")
                print(f"          ?�워?? '{keyword_clean}'")

            # 1. ?�확???�워??매칭
            if keyword_clean in title_clean:
                return True

            # 2. 부�?매칭 (공백 ?�거)
            title_no_space = title_clean.replace(" ", "")
            keyword_no_space = keyword_clean.replace(" ", "")
            if keyword_no_space in title_no_space:
                return True

            # 3. ?�워??변???�인
            if hasattr(Config, 'KEYWORD_VARIATIONS') and Config.KEYWORD_VARIATIONS:
                variations = self.get_keyword_variations(keyword)
                for variation in variations:
                    variation_clean = variation.lower()
                    if variation_clean in title_clean:
                        return True

            # 4. ?�용?�서???�인 (?�는 경우)
            if content:
                content_clean = clean_text(content).lower()
                if keyword_clean in content_clean:
                    return True

            return False

        except Exception as e:
            print(f"        ???�워??매칭 ?�류: {e}")
            return False

    def get_keyword_variations(self, keyword):
        """?�워??변??�??�어 ?�성"""
        variations = []

        try:
            # 기본 변??            variations.append(keyword)
            variations.append(keyword.replace(' ', ''))

            # 공기??관???�어 �?변??            keyword_mappings = {
                '?�국?�력공사': ['?�전', 'kepco', '?�력공사'],
                '?�국?�자?�공??: ['k-water', 'kwater', '?�자?�공??],
                '?�국?��?주택공사': ['lh공사', 'lh', '?��?주택공사'],
                '?�천�?��공항공사': ['공항공사', '?�천공항'],
                '?�국가?�공??: ['가?�공??, 'kogas'],
                '?�국?�유공사': ['?�유공사', 'knoc'],
                '?�국광물?�원공사': ['kores', '광물?�원공사'],
                '?�국철도공사': ['코레??, 'korail', '철도공사'],
                '?�국?�로공사': ['?�로공사'],
                '공기??: ['공공기�?', '준?��?기�?'],
                'ncs': ['�??직무?�력?��?'],
                '면접': ['면접?�기', '면접경험'],
                '?�격': ['?�격?�기', '?�격?�기'],
                '채용': ['채용공고', '채용?�보'],
                '?�소??: ['?�기?�개??],
                '?�기': ['?�기?�험', '?�기준�?]
            }

            # ?�워??매핑 ?�인
            keyword_lower = keyword.lower()
            for main_keyword, aliases in keyword_mappings.items():
                if keyword_lower in main_keyword.lower() or main_keyword.lower() in keyword_lower:
                    variations.extend(aliases)
                    variations.append(main_keyword.lower())

                for alias in aliases:
                    if keyword_lower in alias.lower() or alias.lower() in keyword_lower:
                        variations.append(main_keyword.lower())
                        variations.extend([a for a in aliases if a != alias])

            # 중복 ?�거
            variations = list(set(variations))

        except Exception as e:
            print(f"        ?�워??변???�성 ?�류: {e}")

        return variations

    def crawl_cafe(self, cafe_url, keywords=None):
        """메인 ?�롤�?로직 (1000�?게시글 ?�집, ?�용 �??��? ?�함)"""
        print(f"\n?�� ?�이�?카페 고급 ?�롤�??�작!")
        print(f"?�� ?�??카페: {cafe_url}")
        print(f"?�� ?�집 ?�워?? {keywords}")
        print(f"?�� 목표 ?�집?? 최�? {Config.MAX_TOTAL_POSTS}�?게시글")
        print(f"?�� ?�용 ?�집: {'ON' if Config.EXTRACT_FULL_CONTENT else 'OFF'}")
        print(f"?�� ?��? ?�집: {'ON' if Config.EXTRACT_COMMENTS else 'OFF'}")
        print("=" * 70)

        all_posts = []
        total_collected = 0

        try:
            print(f"?�� 카페 ?�속 �?..")
            self.safe_driver_get(cafe_url)
            safe_wait(self.driver, 3)

            # 로그???�인
            if not self.driver:
                print("???�라?�버가 초기?�되지 ?�았?�니??")
                return []

            # ?�워?�별 검???�행
            if keywords:
                for i, keyword in enumerate(keywords, 1):
                    print(f"\n?�� ?�워??{i}/{len(keywords)}: '{keyword}' 검???�작")
                    print("-" * 50)

                    # ?�워??검??게시글 ?�집
                    keyword_posts = self.search_and_collect_posts(keyword)

                    if keyword_posts:
                        print(f"??'{keyword}' 검??결과: {len(keyword_posts)}�?게시글 ?�집")
                        all_posts.extend(keyword_posts)
                        total_collected += len(keyword_posts)

                        # 목표 ?�집???�달 ?�인
                        if total_collected >= Config.MAX_TOTAL_POSTS:
                            print(f"?�� 목표 ?�집??{Config.MAX_TOTAL_POSTS}�??�성!")
                            break
                    else:
                        print(f"?�️ '{keyword}' 검??결과 ?�음")
            else:
                # ?�워???�이 ?�체 최신 게시글 ?�집
                print(f"?�� ?�체 최신 게시글 ?�집 모드")
                all_posts = self.collect_recent_posts()
                total_collected = len(all_posts)

            print(f"\n?�� 최종 ?�집 결과:")
            print(f"   ?�� �?게시글 ?? {total_collected}�?)
            print(f"   ?�� ?�용 ?�함: {sum(1 for post in all_posts if post.get('full_content'))}")
            print(f"   ?�� ?��? ?�함: {sum(1 for post in all_posts if post.get('comments'))}")
            print(f"   ?���??��?지 ?�함: {sum(len(post.get('images', [])) for post in all_posts)}")

            # ?�집???�이???�??            self.posts_data = all_posts

            return all_posts

        except Exception as e:
            print(f"???�롤�?�??�류 발생: {e}")
            return all_posts

    def search_and_collect_posts(self, keyword):
        """?�워?�로 검?�하??게시글 ?�집 (고급 ?�중 검???�용)"""
        try:
            print(f"?�� 고급 검???�작: '{keyword}'")

            # 고급 ?�중 검???�략 ?�용
            if hasattr(Config, 'MULTI_SCOPE_SEARCH') and Config.MULTI_SCOPE_SEARCH:
                print("    ?? 고급 ?�중 검??모드 ?�성??")
                posts, metadata = self.advanced_multi_search(keyword)

                if posts:
                    print(f"    ?�� 고급 검???�공: {len(posts)}�?게시글 ?�집")
                    print(f"    ?�� ?�용???�략: {', '.join(metadata.get('strategies_used', []))}")

                    # ?�세 ?�보 ?�집 (?�용 �??��?)
                    if Config.EXTRACT_FULL_CONTENT or Config.EXTRACT_COMMENTS:
                        enhanced_posts = self.enhance_posts_with_details(posts, keyword)
                        return enhanced_posts
                    else:
                        # 기본 ?�보??메�??�이??추�?
                        from datetime import datetime
                        for post in posts:
                            post['keyword'] = keyword
                            post['collection_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            post['search_metadata'] = metadata

                        return posts[:Config.MAX_TOTAL_POSTS]

                else:
                    print(f"    ?�️ 고급 검??결과 ?�음 - 기본 검?�으�??�환")
                    return self.fallback_basic_search(keyword)

            else:
                # 기본 검??방식 ?�용
                print(f"    ?�� 기본 검??모드")
                return self.fallback_basic_search(keyword)

        except Exception as e:
            print(f"    ???�워??검??�??�류: {e}")
            return self.fallback_basic_search(keyword)

    def enhance_posts_with_details(self, posts, keyword):
        """게시글 ?�세 ?�보 강화 (?�용, ?��?, ?��?지 ??"""
        try:
            print(f"    ?�� ?�세 ?�보 ?�집 �?.. (�?{len(posts)}�?")
            enhanced_posts = []

            for i, post in enumerate(posts[:Config.MAX_TOTAL_POSTS], 1):
                try:
                    print(f"      ?�� 게시글 {i}/{min(len(posts), Config.MAX_TOTAL_POSTS)} 처리 �?..")

                    # ?�세 ?�용 ?�집
                    if Config.EXTRACT_FULL_CONTENT or Config.EXTRACT_COMMENTS:
                        post_url = post.get('url', '')
                        if post_url:
                            detail_data = self.get_post_content(post_url)

                            # ?�세 ?�보 ?�합
                            if detail_data.get('content'):
                                post['full_content'] = detail_data['content']

                            if detail_data.get('comments'):
                                post['comments'] = detail_data['comments']
                                post['comment_count'] = len(detail_data['comments'])

                            if detail_data.get('images'):
                                post['images'] = detail_data['images']

                            if detail_data.get('attachments'):
                                post['attachments'] = detail_data['attachments']

                    # 추�? 메�??�이??                    from datetime import datetime
                    post['keyword'] = keyword
                    post['collection_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    post['enhanced'] = True

                    enhanced_posts.append(post)

                    # 진행�??�시
                    if i % 10 == 0:
                        print(f"      ?�� 진행�? {i}/{min(len(posts), Config.MAX_TOTAL_POSTS)} ({i/min(len(posts), Config.MAX_TOTAL_POSTS)*100:.1f}%)")

                except Exception as e:
                    print(f"      ??게시글 {i} 처리 ?�류: {e}")
                    # 기본 ?�보?�도 ?��?
                    from datetime import datetime
                    post['keyword'] = keyword
                    post['collection_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    post['enhanced'] = False
                    enhanced_posts.append(post)
                    continue

            print(f"    ???�세 ?�보 ?�집 ?�료: {len(enhanced_posts)}�?)
            return enhanced_posts

        except Exception as e:
            print(f"    ???�세 ?�보 ?�집 ?�류: {e}")
            return posts

    def fallback_basic_search(self, keyword):
        """기본 검??방식 (백업?? - ?�세 ?�보 ?�함"""
        try:
            print(f"    ?�� 기본 검??방식?�로 '{keyword}' 검??..")

            # 기존 search_posts 메서???�용
            posts = self.search_posts(keyword, max_pages=Config.MAX_PAGES)

            if posts:
                print(f"    ??기본 검???�료: {len(posts)}�?게시글 ?�집")

                # ?�세 ?�보 ?�집 (?�용 �??��?)
                if Config.EXTRACT_FULL_CONTENT or Config.EXTRACT_COMMENTS:
                    print(f"    ?�� ?�세 ?�보 ?�집 �?.. (�?{len(posts)}�?")
                    enhanced_posts = self.enhance_posts_with_details(posts, keyword)
                    return enhanced_posts[:Config.MAX_TOTAL_POSTS]
                else:
                    # 기본 ?�보�??�집
                    from datetime import datetime
                    for post in posts:
                        post['keyword'] = keyword
                        post['collection_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        post['search_method'] = 'basic'

                    return posts[:Config.MAX_TOTAL_POSTS]

            else:
                print(f"    ?�️ '{keyword}' 기본 검??결과 ?�음")
                return []

        except Exception as e:
            print(f"    ??기본 검???�류: {e}")
            return []

    def navigate_to_search_url(self, search_url):
        """검??URL�??�동"""
        try:
            if not search_url:
                return False

            self.safe_driver_get(search_url)
            time.sleep(2)

            # ?�이지 로딩 ?��?            self.wait_for_page_load()

            # iframe 처리
            if self.handle_search_iframe():
                return True

            return True

        except Exception as e:
            print(f"검??URL ?�동 ?�류: {e}")
            return False

    def collect_recent_posts(self):
        """최신 게시글 ?�집 (?�워???�이)"""
        posts = []
        current_page = 1

        try:
            print(f"?�� 최신 게시글 ?�집 ?�작...")

            # 카페 메인 ?�이지???�체글 ?�이지�??�동
            self.navigate_to_all_posts()

            while current_page <= Config.MAX_PAGES and len(posts) < Config.MAX_TOTAL_POSTS:
                print(f"    ?�� ?�이지 {current_page} ?�집 �?..")

                page_posts = self.extract_posts()

                if not page_posts:
                    print(f"    ?�️ ?�이지 {current_page}?�서 게시글??찾을 ???�습?�다.")
                    break

                # ?�세 ?�보 ?�집 (?�요??
                if Config.EXTRACT_FULL_CONTENT or Config.EXTRACT_COMMENTS:
                    detailed_posts = self.enhance_posts_with_details(page_posts, keyword=None)
                    posts.extend(detailed_posts)
                else:
                    posts.extend(page_posts)

                print(f"    ???�이지 {current_page}: {len(page_posts)}�?게시글 ?�집 (�?{len(posts)}�?")

                # ?�음 ?�이지�??�동
                if not self.go_to_next_page():
                    print(f"    ?�️ 마�?�??�이지 ?�달")
                    break

                current_page += 1

                # 목표 ?�집???�인
                if len(posts) >= Config.MAX_TOTAL_POSTS:
                    print(f"    ?�� 목표 ?�집??{Config.MAX_TOTAL_POSTS}�??�성!")
                    break

            return posts[:Config.MAX_TOTAL_POSTS]

        except Exception as e:
            print(f"??최신 게시글 ?�집 �??�류: {e}")
            return posts

    def extract_posts(self):
        """?�재 ?�이지?�서 게시글 목록 추출"""
        try:
            posts = []

            # 기존 게시글 추출 로직 ?�용
            post_elements = self.find_post_elements()

            if post_elements:
                print(f"      ?�� {len(post_elements)}�?게시글 ?�소 발견")

                for i, element in enumerate(post_elements):
                    try:
                        post_info = self.extract_single_post_info(element, i)
                        if post_info:
                            posts.append(post_info)

                        # ?�집 ?�한 ?�인
                        if len(posts) >= Config.MAX_POSTS_PER_PAGE:
                            break

                    except Exception as e:
                        continue

            return posts

        except Exception as e:
            print(f"      ??게시글 추출 ?�류: {e}")
            return []

    def advanced_multi_search(self, keyword):
        """?�� 고급 ?�중 검???�략 - 모든 검???�션 ?�용"""
        try:
            print(f"?? 고급 ?�중 검???�작: '{keyword}'")
            all_posts = []
            search_metadata = {
                'keyword': keyword,
                'strategies_used': [],
                'results_per_strategy': {},
                'total_unique_posts': 0
            }

            # ?�중 검??범위 ?�용
            if Config.MULTI_SCOPE_SEARCH:
                print("?�� ?�중 검??범위 ?�략 ?�행...")
                for scope in Config.SEARCH_SCOPES_TO_USE:
                    posts = self.search_with_scope(keyword, scope)
                    if posts:
                        all_posts.extend(posts)
                        search_metadata['strategies_used'].append(f'scope_{scope}')
                        search_metadata['results_per_strategy'][f'scope_{scope}'] = len(posts)
                        print(f"   ??{scope} 범위: {len(posts)}�??�집")

            # ?�중 ?�렬 방식 ?�용
            if Config.MULTI_SORT_SEARCH:
                print("?�� ?�중 ?�렬 방식 ?�략 ?�행...")
                for sort_method in Config.SORT_METHODS_TO_USE:
                    posts = self.search_with_sort(keyword, sort_method)
                    if posts:
                        all_posts.extend(posts)
                        search_metadata['strategies_used'].append(f'sort_{sort_method}')
                        search_metadata['results_per_strategy'][f'sort_{sort_method}'] = len(posts)
                        print(f"   ??{sort_method} ?�렬: {len(posts)}�??�집")

            # ?�중 기간 검??(?�택??
            if Config.MULTI_DATE_SEARCH:
                print("?�� ?�중 기간 ?�터 ?�략 ?�행...")
                for date_filter in Config.DATE_FILTERS_TO_USE:
                    posts = self.search_with_date_filter(keyword, date_filter)
                    if posts:
                        all_posts.extend(posts)
                        search_metadata['strategies_used'].append(f'date_{date_filter}')
                        search_metadata['results_per_strategy'][f'date_{date_filter}'] = len(posts)
                        print(f"   ??{date_filter} 기간: {len(posts)}�??�집")

            # 중복 ?�거
            if Config.REMOVE_DUPLICATES and all_posts:
                unique_posts = self.remove_duplicate_posts(all_posts)
                removed_count = len(all_posts) - len(unique_posts)
                print(f"?�� 중복 ?�거: {removed_count}�??�거, {len(unique_posts)}�??�음")
                all_posts = unique_posts

            # ?�질 ?�터 ?�용
            if Config.QUALITY_FILTER and all_posts:
                filtered_posts = self.apply_quality_filter(all_posts)
                filtered_count = len(all_posts) - len(filtered_posts)
                print(f"?�� ?�질 ?�터: {filtered_count}�??�터�? {len(filtered_posts)}�??�음")
                all_posts = filtered_posts

            search_metadata['total_unique_posts'] = len(all_posts)
            print(f"?�� 고급 ?�중 검???�료: �?{len(all_posts)}�?고품�?게시글 ?�집")

            return all_posts, search_metadata

        except Exception as e:
            print(f"??고급 ?�중 검???�류: {e}")
            return [], {}

    # =====================================================================
    # Phase 7E: 백업 �??�비게이??메서??(8�?
    # =====================================================================

    def fallback_keyword_search(self, keyword):
        """검???�패??백업 방식: ?�반 게시글 ?�터�?""
        try:
            print(f"    ?�� 백업 검??방식 ?�작: '{keyword}'")

            # ?�체글 ?�이지�??�동
            if not self.navigate_to_all_posts():
                print("    ???�체글 ?�이지 ?�동 ?�패")
                return []

            collected_posts = []
            current_page = 1
            max_pages = min(Config.MAX_PAGES, 10)

            while current_page <= max_pages and len(collected_posts) < Config.MAX_TOTAL_POSTS:
                print(f"      ?�� 백업 ?�이지 {current_page} 처리 �?..")

                # ?�재 ?�이지??게시글 추출
                page_posts = self.extract_posts()

                if not page_posts:
                    print("      ??게시글 추출 ?�패")
                    break

                # ?�워??매칭?�는 게시글 ?�터�?                matched_posts = []
                for post in page_posts:
                    if self.check_keyword_match(post.get('title', ''), post.get('content', ''), keyword):
                        matched_posts.append(post)
                        collected_posts.append(post)

                        if len(collected_posts) >= Config.MAX_TOTAL_POSTS:
                            break

                print(f"      ???�이지 {current_page}: {len(matched_posts)}�?매칭")

                # ?�음 ?�이지�??�동
                if not self.go_to_next_page():
                    print("      ???�음 ?�이지 ?�동 ?�패")
                    break

                current_page += 1
                self.adaptive_delay()

            print(f"    ??백업 검???�료: {len(collected_posts)}�??�집")
            return collected_posts

        except Exception as e:
            print(f"    ??백업 검???�류: {e}")
            return []

    def perform_advanced_search(self, keyword):
        """고급 검???�행 (기존 search_posts 메서?��? ?�계)"""
        try:
            print(f"    ?�� 고급 검???�작: '{keyword}'")

            # 기존 search_posts 메서???�용
            posts = self.search_posts(keyword, max_pages=Config.MAX_PAGES)

            if posts:
                print(f"    ??고급 검???�공: {len(posts)}�?게시글 발견")
                return posts
            else:
                print(f"    ?�️ 고급 검??결과 ?�음")
                return []

        except Exception as e:
            print(f"    ??고급 검???�류: {e}")
            return []

    def extract_search_result_posts_simple(self):
        """검??결과 ?�이지?�서 게시글 추출 (간단 버전)"""
        try:
            # 기존 extract_posts 메서???�용
            posts = self.extract_posts()

            if posts:
                print(f"      ?�� 검??결과: {len(posts)}�?게시글 추출")
            else:
                print("      ?�️ 검??결과 ?�음")

            return posts

        except Exception as e:
            print(f"      ??검??결과 추출 ?�류: {e}")
            return []

    def extract_search_results_with_metadata(self, keyword, strategy):
        """검??결과 추출 (메�??�이???�함)"""
        try:
            from datetime import datetime

            posts = []

            # 기존 추출 메서???�용
            page_posts = self.extract_search_result_posts(keyword)

            if page_posts:
                for post in page_posts:
                    if isinstance(post, dict):
                        # 메�??�이??추�?
                        post['search_strategy'] = strategy
                        post['search_keyword'] = keyword
                        post['collection_timestamp'] = datetime.now().isoformat()

                        # ?�질 검??                        if self.passes_quality_check(post):
                            posts.append(post)
                    else:
                        # 기본 ?�셔?�리 ?�태�?변??                        post_dict = {
                            'title': str(post) if post else '',
                            'search_strategy': strategy,
                            'search_keyword': keyword,
                            'collection_timestamp': datetime.now().isoformat()
                        }
                        if self.passes_quality_check(post_dict):
                            posts.append(post_dict)

            return posts

        except Exception as e:
            print(f"         ??검??결과 추출 ?�류: {e}")
            return []

    def remove_duplicate_posts(self, posts):
        """중복 게시글 ?�거"""
        try:
            if not posts:
                return posts

            seen_urls = set()
            seen_titles = set()
            unique_posts = []

            for post in posts:
                if not isinstance(post, dict):
                    continue

                post_url = post.get('url', '')
                post_title = post.get('title', '')

                # URL 기반 중복 ?�거
                if post_url and post_url not in seen_urls:
                    seen_urls.add(post_url)
                    unique_posts.append(post)
                # ?�목 기반 중복 ?�거 (URL???�거???�른 경우)
                elif post_title and post_title not in seen_titles:
                    seen_titles.add(post_title)
                    unique_posts.append(post)

            return unique_posts

        except Exception as e:
            print(f"??중복 ?�거 ?�류: {e}")
            return posts

    def apply_quality_filter(self, posts):
        """?�질 ?�터 ?�용"""
        try:
            if not posts:
                return posts

            filtered_posts = []

            for post in posts:
                if isinstance(post, dict) and self.passes_quality_check(post):
                    filtered_posts.append(post)

            return filtered_posts

        except Exception as e:
            print(f"???�질 ?�터 ?�류: {e}")
            return posts

    def passes_quality_check(self, post):
        """게시글 ?�질 검??""
        try:
            if not isinstance(post, dict):
                return False

            title = post.get('title', '')
            content = post.get('content', '')

            # 최소 길이 검??            if len(title) < Config.MIN_TITLE_LENGTH:
                return False

            if content and len(content) < Config.MIN_CONTENT_LENGTH:
                return False

            # 공�??�항 ?�외
            if Config.EXCLUDE_NOTICE_POSTS:
                notice_keywords = ['공�?', 'notice', '?�림', '?�내', 'Notice']
                if any(keyword in title.lower() for keyword in notice_keywords):
                    return False

            # 광고??게시글 ?�외
            if Config.EXCLUDE_AD_POSTS:
                ad_keywords = ['광고', '?�보', '?�매', '구매', '마�???, 'AD', '?�벤??]
                if any(keyword in title.lower() for keyword in ad_keywords):
                    return False

            return True

        except Exception as e:
            print(f"???�질 검???�류: {e}")
            return True  # ?�류??기본?�으�??�과

    def extract_posts_from_page(self, keyword=None):
        """?�이지?�서 게시글 추출 (?�워??매칭 ?�함)"""
        try:
            posts = []

            # 기존 find_post_elements ?�용
            post_elements = self.find_post_elements()

            if not post_elements:
                print("      ?�️ 게시글 ?�소�?찾을 ???�음")
                return posts

            print(f"      ?�� {len(post_elements)}�?게시글 ?�소 발견")

            for i, element in enumerate(post_elements):
                try:
                    post_info = self.extract_single_post_info(element, i)
                    if post_info and isinstance(post_info, dict):
                        if keyword:
                            title = post_info.get('title', '')
                            content = post_info.get('content', '')

                            # ?�워??매칭 ?�인
                            if self.check_keyword_match(title, content, keyword):
                                post_info['keyword_matched'] = keyword
                                posts.append(post_info)
                        else:
                            posts.append(post_info)

                    # ?�집 ?�한 ?�인
                    if len(posts) >= Config.MAX_POSTS_PER_PAGE:
                        break

                except Exception as e:
                    print(f"      ??게시글 {i+1} 추출 ?�류: {e}")
                    continue

            print(f"      ??최종 추출: {len(posts)}�?게시글")
            return posts

        except Exception as e:
            print(f"      ???�이지 게시글 추출 ?�류: {e}")
            return []

    # =====================================================================
    # Phase 7F: 고급 검??�??�터�?메서??(10�?
    # =====================================================================

    def verify_search_results_page_enhanced(self, keyword):
        """검??결과 ?�이지 ?�인 (강화??버전)"""
        try:
            if not self.driver:
                return False

            current_url = self.safe_get_current_url()
            page_source = self.safe_get_page_source()

            print(f"    ?�� 검??결과 ?�이지 검�?�?..")
            print(f"      URL: {current_url[:100]}...")

            # 1. URL ?�턴 ?�인
            url_indicators = 0
            if 'ArticleSearchList' in current_url:
                url_indicators += 1
                print(f"      ??URL??ArticleSearchList ?�함")
            if 'search.query' in current_url:
                url_indicators += 1
                print(f"      ??URL??search.query ?�함")
            if keyword.lower() in current_url.lower():
                url_indicators += 1
                print(f"      ??URL???�워???�함")

            # 2. ?�이지 ?�용 ?�인
            content_indicators = 0
            search_keywords = ['검?�결�?, '검??, '�?, '�?, '검?�조�?, 'ArticleSearchList']
            for search_keyword in search_keywords:
                if search_keyword in page_source:
                    content_indicators += 1
                    print(f"      ???�이지??'{search_keyword}' ?�함")

            # 3. ?�제 게시글 링크 ?�인 (메뉴 링크?� 구분)
            post_links = self.safe_find_elements(By.CSS_SELECTOR, "a[href*='read.nhn'], a[href*='ArticleRead'], a[href*='articleid']")
            menu_links = self.safe_find_elements(By.CSS_SELECTOR, "a[href*='ArticleList.nhn'], a[href*='menuid']")

            print(f"      ?�� 게시글 링크: {len(post_links)}�? 메뉴 링크: {len(menu_links)}�?)

            # 4. ?�이�?구조 ?�인
            tables = self.safe_find_elements(By.TAG_NAME, "table")
            board_tables = []
            for table in tables:
                table_class = table.get_attribute('class') or ''
                if 'board' in table_class.lower() or 'article' in table_class.lower():
                    board_tables.append(table)

            print(f"      ?���??�체 ?�이�? {len(tables)}�? 게시???�이�? {len(board_tables)}�?)

            # 5. 종합 ?�단
            total_score = url_indicators + content_indicators
            is_valid_search_page = (
                total_score >= 2 and  # 기본 지??만족
                (len(post_links) > 0 or len(board_tables) > 0) and  # ?�제 컨텐�?존재
                len(post_links) >= len(menu_links)  # 게시글 링크가 메뉴 링크보다 많거??같음
            )

            print(f"      ?�� 검�??�수: URL지??{url_indicators}, ?�용지??{content_indicators}, 총점={total_score}")
            print(f"      ?�� 검??결과 ?�이지 ?�정: {'???�효' if is_valid_search_page else '??무효'}")

            return is_valid_search_page

        except Exception as e:
            print(f"    ??검??결과 ?�이지 검�??�패: {e}")
            return False

    def setup_advanced_search_options(self):
        """고급 검???�션 ?�정"""
        try:
            if not self.driver:
                return

            from selenium.webdriver.support.select import Select

            # 검???�션???�정
            search_options = [
                ("select[name='searchBy']", "1"),    # ?�목+?�용
                ("select[name='sortBy']", "date"),    # ?�짜??                ("select[name='option']", "0"),       # 기본 ?�션
            ]

            options_set = 0
            for selector, value in search_options:
                try:
                    elements = self.safe_find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            Select(element).select_by_value(value)
                            options_set += 1
                            break
                except Exception as e:
                    print(f"      ?�️ ?�션 ?�정 ?�패 ({selector}): {e}")

            print(f"    ?�️ 고급 검???�션 ?�정 ?�료: {options_set}�?)

        except Exception as e:
            print(f"    ?�️ 고급 검???�션 ?�정 �??�류: {e}")

    def use_cafe_search_interface(self, keyword):
        """카페 검???�터?�이???�용 (?�상??버전)"""
        try:
            if not self.driver:
                return False

            # 1. 검?�박??찾기 (?�장???�턴)
            search_selectors = [
                "input[name='query']", "input[name='search']", "input[name='keyword']",
                "input[name='searchKeyword']", "input[id='searchKeyword']",
                "input[class*='search_input']", "input[class*='searchInput']",
                "input[class*='cafe_search']", "#cafe_main input[type='text']",
                ".search_area input[type='text']", "input[placeholder*='검??]"
            ]

            search_input = None
            print(f"    ?�� {len(search_selectors)}�?검?�박???�턴?�로 ?�색...")

            for selector in search_selectors:
                try:
                    elements = self.safe_find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            size = element.size
                            if size['width'] > 50 and size['height'] > 15:
                                search_input = element
                                print(f"    ??검?�박??발견! '{selector}' ({size['width']}x{size['height']})")
                                break
                    if search_input:
                        break
                except Exception:
                    continue

            if not search_input:
                print("    ??검?�박?��? 찾을 ???�습?�다")
                return False

            # 2. 검?�어 ?�력
            print(f"    ?�️ 검?�어 '{keyword}' ?�력 �?..")
            search_input.clear()
            self.adaptive_delay(0.5)
            search_input.send_keys(keyword)
            self.adaptive_delay(1)

            # 3. 검???�행
            # 방법 1: ?�터???�력
            try:
                print("    ???�터?�로 검???�행")
                from selenium.webdriver.common.keys import Keys
                search_input.send_keys(Keys.RETURN)
                self.adaptive_delay(3)
                if self.verify_search_results_page(keyword):
                    return True
            except Exception as e:
                print(f"    ???�터??검???�패: {e}")

            # 방법 2: 검??버튼 ?�릭
            search_btn_selectors = [
                "button[type='submit']", ".search_btn", ".btn-search",
                "button[class*='search']", "a[onclick*='search']"
            ]
            for btn_selector in search_btn_selectors:
                try:
                    elements = self.safe_find_elements(By.CSS_SELECTOR, btn_selector)
                    for search_btn in elements:
                        if search_btn.is_displayed() and search_btn.is_enabled():
                            print(f"    ?�� 검??버튼 ?�릭: {btn_selector}")
                            self.safe_execute_script("arguments[0].click();", search_btn)
                            self.adaptive_delay(3)
                            if self.verify_search_results_page(keyword):
                                return True
                except Exception:
                    continue

            return False

        except Exception as e:
            print(f"    ??검???�터?�이???�용 ?�패: {e}")
            return False

    def verify_search_results_page(self, keyword):
        """검??결과 ?�이지 ?�인"""
        try:
            if not self.driver:
                return False

            # 검??결과 ?�이지 ?�인???�한 ?�러 지?�들
            indicators = [
                # URL ?�턴 ?�인
                lambda: 'search' in self.safe_get_current_url().lower(),
                lambda: 'query' in self.safe_get_current_url().lower(),
                lambda: keyword.lower() in self.safe_get_current_url().lower(),

                # ?�이지 ?�소 ?�인
                lambda: len(self.safe_find_elements(By.CSS_SELECTOR, ".search-result")) > 0,
                lambda: len(self.safe_find_elements(By.CSS_SELECTOR, ".article-list")) > 0,
                lambda: len(self.safe_find_elements(By.CSS_SELECTOR, "[class*='search']")) > 0,

                # ?�스???�용 ?�인
                lambda: '검?�결�? in self.safe_get_page_source(),
                lambda: '검?? in self.safe_get_page_source(),
                lambda: keyword in self.safe_get_page_source(),
            ]

            positive_indicators = 0
            for indicator in indicators:
                try:
                    if indicator():
                        positive_indicators += 1
                except:
                    continue

            # ?�반 ?�상??지?��? 만족?�면 검??결과 ?�이지�??�단
            is_search_page = positive_indicators >= len(indicators) // 2

            print(f"    ?�� 검??결과 검�? {positive_indicators}/{len(indicators)} 지??만족 = {'???�효' if is_search_page else '??무효'}")
            return is_search_page

        except Exception as e:
            print(f"    ??검??결과 ?�이지 ?�인 ?�류: {e}")
            return False

    def search_with_sort(self, keyword, sort_method):
        """?�정 ?�렬 방식?�로 검??""
        try:
            print(f"      ?�� {sort_method} ?�렬 검??�?..")

            search_by = Config.SEARCH_SCOPE_OPTIONS.get(Config.DEFAULT_SEARCH_SCOPE, 1)
            sort_by = Config.SORT_OPTIONS.get(sort_method, 'date')

            # 검??URL 구성
            search_url = self.build_advanced_search_url(
                keyword=keyword,
                search_by=search_by,
                sort_by=sort_by,
                date_filter=Config.DEFAULT_DATE_FILTER,
                media_filter=Config.DEFAULT_MEDIA_FILTER
            )

            if not search_url:
                return []

            # 검???�행
            if self.navigate_to_search_url(search_url):
                posts = self.extract_search_results_with_metadata(keyword, sort_method)
                return posts

            return []

        except Exception as e:
            print(f"      ??{sort_method} ?�렬 검???�류: {e}")
            return []

    def search_with_date_filter(self, keyword, date_filter):
        """?�정 기간 ?�터�?검??""
        try:
            print(f"      ?�� {date_filter} 기간 검??�?..")

            search_by = Config.SEARCH_SCOPE_OPTIONS.get(Config.DEFAULT_SEARCH_SCOPE, 1)
            sort_by = Config.SORT_OPTIONS.get(Config.DEFAULT_SORT_METHOD, 'date')
            date_value = Config.DATE_FILTER_OPTIONS.get(date_filter, 'all')

            # 검??URL 구성
            search_url = self.build_advanced_search_url(
                keyword=keyword,
                search_by=search_by,
                sort_by=sort_by,
                date_filter=date_value,
                media_filter=Config.DEFAULT_MEDIA_FILTER
            )

            if not search_url:
                return []

            # 검???�행
            if self.navigate_to_search_url(search_url):
                posts = self.extract_search_results_with_metadata(keyword, date_filter)
                return posts

            return []

        except Exception as e:
            print(f"      ??{date_filter} 기간 검???�류: {e}")
            return []

    def build_advanced_search_url(self, keyword, search_by=1, sort_by='date',
                                 date_filter='all', media_filter='all',
                                 include_words='', exclude_words='', exact_phrase=''):
        """고급 검??URL 구성"""
        try:
            import urllib.parse

            # ?�워???�코??            encoded_keyword = urllib.parse.quote(keyword)
            encoded_include = urllib.parse.quote(include_words) if include_words else ''
            encoded_exclude = urllib.parse.quote(exclude_words) if exclude_words else ''
            encoded_exact = urllib.parse.quote(exact_phrase) if exact_phrase else ''

            # Club ID 가?�오�?            club_id = self.get_cafe_club_id()
            if not club_id:
                print("         ??Club ID�?가?�올 ???�음")
                return None

            # 고급 검??URL ?�라미터 구성
            params = {
                'search.clubid': club_id,
                'search.query': encoded_keyword,
                'search.searchBy': search_by,
                'search.sortBy': sort_by,
                'search.option': 0,
                'search.defaultValue': 1,
                'search.includeAll': 'off',
                'search.exclude': encoded_exclude,
                'search.include': encoded_include,
                'search.exact': encoded_exact,
                'search.searchdate': date_filter,
                'search.media': media_filter,
                'search.searchType': 'post',
                'search.page.currentpage': 1
            }

            # URL 구성
            base_url = f"https://cafe.naver.com/ArticleSearchList.nhn"
            param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            search_url = f"{base_url}?{param_string}"

            print(f"         ?�� 고급 검??URL 구성 ?�료: {search_url[:100]}...")
            return search_url

        except Exception as e:
            print(f"         ??고급 검??URL 구성 ?�류: {e}")
            return None

    def perform_integrated_search(self, keyword):
        """?�합 검???�행"""
        try:
            print(f"    ?�� ?�합 검???�행: '{keyword}'")

            # 기존 advanced_multi_search ?�용
            posts, metadata = self.advanced_multi_search(keyword)

            return {
                'strategy': 'integrated',
                'keyword': keyword,
                'posts': posts,
                'post_count': len(posts),
                'success': len(posts) > 0,
                'metadata': metadata
            }
        except Exception as e:
            print(f"    ???�합 검???�패: {e}")
            return {
                'strategy': 'integrated',
                'keyword': keyword,
                'posts': [],
                'post_count': 0,
                'success': False,
                'error': str(e)
            }

    def perform_scope_specific_search(self, keyword, scope):
        """?�정 범위 검???�행"""
        try:
            print(f"    ?�� 범위�?검?? '{keyword}' in {scope}")

            scope_mapping = {
                'title_content': '1',  # ?�목+?�용
                'title': '2',          # ?�목�?                'content': '3',        # ?�용�?                'author': '4',         # ?�성??                'comment': '5',        # ?��?
                'tag': '6',           # ?�그
                'file_name': '7'      # ?�일�?            }

            search_scope = scope_mapping.get(scope, '1')

            # 고급 검??URL 구성
            search_url = self.build_advanced_search_url(
                keyword=keyword,
                search_by=search_scope
            )

            if not search_url:
                posts = []
            elif self.navigate_to_search_url(search_url):
                posts = self.extract_search_results_with_metadata(keyword, f'scope_{scope}')
            else:
                posts = []

            return {
                'strategy': f'scope_{scope}',
                'keyword': keyword,
                'scope': scope,
                'posts': posts,
                'post_count': len(posts),
                'success': len(posts) > 0
            }

        except Exception as e:
            print(f"    ??범위�?검???�패 ({scope}): {e}")
            return {
                'strategy': f'scope_{scope}',
                'keyword': keyword,
                'posts': [],
                'post_count': 0,
                'success': False,
                'error': str(e)
            }

    def perform_sort_specific_search(self, keyword, sort_method):
        """?�정 ?�렬 방식 검???�행"""
        try:
            print(f"    ?�� ?�렬�?검?? '{keyword}' by {sort_method}")

            sort_mapping = {
                'date_desc': 'date',      # 최신??                'date_asc': 'date_asc',   # ?�래?�순
                'relevance': 'sim',       # ?�확?�순
                'views': 'view',          # 조회?�순
                'comments': 'comment',    # ?��??�순
                'likes': 'like',          # 추천??                'replies': 'reply'        # ?��???            }

            sort_value = sort_mapping.get(sort_method, 'date')
            posts = self.search_with_sort(keyword, sort_method)

            return {
                'strategy': f'sort_{sort_method}',
                'keyword': keyword,
                'sort': sort_method,
                'posts': posts,
                'post_count': len(posts),
                'success': len(posts) > 0
            }

        except Exception as e:
            print(f"    ???�렬�?검???�패 ({sort_method}): {e}")
            return {
                'strategy': f'sort_{sort_method}',
                'keyword': keyword,
                'posts': [],
                'post_count': 0,
                'success': False,
                'error': str(e)
            }

    # =====================================================================
    # Phase 7G: 게시???��? �??�틸리티 메서??(15�?
    # =====================================================================

    def find_dynamic_menus(self):
        """?�적 메뉴 �?iframe ?�색"""
        boards = []

        try:
            # JavaScript�??�겨�?메뉴 ?�장 ?�도
            expand_scripts = [
                "document.querySelectorAll('.menu-toggle, .expand-btn, [data-toggle]').forEach(el => {try{el.click()}catch(e){}});",
                "document.querySelectorAll('[style*=\"display:none\"], [style*=\"visibility:hidden\"]').forEach(el => {el.style.display='block'; el.style.visibility='visible';});",
                "window.scrollTo(0, document.body.scrollHeight);"  # ?�크롤로 lazy loading ?�리�?            ]

            for script in expand_scripts:
                try:
                    self.safe_execute_script(script)
                    self.adaptive_delay(1)
                except:
                    continue

            # iframe ?��? 검??            try:
                iframes = self.safe_find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes[:3]:  # 최�? 3�?iframe�?검??                    try:
                        self.driver.switch_to.frame(iframe)

                        # iframe ?��??�서 게시??링크 찾기
                        iframe_links = self.safe_find_elements(By.CSS_SELECTOR, "a[href*='cafe.naver.com']")
                        for link in iframe_links:
                            try:
                                name = link.text.strip()
                                href = link.get_attribute("href")
                                if self.is_valid_board(name, href):
                                    boards.append((name, href))
                            except:
                                continue

                        self.driver.switch_to.default_content()
                    except:
                        try:
                            self.driver.switch_to.default_content()
                        except:
                            pass
                        continue
            except:
                pass

            if boards:
                print(f"    ?�� ?�적 메뉴?�서 {len(boards)}�?게시??발견")

        except Exception as e:
            print(f"    ?�️ ?�적 메뉴 검???�류: {e}")

        return boards

    def get_priority(self, board_name):
        """게시???�선?�위 계산"""
        try:
            priority_keywords = ['?�체', '?�유', '?�반', '공�?', '?�보', '질문', '?�기']
            name_lower = board_name.lower()

            for i, keyword in enumerate(priority_keywords):
                if keyword in name_lower:
                    return i
            return len(priority_keywords)

        except:
            return 999

    def fallback_detection(self):
        """기본 ?�색 모드 (fallback)"""
        try:
            print("  ?�� 기본 모드�??�환...")

            # 가??기본?�인 링크??검??            all_links = self.safe_find_elements(By.CSS_SELECTOR, "a[href]")
            boards = []

            for link in all_links[:200]:  # 최�? 200�?링크 검??                try:
                    text = link.text.strip()
                    href = link.get_attribute("href")

                    if href and 'cafe.naver.com' in href and len(text) > 0:
                        if self.is_valid_board(text, href):
                            boards.append((text, href))

                    if len(boards) >= 10:  # 10�?찾으�?충분
                        break
                except:
                    pass

            return boards if boards else [("?�체글보기", Config.DEFAULT_CAFE_URL)]

        except:
            return [("?�체글보기", Config.DEFAULT_CAFE_URL)]

    def search_in_current_board(self, keyword, max_pages):
        """?�재 게시?�에???�워??검??- ?�마???�비게이???�함"""
        posts_found = []

        try:
            print(f"    ?�� 게시???�동 ?�색 �??�워??'{keyword}' 검???�작...")

            # 1. ?�이지 ?�태 분석
            self.analyze_current_page()

            # 2. 최적??보기 모드�??�동 ?�환
            self.optimize_view_mode()

            # 3. ?�마???�이지 ?�비게이??            self.smart_page_navigation("all_posts")

            # 4. ?�이지�??�롤�?(?�상??방식)
            for page in range(1, max_pages + 1):
                print(f"    ?�� ?�이지 {page}/{max_pages} 분석 �?.. (?�워?? '{keyword}')")

                # ?�이지 로딩 ?�료 ?��?                self.wait_for_page_load()

                # 게시글 추출
                page_posts = self.extract_posts_from_page(keyword)
                posts_found.extend(page_posts)

                print(f"      ???�이지 {page}?�서 {len(page_posts)}�?매칭 게시글 발견")

                # ?�음 ?�이지 ?�동 (?�마??방식)
                if page < max_pages:
                    if not self.smart_next_page():
                        print("      ?�� 마�?�??�이지 ?�달")
                        break

                # ?�응???�레??(?�이지 로딩 ?�태???�라)
                self.adaptive_delay()

        except Exception as e:
            print(f"    ??게시??검???�류: {e}")

        return posts_found

    def find_main_menu_boards(self):
        """메인 메뉴?�서 게시??찾기"""
        boards = []
        try:
            # 메인 메뉴 ?�택?�들
            menu_selectors = [
                '.cafe-menu a', '.menu-list a', '.main-menu a',
                '[class*="menu"] a', '[class*="nav"] a',
                '.cafe-nav a', '.navigation a'
            ]

            for selector in menu_selectors:
                try:
                    elements = self.safe_find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        board_info = self.extract_board_info(element)
                        if board_info and self.is_valid_board_link(board_info):
                            boards.append(board_info)
                except:
                    continue

        except Exception as e:
            print(f"    ?�️ 메인 메뉴 검???�류: {e}")

        return boards

    def find_sidebar_boards(self):
        """?�이?�바?�서 게시??찾기"""
        boards = []
        try:
            sidebar_selectors = [
                '.sidebar a', '.side-menu a', '.left-menu a',
                '.right-menu a', '[class*="side"] a'
            ]

            for selector in sidebar_selectors:
                try:
                    elements = self.safe_find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        board_info = self.extract_board_info(element)
                        if board_info and self.is_valid_board_link(board_info):
                            boards.append(board_info)
                except:
                    continue

        except Exception as e:
            print(f"    ?�️ ?�이?�바 검???�류: {e}")

        return boards

    def find_dropdown_boards(self):
        """?�롭?�운 메뉴?�서 게시??찾기"""
        boards = []
        try:
            # ?�롭?�운 ?�리�??�릭 ?�도
            dropdown_triggers = [
                '.dropdown-toggle', '.menu-toggle',
                '[class*="dropdown"]', '[class*="toggle"]'
            ]

            for trigger_selector in dropdown_triggers:
                try:
                    triggers = self.safe_find_elements(By.CSS_SELECTOR, trigger_selector)
                    for trigger in triggers:
                        if trigger.is_displayed():
                            trigger.click()
                            self.adaptive_delay(1)

                            # ?�롭?�운 메뉴?�서 링크 찾기
                            dropdown_links = self.safe_find_elements(By.CSS_SELECTOR, '.dropdown-menu a, .submenu a')
                            for link in dropdown_links:
                                board_info = self.extract_board_info(link)
                                if board_info and self.is_valid_board_link(board_info):
                                    boards.append(board_info)

                            # ?�롭?�운 ?�기
                            try:
                                trigger.click()
                            except:
                                continue
                except:
                    pass

        except Exception as e:
            print(f"    ?�️ ?�롭?�운 검???�류: {e}")

        return boards

    def find_hidden_boards(self):
        """?�겨�?게시??찾기"""
        boards = []
        try:
            if not Config.EXPLORE_HIDDEN_BOARDS:
                return boards

            # ?�겨�?메뉴 ?��?
            hidden_selectors = [
                'a[style*="display:none"]',
                '.hidden a', '.hide a',
                '[class*="hidden"] a',
                'li[style*="display:none"] a'
            ]

            for selector in hidden_selectors:
                try:
                    elements = self.safe_find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        board_info = self.extract_board_info(element)
                        if board_info and self.is_valid_board_link(board_info):
                            board_info['is_hidden'] = True
                            boards.append(board_info)
                except:
                    continue

        except Exception as e:
            print(f"    ?�️ ?�겨�?게시??검???�류: {e}")

        return boards

    def find_category_boards(self):
        """카테고리�?게시??찾기"""
        boards = []
        try:
            # 카테고리 링크 찾기
            category_selectors = [
                '.category a', '.cat a', '[class*="category"] a',
                '.board-category a', '.menu-category a'
            ]

            for selector in category_selectors:
                try:
                    elements = self.safe_find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        board_info = self.extract_board_info(element)
                        if board_info and self.is_valid_board_link(board_info):
                            board_info['board_type'] = 'category'
                            boards.append(board_info)
                except:
                    continue

        except Exception as e:
            print(f"    ?�️ 카테고리 게시??검???�류: {e}")

        return boards

    def find_special_boards(self):
        """?�별 게시??찾기 (공�?, ?�벤????"""
        boards = []
        try:
            if not Config.FIND_SPECIAL_BOARDS:
                return boards

            # ?�별 게시???�워??            special_keywords = [
                '공�?', '?�벤??, '?�내', '?�림', '?�소??,
                '공�??�항', '?�벤??, '가?�드', '?��?�?,
                'notice', 'event', 'announcement', 'news'
            ]

            # 모든 링크?�서 ?�별 게시??찾기
            all_links = self.safe_find_elements(By.TAG_NAME, 'a')

            for link in all_links[:100]:  # 최�? 100개만 검??                try:
                    link_text = link.text.lower()
                    href = link.get_attribute('href') or ''

                    # ?�별 ?�워???�함 ?��? ?�인
                    for keyword in special_keywords:
                        if keyword.lower() in link_text or keyword.lower() in href.lower():
                            board_info = self.extract_board_info(link)
                            if board_info and self.is_valid_board_link(board_info):
                                board_info['board_type'] = 'special'
                                board_info['special_type'] = keyword
                                boards.append(board_info)
                            break
                except:
                    continue

        except Exception as e:
            print(f"    ?�️ ?�별 게시??검???�류: {e}")

        return boards

    def extract_board_info(self, element):
        """게시???�보 추출"""
        try:
            href = element.get_attribute('href')
            text = element.text.strip()

            if not href or not text or len(text) < 2:
                return None

            board_info = {
                'name': text,
                'url': href,
                'board_type': 'unknown',
                'is_hidden': False,
                'menu_id': '',
                'description': ''
            }

            # menu_id 추출 ?�도
            if 'menuid=' in href:
                try:
                    menu_id = href.split('menuid=')[1].split('&')[0]
                    board_info['menu_id'] = menu_id
                except:
                    pass

            return board_info

        except Exception as e:
            return None

    def is_valid_board_link(self, board_info):
        """게시??링크 ?�효??검??""
        try:
            if not board_info or not isinstance(board_info, dict):
                return False

            name = board_info.get('name', '')
            href = board_info.get('url', '')

            if not name or not href or len(name.strip()) < 2:
                return False

            # 카페 URL ?�함 ?�인
            if 'cafe.naver.com' not in href:
                return False

            # ?�외???�워?�들
            exclude_keywords = [
                'login', 'logout', 'search', 'write', 'modify', 'delete',
                'reply', 'comment', 'profile', 'member', 'setting', 'admin'
            ]

            name_lower = name.lower()
            href_lower = href.lower()

            for keyword in exclude_keywords:
                if keyword in name_lower or keyword in href_lower:
                    return False

            # ?�무 길거??짧�? ?�름 ?�외
            if len(name) > 50 or len(name) < 1:
                return False

            return True

        except:
            return False

    def deduplicate_posts(self, posts):
        """게시글 중복 ?�거"""
        try:
            seen_urls = set()
            seen_titles = set()
            unique_posts = []

            for post in posts:
                post_url = post.get('url', '')
                post_title = post.get('title', '')

                # URL 기반 중복 ?�거
                if post_url and post_url not in seen_urls:
                    seen_urls.add(post_url)
                    unique_posts.append(post)
                # ?�목 기반 중복 ?�거 (URL???�거???�른 경우)
                elif post_title and post_title not in seen_titles:
                    seen_titles.add(post_title)
                    unique_posts.append(post)

            return unique_posts

        except Exception as e:
            print(f"    ??중복 ?�거 ?�류: {e}")
            return posts

    def save_results_to_excel(self, results, filename_prefix="complete_exploration"):
        """결과�??��?�??�??""
        try:
            if hasattr(CafeDataExporter, 'save_all'):
                filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                return CafeDataExporter.save_all(results, filename)
            else:
                print("    ?�️ CafeDataExporter�??�용?????�음")
                return False
        except Exception as e:
            print(f"    ???��? ?�???�류: {e}")
            return False

    def create_comments_sheet(self, writer, comments):
        """?��? ?�트 ?�성"""
        try:
            comment_data = []

            for comment in comments:
                comment_data.append([
                    comment.get('post_title', ''),
                    comment.get('author', ''),
                    comment.get('date', ''),
                    comment.get('content', ''),
                    comment.get('reply_level', 0),
                    comment.get('post_url', ''),
                    comment.get('board_name', '')
                ])

            # pandas�??�용?????�는 경우?�만 ?�트 ?�성
            try:
                import pandas as pd
                df_comments = pd.DataFrame(comment_data, columns=[
                    '게시글?�목', '?��??�성??, '?��??�성??, '?��??�용', '?��?깊이', '게시글URL', '게시?�명'
                ])
                df_comments.to_excel(writer, sheet_name='?��?��?목록', index=False)
                print(f"    ???��?목록 ?�트 ?�성 ({len(comments)}�?")
            except ImportError:
                print("    ?�️ pandas�??�용?????�어 ?��? ?�트�??�성?????�음")

        except Exception as e:
            print(f"    ???��?목록 ?�트 ?�류: {e}")

    def collect_all_posts_from_results(self, results):
        """결과?�서 모든 게시글 ?�집"""
        all_posts = []

        try:
            # 검??결과?�서 게시글 ?�집
            search_results = results.get('search_results', {})
            if search_results.get('all_posts'):
                all_posts.extend(search_results['all_posts'])

            # 게시?�별 결과?�서 게시글 ?�집
            board_results = results.get('board_results', {})
            for board_name, board_data in board_results.items():
                if board_data.get('posts'):
                    all_posts.extend(board_data['posts'])

            # 중복 ?�거
            return self.deduplicate_posts(all_posts)

        except Exception as e:
            print(f"    ??게시글 ?�집 ?�류: {e}")
            return all_posts


# 기존 코드?�???�환?�을 ?�한 alias
CafeCrawler = CafeCrawlerMigrated

if __name__ == "__main__":
    # ?�용 ?�시 - 기존 코드?� ?�일?�게 ?�용 가??    print("?? CafeCrawler Migration Version ?�스??)
    print(f"?�로??모듈 ?�용 가?? {NEW_MODULES_AVAILABLE}")

    # 컨텍?�트 매니?� ?��????�용 (권장)
    try:
        with CafeCrawlerMigrated() as crawler:
            # 로그??            if crawler.login_naver():
                # 카페 ?�동
                cafe_url = "https://cafe.naver.com/your-cafe"
                crawler.navigate_to_cafe(cafe_url)

                # 검??                results = crawler.search_posts("?�스??, max_pages=2)
                print(f"검??결과: {len(results)}�?)

                # ?�??                if results:
                    crawler.save_to_excel()

    except Exception as e:
        print(f"???�스???�행 �??�류: {e}")

    # 기존 ?��????�용??가??    crawler = CafeCrawlerMigrated()
    try:
        crawler.setup_driver()
        print("??기존 ?��????�라?�버 ?�정 ?�료")
    except Exception as e:
        print(f"??기존 ?��????�류: {e}")
    finally:
        crawler.__exit__(None, None, None)
