from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Numeric, text
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import List, Dict, Any, Optional
import datetime
import requests
import feedparser
from bs4 import BeautifulSoup
import yfinance as yf
from src.config import DATABASE_URL

def get_historical_price_at_date(ticker: str, date: datetime.datetime) -> Optional[float]:
    try:
        t = yf.Ticker(ticker)
        start_str = date.strftime("%Y-%m-%d")
        # Try up to 7 days ahead to handle weekends/holidays when markets are closed
        end_dt = date + datetime.timedelta(days=7)
        end_str = end_dt.strftime("%Y-%m-%d")
        hist = t.history(start=start_str, end=end_str)
        if not hist.empty:
            return float(hist["Close"].iloc[0])
    except Exception as e:
        print(f"Error fetching historical price for {ticker} on {date}: {e}")
    return None


Base = declarative_base()

class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    accuracy_score = Column(Numeric(5, 2))
    alpha_outperformance = Column(Numeric(5, 2))
    system_verdict = Column(String(20))
    confidence_level = Column(Numeric(5, 2))

class NewsEvent(Base):
    __tablename__ = "news_events"
    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    summary = Column(Text)
    source = Column(String(100))
    link = Column(Text)
    published_at = Column(DateTime)
    sentiment_score = Column(Numeric(4, 2))
    embedding = Column(Text)  # Fallback to Text in SQLite, or pgvector Vector(1536) in PostgreSQL

class DatabaseClient:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL, connect_args={"timeout": 15} if DATABASE_URL.startswith("sqlite") else {})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def get_db(self):
        db = self.SessionLocal()
        try:
            return db
        finally:
            db.close()
            
    def get_asset(self, ticker: str) -> Optional[Dict[str, Any]]:
        db = self.SessionLocal()
        try:
            asset = db.query(Asset).filter(Asset.ticker == ticker.upper()).first()
            if not asset:
                return None
            return {
                "id": asset.id,
                "ticker": asset.ticker,
                "name": asset.name,
                "category": asset.category,
                "accuracy_score": float(asset.accuracy_score or 85.0),
                "alpha_outperformance": float(asset.alpha_outperformance or 0.0),
                "system_verdict": asset.system_verdict or "HOLD",
                "confidence_level": float(asset.confidence_level or 50.0)
            }
        finally:
            db.close()

    def get_similar_past_events(self, query_text: str, query_embedding: Optional[List[float]] = None, limit: int = 3, ticker: Optional[str] = None, current_price: Optional[float] = None) -> List[Dict[str, Any]]:
        db = self.SessionLocal()
        db_results = []
        year_2000 = datetime.datetime(2000, 1, 1)
        
        try:
            is_postgres = DATABASE_URL.startswith("postgresql")
            db_limit = limit * 2
            
            if is_postgres and query_embedding is not None:
                # PostgreSQL Vector Search query
                vector_str = f"[{','.join(map(str, query_embedding))}]"
                sql = text("""
                    SELECT id, title, summary, source, link, published_at, sentiment_score,
                           (embedding <=> :vector) AS distance
                    FROM news_events
                    WHERE (embedding <=> :vector) < 0.35 AND published_at >= '2000-01-01'
                    ORDER BY distance ASC
                    LIMIT :limit
                """)
                rows = db.execute(sql, {"vector": vector_str, "limit": db_limit}).fetchall()
                for row in rows:
                    db_results.append({
                        "id": row.id,
                        "title": row.title,
                        "summary": row.summary,
                        "source": row.source,
                        "link": row.link,
                        "published_at": row.published_at,
                        "sentiment_score": float(row.sentiment_score or 0.0),
                        "distance": float(row.distance)
                    })
            else:
                # SQLite fallback: keyword text search
                search_filter = f"%{query_text}%"
                events = db.query(NewsEvent).filter(
                    ((NewsEvent.title.ilike(search_filter)) | (NewsEvent.summary.ilike(search_filter))),
                    NewsEvent.published_at >= year_2000
                ).order_by(NewsEvent.published_at.desc()).limit(db_limit).all()
                
                for ev in events:
                    db_results.append({
                        "id": ev.id,
                        "title": ev.title,
                        "summary": ev.summary,
                        "source": ev.source,
                        "link": ev.link,
                        "published_at": ev.published_at,
                        "sentiment_score": float(ev.sentiment_score or 0.0),
                        "distance": 0.0 # dummy distance
                    })
        except Exception as e:
            print(f"Error querying database for similar events: {e}")
        finally:
            db.close()

        # Fetch from internet (Google News RSS feed)
        internet_results = []
        try:
            import urllib.parse
            encoded_query = urllib.parse.quote_plus(query_text)
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = requests.get(rss_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                feed = feedparser.parse(resp.text)
                for entry in feed.entries[:limit * 2]:
                    title = entry.get("title", "")
                    source = "Google News"
                    if " - " in title:
                        parts = title.rsplit(" - ", 1)
                        title = parts[0].strip()
                        source = parts[1].strip()
                        
                    summary = entry.get("summary", "")
                    if summary:
                        soup = BeautifulSoup(summary, "html.parser")
                        summary = soup.get_text().strip()
                        
                    link = entry.get("link", "")
                    
                    published_at = None
                    if entry.get("published_parsed"):
                        try:
                            published_at = datetime.datetime(*entry.published_parsed[:6])
                        except Exception:
                            pass
                    
                    if not published_at and entry.get("published"):
                        try:
                            import dateutil.parser
                            published_at = dateutil.parser.parse(entry.get("published"))
                        except Exception:
                            pass
                            
                    if not published_at:
                        published_at = datetime.datetime.utcnow()
                        
                    if published_at.tzinfo is not None:
                        published_at = published_at.replace(tzinfo=None)
                        
                    if published_at >= year_2000:
                        internet_results.append({
                            "id": None,
                            "title": title,
                            "summary": summary,
                            "source": source,
                            "link": link,
                            "published_at": published_at,
                            "sentiment_score": 0.0,
                            "distance": 0.5 # dummy distance
                        })
        except Exception as ie:
            print(f"Error fetching news from internet: {ie}")

        # Combine and deduplicate
        merged_events = []
        seen_links = set()
        
        for ev in db_results:
            link = ev.get("link")
            if link and link not in seen_links:
                seen_links.add(link)
                merged_events.append(ev)
                
        for ev in internet_results:
            link = ev.get("link")
            if link and link not in seen_links:
                seen_links.add(link)
                merged_events.append(ev)

        # Sort combined results
        has_real_distance = any(ev.get("id") is not None and ev.get("distance", 0.0) > 0.0 for ev in merged_events)
        if has_real_distance:
            merged_events.sort(key=lambda x: x.get("distance", 1.0))
        else:
            merged_events.sort(key=lambda x: x.get("published_at") or year_2000, reverse=True)

        selected_events = merged_events[:limit]
        
        # Populate historical price comparison
        results = []
        for ev in selected_events:
            pub_date = ev.get("published_at")
            hist_price = None
            price_change_pct = None
            
            if ticker and pub_date:
                hist_price = get_historical_price_at_date(ticker, pub_date)
                if hist_price is not None and current_price is not None:
                    price_change_pct = ((current_price - hist_price) / hist_price) * 100.0
            
            results.append({
                "id": ev.get("id"),
                "title": ev.get("title"),
                "summary": ev.get("summary"),
                "source": ev.get("source"),
                "link": ev.get("link"),
                "published_at": pub_date.isoformat() if isinstance(pub_date, datetime.datetime) else str(pub_date),
                "sentiment_score": float(ev.get("sentiment_score") or 0.0),
                "distance": float(ev.get("distance") or 0.0),
                "historical_price": round(hist_price, 4) if hist_price is not None else None,
                "price_change_pct": round(price_change_pct, 2) if price_change_pct is not None else None,
                "current_price": current_price
            })
            
        return results

db_client = DatabaseClient()
