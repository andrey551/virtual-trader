from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Numeric, text
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import List, Dict, Any, Optional
import datetime
from src.config import DATABASE_URL

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

    def get_similar_past_events(self, query_text: str, query_embedding: Optional[List[float]] = None, limit: int = 3) -> List[Dict[str, Any]]:
        db = self.SessionLocal()
        try:
            is_postgres = DATABASE_URL.startswith("postgresql")
            results = []
            
            if is_postgres and query_embedding is not None:
                # PostgreSQL Vector Search query
                vector_str = f"[{','.join(map(str, query_embedding))}]"
                sql = text("""
                    SELECT id, title, summary, source, link, published_at, sentiment_score,
                           (embedding <=> :vector) AS distance
                    FROM news_events
                    WHERE (embedding <=> :vector) < 0.35
                    ORDER BY distance ASC
                    LIMIT :limit
                """)
                rows = db.execute(sql, {"vector": vector_str, "limit": limit}).fetchall()
                for row in rows:
                    results.append({
                        "id": row.id,
                        "title": row.title,
                        "summary": row.summary,
                        "source": row.source,
                        "link": row.link,
                        "published_at": row.published_at.isoformat() if row.published_at else None,
                        "sentiment_score": float(row.sentiment_score or 0.0),
                        "distance": float(row.distance)
                    })
            else:
                # SQLite fallback: keyword text search
                search_filter = f"%{query_text}%"
                events = db.query(NewsEvent).filter(
                    (NewsEvent.title.ilike(search_filter)) | (NewsEvent.summary.ilike(search_filter))
                ).order_by(NewsEvent.published_at.desc()).limit(limit).all()
                
                for ev in events:
                    results.append({
                        "id": ev.id,
                        "title": ev.title,
                        "summary": ev.summary,
                        "source": ev.source,
                        "link": ev.link,
                        "published_at": ev.published_at.isoformat() if ev.published_at else None,
                        "sentiment_score": float(ev.sentiment_score or 0.0),
                        "distance": 0.0 # dummy distance
                    })
            return results
        except Exception as e:
            print(f"Error querying database for similar events: {e}")
            return []
        finally:
            db.close()

db_client = DatabaseClient()
