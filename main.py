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
            
          # ... (початок скрипта залишаємо таким самим)
        
        try:
            # 1. Збільшуємо тайм-аут завантаження сторінки до 60 секунд
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # 2. Перевіряємо, чи не заблокували нас (шукаємо текст про перевірку браузера)
            content = await page.content()
            if "Cloudflare" in content or "Pardon Our Interruption" in content:
                return {"status": "error", "step": "blocked", "details": "Сайт Copart заблокував запит (капча)"}

            # 3. Чекаємо на селектор довше (збільшуємо з 15 до 30 секунд)
            # Також додаємо перевірку на наявність тексту "No results found"
            try:
                await page.wait_for_selector('a[data-aid="lot-description"]', timeout=30000)
            except:
                if "No results found" in content:
                    return {"status": "success", "total": 0, "lots": [], "message": "Нічого не знайдено"}
                raise  # Якщо це не порожній пошук, то це справжній тайм-аут
            
            # ... (решта коду для збору даних)

    except Exception as e:
        return {"status": "error", "step": "general", "details": str(e)}
