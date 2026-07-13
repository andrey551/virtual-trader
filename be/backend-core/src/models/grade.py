from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from src.database import Base
import datetime

class PredictionGrade(Base):
    __tablename__ = "prediction_grades"
    
    id = Column(Integer, primary_key=True, index=True)
    prediction_cache_id = Column(Integer, ForeignKey("prediction_cache.id"), unique=True, nullable=False)
    ticker = Column(String(20), index=True, nullable=False)
    
    # MAPE errors (%)
    mape_5s = Column(Float, nullable=True)
    mape_5m = Column(Float, nullable=True)
    mape_5h = Column(Float, nullable=True)
    mape_5d = Column(Float, nullable=True)
    
    # Trend Accuracy (0-100%)
    trend_acc_5s = Column(Float, nullable=True)
    trend_acc_5m = Column(Float, nullable=True)
    trend_acc_5h = Column(Float, nullable=True)
    trend_acc_5d = Column(Float, nullable=True)
    
    graded_at = Column(DateTime, default=datetime.datetime.utcnow)

class DailyAssetScore(Base):
    __tablename__ = "daily_asset_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    
    avg_mape_5d = Column(Float, nullable=True)
    avg_trend_acc_5d = Column(Float, nullable=True)
    total_predictions_evaluated = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
