from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.knowledge_graph import KnowledgeNode, KnowledgeEdge
from src.services.graph_ingestion import decay_graph_edges
from typing import List, Dict, Any
from decimal import Decimal
import datetime

router = APIRouter(prefix="/knowledge-graph", tags=["Knowledge Graph"])

@router.get("/asset/{ticker}", response_model=Dict[str, Any])
def get_asset_knowledge_graph(ticker: str, db: Session = Depends(get_db)):
    """
    Traverses the multigraph to return related nodes and edges within 2-hops
    centered around the specified asset ticker.
    """
    ticker_upper = ticker.upper()
    asset_node = db.query(KnowledgeNode).filter(
        KnowledgeNode.name == ticker_upper,
        KnowledgeNode.entity_type == "ASSET"
    ).first()
    
    if not asset_node:
        # Check if asset exists, if not, create it to center the graph
        from src.models.asset import Asset
        db_asset = db.query(Asset).filter(Asset.ticker == ticker_upper).first()
        if db_asset:
            asset_node = KnowledgeNode(
                name=db_asset.ticker,
                entity_type="ASSET",
                description=db_asset.name
            )
            db.add(asset_node)
            db.commit()
            db.refresh(asset_node)
        else:
            return {"nodes": [], "edges": []}
            
    # Sets to track visited elements and avoid duplicate items in payload
    visited_node_ids = {asset_node.id}
    nodes_map = {asset_node.id: {
        "id": asset_node.id,
        "name": asset_node.name,
        "type": asset_node.entity_type,
        "description": asset_node.description
    }}
    edges_map = {} # key: edge_id
    
    # 1. First Hop traversal
    first_hop_edges = db.query(KnowledgeEdge).filter(
        (KnowledgeEdge.source_node_id == asset_node.id) | 
        (KnowledgeEdge.target_node_id == asset_node.id)
    ).all()
    
    first_hop_node_ids = set()
    for edge in first_hop_edges:
        edges_map[edge.id] = {
            "id": edge.id,
            "source": edge.source_node_id,
            "target": edge.target_node_id,
            "type": edge.relationship_type,
            "strength": float(edge.strength),
            "description": edge.description
        }
        
        # Capture the neighbor node id
        neighbor_id = edge.target_node_id if edge.source_node_id == asset_node.id else edge.source_node_id
        if neighbor_id not in visited_node_ids:
            visited_node_ids.add(neighbor_id)
            first_hop_node_ids.add(neighbor_id)
            neighbor_node = db.query(KnowledgeNode).filter(KnowledgeNode.id == neighbor_id).first()
            if neighbor_node:
                nodes_map[neighbor_id] = {
                    "id": neighbor_node.id,
                    "name": neighbor_node.name,
                    "type": neighbor_node.entity_type,
                    "description": neighbor_node.description
                }
                
    # 2. Second Hop traversal
    for node_id in first_hop_node_ids:
        second_hop_edges = db.query(KnowledgeEdge).filter(
            (KnowledgeEdge.source_node_id == node_id) | 
            (KnowledgeEdge.target_node_id == node_id)
        ).all()
        
        for edge in second_hop_edges:
            if edge.id not in edges_map:
                edges_map[edge.id] = {
                    "id": edge.id,
                    "source": edge.source_node_id,
                    "target": edge.target_node_id,
                    "type": edge.relationship_type,
                    "strength": float(edge.strength),
                    "description": edge.description
                }
                
            # Capture secondary neighbor
            neighbor_id = edge.target_node_id if edge.source_node_id == node_id else edge.source_node_id
            if neighbor_id not in visited_node_ids:
                visited_node_ids.add(neighbor_id)
                neighbor_node = db.query(KnowledgeNode).filter(KnowledgeNode.id == neighbor_id).first()
                if neighbor_node:
                    nodes_map[neighbor_id] = {
                        "id": neighbor_node.id,
                        "name": neighbor_node.name,
                        "type": neighbor_node.entity_type,
                        "description": neighbor_node.description
                    }
                    
    return {
        "nodes": list(nodes_map.values()),
        "edges": list(edges_map.values())
    }

@router.post("/clean")
def trigger_graph_decay(db: Session = Depends(get_db)):
    """
    Manually triggers relationship base weight settling and decay.
    """
    decay_graph_edges(db)
    return {"status": "success", "message": "Graph decay settling loop executed successfully."}

@router.post("/seed")
def seed_knowledge_graph(db: Session = Depends(get_db)):
    """
    Pre-populates baseline abstract concepts, sectors, suppliers, macro indicators
    and their multi-relation connections to demonstrate consensus reasoning.
    """
    # 1. Define nodes
    baseline_nodes = [
        # Assets (ensure nodes match asset table records)
        {"name": "AAPL", "entity_type": "ASSET", "description": "Apple Inc. Equity Stock Node"},
        {"name": "TSLA", "entity_type": "ASSET", "description": "Tesla Inc. Equity Stock Node"},
        {"name": "BTC-USD", "entity_type": "ASSET", "description": "Bitcoin Currency Crypto Node"},
        {"name": "ETH-USD", "entity_type": "ASSET", "description": "Ethereum Currency Crypto Node"},
        {"name": "SOL-USD", "entity_type": "ASSET", "description": "Solana Currency Crypto Node"},
        {"name": "EURUSD=X", "entity_type": "ASSET", "description": "EUR/USD Forex Exchange Pair Node"},
        {"name": "USO", "entity_type": "ASSET", "description": "United States Oil Fund ETF Node"},
        
        # Sectors
        {"name": "Tech Sector", "entity_type": "SECTOR", "description": "Global technology sector focusing on software and hardware."},
        {"name": "EV Sector", "entity_type": "SECTOR", "description": "Electric Vehicle manufacture, battery, and distribution markets."},
        {"name": "Crypto Market", "entity_type": "SECTOR", "description": "Decentralized digital currency and token markets."},
        {"name": "Forex Market", "entity_type": "SECTOR", "description": "Global currency exchange pairs network."},
        
        # Macro Indicators
        {"name": "Inflation", "entity_type": "INDICATOR", "description": "Consumer Price Index (CPI) showing baseline purchasing power erosion."},
        {"name": "Interest Rates", "entity_type": "INDICATOR", "description": "Central bank base borrowing rates."},
        {"name": "Oil Price", "entity_type": "INDICATOR", "description": "WTI and Brent Crude benchmarks raw pricing index."},
        
        # Partners / Suppliers
        {"name": "Taiwan Semiconductor", "entity_type": "ASSET", "description": "TSMC - major processor foundry supplying chips globally."},
        {"name": "Lithium Supply", "entity_type": "INDICATOR", "description": "Global raw lithium supply commodity index for batteries."},
        
        # Abstract Event Classes
        {"name": "Monetary Policy Action", "entity_type": "ABSTRACT_EVENT", "description": "Central bank monetary policy decisions and discount rate changes."},
        {"name": "Energy Supply Shock", "entity_type": "ABSTRACT_EVENT", "description": "Geopolitical friction or supply cuts impacting fuel resources."},
        {"name": "Supply Chain Disruption", "entity_type": "ABSTRACT_EVENT", "description": "Factory fires, logistics blockages, or chip packaging shortfalls."}
    ]
    
    nodes_created = 0
    node_id_map = {}
    
    for n in baseline_nodes:
        node = db.query(KnowledgeNode).filter(KnowledgeNode.name == n["name"]).first()
        if not node:
            node = KnowledgeNode(**n)
            db.add(node)
            db.commit()
            db.refresh(node)
            nodes_created += 1
        node_id_map[n["name"]] = node.id
        
    # 2. Define Multi-Relations
    baseline_edges = [
        # Sector relationships
        {"src": "AAPL", "tgt": "Tech Sector", "type": "IN_SECTOR", "w": 0.95, "desc": "Apple is a major driver of tech stock indices."},
        {"src": "TSLA", "tgt": "EV Sector", "type": "IN_SECTOR", "w": 0.90, "desc": "Tesla leads the electric vehicle manufacturer sector."},
        {"src": "BTC-USD", "tgt": "Crypto Market", "type": "IN_SECTOR", "w": 0.95, "desc": "Bitcoin represents over 50% of total crypto sector weight."},
        {"src": "ETH-USD", "tgt": "Crypto Market", "type": "IN_SECTOR", "w": 0.85, "desc": "Ethereum is the leading smart-contract platform in crypto."},
        {"src": "SOL-USD", "tgt": "Crypto Market", "type": "IN_SECTOR", "w": 0.75, "desc": "Solana is a high-speed L1 crypto asset."},
        {"src": "EURUSD=X", "tgt": "Forex Market", "type": "IN_SECTOR", "w": 0.90, "desc": "EUR/USD is the most traded fiat trading pair globally."},
        
        # Supply / Dependency relationships
        {"src": "Taiwan Semiconductor", "tgt": "AAPL", "type": "SUPPLIES", "w": 0.85, "desc": "TSMC manufactures Apple Silicon processors for iPhones & Macs."},
        {"src": "Taiwan Semiconductor", "tgt": "Tech Sector", "type": "SUPPLIES", "w": 0.90, "desc": "TSMC produces chips for all major hardware designers."},
        {"src": "Lithium Supply", "tgt": "EV Sector", "type": "SUPPLIES", "w": 0.80, "desc": "Lithium is the key component in EV batteries."},
        
        # Macro Indicators influences
        {"src": "Inflation", "tgt": "Interest Rates", "type": "INFLUENCES", "w": 0.85, "desc": "Rising inflation pressures central banks to raise interest rates."},
        {"src": "Interest Rates", "tgt": "Tech Sector", "type": "DEPRESSES", "w": 0.70, "desc": "Higher discount rates reduce the net present value of tech growth cashflows."},
        {"src": "Interest Rates", "tgt": "Crypto Market", "type": "DEPRESSES", "w": 0.75, "desc": "High yield rates draw capital away from risk assets like cryptocurrencies."},
        
        # Abstract Event relationships (multiple relations for deeper reasoning)
        {"src": "Monetary Policy Action", "tgt": "Interest Rates", "type": "INFLUENCES", "w": 0.95, "desc": "Monetary policy decisions directly modify interest rate policies."},
        {"src": "Monetary Policy Action", "tgt": "EURUSD=X", "type": "INFLUENCES", "w": 0.80, "desc": "Federal Reserve monetary actions influence global fiat currency pairs."},
        
        {"src": "Energy Supply Shock", "tgt": "Oil Price", "type": "BOOSTS", "w": 0.90, "desc": "Supply shocks decrease oil inventories, boosting raw barrel prices."},
        {"src": "Energy Supply Shock", "tgt": "USO", "type": "BOOSTS", "w": 0.85, "desc": "Higher crude prices translate to direct appreciation in USO ETF."},
        {"src": "Energy Supply Shock", "tgt": "EV Sector", "type": "BOOSTS", "w": 0.50, "desc": "Sustained high fuel prices speed up alternative EV adoption."},
        
        {"src": "Supply Chain Disruption", "tgt": "Tech Sector", "type": "DEPRESSES", "w": 0.80, "desc": "Supply chain bottlenecks delay tech product shipments and compress margins."},
        {"src": "Supply Chain Disruption", "tgt": "TSLA", "type": "DEPRESSES", "w": 0.70, "desc": "Tesla factories rely on precise parts shipping times."}
    ]
    
    edges_created = 0
    for e in baseline_edges:
        src_id = node_id_map.get(e["src"])
        tgt_id = node_id_map.get(e["tgt"])
        
        if src_id and tgt_id:
            edge = db.query(KnowledgeEdge).filter(
                KnowledgeEdge.source_node_id == src_id,
                KnowledgeEdge.target_node_id == tgt_id,
                KnowledgeEdge.relationship_type == e["type"]
            ).first()
            
            if not edge:
                edge = KnowledgeEdge(
                    source_node_id=src_id,
                    target_node_id=tgt_id,
                    relationship_type=e["type"],
                    strength=Decimal(str(e["w"])),
                    historical_base_weight=Decimal(str(e["w"])),
                    description=e["desc"]
                )
                db.add(edge)
                edges_created += 1
                
    db.commit()
    return {
        "status": "success",
        "nodes_created": nodes_created,
        "edges_created": edges_created,
        "total_nodes": db.query(KnowledgeNode).count(),
        "total_edges": db.query(KnowledgeEdge).count()
    }
