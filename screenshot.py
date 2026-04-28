import asyncio
from playwright.async_api import async_playwright

APP_URL = "http://localhost:8501"
VIEWPORT = {"width": 1280, "height": 900}
OUTPUT_DIR = "/screenshots"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport=VIEWPORT, locale="de-DE")
        page = await context.new_page()
        await page.goto(APP_URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # Tab 1 = "Neuer Antrag" (default view = dashboard)
        await page.screenshot(path=f"{OUTPUT_DIR}/dashboard.png")
        print("OK: dashboard.png")
        
        # Tab 2 = "KI-Analyse"
        try:
            await page.locator("[data-baseweb='tab'] >> nth=1").click()
            await page.wait_for_timeout(2000)
        except:
            pass
        await page.screenshot(path=f"{OUTPUT_DIR}/antrag_pruefen.png")
        print("OK: antrag_pruefen.png")
        
        # Sidebar is always visible - just crop or take full page showing sidebar
        await page.screenshot(path=f"{OUTPUT_DIR}/einstellungen.png")
        print("OK: einstellungen.png")
        
        await browser.close()

asyncio.run(main())
