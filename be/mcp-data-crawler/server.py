import asyncio
import json
import os
import sys
from datetime import datetime

# Adjust python load path to resolve src modules correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.models import InitializationOptions
from mcp.server import Notification, Server
import mcp.types as types
from mcp.server.stdio import stdio_server

# Import tool handlers from modular src files
from src.tools.crawler import handle_scrape_dynamic_page
from src.tools.finance import handle_get_market_price, handle_get_historical_candles
from src.tools.crypto import handle_get_crypto_ticker
from src.tools.news import handle_get_market_news

server = Server("virtual-trader-mcp")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Define the tools this server provides"""
    return [
        types.Tool(
            name="scrape_dynamic_page",
            description="Scrape content from any website. Supports raw HTML retrieval or dynamic JS rendering.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The target website URL to scrape."
                    },
                    "selectors": {
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                        "description": "Optional mapping of keys to CSS Selectors. e.g. {'title': 'h1', 'price': '.price-tag'}"
                    },
                    "wait_selector": {
                        "type": "string",
                        "description": "Optional CSS selector to wait for before extracting data."
                    },
                    "raw_html": {
                        "type": "boolean",
                        "default": False,
                        "description": "If True, skips browser loading and performs a fast raw HTML scrape."
                    },
                    "auto_scroll": {
                        "type": "boolean",
                        "default": False,
                        "description": "If True, scroll down the page dynamically to trigger AJAX/lazy loads."
                    },
                    "timeout": {
                        "type": "integer",
                        "default": 30000,
                        "description": "Timeout limit in milliseconds."
                    }
                },
                "required": ["url"],
            }
        ),
        types.Tool(
            name="get_market_price",
            description="Retrieve near real-time pricing and changes for stocks, crypto, indices, and forex assets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Asset ticker symbol (e.g. AAPL, TSLA, BTC-USD, EURUSD=X, ^GSPC, ^VIX)."
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="get_historical_candles",
            description="Fetch historical OHLCV candle charts for technical analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Asset ticker symbol (e.g. AAPL, BTC-USD)."
                    },
                    "interval": {
                        "type": "string",
                        "enum": ["1m", "2m", "5m", "15m", "30m", "60m", "1h", "1d", "5d", "1wk", "1mo"],
                        "default": "1d",
                        "description": "Time interval between candles."
                    },
                    "period": {
                        "type": "string",
                        "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
                        "default": "1mo",
                        "description": "Historical duration to retrieve."
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="get_crypto_ticker",
            description="Retrieve instant prices and order book depth (bid/ask) from the Binance Exchange.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Binance symbol format (e.g. BTCUSDT, ETHUSDT, SOLUSDT)."
                    },
                    "depth": {
                        "type": "integer",
                        "default": 10,
                        "description": "Number of bid/ask levels to fetch (max 100)."
                    }
                },
                "required": ["symbol"]
            }
        ),
        types.Tool(
            name="get_market_news",
            description="Fetch global economic and financial news, calculate keyword sentiment, and map relevant assets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query or ticker to scan for (e.g. 'OPEC', 'Federal Reserve', 'NVIDIA')."
                    },
                    "limit": {
                        "type": "integer",
                        "default": 5,
                        "description": "Maximum number of articles to return."
                    }
                },
                "required": ["query"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    """Execute the matching tool function based on name"""
    args = arguments or {}
    try:
        if name == "scrape_dynamic_page":
            result = await handle_scrape_dynamic_page(args)
        elif name == "get_market_price":
            result = await handle_get_market_price(args)
        elif name == "get_historical_candles":
            result = await handle_get_historical_candles(args)
        elif name == "get_crypto_ticker":
            result = await handle_get_crypto_ticker(args)
        elif name == "get_market_news":
            result = await handle_get_market_news(args)
        else:
            raise ValueError(f"Unknown tool: {name}")
            
        return [
            types.TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False)
            )
        ]
    except Exception as e:
        error_result = {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        return [
            types.TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )
        ]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="virtual-trader-mcp",
                server_version="2.0.0",
                capabilities=server.get_capabilities(
                    notification_options=Notification.options(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())