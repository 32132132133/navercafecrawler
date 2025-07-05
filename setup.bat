REM Disclaimer: use at your own risk. The authors take no responsibility for misuse.
@echo off
chcp 65001 >nul
title 네이버 카페 크롤러 - 초기 설정

echo.
echo ========================================
echo 네이버 카페 크롤러 초기 설정
echo ========================================
echo.

:: Python 설치 확인
echo 1️⃣ Python 설치 확인 중...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python이 설치되지 않았습니다.
    echo.
    echo 📥 다음 링크에서 Python을 다운로드하세요:
    echo https://python.org/downloads/
    echo.
    echo ⚠️  설치 시 "Add Python to PATH" 옵션을 체크하세요!
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version') do echo ✅ Python %%i 설치됨
)

echo.
echo 2️⃣ 필요한 패키지 설치 중...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ 패키지 설치 실패
    echo.
    echo 💡 다음을 시도해보세요:
    echo    1. 인터넷 연결 확인
    echo    2. 관리자 권한으로 실행
    echo    3. pip install --upgrade pip
    echo.
    pause
    exit /b 1
)
echo ✅ 패키지 설치 완료

echo.
echo 3️⃣ 로그인 정보 설정...
if exist ".env" (
    echo ⚠️  .env 파일이 이미 존재합니다.
    set /p overwrite="기존 설정을 덮어쓸까요? (y/n): "
    if /i not "%overwrite%"=="y" goto skip_env
)

echo.
echo 📝 네이버 로그인 정보를 입력하세요:
echo ⚠️  보안을 위해 입력 시 비밀번호가 보이지 않을 수 있습니다.
echo.

set /p naver_id="네이버 아이디: "
set /p naver_password="네이버 비밀번호: "

if "%naver_id%"=="" (
    echo ❌ 아이디를 입력해주세요.
    pause
    exit /b 1
)

if "%naver_password%"=="" (
    echo ❌ 비밀번호를 입력해주세요.
    pause
    exit /b 1
)

:: .env 파일 생성
(
echo NAVER_ID=%naver_id%
echo NAVER_PASSWORD=%naver_password%
) > .env

echo ✅ 로그인 정보 저장 완료

:skip_env
echo.
echo 4️⃣ 출력 디렉토리 생성...
if not exist "output" (
    mkdir output
    echo ✅ output 폴더 생성 완료
) else (
    echo ✅ output 폴더 이미 존재
)

echo.
echo ========================================
echo 🎉 설정 완료!
echo ========================================
echo.
echo 이제 다음 방법으로 크롤러를 실행할 수 있습니다:
echo.
echo 1️⃣ run_crawler.bat 더블클릭
echo 2️⃣ 또는 터미널에서 python main.py
echo.
echo ⚠️  주의사항:
echo   - 네이버 2단계 인증이 설정된 경우 앱 비밀번호를 사용하세요
echo   - 크롤링할 카페에 미리 가입되어 있어야 합니다
echo   - 적절한 간격으로 요청하여 서버에 부하를 주지 마세요
echo.

set /p run_now="지금 바로 크롤러를 실행할까요? (y/n): "
if /i "%run_now%"=="y" (
    call run_crawler.bat
) else (
    echo.
    echo 설정이 완료되었습니다. 언제든 run_crawler.bat을 실행하세요!
    pause
) 