REM Disclaimer: use at your own risk. The authors take no responsibility for misuse.
@echo off
chcp 65001 > nul
title 🚀 네이버 카페 스마트 크롤러 v3.0 - 완전 탐색 모드
echo.
echo ███████╗███╗   ███╗ █████╗ ██████╗ ████████╗     ██████╗██████╗  █████╗ ██╗    ██╗██╗     
echo ██╔════╝████╗ ████║██╔══██╗██╔══██╗╚══██╔══╝    ██╔════╝██╔══██╗██╔══██╗██║    ██║██║     
echo ███████╗██╔████╔██║███████║██████╔╝   ██║       ██║     ██████╔╝███████║██║ █╗ ██║██║     
echo ╚════██║██║╚██╔╝██║██╔══██║██╔══██╗   ██║       ██║     ██╔══██╗██╔══██║██║███╗██║██║     
echo ███████║██║ ╚═╝ ██║██║  ██║██║  ██║   ██║       ╚██████╗██║  ██║██║  ██║╚███╔███╔╝███████╗
echo ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝        ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚══════╝
echo.
echo 🔥 NAVER CAFE COMPLETE EXPLORATION SYSTEM v3.0 🔥
echo ================================================================
echo.

:MENU
echo 🎯 네이버 카페 완전 탐색 메뉴
echo ================================================================
echo.
echo 📋 기본 크롤링 옵션:
echo   1️⃣  키워드 검색 크롤링 (고급 다중 검색)
echo   2️⃣  카페 전체 게시글 크롤링
echo   3️⃣  특정 게시판 크롤링
echo   4️⃣  사용자 정의 크롤링
echo.
echo 🚀 완전 탐색 옵션 (NEW!):
echo   5️⃣  네이버 카페 완전 탐색 모드 (모든 검색 기능 + 모든 게시판)
echo   6️⃣  검색 기능 완전 활용 모드 (내부 검색 엔진 100%% 활용)
echo   7️⃣  게시판 구조 완전 분석 모드 (숨겨진 게시판까지)
echo   8️⃣  카페 메타데이터 수집 모드 (카페 정보 + 통계)
echo.
echo 🔧 유틸리티:
echo   9️⃣  설정 확인 및 테스트
echo   0️⃣  종료
echo.
echo ================================================================

set /p choice=선택하세요 (1-9, 0): 

if "%choice%"=="1" goto KEYWORD_SEARCH
if "%choice%"=="2" goto FULL_CRAWL  
if "%choice%"=="3" goto BOARD_CRAWL
if "%choice%"=="4" goto CUSTOM_CRAWL
if "%choice%"=="5" goto COMPLETE_EXPLORATION
if "%choice%"=="6" goto SEARCH_EXPLORATION
if "%choice%"=="7" goto BOARD_ANALYSIS
if "%choice%"=="8" goto METADATA_COLLECTION
if "%choice%"=="9" goto CONFIG_TEST
if "%choice%"=="0" goto EXIT

echo ❌ 잘못된 선택입니다. 다시 선택해주세요.
goto MENU

:COMPLETE_EXPLORATION
echo.
echo 🚀 네이버 카페 완전 탐색 모드
echo ================================================================
echo 이 모드는 다음을 모두 수행합니다:
echo   ✅ 카페 메타데이터 완전 수집 (이름, 멤버수, 설명 등)
echo   ✅ 모든 게시판 자동 발견 (숨겨진 게시판 포함)
echo   ✅ 네이버 카페 내부 검색 기능 100%% 활용
echo   ✅ 모든 게시판별 게시글 + 댓글 수집
echo   ✅ 종합 통계 및 분석 리포트 생성
echo.
echo ⚠️  주의: 이 모드는 매우 강력하며 시간이 오래 걸릴 수 있습니다.
echo.

set /p cafe_url=카페 URL을 입력하세요: 
if "%cafe_url%"=="" (
    echo ❌ 카페 URL이 필요합니다.
    pause
    goto MENU
)

set /p use_keywords=키워드 검색도 함께 하시겠습니까? (y/n): 
if /i "%use_keywords%"=="y" (
    set /p keywords=검색할 키워드를 입력하세요 (쉼표로 구분): 
) else (
    set keywords=
)

echo.
echo 🚀 완전 탐색을 시작합니다...
echo   📍 대상 카페: %cafe_url%
if not "%keywords%"=="" echo   🔍 검색 키워드: %keywords%
echo   ⏰ 예상 시간: 30분 ~ 2시간
echo.
echo 계속하려면 아무 키나 누르세요...
pause > nul

python -c "
import sys
sys.path.append('.')
from cafe_crawler_migrated import CafeCrawlerMigrated as NaverCafeCrawler
from config import Config

# 완전 탐색 모드로 설정
Config.FULL_CAFE_EXPLORATION = True
Config.EXPLORE_ALL_BOARDS = True
Config.EXPLORE_HIDDEN_BOARDS = True
Config.COLLECT_CAFE_METADATA = True

crawler = NaverCafeCrawler()
try:
    keywords_list = None
    if '%keywords%':
        keywords_list = ['%keywords%'.replace(' ', '').split(',') if ',' in '%keywords%' else '%keywords%'][0]
    
    print('🚀 네이버 카페 완전 탐색 시작!')
    results = crawler.explore_cafe_completely('%cafe_url%', keywords_list)
    
    if results and (results.get('total_posts', 0) > 0 or results.get('all_boards')):
        crawler.save_results_to_excel(results, 'complete_exploration')
        print('\\n🎉 완전 탐색이 성공적으로 완료되었습니다!')
        print(f'📊 결과: {results.get(\"total_posts\", 0)}개 게시글, {results.get(\"total_comments\", 0)}개 댓글')
        print(f'🗂️ 발견된 게시판: {len(results.get(\"all_boards\", []))}개')
    else:
        print('❌ 탐색 결과가 없습니다.')
        
except Exception as e:
    print(f'❌ 오류가 발생했습니다: {e}')
finally:
    crawler.quit()
"

echo.
echo 완전 탐색이 완료되었습니다!
pause
goto MENU

:SEARCH_EXPLORATION
echo.
echo 🔍 검색 기능 완전 활용 모드
echo ================================================================
echo 이 모드는 네이버 카페의 모든 검색 기능을 활용합니다:
echo   ✅ 통합 검색 (제목+내용)
echo   ✅ 범위별 검색 (제목만, 내용만, 작성자, 댓글, 태그, 파일명)
echo   ✅ 정렬별 검색 (최신순, 관련도순, 조회수순, 댓글수순 등)
echo   ✅ 기간별 검색 (1일, 1주일, 1개월, 3개월, 6개월, 1년 등)
echo.

set /p cafe_url=카페 URL을 입력하세요: 
if "%cafe_url%"=="" (
    echo ❌ 카페 URL이 필요합니다.
    pause
    goto MENU
)

set /p keywords=검색할 키워드를 입력하세요: 
if "%keywords%"=="" (
    echo ❌ 키워드가 필요합니다.
    pause
    goto MENU
)

echo.
echo 🔍 검색 기능 완전 활용을 시작합니다...
echo   📍 대상 카페: %cafe_url%
echo   🎯 키워드: %keywords%
echo   📊 예상 검색 수: 50+ 가지 검색 조합
echo.
pause

python -c "
import sys
sys.path.append('.')
from cafe_crawler_migrated import CafeCrawlerMigrated as NaverCafeCrawler
from config import Config

# 검색 기능 완전 활용 모드
Config.USE_INTEGRATED_SEARCH = True
Config.USE_BOARD_SPECIFIC_SEARCH = True
Config.USE_AUTHOR_SEARCH = True
Config.USE_PERIOD_SEARCH = True
Config.USE_FILE_TYPE_SEARCH = True
Config.USE_POPULAR_SEARCH = True
Config.USE_LATEST_SEARCH = True
Config.USE_RECOMMENDED_SEARCH = True

crawler = NaverCafeCrawler()
try:
    crawler.navigate_to_cafe('%cafe_url%')
    search_results = crawler.comprehensive_search_exploration('%keywords%')
    
    if search_results and search_results.get('all_posts'):
        crawler.save_search_results_to_excel(search_results, 'comprehensive_search')
        print(f'\\n🎉 검색 완료! {len(search_results[\"all_posts\"])}개 게시글 발견')
        print(f'📊 총 {search_results.get(\"total_searches\", 0)}번 검색 수행')
        print(f'✅ 성공률: {search_results.get(\"successful_searches\", 0)}/{search_results.get(\"total_searches\", 0)}')
    else:
        print('❌ 검색 결과가 없습니다.')
        
except Exception as e:
    print(f'❌ 오류가 발생했습니다: {e}')
finally:
    crawler.quit()
"

echo.
echo 검색 기능 완전 활용이 완료되었습니다!
pause
goto MENU

:BOARD_ANALYSIS
echo.
echo 🗂️ 게시판 구조 완전 분석 모드
echo ================================================================
echo 이 모드는 카페의 모든 게시판을 발견하고 분석합니다:
echo   ✅ 메인 메뉴 게시판 발견
echo   ✅ 사이드바 게시판 발견  
echo   ✅ 드롭다운 메뉴 게시판 발견
echo   ✅ 숨겨진 게시판 탐지
echo   ✅ 게시판 유형 자동 분류
echo   ✅ 활동도 분석
echo.

set /p cafe_url=카페 URL을 입력하세요: 
if "%cafe_url%"=="" (
    echo ❌ 카페 URL이 필요합니다.
    pause
    goto MENU
)

echo.
echo 🗂️ 게시판 구조 분석을 시작합니다...
pause

python -c "
import sys
sys.path.append('.')
from cafe_crawler_migrated import CafeCrawlerMigrated as NaverCafeCrawler
from config import Config

# 게시판 분석 모드
Config.EXPLORE_ALL_BOARDS = True
Config.EXPLORE_HIDDEN_BOARDS = True
Config.CLASSIFY_BOARD_TYPES = True
Config.ANALYZE_BOARD_ACTIVITY = True

crawler = NaverCafeCrawler()
try:
    crawler.navigate_to_cafe('%cafe_url%')
    all_boards = crawler.discover_all_boards()
    
    if all_boards:
        print(f'\\n🎉 게시판 발견 완료! 총 {len(all_boards)}개 게시판')
        
        # 게시판 유형별 분류 출력
        board_types = {}
        for board in all_boards:
            board_type = board.get('board_type', 'unknown')
            if board_type not in board_types:
                board_types[board_type] = []
            board_types[board_type].append(board['name'])
        
        print('\\n📋 게시판 유형별 분류:')
        for board_type, boards in board_types.items():
            print(f'  {board_type}: {len(boards)}개 - {boards[:3]}...' if len(boards) > 3 else f'  {board_type}: {len(boards)}개 - {boards}')
        
        # 결과를 파일로 저장
        import json
        with open('output/board_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(all_boards, f, ensure_ascii=False, indent=2)
        print('\\n💾 게시판 분석 결과가 output/board_analysis.json에 저장되었습니다.')
    else:
        print('❌ 게시판을 발견하지 못했습니다.')
        
except Exception as e:
    print(f'❌ 오류가 발생했습니다: {e}')
finally:
    crawler.quit()
"

echo.
echo 게시판 구조 분석이 완료되었습니다!
pause
goto MENU

:METADATA_COLLECTION
echo.
echo 📊 카페 메타데이터 수집 모드
echo ================================================================
echo 이 모드는 카페의 상세 정보를 수집합니다:
echo   ✅ 카페 이름, URL, 설명
echo   ✅ 멤버 수, 개설일, 카테고리
echo   ✅ 활동 통계, 인기 콘텐츠
echo   ✅ 관리자 정보 (공개된 경우)
echo.

set /p cafe_url=카페 URL을 입력하세요: 
if "%cafe_url%"=="" (
    echo ❌ 카페 URL이 필요합니다.
    pause
    goto MENU
)

echo.
echo 📊 메타데이터 수집을 시작합니다...
pause

python -c "
import sys
sys.path.append('.')
from cafe_crawler_migrated import CafeCrawlerMigrated as NaverCafeCrawler
from config import Config

# 메타데이터 수집 모드
Config.COLLECT_CAFE_METADATA = True
Config.COLLECT_CAFE_INFO = True
Config.COLLECT_MEMBER_COUNT = True
Config.COLLECT_ACTIVITY_STATS = True

crawler = NaverCafeCrawler()
try:
    crawler.navigate_to_cafe('%cafe_url%')
    metadata = crawler.collect_cafe_metadata()
    
    if metadata:
        print('\\n📊 카페 메타데이터 수집 완료!')
        print(f'📝 카페명: {metadata.get(\"cafe_name\", \"알 수 없음\")}')
        print(f'👥 멤버수: {metadata.get(\"member_count\", 0):,}명')
        print(f'📝 설명: {metadata.get(\"description\", \"없음\")[:100]}...')
        print(f'🌐 URL: {metadata.get(\"cafe_url\", \"\")}')
        
        # 결과를 파일로 저장
        import json
        with open('output/cafe_metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        print('\\n💾 메타데이터가 output/cafe_metadata.json에 저장되었습니다.')
    else:
        print('❌ 메타데이터를 수집하지 못했습니다.')
        
except Exception as e:
    print(f'❌ 오류가 발생했습니다: {e}')
finally:
    crawler.quit()
"

echo.
echo 메타데이터 수집이 완료되었습니다!
pause
goto MENU

:KEYWORD_SEARCH
echo.
echo 🧠 AI 완전분석 모드 (1000개 게시글 + 댓글)
echo.
echo 🔍 활성화된 고급 기능들:
echo    ✅ 네이버 카페 고급 검색 API 활용
echo    ✅ 1000개 게시글 수집
echo    ✅ 게시글 전체 내용 수집
echo    ✅ 댓글 및 대댓글 수집
echo    ✅ 이미지 정보 수집
echo    ✅ 통계 분석 자동 생성
echo    ✅ 최대 50페이지 탐색
echo.
echo ⏱️ 예상 소요 시간: 10-20분
echo.
set /p keyword="🔍 검색할 키워드를 입력하세요: "
if "%keyword%"=="" (
    echo ❌ 키워드를 입력해주세요.
    goto KEYWORD_SEARCH
)
echo.
echo 🚀 AI 완전분석으로 '%keyword%' 모든 데이터 수집 중...
python main.py --keyword="%keyword%" --max-posts=1000 --max-pages=50 --with-images --verbose
goto success

:FULL_CRAWL
echo.
echo 🎯 스마트 키워드 검색 모드 (카페 검색엔진 활용)
echo.
echo 💡 새로운 검색 기능 안내:
echo    → 네이버 카페 내장 검색엔진 직접 활용
echo    → 검색 정확도 대폭 향상
echo    → 게시글 내용 및 댓글 수집
echo    → 3가지 검색 방식 자동 시도
echo    → 실패시 필터링 방식 자동 전환
echo.
set /p keyword="🔍 검색할 키워드를 입력하세요: "
if "%keyword%"=="" (
    echo ❌ 키워드를 입력해주세요.
    goto FULL_CRAWL
)
echo.
echo 🚀 향상된 AI가 '%keyword%' 관련 모든 글을 찾고 있습니다...
echo.
echo 🔄 실행 중인 고급 검색 단계들:
echo    1️⃣ 직접 검색 URL 구성 시도...
echo    2️⃣ 카페 검색 인터페이스 탐색...
echo    3️⃣ 고급 검색 옵션 자동 설정...
echo    4️⃣ 검색 결과 페이지 자동 검증...
echo    5️⃣ 스마트 데이터 수집 진행...
echo.
python main.py --keyword="%keyword%" --max-posts=500 --max-pages=25 --verbose
goto success

:BOARD_CRAWL
echo.
echo 🎯 스마트 키워드 검색 모드 (카페 검색엔진 활용)
echo.
echo 💡 새로운 검색 기능 안내:
echo    → 네이버 카페 내장 검색엔진 직접 활용
echo    → 검색 정확도 대폭 향상
echo    → 게시글 내용 및 댓글 수집
echo    → 3가지 검색 방식 자동 시도
echo    → 실패시 필터링 방식 자동 전환
echo.
set /p keyword="🔍 검색할 키워드를 입력하세요: "
if "%keyword%"=="" (
    echo ❌ 키워드를 입력해주세요.
    goto BOARD_CRAWL
)
echo.
echo 🚀 향상된 AI가 '%keyword%' 관련 모든 글을 찾고 있습니다...
echo.
echo 🔄 실행 중인 고급 검색 단계들:
echo    1️⃣ 직접 검색 URL 구성 시도...
echo    2️⃣ 카페 검색 인터페이스 탐색...
echo    3️⃣ 고급 검색 옵션 자동 설정...
echo    4️⃣ 검색 결과 페이지 자동 검증...
echo    5️⃣ 스마트 데이터 수집 진행...
echo.
python main.py --keyword="%keyword%" --max-posts=500 --max-pages=25 --verbose
goto success

:CUSTOM_CRAWL
echo.
echo 🎯 스마트 키워드 검색 모드 (카페 검색엔진 활용)
echo.
echo 💡 새로운 검색 기능 안내:
echo    → 네이버 카페 내장 검색엔진 직접 활용
echo    → 검색 정확도 대폭 향상
echo    → 게시글 내용 및 댓글 수집
echo    → 3가지 검색 방식 자동 시도
echo    → 실패시 필터링 방식 자동 전환
echo.
set /p keyword="🔍 검색할 키워드를 입력하세요: "
if "%keyword%"=="" (
    echo ❌ 키워드를 입력해주세요.
    goto CUSTOM_CRAWL
)
echo.
echo 🚀 향상된 AI가 '%keyword%' 관련 모든 글을 찾고 있습니다...
echo.
echo 🔄 실행 중인 고급 검색 단계들:
echo    1️⃣ 직접 검색 URL 구성 시도...
echo    2️⃣ 카페 검색 인터페이스 탐색...
echo    3️⃣ 고급 검색 옵션 자동 설정...
echo    4️⃣ 검색 결과 페이지 자동 검증...
echo    5️⃣ 스마트 데이터 수집 진행...
echo.
python main.py --keyword="%keyword%" --max-posts=500 --max-pages=25 --verbose
goto success

:success
echo.
echo ═══════════════════════════════════════════════════════════════
echo [SUCCESS] Enhanced Smart Crawling Complete! 🎉
echo.
echo [PERFORMANCE] 향상된 성능 결과:
echo    → 검색 정확도: 크게 향상됨 ✅
echo    → 데이터 품질: 네이버 카페 검색엔진 활용으로 최적화 🎯
echo    → 수집 데이터: 게시글 내용 + 댓글 + 통계 분석 📊
echo.
echo [INFO] Check results in 'output' folder
echo [INFO] Advanced search metadata included
echo.
if exist "output\*.xlsx" (
    echo [FILES] Generated files:
    dir /b output\*.xlsx 2>nul | findstr "." >nul && (
        for %%f in (output\*.xlsx) do echo    📊 %%~nxf
    )
)
echo.
echo 🔍 검색 방식 활용 결과:
echo    1️⃣ 직접 URL 검색: 성공률 높음
echo    2️⃣ 카페 인터페이스 검색: 백업 역할
echo    3️⃣ 필터링 검색: 최종 백업
echo.
echo 💾 엑셀 파일 구성:
echo    📋 게시글정보: 제목, 작성자, 내용, 댓글수 등
echo    💬 댓글정보: 댓글 작성자, 내용, 날짜 등  
echo    📊 통계분석: 작성자별, 키워드별, 월별 분포
echo.
echo ===============================================================

:continue_choice
echo.
set /p continue="🔄 다른 검색을 하시겠습니까? (y/n): "
if /i "%continue%"=="y" goto MENU
if /i "%continue%"=="yes" goto MENU
if /i "%continue%"=="n" goto end
if /i "%continue%"=="no" goto end
echo ❌ y 또는 n을 입력해주세요.
goto continue_choice

:end
echo.
echo 🙏 감사합니다! 향상된 스마트 크롤링 시스템을 이용해주셔서 감사합니다.
echo 📊 수집된 데이터는 output 폴더에서 확인하실 수 있습니다.
echo.
pause

:CONFIG_TEST
echo.
echo 🛠️ 검색 방식 설정
echo.
echo 현재 설정된 고급 검색 기능들:
echo    ✅ 고급 검색 기능 사용: 활성화
echo    ✅ 직접 검색 URL 구성: 활성화  
echo    ✅ 제목+내용 통합 검색: 활성화
echo    ✅ 날짜순 정렬: 활성화
echo    ✅ 게시글만 검색: 활성화
echo    ✅ 검색 결과 검증: 활성화
echo    ✅ 내용 및 댓글 수집: 활성화
echo    ✅ 필터링 백업: 활성화
echo.
echo 📝 설정 변경 방법:
echo    → config.py 파일에서 다음 옵션들을 수정하세요:
echo    → USE_ADVANCED_SEARCH = True/False
echo    → USE_DIRECT_SEARCH_URL = True/False  
echo    → SEARCH_TITLE_AND_CONTENT = True/False
echo    → SEARCH_SORT_BY_DATE = True/False
echo    → EXTRACT_FULL_CONTENT = True/False
echo    → EXTRACT_COMMENTS = True/False
echo.
echo 💡 사용 가능한 명령행 옵션들:
echo    → --keyword="키워드"
echo    → --max-posts=1000 (최대 게시글 수)
echo    → --max-pages=50 (최대 페이지 수)
echo    → --no-content (내용 수집 안함)
echo    → --no-comments (댓글 수집 안함)
echo    → --with-images (이미지 정보 수집)
echo    → --headless (브라우저 숨김)
echo    → --verbose (상세 로그)
echo.
pause
goto MENU

:EXIT
echo.
echo 🙏 감사합니다! 향상된 스마트 크롤링 시스템을 이용해주셔서 감사합니다.
echo 📊 수집된 데이터는 output 폴더에서 확인하실 수 있습니다.
echo.
pause

:advanced_multi_search
echo.
echo 🚀 고급 다중 검색 모드 (모든 검색 옵션 활용)
echo.
echo 💡 고급 다중 검색 기능 안내:
echo    → 제목, 내용, 제목+내용 검색 동시 실행
echo    → 최신순, 관련도순, 조회수순 정렬 활용
echo    → 중복 제거 및 품질 필터 자동 적용
echo    → 검색 메타데이터 상세 분석
echo    → 최대 1000개 게시글 수집
echo.
set /p keyword="🔍 검색할 키워드를 입력하세요: "

echo.
echo 🚀 AI가 모든 검색 전략으로 '%keyword%' 관련 글을 수집합니다...
echo.
echo 🔄 실행 중인 고급 검색 전략들:
echo    1️⃣ 제목+내용 검색 (최신순)
echo    2️⃣ 제목+내용 검색 (관련도순)  
echo    3️⃣ 제목만 검색 (최신순)
echo    4️⃣ 내용만 검색 (최신순)
echo    5️⃣ 제목+내용 검색 (조회수순)
echo    6️⃣ 중복 제거 및 품질 필터링
echo    7️⃣ 상세 내용 및 댓글 수집
echo.

python main.py --keyword="%keyword%" --mode=advanced_multi --max-posts=1000 --verbose
goto continue_prompt

:search_scope_settings
echo.
echo 📊 검색 범위 맞춤 설정
echo.
echo 🎯 검색 범위 옵션을 선택하세요:
echo [1] 제목만 검색 (빠른 검색)
echo [2] 내용만 검색 (상세 검색)
echo [3] 제목+내용 검색 (균형 검색, 기본값)
echo [4] 작성자 검색 (특정 작성자)
echo [5] 댓글 검색 (댓글 내 키워드)
echo [6] 다중 범위 검색 (모든 범위 활용)
echo [7] ← 메인 메뉴로
echo.
set /p scope_choice="선택하세요 (1-7): "

if "%scope_choice%"=="1" goto title_only_search
if "%scope_choice%"=="2" goto content_only_search
if "%scope_choice%"=="3" goto title_content_search
if "%scope_choice%"=="4" goto author_search
if "%scope_choice%"=="5" goto comment_search
if "%scope_choice%"=="6" goto multi_scope_search
if "%scope_choice%"=="7" goto menu

echo ❌ 잘못된 선택입니다.
goto search_scope_settings

:title_only_search
echo.
echo 📝 제목만 검색 모드
set /p keyword="🔍 검색할 키워드를 입력하세요: "
echo 🚀 제목에서만 '%keyword%' 검색 중...
python main.py --keyword="%keyword%" --search-scope=title --max-posts=500
goto continue_prompt

:content_only_search
echo.
echo 📄 내용만 검색 모드
set /p keyword="🔍 검색할 키워드를 입력하세요: "
echo 🚀 내용에서만 '%keyword%' 검색 중...
python main.py --keyword="%keyword%" --search-scope=content --max-posts=500
goto continue_prompt

:title_content_search
echo.
echo 📋 제목+내용 검색 모드 (기본값)
set /p keyword="🔍 검색할 키워드를 입력하세요: "
echo 🚀 제목+내용에서 '%keyword%' 검색 중...
python main.py --keyword="%keyword%" --search-scope=title_content --max-posts=500
goto continue_prompt

:author_search
echo.
echo 👤 작성자 검색 모드
set /p author="👤 검색할 작성자명을 입력하세요: "
echo 🚀 작성자 '%author%'의 게시글 검색 중...
python main.py --keyword="%author%" --search-scope=author --max-posts=300
goto continue_prompt

:comment_search
echo.
echo 💬 댓글 검색 모드
set /p keyword="🔍 댓글에서 검색할 키워드를 입력하세요: "
echo 🚀 댓글에서 '%keyword%' 검색 중...
python main.py --keyword="%keyword%" --search-scope=comment --max-posts=200
goto continue_prompt

:multi_scope_search
echo.
echo 🎯 다중 범위 검색 모드
set /p keyword="🔍 검색할 키워드를 입력하세요: "
echo 🚀 모든 범위에서 '%keyword%' 검색 중...
python main.py --keyword="%keyword%" --search-scope=multi --max-posts=1000
goto continue_prompt

:advanced_settings
echo.
echo ⚙️ 고급 설정
echo.
echo 🔧 고급 설정 옵션:
echo [1] 정렬 방식 설정 (최신순/관련도순/조회수순)
echo [2] 기간 필터 설정 (1일/1주일/1개월/3개월/1년)
echo [3] 미디어 필터 설정 (텍스트/이미지/동영상/파일)
echo [4] 품질 필터 설정 (공지사항/광고 제외)
echo [5] 중복 제거 설정
echo [6] 고급 검색어 설정 (포함/제외/정확한문구)
echo [7] ← 메인 메뉴로
echo.
set /p adv_choice="선택하세요 (1-7): "

if "%adv_choice%"=="1" goto sort_settings
if "%adv_choice%"=="2" goto date_filter_settings
if "%adv_choice%"=="3" goto media_filter_settings
if "%adv_choice%"=="4" goto quality_filter_settings
if "%adv_choice%"=="5" goto duplicate_settings
if "%adv_choice%"=="6" goto advanced_query_settings
if "%adv_choice%"=="7" goto menu

echo ❌ 잘못된 선택입니다.
goto advanced_settings

:sort_settings
echo.
echo 📊 정렬 방식 설정
echo.
echo [1] 최신순 (기본값)
echo [2] 관련도순
echo [3] 조회수순
echo [4] 댓글수순
echo [5] 다중 정렬 (모든 방식 활용)
echo.
set /p sort_choice="정렬 방식을 선택하세요: "
set /p keyword="🔍 검색할 키워드를 입력하세요: "

if "%sort_choice%"=="1" (
    echo 🚀 최신순으로 '%keyword%' 검색 중...
    python main.py --keyword="%keyword%" --sort=date_desc --max-posts=500
) else if "%sort_choice%"=="2" (
    echo 🚀 관련도순으로 '%keyword%' 검색 중...
    python main.py --keyword="%keyword%" --sort=relevance --max-posts=500
) else if "%sort_choice%"=="3" (
    echo 🚀 조회수순으로 '%keyword%' 검색 중...
    python main.py --keyword="%keyword%" --sort=views --max-posts=500
) else if "%sort_choice%"=="4" (
    echo 🚀 댓글수순으로 '%keyword%' 검색 중...
    python main.py --keyword="%keyword%" --sort=comments --max-posts=500
) else if "%sort_choice%"=="5" (
    echo 🚀 다중 정렬로 '%keyword%' 검색 중...
    python main.py --keyword="%keyword%" --sort=multi --max-posts=1000
)
goto continue_prompt

:continue_prompt
echo.
set /p continue="🔄 다른 검색을 하시겠습니까? (y/n): "
if /i "%continue%"=="y" goto MENU
if /i "%continue%"=="yes" goto MENU
if /i "%continue%"=="n" goto end
if /i "%continue%"=="no" goto end
echo ❌ y 또는 n을 입력해주세요.
goto continue_prompt 