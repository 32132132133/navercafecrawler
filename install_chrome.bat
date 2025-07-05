REM Disclaimer: use at your own risk. The authors take no responsibility for misuse.
@echo off
chcp 65001 >nul
title Chrome 브라우저 설치 도우미

echo.
echo ========================================
echo Chrome 브라우저 설치 도우미
echo ========================================
echo.

:: Chrome 설치 확인
where chrome >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Chrome 브라우저가 이미 설치되어 있습니다.
    chrome --version 2>nul
    echo.
    echo 🎉 설치가 완료되었습니다!
    pause
    exit /b 0
)

echo 🔍 Chrome 브라우저를 찾고 있습니다...

:: 일반적인 Chrome 설치 경로 확인
set chrome_paths[0]="C:\Program Files\Google\Chrome\Application\chrome.exe"
set chrome_paths[1]="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
set chrome_paths[2]="%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

for /l %%i in (0,1,2) do (
    if exist !chrome_paths[%%i]! (
        echo ✅ Chrome 브라우저를 찾았습니다: !chrome_paths[%%i]!
        echo.
        echo 🎉 설치가 완료되었습니다!
        pause
        exit /b 0
    )
)

echo ❌ Chrome 브라우저가 설치되지 않았습니다.
echo.
echo 📥 Chrome 브라우저를 다운로드하고 설치해야 합니다.
echo.
echo 다음 두 가지 방법 중 선택하세요:
echo.
echo 1️⃣ 자동으로 다운로드 페이지 열기
echo 2️⃣ 수동으로 설치하기
echo.

set /p choice="선택 (1 또는 2): "

if "%choice%"=="1" (
    echo.
    echo 🌐 Chrome 다운로드 페이지를 여는 중...
    start "" "https://www.google.com/chrome/"
    echo.
    echo 💡 다운로드가 완료되면 설치를 진행하고
    echo    설치 완료 후 이 프로그램을 다시 실행하세요.
) else if "%choice%"=="2" (
    echo.
    echo 📋 수동 설치 방법:
    echo.
    echo 1. 웹 브라우저에서 https://www.google.com/chrome/ 접속
    echo 2. "Chrome 다운로드" 클릭
    echo 3. 다운로드된 파일 실행
    echo 4. 설치 완료 후 이 프로그램 다시 실행
) else (
    echo ❌ 잘못된 선택입니다.
)

echo.
echo ⚠️  설치 완료 후 컴퓨터를 다시 시작하는 것을 권장합니다.
echo.
pause 