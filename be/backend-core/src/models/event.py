from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base
from src.config import settings
import datetime

# Handle pgvector conditional import depending on database engine
is_sqlite = settings.DATABASE_URL.startswith("sqlite")
if is_sqlite:
    # Use standard Text column in SQLite
    EmbeddingType = Text
else:
    from pgvector.sqlalchemy import Vector
    EmbeddingType = Vector(1536)

class NewsEvent(Base):
    __tablename__ = "news_events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    summary = Column(Text)
    source = Column(String(100))
    link = Column(Text, unique=True, index=True)
    published_at = Column(DateTime)
    sentiment_score = Column(Numeric(4, 2), default=0.0)
    embedding = Column(EmbeddingType)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    impacts = relationship("EventAssetImpact", back_populates="event", cascade="all, delete-orphan")

class EventAssetImpact(Base):
    __tablename__ = "event_asset_impacts"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("news_events.id", ondelete="CASCADE"), nullable=False)
    asset_ticker = Column(String(20), nullable=False)  # Maps to asset ticker (e.g. USO, AAPL, BTC-USD)
    impact_direction = Column(String(20), default="NEUTRAL")  # POSITIVE, NEGATIVE, NEUTRAL
    estimated_impact_factor = Column(Numeric(4, 2), default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    event = relationship("NewsEvent", back_populates="impacts")
