import json
import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from src.config import settings
from src.models.event import NewsEvent
from src.models.recommendation import Recommendation
from src.models.knowledge_graph import KnowledgeNode, KnowledgeEdge

# Try importing langchain_google_genai safely
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

def get_llm():
    if HAS_LANGCHAIN and settings.GEMINI_API_KEY:
        try:
            return ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-lite",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.1
            )
        except Exception as e:
            print(f"[Graph Ingestion] Failed to initialize Gemini LLM: {e}")
    return None

async def ingest_news_to_abstract_event(news: NewsEvent, db: Session):
    """
    Ingests a newly scraped news event, extracts abstract entities/relations,
    inserts/updates nodes, and links them to the abstract event class.
    """
    print(f"[Graph Ingestion] Processing news event into abstract graph: '{news.title[:55]}...'")
    llm = get_llm()
    extracted_data = None
    
    if llm:
        prompt_system = (
            "You are a financial knowledge graph builder. Analyze the news event and extract: \n"
            "1. An generalized, abstract event class that this news belongs to (e.g., 'Rate Hike', 'Supply Chain Disruption', 'Energy Supply Shock', 'Geopolitical Conflict', 'Industrial Disaster'). Keep it general.\n"
            "2. A brief general description for this abstract class.\n"
            "3. Relationships between this abstract class and other entities (Assets, Sectors, or Indicators).\n"
            "You MUST reply ONLY with a JSON object, matching this format:\n"
            "{\n"
            "  \"abstract_event_class\": \"Name of Abstract Event Class\",\n"
            "  \"abstract_event_description\": \"Generalized explanation of this type of event.\",\n"
            "  \"relations\": [\n"
            "    {\n"
            "      \"target_name\": \"Name of related entity (e.g. BTC-USD, AAPL, Tech Sector, Oil Price, Inflation)\",\n"
            "      \"target_type\": \"ASSET\" | \"SECTOR\" | \"INDICATOR\",\n"
            "      \"relationship_type\": \"BOOSTS\" | \"DEPRESSES\" | \"INFLUENCES\",\n"
            "      \"strength\": 0.1 to 1.0,\n"
            "      \"description\": \"Why it affects the target\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )
        prompt_user = f"Title: {news.title}\nSummary: {news.summary}"
        
        try:
            res = await llm.ainvoke([
                ("system", prompt_system),
                ("user", prompt_user)
            ])
            text = res.content.strip()
            # Clean possible markdown wrap
            if text.startswith("```json"):
                text = text.split("```json")[1].split("```")[0].strip()
            elif text.startswith("```"):
                text = text.split("```")[1].split("```")[0].strip()
            extracted_data = json.loads(text)
        except Exception as e:
            print(f"[Graph Ingestion] LLM classification error: {e}. Falling back to rule-based parser.")
            
    # Fallback to rule-based matcher if LLM failed or not available
    if not extracted_data:
        extracted_data = fallback_classify_news(news)
        
    try:
        # 1. Fetch or create the Abstract Event Node
        class_name = extracted_data.get("abstract_event_class", "Market Event").strip()
        class_desc = extracted_data.get("abstract_event_description", "General market news catalyst").strip()
        
        abstract_node = db.query(KnowledgeNode).filter(
            KnowledgeNode.name == class_name,
            KnowledgeNode.entity_type == "ABSTRACT_EVENT"
        ).first()
        
        if not abstract_node:
            abstract_node = KnowledgeNode(
                name=class_name,
                entity_type="ABSTRACT_EVENT",
                description=class_desc
            )
            db.add(abstract_node)
            db.commit()
            db.refresh(abstract_node)
            print(f"[Graph Ingestion] Created new Abstract Node: '{class_name}'")
            
        # 2. Store the specific News Article Event as a Node and link as INSTANCE_OF
        article_name = f"Event: {news.title[:80]}"
        article_node = db.query(KnowledgeNode).filter(KnowledgeNode.name == article_name).first()
        if not article_node:
            article_node = KnowledgeNode(
                name=article_name,
                entity_type="EVENT",
                description=news.summary or news.title
            )
            db.add(article_node)
            db.commit()
            db.refresh(article_node)
            
            # Create instance edge
            instance_edge = KnowledgeEdge(
                source_node_id=article_node.id,
                target_node_id=abstract_node.id,
                relationship_type="INSTANCE_OF",
                strength=Decimal("1.00"),
                historical_base_weight=Decimal("1.00"),
                description=f"Specific instance published by {news.source}"
            )
            db.add(instance_edge)
            db.commit()
            
        # 3. Create or update dynamic multi-relation edges
        for rel in extracted_data.get("relations", []):
            target_name = rel.get("target_name", "").strip()
            target_type = rel.get("target_type", "ASSET").strip().upper()
            rel_type = rel.get("relationship_type", "INFLUENCES").strip().upper()
            strength_val = float(rel.get("strength", 0.50))
            rel_desc = rel.get("description", "Dynamic market correlation").strip()
            
            # Retrieve or create target node
            target_node = db.query(KnowledgeNode).filter(KnowledgeNode.name == target_name).first()
            if not target_node:
                target_node = KnowledgeNode(
                    name=target_name,
                    entity_type=target_type,
                    description=f"Automated node for {target_name}"
                )
                db.add(target_node)
                db.commit()
                db.refresh(target_node)
                
            # Check for existing specific relationship type edge (multirelation support)
            edge = db.query(KnowledgeEdge).filter(
                KnowledgeEdge.source_node_id == abstract_node.id,
                KnowledgeEdge.target_node_id == target_node.id,
                KnowledgeEdge.relationship_type == rel_type
            ).first()
            
            if edge:
                # Update strength via EMA
                old_w = float(edge.strength)
                new_w = (1.0 - 0.30) * old_w + 0.30 * strength_val
                edge.strength = Decimal(str(round(new_w, 2)))
                edge.description = f"{rel_desc} (Updated: {datetime.datetime.utcnow().strftime('%Y-%m-%d')})"
                print(f"[Graph Ingestion] Updated Edge {class_name} --({rel_type})--> {target_name} to strength {new_w:.2f}")
            else:
                # Create a fresh multi-relation edge
                edge = KnowledgeEdge(
                    source_node_id=abstract_node.id,
                    target_node_id=target_node.id,
                    relationship_type=rel_type,
                    strength=Decimal(str(round(strength_val, 2))),
                    historical_base_weight=Decimal(str(round(strength_val, 2))),
                    description=rel_desc
                )
                db.add(edge)
                print(f"[Graph Ingestion] Created Edge {class_name} --({rel_type})--> {target_name} (strength {strength_val})")
                
            db.commit()
            
    except Exception as db_err:
        db.rollback()
        print(f"[Graph Ingestion] Database error in ingestion: {db_err}")

def fallback_classify_news(news: NewsEvent) -> dict:
    """
    Fallback regex/keyword rules to classify news events when Gemini key is not set.
    """
    title_upper = news.title.upper()
    summary_upper = (news.summary or "").upper()
    combined = title_upper + " " + summary_upper
    
    # Defaults
    class_name = "Macroeconomic Catalyst"
    class_desc = "Broader market news event triggering sentiment swings."
    relations = []
    
    if "FED" in combined or "FEDERAL RESERVE" in combined or "RATE" in combined or "INFLATION" in combined:
        class_name = "Monetary Policy Action"
        class_desc = "Central bank updates on interest rates, monetary policy, and macroeconomic trends."
        relations = [
            {"target_name": "Inflation", "target_type": "INDICATOR", "relationship_type": "INFLUENCES", "strength": 0.85, "description": "Monetary policy adjustments directly target inflation levels."},
            {"target_name": "^GSPC", "target_type": "INDEX", "relationship_type": "INFLUENCES", "strength": 0.70, "description": "Rate choices alter valuation models for major index equities."},
            {"target_name": "BTC-USD", "target_type": "ASSET", "relationship_type": "INFLUENCES", "strength": 0.75, "description": "Liquidity cycles alter high-beta cryptocurrency valuations."}
        ]
    elif "OIL" in combined or "OPEC" in combined or "SPILL" in combined or "ENERGY" in combined:
        class_name = "Energy Supply Shock"
        class_desc = "Production cuts, environmental incidents, or extraction updates impacting oil supplies."
        relations = [
            {"target_name": "Oil Price", "target_type": "INDICATOR", "relationship_type": "BOOSTS" if "CUT" in combined or "SPILL" in combined else "DEPRESSES", "strength": 0.90, "description": "Supply chain disruptions decrease raw crude supply."},
            {"target_name": "TSLA", "target_type": "ASSET", "relationship_type": "INFLUENCES", "strength": 0.40, "description": "Alternative energy adoption rates speed up as crude costs rise."}
        ]
    elif "TECH" in combined or "CHIP" in combined or "SEMICONDUCTOR" in combined or "AI" in combined:
        class_name = "Tech Sector Innovation"
        class_desc = "Innovations, chip shortages, or breakthroughs in the technology sector."
        relations = [
            {"target_name": "Tech Sector", "target_type": "SECTOR", "relationship_type": "BOOSTS", "strength": 0.80, "description": "Innovation cycles boost tech valuation multiples."},
            {"target_name": "AAPL", "target_type": "ASSET", "relationship_type": "INFLUENCES", "strength": 0.75, "description": "Apple relies on hardware innovation to drive customer growth."}
        ]
        
    return {
        "abstract_event_class": class_name,
        "abstract_event_description": class_desc,
        "relations": relations
    }

def update_relations_from_prediction_outcome(recommendation: Recommendation, db: Session):
    """
    Cumulative learning: matches closed trade results to related edges in the database.
    Increases strength for correct forecast assumptions and decreases strength for incorrect ones.
    """
    ticker = recommendation.ticker.upper()
    status = recommendation.status.upper()
    if status != "CLOSED":
        return
        
    ret = float(recommendation.realized_return or 0.0)
    rec_type = recommendation.recommendation_type.upper()
    
    # Determine if it was a correct prediction (profitable trade suggestion)
    is_success = ret > 0.0
    
    print(f"[Knowledge Feedback] Closing feedback loop for {ticker} recommendation {recommendation.id}. Outcome success: {is_success}")
    
    try:
        # Find the asset's knowledge node ID
        asset_node = db.query(KnowledgeNode).filter(KnowledgeNode.name == ticker).first()
        if not asset_node:
            return
            
        # Locate edges targeting this asset node
        edges = db.query(KnowledgeEdge).filter(KnowledgeEdge.target_node_id == asset_node.id).all()
        for edge in edges:
            source = edge.source_node
            # We only adjust abstract event relations (the core engine memory)
            if source and source.entity_type == "ABSTRACT_EVENT":
                rel_type = edge.relationship_type
                old_strength = float(edge.strength)
                new_strength = old_strength
                
                # Rule logic:
                if rec_type == "BUY":
                    if is_success:
                        # Success validates a BOOSTS edge or contradicts a DEPRESSES edge
                        if rel_type == "BOOSTS":
                            new_strength = min(1.0, old_strength + 0.08)
                        elif rel_type == "DEPRESSES":
                            new_strength = max(0.0, old_strength - 0.08)
                    else:
                        # Failure contradicts a BOOSTS edge or validates a DEPRESSES edge
                        if rel_type == "BOOSTS":
                            new_strength = max(0.0, old_strength - 0.08)
                        elif rel_type == "DEPRESSES":
                            new_strength = min(1.0, old_strength + 0.04)
                elif rec_type == "SELL":
                    if is_success:
                        # Success validates a DEPRESSES edge or contradicts a BOOSTS edge
                        if rel_type == "DEPRESSES":
                            new_strength = min(1.0, old_strength + 0.08)
                        elif rel_type == "BOOSTS":
                            new_strength = max(0.0, old_strength - 0.08)
                    else:
                        # Failure contradicts a DEPRESSES edge or validates a BOOSTS edge
                        if rel_type == "DEPRESSES":
                            new_strength = max(0.0, old_strength - 0.08)
                        elif rel_type == "BOOSTS":
                            new_strength = min(1.0, old_strength + 0.04)
                            
                if new_strength != old_strength:
                    edge.strength = Decimal(str(round(new_strength, 2)))
                    print(f"[Knowledge Feedback] Loop adjusted '{source.name}' --({rel_type})--> {ticker} weight: {old_strength:.2f} -> {new_strength:.2f}")
                    
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Knowledge Feedback] Error propagating outcomes: {e}")

def decay_graph_edges(db: Session):
    """
    Decays temporary news-driven edge weights back toward their historical base weight priors.
    """
    print("[Knowledge Graph] Executing base-weight decay cycle...")
    try:
        edges = db.query(KnowledgeEdge).all()
        for edge in edges:
            curr_str = float(edge.strength)
            base_str = float(edge.historical_base_weight)
            
            # Settle 5% closer to base prior
            new_str = curr_str - 0.05 * (curr_str - base_str)
            edge.strength = Decimal(str(round(new_str, 2)))
            
        db.commit()
        print(f"[Knowledge Graph] Settle cycle completed for {len(edges)} relations.")
    except Exception as e:
        db.rollback()
        print(f"[Knowledge Graph] Error in decay cycle: {e}")
