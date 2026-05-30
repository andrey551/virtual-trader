from sqlalchemy import Column, Integer, String, Numeric, DateTime
from src.database import Base
import datetime

class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # STOCKS, CRYPTO, FOREX, INDEX
    accuracy_score = Column(Numeric(5, 2), default=0.0)
    alpha_outperformance = Column(Numeric(5, 2), default=0.0)
    system_verdict = Column(String(20), default="HOLD")  # BUY, STRONG_BUY, SELL, STRONG_SELL, HOLD
    confidence_level = Column(Numeric(5, 2), default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
