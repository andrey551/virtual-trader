import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from playwright.async_api import async_playwright

async def handle_scrape_dynamic_page(arguments: dict) -> dict:
    url = arguments.get("url")
    if not url:
        raise ValueError("Missing parameter 'url'")
        
    selectors = arguments.get("selectors")
    wait_selector = arguments.get("wait_selector")
    raw_html = arguments.get("raw_html", False)
    auto_scroll = arguments.get("auto_scroll", False)
    timeout = arguments.get("timeout", 30000)
    
    try:
        timeout = int(timeout)
    except (ValueError, TypeError):
        timeout = 30000
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Fast flow: skip browser initialization, perform straight HTTP get
    if raw_html:
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=timeout/1000.0) as response:
                    if response.status != 200:
                        raise ValueError(f"HTTP GET returned status code {response.status}")
                    html_content = await response.text()
                    
            soup = BeautifulSoup(html_content, "html.parser")
            page_title = soup.title.string.strip() if soup.title else ""
            
            extracted_data = {}
            extracted_data["_page_title"] = page_title
            
            if selectors and isinstance(selectors, dict):
                for key, sel in selectors.items():
                    elements = soup.select(sel)
                    if not elements:
                        extracted_data[key] = None
                    elif len(elements) == 1:
                        extracted_data[key] = elements[0].get_text(strip=True)
                    else:
                        extracted_data[key] = [el.get_text(strip=True) for el in elements]
            else:
                # Strip style, script, footer, header to get meaningful content only
                for element in soup(["script", "style", "header", "footer", "nav"]):
                    element.extract()
                extracted_data["body_text"] = soup.get_text(separator=" ", strip=True)
                
            return {
                "status": "success",
                "url": url,
                "engine": "aiohttp-raw-html",
                "data": extracted_data,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as raw_err:
            return {
                "status": "error",
                "url": url,
                "engine": "aiohttp-raw-html",
                "message": f"Raw HTML fetch failed: {str(raw_err)}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
    # Full browser flow via Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=headers["User-Agent"],
            viewport={"width": 1280, "height": 800}
        )
        
        # Optimize performance by blocking heavy assets
        async def block_resources(route):
            if route.request.resource_type in ["image", "font", "media"]:
                await route.abort()
            else:
                await route.continue_()
                
        page = await context.new_page()
        await page.route("**/*", block_resources)
        
        try:
            # Load page
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            
            # Wait for specific visual elements
            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=timeout)
                
            # Scroll down slowly if lazy load is enabled
            if auto_scroll:
                await page.evaluate("""
                    async () => {
                        await new Promise((resolve) => {
                            let totalHeight = 0;
                            let distance = 150;
                            let timer = setInterval(() => {
                                let scrollHeight = document.body.scrollHeight;
                                window.scrollBy(0, distance);
                                totalHeight += distance;
                                if(totalHeight >= scrollHeight || totalHeight > 4000){
                                    clearInterval(timer);
                                    resolve();
                                }
                            }, 50);
                        });
                    }
                """)
                await page.wait_for_timeout(300)
                
            extracted_data = {}
            page_title = await page.title()
            extracted_data["_page_title"] = page_title
            
            if selectors and isinstance(selectors, dict):
                for key, sel in selectors.items():
                    try:
                        locator = page.locator(sel)
                        count = await locator.count()
                        if count == 0:
                            extracted_data[key] = None
                        elif count == 1:
                            txt = await locator.text_content()
                            extracted_data[key] = txt.strip() if txt else ""
                        else:
                            txts = await locator.all_text_contents()
                            extracted_data[key] = [t.strip() for t in txts]
                    except Exception as sel_err:
                        extracted_data[key] = f"Selector Error: {str(sel_err)}"
            else:
                # Extract clean innerText, strip script, style, nav, header, footer elements
                body_txt = await page.evaluate("""() => {
                    const el = document.body.cloneNode(true);
                    const clean_targets = el.querySelectorAll('script, style, nav, footer, header');
                    clean_targets.forEach(t => t.remove());
                    return el.innerText;
                }""")
                extracted_data["body_text"] = body_txt.strip() if body_txt else ""
                
            await browser.close()
            return {
                "status": "success",
                "url": url,
                "engine": "playwright-chromium",
                "data": extracted_data,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as browser_err:
            await browser.close()
            return {
                "status": "error",
                "url": url,
                "engine": "playwright-chromium",
                "message": f"Browser rendering failed: {str(browser_err)}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
