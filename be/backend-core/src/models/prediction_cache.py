from sqlalchemy import Column, Integer, String, Float, DateTime
from src.database import Base
import datetime

class PredictionCache(Base):
    __tablename__ = "prediction_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), index=True, nullable=False)
    session_id = Column(String(50), nullable=False) # Maps to AgentDebate session_id
    price_at_predict = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
