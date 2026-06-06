from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from src.database import Base
import datetime

class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # ASSET, SECTOR, INDICATOR, ABSTRACT_EVENT
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"
    
    id = Column(Integer, primary_key=True, index=True)
    source_node_id = Column(Integer, ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id = Column(Integer, ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String(50), nullable=False)  # e.g., MONITORS, IN_SECTOR, SUPPLIES, DEPRESSES, BOOSTS, INFLUENCES
    strength = Column(Numeric(4, 2), default=0.50)
    historical_base_weight = Column(Numeric(4, 2), default=0.50)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Establish distinct relationships back to KnowledgeNode
    source_node = relationship("KnowledgeNode", foreign_keys=[source_node_id], backref="outgoing_edges")
    target_node = relationship("KnowledgeNode", foreign_keys=[target_node_id], backref="incoming_edges")
    
    # Enable multigraph: multiple relations between same pair of nodes are allowed
    __table_args__ = (
        UniqueConstraint("source_node_id", "target_node_id", "relationship_type", name="uq_source_target_rel"),
    )
