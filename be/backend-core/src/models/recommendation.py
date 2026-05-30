from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text
from src.database import Base
import datetime

class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), index=True, nullable=False)
    recommendation_type = Column(String(20), nullable=False)  # BUY, SELL, HOLD
    entry_price = Column(Numeric(12, 4), nullable=False)
    target_price = Column(Numeric(12, 4))
    stop_loss = Column(Numeric(12, 4))
    current_price = Column(Numeric(12, 4))
    system_rating = Column(Numeric(5, 2))  # Score e.g. 85.00
    status = Column(String(20), default="ACTIVE")  # ACTIVE, CLOSED
    realized_return = Column(Numeric(6, 2))  # Percentage e.g. 12.50
    verdict_reasoning = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
