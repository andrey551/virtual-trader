import asyncio
import json
from datetime import datetime
from mcp.server.models import InitializationOptions
from mcp.server import Notification, Server
import mcp.types as types
from mcp.server.stdio import stdio_server
from playwright.async_api import async_playwright

# Khởi tạo MCP Server
server = Server("mcp-trading-python")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Định nghĩa các tool mà server này cung cấp"""
    return [
        types.Tool(
            name="get_market_price",
            description="Lấy dữ liệu giá và biến động thị trường của một mã tài sản (chứng khoán, crypto...) từ Yahoo Finance dưới dạng JSON.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Mã trading (Ví dụ: BTC-USD, AAPL, TSLA)",
                    }
                },
                "required": ["ticker"],
            },
        ),
        types.Tool(
            name="scrape_dynamic_page",
            description="Cào dữ liệu từ trang web bất kỳ sử dụng trình duyệt Playwright (JS dynamic rendering). Trả về dữ liệu dạng cấu trúc JSON.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL của trang web cần cào.",
                    },
                    "selectors": {
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                        "description": "Object mapping key đặt tên với CSS selector cần trích xuất (Ví dụ: {\"price\": \".price-class\", \"title\": \"h1\"}).",
                    },
                    "wait_selector": {
                        "type": "string",
                        "description": "CSS selector cần đợi hiển thị trước khi lấy dữ liệu (đảm bảo JS load xong).",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Thời gian chờ tối đa (ms), mặc định 30000.",
                    }
                },
                "required": ["url"],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Xử lý logic khi AI hoặc client gọi tool"""
    if name == "get_market_price":
        ticker = arguments.get("ticker")
        if not ticker:
            raise ValueError("Thiếu tham số ticker")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            try:
                url = f"https://finance.yahoo.com/quote/{ticker}"
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_selector("span[data-regular-market-price]", timeout=10000)

                price = await page.locator("span[data-regular-market-price]").text_content()
                
                # Biến động giá có thể nằm ở span có attribute data-price-change hoặc selector tương ứng
                change = ""
                try:
                    change = await page.locator("span[data-price-change]").text_content()
                except Exception:
                    # Fallback locator
                    try:
                        change = await page.locator("span[data-regular-market-price] + span").text_content()
                    except Exception:
                        pass

                await browser.close()

                result = {
                    "status": "success",
                    "ticker": ticker.upper(),
                    "price": price.strip() if price else "",
                    "change": change.strip() if change else "",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }

                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False)
                    )
                ]

            except Exception as e:
                await browser.close()
                result = {
                    "status": "error",
                    "ticker": ticker.upper(),
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False)
                    )
                ]

    elif name == "scrape_dynamic_page":
        url = arguments.get("url")
        selectors = arguments.get("selectors")
        wait_selector = arguments.get("wait_selector")
        timeout = arguments.get("timeout", 30000)

        if not url:
            raise ValueError("Thiếu tham số url")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=timeout)

                if wait_selector:
                    await page.wait_for_selector(wait_selector, timeout=timeout)

                extracted_data = {}
                title = await page.title()
                extracted_data["_page_title"] = title

                if selectors and isinstance(selectors, dict):
                    for key, selector in selectors.items():
                        try:
                            locator = page.locator(selector)
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
                            extracted_data[key] = f"Error: {str(sel_err)}"
                else:
                    # Mặc định lấy body text nếu không có selectors
                    body_text = await page.locator("body").text_content()
                    extracted_data["body_text"] = body_text.strip() if body_text else ""

                await browser.close()

                result = {
                    "status": "success",
                    "url": url,
                    "data": extracted_data,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False)
                    )
                ]

            except Exception as e:
                await browser.close()
                result = {
                    "status": "error",
                    "url": url,
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False)
                    )
                ]
    else:
        raise ValueError(f"Tool không tồn tại: {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-trading-python",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=Notification.options(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())