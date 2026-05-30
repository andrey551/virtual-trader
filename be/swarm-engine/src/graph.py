import json
from langgraph.graph import StateGraph, END
from src.state import SwarmState, AgentOpinion, DebateMessage
from src.personas import AGENT_PERSONAS
from src.agents import stream_agent_speech, GEMINI_API_KEY
from src.database_client import db_client
from src.mock_debate import run_mock_debate

def retrieve_analogy_node(state: SwarmState) -> dict:
    """
    Retrieves similar historical events from pgvector or SQLite fallback
    based on the current asset category or vĩ mô topics.
    """
    ticker = state["ticker"]
    category = state["category"]
    print(f"[Node: RetrieveAnalogy] Querying historical events correlating with {ticker} ({category})...")
    
    # Query matching keywords
    query_text = "lãi suất" if category == "FOREX" else ("oil" if ticker in ["USO", "CL=F"] else ticker)
    past_events = db_client.get_similar_past_events(query_text=query_text, limit=3)
    
    return {"similar_historical_events": past_events}

def specialist_analysis_node(state: SwarmState) -> dict:
    """
    Executes independent rounds of specialist analysis (Round 1)
    """
    ticker = state["ticker"]
    category = state["category"]
    price = state["current_price"]
    events_str = json.dumps(state.get("similar_historical_events", []), ensure_ascii=False, indent=2)
    
    opinions = {}
    
    # Select active specialist codes based on asset category
    active_codes = ["TECH_A", "FUND_A", "MACRO_A", "GEOPOL_A", "SENT_A", "RISK_M"]
    if category.upper() == "CRYPTO":
        active_codes.append("CRYPTO_A")
    elif category.upper() == "FOREX":
        active_codes.append("FOREX_A")
    elif category.upper() == "COMMODITY":
        active_codes.append("COMM_A")
        
    for code in active_codes:
        if code == "RISK_M":
            # Risk manager speaks in a later node
            continue
            
        persona = AGENT_PERSONAS[code]
        prompt_system = f"System Instruction: {persona['prompt']} Your name is {persona['name']}. Always express a verdict (BUY, SELL, or HOLD), confidence level (0 to 100) and rationale."
        
        prompt_user = f"""
        Asset: {ticker}
        Category: {category}
        Current Price: {price}
        
        Similar Past Events (Context):
        {events_str}
        
        Based on your specialist persona, evaluate the current price and market environment. Propose your verdict and confidence rating.
        """
        
        speech = stream_agent_speech(code, prompt_system, prompt_user)
        
        # Simple parser to extract verdict & confidence from LLM output
        verdict = "HOLD"
        if "STRONG BUY" in speech.upper() or "STRONG_BUY" in speech.upper():
            verdict = "STRONG_BUY"
        elif "BUY" in speech.upper():
            verdict = "BUY"
        elif "STRONG SELL" in speech.upper() or "STRONG_SELL" in speech.upper():
            verdict = "STRONG_SELL"
        elif "SELL" in speech.upper():
            verdict = "SELL"
            
        confidence = 50.0
        for word in speech.split():
            if "%" in word:
                try:
                    val = float(word.replace("%", "").replace("(", "").replace(")", "").strip())
                    if 0 < val <= 100:
                        confidence = val
                        break
                except ValueError:
                    pass
                    
        opinions[code] = AgentOpinion(
            agent_name=persona["name"],
            verdict=verdict,
            confidence=confidence,
            rationale=speech[:500],  # store summary
            indicators_audited=[category, "News Match"]
        )
        
    return {"opinions": opinions}

def swarm_debate_node(state: SwarmState) -> dict:
    """
    Executes a round of cross-criticism and debate (Round 2)
    """
    ticker = state["ticker"]
    opinions_str = ""
    for code, op in state["opinions"].items():
        opinions_str += f"- {op.agent_name} Verdict: {op.verdict} (Confidence: {op.confidence}%). Rationale: {op.rationale}\n"
        
    debate_history = []
    
    # Let 3 core specialists argue (Technical, Fundamental/Macro, and Sentiment)
    debaters = ["TECH_A", "SENT_A"]
    if state["category"].upper() == "CRYPTO":
        debaters.append("CRYPTO_A")
    else:
        debaters.append("MACRO_A")
        
    for code in debaters:
        persona = AGENT_PERSONAS[code]
        prompt_system = f"System Instruction: {persona['prompt']} You are entering Round 2 of the Swarm Debate. You must critique, agree, or disagree with the opinions of the other agents. Be conversational and references other agents by name."
        
        prompt_user = f"""
        All Specialist Opinions from Round 1:
        {opinions_str}
        
        Write your debate entry responding to these opinions. Direct your comments to specific agents if you disagree or want to reinforce their points.
        """
        
        speech = stream_agent_speech(code, prompt_system, prompt_user)
        debate_history.append(DebateMessage(
            agent_name=persona["name"],
            avatar_code=persona["avatar_code"],
            message=speech
        ))
        
    return {"debate_history": debate_history}

def risk_assessment_node(state: SwarmState) -> dict:
    """
    Invokes the Risk Manager to audit consensus and recommend safe SL / TP levels
    """
    ticker = state["ticker"]
    price = state["current_price"]
    opinions_str = json.dumps([op.dict() for op in state["opinions"].values()], ensure_ascii=False)
    
    code = "RISK_M"
    persona = AGENT_PERSONAS[code]
    
    prompt_system = f"System Instruction: {persona['prompt']}"
    prompt_user = f"""
    Asset: {ticker}
    Current Price: {price}
    Specialist Opinions: {opinions_str}
    
    Provide your risk audit, calculating the Entry zone, Target Profit (TP), and Stop Loss (SL) boundaries. Return the risk profile clearly.
    """
    
    speech = stream_agent_speech(code, prompt_system, prompt_user)
    
    # Mock bounds from speech or fallback math
    risk_profile = {
        "entry": price * 0.99,
        "target": price * 1.12,
        "stop_loss": price * 0.94,
        "rationale": speech[:300]
    }
    
    return {"risk_profile": risk_profile}

def consensus_moderator_node(state: SwarmState) -> dict:
    """
    Invokes the Swarm Moderator (Gemini 1.5 Pro) to synthesize the debate
    and output the final Verdict and confidence rating.
    """
    ticker = state["ticker"]
    opinions_str = json.dumps([op.dict() for op in state["opinions"].values()], ensure_ascii=False)
    debate_str = json.dumps([d.dict() for d in state["debate_history"]], ensure_ascii=False)
    risk_str = json.dumps(state["risk_profile"], ensure_ascii=False)
    
    code = "MOD_O"
    persona = AGENT_PERSONAS[code]
    
    prompt_system = f"System Instruction: {persona['prompt']} Your output must contain a final summary of the swarm consensus, a final recommendation score (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL), and a final confidence score (0 to 100)."
    
    prompt_user = f"""
    Ticker: {ticker}
    Round 1 Opinions: {opinions_str}
    Round 2 Debate: {debate_str}
    Risk Assessment: {risk_str}
    
    Synthesize all arguments. Give a final unified recommendation verdict (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL) and a confidence percentage (0 to 100).
    """
    
    speech = stream_agent_speech(code, prompt_system, prompt_user)
    
    verdict = "HOLD"
    if "STRONG_BUY" in speech or "STRONG BUY" in speech.upper():
        verdict = "STRONG_BUY"
    elif "BUY" in speech.upper():
        verdict = "BUY"
    elif "STRONG_SELL" in speech or "STRONG SELL" in speech.upper():
        verdict = "STRONG_SELL"
    elif "SELL" in speech.upper():
        verdict = "SELL"
        
    confidence = 50.0
    for word in speech.split():
        if "%" in word:
            try:
                val = float(word.replace("%", "").replace("(", "").replace(")", "").strip())
                if 0 < val <= 100:
                    confidence = val
                    break
            except ValueError:
                pass
                
    return {
        "consensus_verdict": verdict,
        "consensus_confidence": confidence
    }

def create_swarm_graph() -> StateGraph:
    """
    Configures the LangGraph StateGraph mapping nodes and sequential edges.
    """
    workflow = StateGraph(SwarmState)
    
    # Add nodes
    workflow.add_node("retrieve_analogy", retrieve_analogy_node)
    workflow.add_node("specialist_analysis", specialist_analysis_node)
    workflow.add_node("swarm_debate", swarm_debate_node)
    workflow.add_node("risk_assessment", risk_assessment_node)
    workflow.add_node("consensus_moderator", consensus_moderator_node)
    
    # Configure sequential routing flow
    workflow.set_entry_point("retrieve_analogy")
    workflow.add_edge("retrieve_analogy", "specialist_analysis")
    workflow.add_edge("specialist_analysis", "swarm_debate")
    workflow.add_edge("swarm_debate", "risk_assessment")
    workflow.add_edge("risk_assessment", "consensus_moderator")
    workflow.add_edge("consensus_moderator", END)
    
    return workflow.compile()
