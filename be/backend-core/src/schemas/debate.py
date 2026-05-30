from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AgentDebateBase(BaseModel):
    session_id: str
    ticker: Optional[str] = None
    agent_name: str
    avatar_code: Optional[str] = None
    message: str

class AgentDebateCreate(AgentDebateBase):
    pass

class AgentDebateRead(AgentDebateBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
