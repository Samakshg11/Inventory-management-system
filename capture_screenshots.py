import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    os.makedirs("docs/screenshots", exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        # 1. Dashboard
        await page.goto("http://localhost:5001/")
        await page.wait_for_selector(".stat-card", timeout=5000)
        await asyncio.sleep(1)
        await page.screenshot(path="docs/screenshots/dashboard.png", full_page=True)
        print("Captured dashboard.png")

        # 2. Products Page
        await page.click("#nav-products")
        await asyncio.sleep(1.5)
        await page.screenshot(path="docs/screenshots/products.png", full_page=True)
        print("Captured products.png")

        # 3. Suppliers Page
        await page.click("#nav-suppliers")
        await asyncio.sleep(1.5)
        await page.screenshot(path="docs/screenshots/suppliers.png", full_page=True)
        print("Captured suppliers.png")

        # 4. Stock Operations Page
        await page.click("#nav-stock")
        await asyncio.sleep(1.5)
        await page.screenshot(path="docs/screenshots/stock.png", full_page=True)
        print("Captured stock.png")

        # 5. Reports Page
        await page.click("#nav-reports")
        await asyncio.sleep(1.5)
        await page.screenshot(path="docs/screenshots/reports.png", full_page=True)
        print("Captured reports.png")

        await browser.close()

asyncio.run(main())
