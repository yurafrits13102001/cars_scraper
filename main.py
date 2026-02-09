from fastapi import FastAPI, Query
from playwright.async_api import async_playwright
import asyncio

app = FastAPI()

@app.get("/search")
async def search_copart(query: str = Query(..., description="Пошуковий запит, наприклад: BMW X5")):
    async with async_playwright() as p:
        # Запускаємо браузер
        browser = await p.chromium.launch(headless=True)
        # Додаємо User-Agent, щоб сайт не одразу розпізнав у нас бота
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Формуємо URL пошуку Copart
        search_url = f"https://www.copart.com/lotSearchResults?freeForm=true&searchTerm={query}"
        
        try:
            await page.goto(search_url, wait_until="networkidle", timeout=60000)
            
            # Чекаємо, поки завантажиться таблиця або список лотів
            # На Copart назви зазвичай знаходяться в посиланнях усередині таблиці
            await page.wait_for_selector('a[data-aid="lot-description"]', timeout=10000)
            
            # Збираємо дані: назву та посилання на лот
            lots = await page.eval_on_selector_all(
                'a[data-aid="lot-description"]',
                'elements => elements.map(el => ({ title: el.innerText, url: el.href }))'
            )
            
            await browser.close()
            return {"query": query, "total_found": len(lots), "lots": lots[:10]} # Повертаємо топ-10
            
        except Exception as e:
            await browser.close()
            return {"error": str(e), "message": "Не вдалося отримати дані. Можливо, сайт заблокував запит або змінив структуру."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
