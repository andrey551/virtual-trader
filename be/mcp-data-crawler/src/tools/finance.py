from datetime import datetime
import yfinance as yf
from src.utils.cache import global_cache

def format_large_number(num):
    if num is None:
        return "N/A"
    try:
        num = float(num)
        if num >= 1e12:
            return f"${num / 1e12:.2f}T"
        elif num >= 1e9:
            return f"${num / 1e9:.2f}B"
        elif num >= 1e6:
            return f"${num / 1e6:.2f}M"
        else:
            return f"${num:,.2f}"
    except Exception:
        return "N/A"

async def handle_get_market_price(arguments: dict) -> dict:
    ticker_str = arguments.get("ticker")
    if not ticker_str:
        raise ValueError("Missing parameter 'ticker'")
    
    ticker_upper = ticker_str.upper()
    cache_key = f"price_{ticker_upper}"
    
    # Check cache (15 seconds TTL)
    cached = global_cache.get(cache_key)
    if cached:
        return cached
        
    try:
        t = yf.Ticker(ticker_upper)
        
        last_price = None
        prev_close = None
        currency = "USD"
        
        # Level 1: try fast_info (extremely fast, doesn't fetch web pages)
        try:
            info = t.fast_info
            last_price = info.get("last_price")
            prev_close = info.get("previous_close")
            currency = info.get("currency", "USD")
        except Exception:
            pass
            
        # Level 2: try t.info dictionary (fetches full profile JSON)
        if last_price is None or prev_close is None:
            try:
                info_full = t.info
                if last_price is None:
                    last_price = info_full.get("currentPrice") or info_full.get("regularMarketPrice") or info_full.get("navPrice")
                if prev_close is None:
                    prev_close = info_full.get("regularMarketPreviousClose") or info_full.get("previousClose")
                currency = info_full.get("currency") or currency
            except Exception:
                pass
                
        # Level 3: try fetching recent history (OHLCV candles)
        if last_price is None or prev_close is None:
            try:
                hist = t.history(period="5d")
                if not hist.empty:
                    if last_price is None:
                        last_price = float(hist["Close"].iloc[-1])
                    if prev_close is None:
                        if len(hist) > 1:
                            prev_close = float(hist["Close"].iloc[-2])
                        else:
                            prev_close = float(hist["Open"].iloc[-1])
            except Exception:
                pass
                
        if last_price is None:
            raise ValueError(f"Could not retrieve market price for ticker: {ticker_upper}")
            
        # Calculate change absolute and percent
        change = 0.0
        change_percent = 0.0
        if prev_close:
            change = last_price - prev_close
            change_percent = (change / prev_close) * 100.0
            
        # Fetch detailed metrics (market cap, volume, P/E, name)
        market_cap_val = None
        volume_val = None
        pe_ratio_val = None
        long_name_val = ticker_upper
        
        try:
            f_info = t.fast_info
            market_cap_val = f_info.get("market_cap")
            volume_val = f_info.get("last_volume")
        except Exception:
            pass
            
        try:
            info_full = t.info
            long_name_val = info_full.get("longName") or info_full.get("shortName") or long_name_val
            if not market_cap_val:
                market_cap_val = info_full.get("marketCap")
            if not volume_val:
                volume_val = info_full.get("volume") or info_full.get("regularMarketVolume") or info_full.get("volume24h")
            pe_ratio_val = info_full.get("trailingPE") or info_full.get("forwardPE")
        except Exception:
            pass
            
        result = {
            "status": "success",
            "ticker": ticker_upper,
            "name": long_name_val,
            "price": round(last_price, 4),
            "change": round(change, 4),
            "changePercent": round(change_percent, 2),
            "currency": currency,
            "marketCap": format_large_number(market_cap_val),
            "volume24h": format_large_number(volume_val),
            "peRatio": f"{pe_ratio_val:.2f}" if pe_ratio_val is not None else None,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Save to cache for 15s
        global_cache.set(cache_key, result, 15)
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "ticker": ticker_upper,
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

async def handle_get_historical_candles(arguments: dict) -> dict:
    ticker_str = arguments.get("ticker")
    if not ticker_str:
        raise ValueError("Missing parameter 'ticker'")
        
    ticker_upper = ticker_str.upper()
    interval = arguments.get("interval", "1d")
    period = arguments.get("period", "1mo")
    
    # Supported yfinance intervals and periods
    valid_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
    valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
    
    if interval not in valid_intervals:
        interval = "1d"
    if period not in valid_periods:
        period = "1mo"
        
    cache_key = f"candles_{ticker_upper}_{interval}_{period}"
    
    # Check cache (30 minutes TTL = 1800s)
    cached = global_cache.get(cache_key)
    if cached:
        return cached
        
    try:
        t = yf.Ticker(ticker_upper)
        df = t.history(period=period, interval=interval)
        
        if df.empty:
            raise ValueError(f"No historical data returned for ticker {ticker_upper} with period {period} and interval {interval}")
            
        candles = []
        for idx, row in df.iterrows():
            time_str = idx.isoformat()
            candles.append({
                "time": time_str,
                "open": round(float(row["Open"]), 4),
                "high": round(float(row["High"]), 4),
                "low": round(float(row["Low"]), 4),
                "close": round(float(row["Close"]), 4),
                "volume": int(row["Volume"])
            })
            
        result = {
            "status": "success",
            "ticker": ticker_upper,
            "interval": interval,
            "period": period,
            "candles": candles,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Cache candles for 30 minutes
        global_cache.set(cache_key, result, 1800)
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "ticker": ticker_upper,
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
