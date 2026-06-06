from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Numeric, ForeignKey, text
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

class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    entity_type = Column(String(50), nullable=False)
    description = Column(Text)

class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"
    id = Column(Integer, primary_key=True)
    source_node_id = Column(Integer, ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id = Column(Integer, ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String(50), nullable=False)
    strength = Column(Numeric(4, 2))
    description = Column(Text)

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
            
    def get_related_knowledge_paths(self, ticker: str) -> List[str]:
        db = self.SessionLocal()
        paths = []
        try:
            ticker_upper = ticker.upper()
            # 1. Find asset node
            asset_node = db.query(KnowledgeNode).filter(
                KnowledgeNode.name == ticker_upper,
                KnowledgeNode.entity_type == "ASSET"
            ).first()
            
            if not asset_node:
                return []
                
            # 2. Walk edges within 2-hops
            direct_edges = db.query(KnowledgeEdge).filter(
                (KnowledgeEdge.source_node_id == asset_node.id) |
                (KnowledgeEdge.target_node_id == asset_node.id)
            ).all()
            
            visited_edges = set()
            
            for edge in direct_edges:
                visited_edges.add(edge.id)
                src = db.query(KnowledgeNode).filter(KnowledgeNode.id == edge.source_node_id).first()
                tgt = db.query(KnowledgeNode).filter(KnowledgeNode.id == edge.target_node_id).first()
                if src and tgt:
                    paths.append(
                        f"- {src.name} ({src.entity_type}) --[{edge.relationship_type}]--> "
                        f"{tgt.name} ({tgt.entity_type}) [Strength: {float(edge.strength or 0.50):.2f}]"
                    )
                    
                    # Second hop
                    neighbor_id = edge.source_node_id if edge.target_node_id == asset_node.id else edge.target_node_id
                    neighbor_node = src if edge.target_node_id == asset_node.id else tgt
                    
                    if neighbor_node and neighbor_node.entity_type in ["SECTOR", "INDICATOR", "ABSTRACT_EVENT"]:
                        second_edges = db.query(KnowledgeEdge).filter(
                            (KnowledgeEdge.source_node_id == neighbor_id) |
                            (KnowledgeEdge.target_node_id == neighbor_id)
                        ).all()
                        for s_edge in second_edges:
                            if s_edge.id not in visited_edges:
                                visited_edges.add(s_edge.id)
                                s_src = db.query(KnowledgeNode).filter(KnowledgeNode.id == s_edge.source_node_id).first()
                                s_tgt = db.query(KnowledgeNode).filter(KnowledgeNode.id == s_edge.target_node_id).first()
                                if s_src and s_tgt:
                                    paths.append(
                                        f"  * Path extension: {s_src.name} ({s_src.entity_type}) --[{s_edge.relationship_type}]--> "
                                        f"{s_tgt.name} ({s_tgt.entity_type}) [Strength: {float(s_edge.strength or 0.50):.2f}]"
                                    )
                                    
        except Exception as e:
            print(f"Error querying knowledge paths for {ticker}: {e}")
        finally:
            db.close()
        return paths

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

    def calculate_technical_indicators(self, ticker: str) -> Dict[str, Any]:
        """
        Calculates key market indicators (RSI, MACD, 50-day SMA, Volume, etc.)
        for the given ticker using yfinance.
        """
        import pandas as pd
        import numpy as np
        import yfinance as yf
        
        print(f"[Indicators Engine] Computing metrics for {ticker}...")
        
        # Default fallback indicators
        default_indicators = {
            "price": 0.0,
            "change_percent": 0.0,
            "rsi": 50.0,
            "macd_line": 0.0,
            "macd_signal": 0.0,
            "macd_hist": 0.0,
            "macd_verdict": "Neutral",
            "sma_50": 0.0,
            "sma_50_verdict": "Neutral",
            "volume_24h": 0.0,
            "volume_avg_50d": 0.0,
            "volume_surge_ratio": 1.0,
            "status": "FALLBACK"
        }
        
        try:
            t = yf.Ticker(ticker)
            # Fetch 3 months of daily candle data to cover 50 days SMA
            df = t.history(period="3mo", interval="1d")
            
            if df.empty or len(df) < 15:
                print(f"[Indicators Engine] Warning: Not enough candle data for {ticker}. Using fallback indicators.")
                return default_indicators
                
            close_prices = df["Close"]
            last_price = float(close_prices.iloc[-1])
            
            # 1. 24h Change Percent
            prev_price = float(close_prices.iloc[-2]) if len(close_prices) > 1 else last_price
            change_pct = ((last_price - prev_price) / prev_price) * 100.0 if prev_price > 0 else 0.0
            
            # 2. RSI (14-period)
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            
            rs = gain / (loss + 1e-9)
            rsi_series = 100 - (100 / (1 + rs))
            current_rsi = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50.0
            
            # 3. MACD (12, 26, 9)
            ema_12 = close_prices.ewm(span=12, adjust=False).mean()
            ema_26 = close_prices.ewm(span=26, adjust=False).mean()
            macd_line = ema_12 - ema_26
            macd_signal = macd_line.ewm(span=9, adjust=False).mean()
            macd_hist = macd_line - macd_signal
            
            curr_macd = float(macd_line.iloc[-1])
            curr_signal = float(macd_signal.iloc[-1])
            curr_hist = float(macd_hist.iloc[-1])
            
            # MACD Crossover Verdict
            macd_verdict = "Neutral"
            if len(macd_hist) >= 2:
                prev_hist = float(macd_hist.iloc[-2])
                if prev_hist <= 0 < curr_hist:
                    macd_verdict = "Bullish Crossover"
                elif prev_hist >= 0 > curr_hist:
                    macd_verdict = "Bearish Crossover"
                elif curr_hist > 0:
                    macd_verdict = "Bullish Momentum"
                elif curr_hist < 0:
                    macd_verdict = "Bearish Momentum"
            
            # 4. SMA (50-period)
            sma_50_series = close_prices.rolling(window=50).mean()
            if len(close_prices) < 50:
                sma_50_series = close_prices.rolling(window=len(close_prices)).mean()
            curr_sma_50 = float(sma_50_series.iloc[-1]) if not pd.isna(sma_50_series.iloc[-1]) else last_price
            
            sma_50_verdict = "Bullish (Above 50 MA)" if last_price > curr_sma_50 else "Bearish (Below 50 MA)"
            
            # 5. Volume metrics
            volume_series = df["Volume"]
            curr_vol = float(volume_series.iloc[-1])
            avg_vol = float(volume_series.rolling(window=50).mean().iloc[-1]) if len(volume_series) >= 50 else float(volume_series.mean())
            surge_ratio = curr_vol / (avg_vol + 1e-9)
            
            print(f"[Indicators Engine] Completed calculations for {ticker}: Price={last_price:.2f}, RSI={current_rsi:.2f}, Volume Surge={surge_ratio:.2f}x")
            
            return {
                "price": round(last_price, 4),
                "change_percent": round(change_pct, 2),
                "rsi": round(current_rsi, 2),
                "macd_line": round(curr_macd, 4),
                "macd_signal": round(curr_signal, 4),
                "macd_hist": round(curr_hist, 4),
                "macd_verdict": macd_verdict,
                "sma_50": round(curr_sma_50, 4),
                "sma_50_verdict": sma_50_verdict,
                "volume_24h": int(curr_vol),
                "volume_avg_50d": int(avg_vol),
                "volume_surge_ratio": round(surge_ratio, 2),
                "status": "SUCCESS"
            }
            
        except Exception as e:
            print(f"[Indicators Engine] Error calculating indicators: {e}")
            return default_indicators

db_client = DatabaseClient()
