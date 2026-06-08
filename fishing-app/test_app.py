import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Collect console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append({
            "type": msg.type,
            "text": msg.text
        }))

        # Collect page errors
        page_errors = []
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        print("Opening http://localhost:5182...")
        try:
            response = await page.goto("http://localhost:5182", wait_until="networkidle", timeout=10000)
            print(f"Response status: {response.status if response else 'None'}")
        except Exception as e:
            print(f"Error loading page: {e}")
            await browser.close()
            return

        # Wait a bit for the app to fully load
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Take a screenshot
        await page.screenshot(path="/d/DEV/fishing-app/app_screenshot.png")
        print("Screenshot saved: app_screenshot.png")

        # Check page title
        title = await page.title()
        print(f"Page Title: {title}")

        # Check for main content
        try:
            root = await page.query_selector("#root")
            print(f"Root element exists: {root is not None}")
        except Exception as e:
            print(f"Error checking root: {e}")

        # Check for any errors in console
        print("\n=== Console Messages ===")
        for msg in console_messages:
            print(f"[{msg['type'].upper()}] {msg['text']}")

        if page_errors:
            print("\n=== Page Errors ===")
            for err in page_errors:
                print(f"Error: {err}")

        # Try to interact with the app - look for elements
        print("\n=== Testing Element Detection ===")
        try:
            # Look for common elements
            navbar = await page.query_selector(".navbar, [role='navigation']")
            print(f"Navigation element found: {navbar is not None}")

            buttons = await page.locator("button").count()
            print(f"Number of buttons: {buttons}")

            inputs = await page.locator("input").count()
            print(f"Number of input fields: {inputs}")
        except Exception as e:
            print(f"Error checking elements: {e}")

        # Check for API connectivity
        print("\n=== Testing API Connectivity ===")
        try:
            response = await page.evaluate("""
                async () => {
                    try {
                        const res = await fetch('http://localhost:5000/api/health');
                        return await res.json();
                    } catch(e) {
                        return { error: e.message };
                    }
                }
            """)
            print(f"API Health Check: {response}")
        except Exception as e:
            print(f"Error checking API: {e}")

        print("\nKeeping browser open for 5 seconds for manual inspection...")
        await asyncio.sleep(5)

        await browser.close()

        # Summary
        print("\n=== Summary ===")
        print(f"Total console messages: {len(console_messages)}")
        print(f"Total page errors: {len(page_errors)}")

asyncio.run(main())
