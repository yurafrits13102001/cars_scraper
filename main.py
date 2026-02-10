import os
os.system("playwright install chromium")
from fastapi import FastAPI, Query
from playwright.async_api import async_playwright

app = FastAPI()

# Додаємо головну сторінку, щоб не було 404
@app.get("/")
async def root():
    return {"message": "Copart Scraper is running! Use /search?query=car_name"}

@app.get("/search")
async def search_copart(query: str = Query(..., description="Пошук, наприклад: BMW X5")):
    try:
        async with async_playwright() as p:
            # Спробуємо запустити браузер
            try:
                browser = await p.chromium.launch(headless=True)
            except Exception as launch_error:
                return {"status": "error", "step": "browser_launch", "details": str(launch_error)}

            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # Логіка пошуку
            url = f"https://www.copart.com/lotSearchResults?freeForm=true&searchTerm={query}"
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Чекаємо на селектор назв лотів
            await page.wait_for_selector('a[data-aid="lot-description"]', timeout=15000)
            
            lots = await page.eval_on_selector_all(
                'a[data-aid="lot-description"]',
                'elements => elements.map(el => ({ title: el.innerText, url: el.href }))'
            )
            
            await browser.close()
            return {"query": query, "total": len(lots), "lots": lots[:5]}

    except Exception as e:
        return {"status": "error", "step": "general", "details": str(e)}
