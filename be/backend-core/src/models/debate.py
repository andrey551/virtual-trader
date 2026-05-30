from sqlalchemy import Column, Integer, String, Text, DateTime
from src.database import Base
import datetime

class AgentDebate(Base):
    __tablename__ = "agent_debates"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), index=True, nullable=False)  # Session identifier
    ticker = Column(String(20), index=True)
    agent_name = Column(String(50), nullable=False)  # e.g. Technical Agent, Fundamental Agent
    avatar_code = Column(String(20))  # e.g. TECH_A, FUND_A
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
