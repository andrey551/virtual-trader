import urllib.parse
import aiohttp
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from src.utils.cache import global_cache
from src.utils.sentiment import analyze_sentiment

# Mapping event keywords to assets affected
EVENT_IMPACT_MAP = {
    "oil spill": ["USO", "CL=F", "XOM", "CVX", "BP", "SHEL"],
    "spill": ["USO", "CL=F", "XOM", "CVX"],
    "opec": ["USO", "CL=F", "XOM", "CVX", "COP"],
    "crude oil": ["USO", "CL=F"],
    "fed rate": ["^GSPC", "QQQ", "DIA", "TLT", "GLD", "UUP"],
    "interest rate": ["^GSPC", "QQQ", "TLT", "GLD"],
    "inflation": ["^GSPC", "TLT", "GLD", "UUP"],
    "cpi": ["^GSPC", "QQQ", "TLT", "GLD"],
    "semiconductor": ["NVDA", "SMH", "SOXX", "TSMC", "AMD", "INTC"],
    "chip": ["NVDA", "AMD", "INTC", "TSMC"],
    "taiwan": ["TSMC", "SMH", "EWT"],
    "crypto ban": ["BTC-USD", "ETH-USD", "COIN", "MARA", "RIOT"],
    "halving": ["BTC-USD", "COIN", "MARA"],
    "china tariff": ["FXI", "KWEB", "AAPL", "TSLA"]
}

async def handle_get_market_news(arguments: dict) -> dict:
    query = arguments.get("query")
    if not query:
        raise ValueError("Missing parameter 'query'")
        
    limit = arguments.get("limit", 5)
    try:
        limit = max(1, min(20, int(limit)))
    except (ValueError, TypeError):
        limit = 5
        
    cache_key = f"news_{query}_{limit}"
    cached = global_cache.get(cache_key)
    if cached:
        return cached
        
    encoded_query = urllib.parse.quote_plus(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(rss_url, timeout=15) as response:
                if response.status != 200:
                    raise ValueError(f"Google News RSS request returned HTTP status {response.status}")
                xml_data = await response.text()
                
        # Parse RSS using feedparser
        feed = feedparser.parse(xml_data)
        
        articles = []
        for entry in feed.entries[:limit]:
            # Remove HTML tags in summary
            summary_html = entry.get("summary", "")
            soup = BeautifulSoup(summary_html, "html.parser")
            summary_text = soup.get_text().strip()
            
            # Clean headline title and extract source (e.g. "US Core CPI Rises - Reuters" -> title: "US Core CPI Rises", source: "Reuters")
            title = entry.get("title", "")
            source = "Google News"
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                title = parts[0].strip()
                source = parts[1].strip()
                
            # Perform sentiment analysis on combined title and content summary
            combined_text = f"{title}. {summary_text}"
            sentiment_score = analyze_sentiment(combined_text)
            
            # Match keywords to assets
            impacted_assets = []
            combined_lower = combined_text.lower()
            for event_kw, tickers in EVENT_IMPACT_MAP.items():
                if event_kw in combined_lower:
                    for ticker in tickers:
                        if ticker not in impacted_assets:
                            impacted_assets.append(ticker)
                            
            articles.append({
                "title": title,
                "source": source,
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "summary": summary_text,
                "sentimentScore": round(sentiment_score, 2),
                "impactedAssets": impacted_assets
            })
            
        result = {
            "status": "success",
            "query": query,
            "articles": articles,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Cache for 5 minutes (300 seconds)
        global_cache.set(cache_key, result, 300)
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "query": query,
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
