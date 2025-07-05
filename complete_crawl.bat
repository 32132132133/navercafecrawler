REM Disclaimer: use at your own risk. The authors take no responsibility for misuse.
@echo off
chcp 65001 >nul
title 완전 크롤링 - 공준모 카페 모든 글 수집

echo.
echo 🔥 공준모 카페 완전 크롤링 (모든 글 수집)
echo ================================================
echo.

:: .env 파일 확인
if not exist ".env" (
    echo ❌ 설정이 필요합니다. setup.bat을 먼저 실행하세요.
    pause
    exit /b 1
)

:: 완전 크롤링 안내
echo 📍 대상: 공준모 카페 (https://cafe.naver.com/studentstudyhard)
echo 🔍 키워드: 모든 공기업 관련 키워드 (47개)
echo 📄 페이지: 최대 100페이지/키워드
echo 📋 게시판: 모든 게시판 탐색
echo 🤖 배치 모드로 실행됩니다
echo.
echo ⚠️  주의사항:
echo    - 완전 크롤링은 2-5시간 소요될 수 있습니다
echo    - 수천 개의 게시글을 수집할 수 있습니다
echo    - 브라우저 창을 닫지 마세요
echo    - 네트워크가 안정적인 곳에서 실행하세요
echo.

:: 사용자 확인
set /p "confirm=계속 진행하시겠습니까? (y/N): "
if /i not "%confirm%"=="y" (
    echo ❌ 사용자에 의해 취소되었습니다.
    pause
    exit /b 0
)

echo.
echo 🚀 완전 크롤링을 시작합니다...
echo ================================================
echo.

:: 배치 모드로 프로그램 실행 (모든 키워드 자동 선택)
(
echo y
echo 2
echo y
) | python -u main.py

if %errorlevel% equ 0 (
    echo.
    echo ================================================
    echo ✅ 완전 크롤링 완료!
    echo ================================================
    echo.
    echo 📊 결과를 확인하세요:
    start "" "output"
    echo.
    echo 💡 팁: Excel 파일을 열어서 데이터를 분석해보세요!
) else (
    echo.
    echo ================================================
    echo ❌ 크롤링 중 오류가 발생했습니다.
    echo ================================================
    echo.
    echo 💡 문제 해결 방법:
    echo 1. 인터넷 연결을 확인하세요
    echo 2. 네이버 로그인이 차단되었는지 확인하세요
    echo 3. quick_start.bat으로 간단한 테스트를 해보세요
)

echo.
pause 