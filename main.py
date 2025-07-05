#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 카페 크롤러 메인 실행 파일
향상된 검색 기능과 내용/댓글 수집 지원

사용법:
    python main.py --keyword="키워드"
    python main.py --cafe="카페URL" --keyword="키워드1,키워드2"
    python main.py --help
"""

import sys
import argparse
from cafe_crawler_migrated import CafeCrawlerMigrated as NaverCafeCrawler
from utils import safe_wait
from config import Config
import os

def print_banner():
    """시작 배너 출력"""
    print("=" * 80)
    print("🔥 네이버 카페 고급 크롤러 v3.0")
    print("   📊 1000개 게시글 수집 | 📝 내용 분석 | 💬 댓글 수집")
    print("   🔍 네이버 카페 고급 검색 기능 완전 활용")
    print("=" * 80)

def print_config_info():
    """현재 설정 정보 출력"""
    print(f"📋 현재 크롤링 설정:")
    print(f"   🎯 최대 수집량: {Config.MAX_TOTAL_POSTS}개 게시글")
    print(f"   📄 최대 페이지: {Config.MAX_PAGES}페이지")
    print(f"   📝 게시글 내용: {'수집함' if Config.EXTRACT_FULL_CONTENT else '수집 안함'}")
    print(f"   💬 댓글 수집: {'수집함' if Config.EXTRACT_COMMENTS else '수집 안함'}")
    print(f"   🖼️ 이미지 정보: {'수집함' if Config.EXTRACT_IMAGES else '수집 안함'}")
    print(f"   🔍 고급 검색: {'활성화' if Config.USE_ADVANCED_SEARCH else '비활성화'}")
    print(f"   ⚙️ 브라우저 모드: {'백그라운드' if Config.HEADLESS else '화면 표시'}")
    print()

def validate_environment():
    """실행 환경 검증"""
    print("🔍 실행 환경 검증 중...")
    
    # 환경변수 확인
    if not Config.NAVER_ID or not Config.NAVER_PASSWORD:
        print("⚠️ 네이버 로그인 정보가 설정되지 않았습니다.")
        print("   .env 파일을 확인하거나 수동 로그인을 진행하세요.")
        print()
    
    # 출력 디렉토리 확인
    if not os.path.exists(Config.OUTPUT_DIR):
        print(f"📁 출력 디렉토리 생성: {Config.OUTPUT_DIR}")
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    
    print("✅ 환경 검증 완료")
    print()

def parse_arguments():
    """명령행 인수 파싱"""
    parser = argparse.ArgumentParser(
        description="네이버 카페 고급 크롤러 - 내용 및 댓글 수집",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python main.py --keyword="가스공사"
  python main.py --keyword="가스공사,공기업,채용" --max-posts=500
  python main.py --cafe="https://cafe.naver.com/studentstudyhard" --keyword="취업"
  python main.py --keyword="공무원" --no-comments --headless
  
주요 기능:
  - 네이버 카페 내장 검색엔진 활용
  - 게시글 전체 내용 수집
  - 댓글 및 대댓글 수집
  - 이미지 및 첨부파일 정보 수집
  - 엑셀 파일로 체계적 정리
  - 통계 분석 자동 생성
        """
    )
    
    parser.add_argument('--keyword', '-k', 
                       help='검색할 키워드 (쉼표로 구분하여 여러 개 가능)')
    
    parser.add_argument('--cafe', '-c',
                       default=Config.DEFAULT_CAFE_URL,
                       help=f'대상 카페 URL (기본값: {Config.DEFAULT_CAFE_URL})')
    
    parser.add_argument('--max-posts', '-m',
                       type=int,
                       default=Config.MAX_TOTAL_POSTS,
                       help=f'최대 수집 게시글 수 (기본값: {Config.MAX_TOTAL_POSTS})')
    
    parser.add_argument('--max-pages', '-p',
                       type=int,
                       default=Config.MAX_PAGES,
                       help=f'최대 탐색 페이지 수 (기본값: {Config.MAX_PAGES})')
    
    parser.add_argument('--no-content',
                       action='store_true',
                       help='게시글 내용 수집하지 않음')
    
    parser.add_argument('--no-comments',
                       action='store_true',
                       help='댓글 수집하지 않음')
    
    parser.add_argument('--with-images',
                       action='store_true',
                       help='이미지 정보 수집')
    
    parser.add_argument('--headless',
                       action='store_true',
                       help='브라우저 창 숨김 모드')
    
    parser.add_argument('--output', '-o',
                       help='출력 파일명 (기본값: 자동 생성)')
    
    parser.add_argument('--verbose', '-v',
                       action='store_true',
                       help='상세 로그 출력')
    
    return parser.parse_args()

def apply_arguments(args):
    """명령행 인수를 설정에 적용"""
    
    # 수집 설정 업데이트 (setattr 사용하여 안전하게 변경)
    if args.max_posts:
        setattr(Config, 'MAX_TOTAL_POSTS', args.max_posts)
    
    if args.max_pages:
        setattr(Config, 'MAX_PAGES', args.max_pages)
    
    if args.no_content:
        setattr(Config, 'EXTRACT_FULL_CONTENT', False)
        setattr(Config, 'INCLUDE_CONTENT', False)
    
    if args.no_comments:
        setattr(Config, 'EXTRACT_COMMENTS', False)
        setattr(Config, 'INCLUDE_COMMENTS', False)
    
    if args.with_images:
        setattr(Config, 'EXTRACT_IMAGES', True)
    
    if args.headless:
        setattr(Config, 'HEADLESS', True)
    
    if args.verbose:
        setattr(Config, 'VERBOSE_SEARCH_LOGGING', True)

def interactive_keyword_input():
    """키워드 대화식 입력"""
    print("🎯 검색할 키워드를 입력하세요.")
    print("   (여러 키워드는 쉼표로 구분, 예: 가스공사,공기업,채용)")
    print()
    
    while True:
        keyword_input = input("키워드: ").strip()
        
        if keyword_input:
            keywords = [k.strip() for k in keyword_input.split(',') if k.strip()]
            if keywords:
                return keywords
        
        print("❌ 키워드를 입력해주세요.")

def main():
    """메인 실행 함수"""
    try:
        # 배너 출력
        print_banner()
        
        # 환경 검증
        validate_environment()
        
        # 명령행 인수 파싱
        args = parse_arguments()
        
        # 설정 적용
        apply_arguments(args)
        
        # 설정 정보 출력
        print_config_info()
        
        # 키워드 처리
        keywords = None
        if args.keyword:
            keywords = [k.strip() for k in args.keyword.split(',') if k.strip()]
            print(f"🎯 검색 키워드: {', '.join(keywords)}")
        else:
            keywords = interactive_keyword_input()
            print(f"🎯 입력된 키워드: {', '.join(keywords)}")
        
        print(f"📍 대상 카페: {args.cafe}")
        print()
    
        # 크롤러 초기화 및 실행
        crawler = NaverCafeCrawler()
        
        print("🚀 크롤링 시작...")
        print("   (로그인이 필요한 경우 브라우저에서 수동으로 진행하세요)")
        print()
        
        # 드라이버 설정
        if not crawler.setup_driver():
            print("❌ 브라우저 초기화 실패")
            return False
        
        # 로그인 시도
        if Config.NAVER_ID and Config.NAVER_PASSWORD:
            print("🔐 자동 로그인 시도 중...")
            if not crawler.login_naver():
                print("⚠️ 자동 로그인 실패 - 수동 로그인 진행")
                input("브라우저에서 로그인 완료 후 Enter를 눌러주세요...")
        else:
            print("🔐 수동 로그인 모드")
            input("브라우저에서 네이버 로그인 완료 후 Enter를 눌러주세요...")
        
        # 크롤링 실행
        all_posts = crawler.crawl_cafe(args.cafe, keywords)  # type: ignore
        
        if all_posts:
            print(f"\n🎉 크롤링 성공!")
            print(f"   📊 총 수집 게시글: {len(all_posts)}개")
            
            # 데이터 저장
            crawler.posts_data = all_posts  # 크롤러에 데이터 설정 (기존 유지)

            from exporter import CafeDataExporter
            output_file = args.output
            saved_file = CafeDataExporter.save_all(all_posts, output_file)
            
            if saved_file and isinstance(saved_file, str):
                print(f"\n💾 데이터 저장 완료!")
                print(f"   📁 파일 위치: {saved_file}")
                print(f"   📊 포함된 데이터:")
                print(f"      - 게시글 정보: {len(all_posts)}개")
                print(f"      - 댓글 정보: {sum(len(post.get('comments', [])) for post in all_posts)}개")
                print(f"      - 이미지 정보: {sum(len(post.get('images', [])) for post in all_posts)}개")
                print(f"      - 통계 분석: 자동 생성")
                
                # 파일 탐색기에서 열기 (Windows)
                if sys.platform == "win32":
                    print(f"\n📂 파일 탐색기에서 결과 확인:")
                    print(f"   explorer {os.path.dirname(saved_file)}")
        
                    # 자동으로 폴더 열기 (선택사항)
                    try:
                        import subprocess
                        subprocess.run(['explorer', os.path.dirname(saved_file)])
                    except:
                        pass
            else:
                print("❌ 데이터 저장 실패")
        else:
            print(f"\n⚠️ 수집된 데이터가 없습니다.")
            print(f"   - 키워드를 다시 확인해보세요: {', '.join(keywords)}")
            print(f"   - 카페 URL이 올바른지 확인해보세요: {args.cafe}")
            print(f"   - 로그인 상태를 확인해보세요.")
        
        return True
        
    except KeyboardInterrupt:
        print(f"\n⚠️ 사용자에 의해 중단되었습니다.")
        return False
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        if args.verbose if 'args' in locals() else False:
            import traceback
            traceback.print_exc()
        return False
        
    finally:
        # 브라우저 정리
        try:
            if 'crawler' in locals() and crawler.driver:
                print("\n🧹 브라우저 정리 중...")
                crawler.driver.quit()
        except:
            pass

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 