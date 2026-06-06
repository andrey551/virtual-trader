from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.services.mcp_client import mcp_client
from src.models.event import NewsEvent, EventAssetImpact
from src.workers.accuracy_worker import evaluate_active_recommendations
from decimal import Decimal
import datetime
import asyncio

# Main macroeconomic and geopolitical search queries to monitor
MONITORED_QUERIES = ["Federal Reserve", "OPEC", "inflation", "oil spill"]

async def fetch_and_save_news(query: str):
    """
    Calls the get_market_news MCP tool to crawl news feeds, saves new items to the DB,
    and maps asset impact correlations based on event keywords.
    """
    print(f"[News Worker] Scanning geopolitical feeds for query: '{query}'")
    try:
        res = await mcp_client.call_tool("get_market_news", {"query": query, "limit": 3})
        if res.get("status") != "success":
            print(f"[News Worker] MCP Tool returned error for query '{query}': {res.get('message')}")
            return
            
        articles = res.get("articles", [])
        db = SessionLocal()
        try:
            for art in articles:
                link = art.get("link")
                # Filter duplicates based on unique url link
                existing = db.query(NewsEvent).filter(NewsEvent.link == link).first()
                if existing:
                    continue
                    
                pub_date = datetime.datetime.utcnow()
                sentiment_val = art.get("sentimentScore", 0.0)
                
                # Write news event record
                event = NewsEvent(
                    title=art.get("title"),
                    summary=art.get("summary"),
                    source=art.get("source", "Google News"),
                    link=link,
                    published_at=pub_date,
                    sentiment_score=Decimal(str(sentiment_val))
                )
                db.add(event)
                db.commit()
                db.refresh(event)
                
                # Iterate and link affected assets dynamically based on keywords
                impacted = art.get("impactedAssets", [])
                for ticker in impacted:
                    direction = "NEUTRAL"
                    factor = Decimal("0.0")
                    if sentiment_val > 0.1:
                        direction = "POSITIVE"
                        factor = Decimal(str(sentiment_val))
                    elif sentiment_val < -0.1:
                        direction = "NEGATIVE"
                        factor = Decimal(str(sentiment_val))
                        
                    impact = EventAssetImpact(
                        event_id=event.id,
                        asset_ticker=ticker,
                        impact_direction=direction,
                        estimated_impact_factor=factor
                    )
                    db.add(impact)
                db.commit()
                print(f"[News Worker] Logged new event: '{event.title[:50]}...' [Sentiment: {sentiment_val}]")
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"[News Worker] Error scanning query '{query}': {str(e)}")

async def scan_all_topics():
    for q in MONITORED_QUERIES:
        await fetch_and_save_news(q)
        # Brief pause between calls to mitigate IP rate-limiting issues
        await asyncio.sleep(2)

scheduler = AsyncIOScheduler()

def start_scheduler():
    if not scheduler.running:
        # Set up recurring interval triggers
        scheduler.add_job(scan_all_topics, "interval", seconds=60, id="news_scanner_job", replace_existing=True)
        scheduler.add_job(evaluate_active_recommendations, "interval", seconds=30, id="accuracy_eval_job", replace_existing=True)
        scheduler.start()
        print("AsyncIOScheduler background worker initiated successfully with news and accuracy jobs.")

def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("AsyncIOScheduler background worker terminated cleanly.")
