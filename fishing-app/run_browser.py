
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        
        print("Opening http://localhost:5173...")
        await page.goto("http://localhost:5173", wait_until="networkidle")
        
        # 페이지 로드 완료 대기
        await page.wait_for_selector("#root", timeout=5000)
        
        # 스크린샷 저장
        await page.screenshot(path="fishing_app_screenshot.png")
        print("Screenshot saved: fishing_app_screenshot.png")
        
        # 요소 확인
        title = await page.title()
        print(f"Page Title: {title}")
        
        # 주요 요소 확인
        has_navbar = await page.query_selector(".navbar") is not None
        print(f"Navbar exists: {has_navbar}")
        
        await asyncio.sleep(2)
        await browser.close()

asyncio.run(main())
