import asyncio
import aiohttp
from datetime import datetime
from src.utils.cache import global_cache

async def handle_get_crypto_ticker(arguments: dict) -> dict:
    symbol_str = arguments.get("symbol")
    if not symbol_str:
        raise ValueError("Missing parameter 'symbol'")
        
    # Standardize symbol (e.g. BTC-USDT or BTC/USDT to BTCUSDT)
    symbol_upper = symbol_str.upper().replace("-", "").replace("/", "").replace(" ", "")
    depth = arguments.get("depth", 10)
    
    try:
        depth = max(1, min(100, int(depth)))
    except (ValueError, TypeError):
        depth = 10
        
    cache_key = f"crypto_{symbol_upper}_{depth}"
    cached = global_cache.get(cache_key)
    if cached:
        return cached
        
    price_url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol_upper}"
    depth_url = f"https://api.binance.com/api/v3/depth?symbol={symbol_upper}&limit={depth}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async def fetch_json(url: str) -> dict:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        err_text = await response.text()
                        raise ValueError(f"Binance API returned HTTP {response.status}: {err_text}")
                    return await response.json()
            
            # Retrieve price and depth concurrently
            price_task = fetch_json(price_url)
            depth_task = fetch_json(depth_url)
            
            price_data, depth_data = await asyncio.gather(price_task, depth_task)
            
            price = float(price_data.get("price", 0.0))
            bids = depth_data.get("bids", [])
            asks = depth_data.get("asks", [])
            
            # Format bids/asks to floating numbers for clean mathematical calculations by AI agents
            formatted_bids = [[float(b[0]), float(b[1])] for b in bids]
            formatted_asks = [[float(a[0]), float(a[1])] for a in asks]
            
            result = {
                "status": "success",
                "symbol": symbol_upper,
                "price": price,
                "bids": formatted_bids,
                "asks": formatted_asks,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            # Cache crypto details for 5 seconds
            global_cache.set(cache_key, result, 5)
            return result
            
    except Exception as e:
        return {
            "status": "error",
            "symbol": symbol_upper,
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
