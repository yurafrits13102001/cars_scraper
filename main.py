from fastapi import FastAPI, Query
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import os
os.system("playwright install chromium")

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Copart Scraper is live!"}

@app.get("/search")
async def search_copart(query: str = Query(..., description="Запит для Copart")):
    try:
        async with async_playwright() as p:
            # 1. Запуск браузера
            try:
                browser = await p.chromium.launch(headless=True)
            except Exception as launch_error:
                return {"status": "error", "step": "browser_launch", "details": str(launch_error)}

            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # 2. Формуємо URL
            url = f"https://www.copart.com/lotSearchResults?freeForm=true&searchTerm={query}"
            
            try:
                # 3. Перехід на сайт (чекаємо до 60 сек)
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # 4. Перевірка на капчу/блокування
                content = await page.content()
                if "Pardon Our Interruption" in content or "Cloudflare" in content:
                    await browser.close()
                    return {"status": "error", "step": "blocked", "details": "Сайт Copart заблокував запит"}

                # 5. Очікування результатів (30 сек)
                try:
                    await page.wait_for_selector('a[data-aid="lot-description"]', timeout=30000)
                except:
                    if "No results found" in content or "0 Results" in content:
                        await browser.close()
                        return {"status": "success", "total": 0, "lots": [], "message": "Нічого не знайдено"}
                    await browser.close()
                    return {"status": "error", "step": "timeout", "details": "Сторінка вантажилася занадто довго (30с+)"}

                # 6. Збір даних
                lots = await page.eval_on_selector_all(
                    'a[data-aid="lot-description"]',
                    'elements => elements.map(el => ({ title: el.innerText, url: el.href }))'
                )
                
                await browser.close()
                return {"query": query, "total": len(lots), "lots": lots[:10]}

            except Exception as nav_error:
                await browser.close()
                return {"status": "error", "step": "navigation", "details": str(nav_error)}

    except Exception as e:
        return {"status": "error", "step": "general", "details": str(e)}
