import argparse
import asyncio
import json
import os
import sys

# Ensure local directories can be resolved
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools.crawler import handle_scrape_dynamic_page
from src.tools.finance import handle_get_market_price, handle_get_historical_candles
from src.tools.crypto import handle_get_crypto_ticker
from src.tools.news import handle_get_market_news

async def run_tool(name: str, args: dict):
    print(f"Executing tool '{name}' with arguments: {json.dumps(args)}")
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
            print(f"Error: Unknown tool name '{name}'")
            return
            
        print("\n--- RESULT ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("--------------\n")
    except Exception as e:
        print(f"Exception during execution: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Test Virtual Trader MCP tools locally.")
    parser.add_argument("--tool", required=True, help="Name of the tool to execute (e.g. get_market_price, get_market_news).")
    parser.add_argument("--args", default="{}", help="JSON string representing the arguments (e.g. '{\"ticker\": \"AAPL\"}').")
    
    args = parser.parse_args()
    
    try:
        parsed_args = json.loads(args.args)
    except Exception as e:
        print(f"Error parsing args JSON: {str(e)}")
        sys.exit(1)
        
    asyncio.run(run_tool(args.tool, parsed_args))

if __name__ == "__main__":
    main()
