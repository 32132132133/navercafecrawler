"""driver.py
Selenium WebDriver factory for the Naver Cafe crawler.

This module centralises the browser–driver boot-strapping logic so the rest
of the codebase can stay focused on crawling concerns.
The factory takes care of:
  • Choosing an available browser (Chrome → Edge fallback)
  • Applying the project-wide Config options (HEADLESS, WINDOW_SIZE, user-agent …)
  • Hiding automation fingerprints where possible

Usage
-----
from driver import create_driver

driver = create_driver()  # returns an initialised WebDriver or None
"""
# Disclaimer: use at your own risk. The authors take no responsibility for misuse.

from __future__ import annotations

import sys
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

try:
    # Edge is optional runtime dependency – import lazily
    from selenium.webdriver.edge.options import Options as EdgeOptions
    from selenium.webdriver.edge.service import Service as EdgeService
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
except ImportError:  # pragma: no cover – Edge deps not installed
    EdgeOptions = None  # type: ignore
    EdgeService = None  # type: ignore

from config import Config

__all__ = ["create_driver"]


# ---------------------------------------------------------------------------
# _helpers
# ---------------------------------------------------------------------------

def _apply_common_options(options, *, headless: bool):
    """Apply flags that should be common to all Chromium-based browsers."""
    if headless:
        options.add_argument("--headless")

    options.add_argument(f"--window-size={Config.WINDOW_SIZE[0]},{Config.WINDOW_SIZE[1]}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # Hide the Chrome "Chrome is being controlled by automated software" infobar
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)


# ---------------------------------------------------------------------------
# factory
# ---------------------------------------------------------------------------

def create_driver() -> Optional[webdriver.Remote]:
    """Return an initialised Selenium *WebDriver* or *None* if no browser is available.

    The factory first tries Chrome because it provides the most stable support
    for Selenium. If Chrome isn't available, it falls back to Microsoft Edge
    (which is Chromium-based under the hood).
    """

    # ---------------------------------------------------------------------
    # 1️⃣  Try Chrome first
    # ---------------------------------------------------------------------
    try:
        print("Chrome 브라우저 설정 시도 중…")
        chrome_options = ChromeOptions()
        _apply_common_options(chrome_options, headless=Config.HEADLESS)

        # Spoof User-Agent – this reduces the chance of being blocked
        chrome_options.add_argument(
            "--user-agent="
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Remove Selenium webdriver flag
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("✅ Chrome 드라이버 설정 완료")
        return driver

    except Exception as chrome_error:
        print(f"Chrome 설정 실패: {chrome_error}")

    # ---------------------------------------------------------------------
    # 2️⃣  Fallback: Microsoft Edge
    # ---------------------------------------------------------------------
    if EdgeOptions is None or EdgeService is None:
        # Edge deps not available – skip silently so we can print consistent error later
        edge_error: Optional[Exception] = None
    else:
        try:
            print("Edge 브라우저 설정 시도 중…")
            edge_options = EdgeOptions()
            _apply_common_options(edge_options, headless=Config.HEADLESS)

            edge_options.add_argument(
                "--user-agent="
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
            )

            service = EdgeService(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=edge_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✅ Edge 드라이버 설정 완료")
            return driver
        except Exception as e:
            edge_error = e
            print(f"Edge 설정 실패: {edge_error}")

    # ---------------------------------------------------------------------
    # 3️⃣  No supported browser found
    # ---------------------------------------------------------------------
    print("\n❌ 사용 가능한 브라우저를 찾을 수 없습니다.")
    print("\n📋 해결 방법:")
    print("1. Chrome 브라우저 설치: https://www.google.com/chrome/")
    print("2. 또는 install_chrome.bat 실행")
    print("3. Edge는 Windows에 기본 설치되어 있어야 합니다.")
    print("\n💡 설치 후 프로그램을 다시 실행하세요.")

    return None 