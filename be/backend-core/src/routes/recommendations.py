from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.recommendation import Recommendation
from src.schemas.recommendation import RecommendationRead, RecommendationCreate
from typing import List, Optional
from decimal import Decimal
import datetime

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.get("", response_model=List[RecommendationRead])
def get_recommendations(
    ticker: Optional[str] = Query(None, description="Filter by ticker"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, CLOSED)"),
    db: Session = Depends(get_db)
):
    query = db.query(Recommendation)
    
    if ticker:
        query = query.filter(Recommendation.ticker == ticker.upper())
    if status:
        query = query.filter(Recommendation.status == status.upper())
        
    return query.order_by(Recommendation.created_at.desc()).all()

@router.post("", response_model=RecommendationRead)
def create_recommendation(rec_in: RecommendationCreate, db: Session = Depends(get_db)):
    db_rec = Recommendation(**rec_in.model_dump())
    db.add(db_rec)
    db.commit()
    db.refresh(db_rec)
    return db_rec
