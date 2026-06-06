import json
import sys
from langgraph.graph import StateGraph, END
from src.state import SwarmState, AgentOpinion, DebateMessage
from src.personas import AGENT_PERSONAS
from src.agents import (
    stream_agent_speech,
    stream_structured_agent_speech,
    AnalystOutput,
    RiskManagerOutput,
    ModeratorOutput,
    GEMINI_API_KEY,
    should_awake_agent
)
from src.database_client import db_client
from src.mock_debate import run_mock_debate

def retrieve_analogy_node(state: SwarmState) -> dict:
    """
    Retrieves similar historical events from pgvector or SQLite fallback,
    calculates live technical indicators, and walks the Knowledge Graph within 2-hops.
    """
    ticker = state["ticker"]
    category = state["category"]
    price = state["current_price"]
    print(f"[Node: RetrieveAnalogy] Querying historical events & Knowledge Graph paths for {ticker} ({category})...")
    
    # Query matching keywords
    query_text = "lãi suất" if category == "FOREX" else ("oil" if ticker in ["USO", "CL=F"] else ticker)
    past_events = db_client.get_similar_past_events(
        query_text=query_text, 
        limit=3, 
        ticker=ticker, 
        current_price=price
    )
    
    # Walk the Knowledge Graph
    paths = db_client.get_related_knowledge_paths(ticker)
    
    # Calculate live technical indicators
    indicators = db_client.calculate_technical_indicators(ticker)
    
    return {
        "similar_historical_events": past_events,
        "knowledge_graph_paths": paths,
        "market_indicators": indicators
    }


def specialist_analysis_node(state: SwarmState) -> dict:
    """
    Executes independent rounds of specialist analysis (Round 1) using structured output.
    """
    ticker = state["ticker"]
    category = state["category"]
    price = state["current_price"]
    events_str = json.dumps(state.get("similar_historical_events", []), ensure_ascii=False, indent=2)
    kg_paths = state.get("knowledge_graph_paths", [])
    kg_paths_str = "\n".join(kg_paths) if kg_paths else "- No explicit baseline relations mapped."
    
    # Format computed technical indicators
    indicators = state.get("market_indicators", {})
    if indicators and indicators.get("status") == "SUCCESS":
        indicators_str = (
            f"- Current Price: {indicators['price']}\n"
            f"- 24h Change Percent: {indicators['change_percent']}%\n"
            f"- RSI (14-period): {indicators['rsi']} (Interpretation: {'Oversold' if indicators['rsi'] < 30 else 'Overbought' if indicators['rsi'] > 70 else 'Neutral'})\n"
            f"- MACD: Line={indicators['macd_line']}, Signal={indicators['macd_signal']}, Histogram={indicators['macd_hist']} ({indicators['macd_verdict']})\n"
            f"- 50-day SMA: {indicators['sma_50']} ({indicators['sma_50_verdict']})\n"
            f"- 24h Trading Volume: {indicators['volume_24h']:,} (vs 50-day average: {indicators['volume_avg_50d']:,}, Surge Ratio: {indicators['volume_surge_ratio']}x)"
        )
    else:
        indicators_str = "- No live technical indicators telemetry available (using default fallbacks)."

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
            
        should_awake, skip_reason = should_awake_agent(code, category, state.get("similar_historical_events", []))
        if not should_awake:
            persona = AGENT_PERSONAS[code]
            print(json.dumps({
                "agent_name": persona["name"],
                "avatar_code": persona["avatar_code"],
                "message": f"[{persona['name']} did not join the debate: {skip_reason}]",
                "status": "COMPLETED"
            }))
            sys.stdout.flush()
            continue
            
        persona = AGENT_PERSONAS[code]
        prompt_system = f"System Instruction: {persona['prompt']} Your name is {persona['name']}."
        
        prompt_user = f"""
        Asset: {ticker}
        Category: {category}
        Current Price: {price}
        
        Live Technical Indicators & Market Telemetry:
        {indicators_str}
        
        Knowledge Graph Pathways (Priors & Dependencies):
        {kg_paths_str}
        
        Similar Past Events (Context):
        {events_str}
        
        Based on your specialist persona, computed indicators, and the semantic connections above, evaluate the current price and market environment. Propose your verdict and confidence rating.
        """
        
        # Enforce structured output using stream_structured_agent_speech
        structured_out = stream_structured_agent_speech(code, prompt_system, prompt_user, AnalystOutput)
        
        opinions[code] = AgentOpinion(
            agent_name=persona["name"],
            verdict=structured_out.verdict,
            confidence=structured_out.confidence,
            rationale=structured_out.analysis,
            key_argument=structured_out.key_argument,
            indicators_audited=[category, "News Match", "Structured Technical Indicators"]
        )
        
    return {"opinions": opinions}

def swarm_debate_node(state: SwarmState) -> dict:
    """
    Executes a round of cross-criticism and debate (Round 2) using structured output and state reduction.
    """
    ticker = state["ticker"]
    category = state["category"]
    price = state["current_price"]
    
    # State Reduction: format condensed summaries of Round 1 opinions to save tokens
    opinions_str = ""
    for code, op in state["opinions"].items():
        opinions_str += f"- {op.agent_name}: {op.verdict} ({op.confidence}% confidence) - Key Argument: {op.key_argument}\n"
        
    # Format computed technical indicators to maintain context in Round 2
    indicators = state.get("market_indicators", {})
    if indicators and indicators.get("status") == "SUCCESS":
        indicators_str = (
            f"- Current Price: {indicators['price']}\n"
            f"- 24h Change Percent: {indicators['change_percent']}%\n"
            f"- RSI (14-period): {indicators['rsi']}\n"
            f"- MACD: Line={indicators['macd_line']}, Signal={indicators['macd_signal']}, Histogram={indicators['macd_hist']} ({indicators['macd_verdict']})\n"
            f"- 50-day SMA: {indicators['sma_50']} ({indicators['sma_50_verdict']})\n"
            f"- Volume: {indicators['volume_24h']:,} (vs 50-day average: {indicators['volume_avg_50d']:,})"
        )
    else:
        indicators_str = "- No live indicators telemetry."
        
    debate_history = []
    
    # Let 3 core specialists argue (Technical, Fundamental/Macro, and Sentiment)
    debaters = ["TECH_A", "SENT_A"]
    if category.upper() == "CRYPTO":
        debaters.append("CRYPTO_A")
    else:
        debaters.append("MACRO_A")
        
    # Only allow agents who have entered an opinion in Round 1
    debaters = [d for d in debaters if d in state["opinions"]]
    
    for code in debaters:
        persona = AGENT_PERSONAS[code]
        prompt_system = (
            f"System Instruction: {persona['prompt']} "
            "You are entering Round 2 of the Swarm Debate. You must critique, agree, or disagree with the opinions of the other agents converse-style. "
            "Do NOT simply rephrase or repeat your own analysis or arguments from Round 1. Focus on addressing disagreements, key arguments, or limitations raised by other agents. "
            "Reference other agents by name (e.g. 'Technical Analyst'). Keep it concise and debate-focused."
        )
        
        prompt_user = f"""
        Asset: {ticker}
        Category: {category}
        Current Price: {price}
        
        Live Technical Indicators:
        {indicators_str}
        
        All Specialist Opinions from Round 1 (Summary List):
        {opinions_str}
        
        Write your debate entry responding to these opinions. Direct your comments to specific agents if you disagree or want to reinforce their points.
        """
        
        structured_out = stream_structured_agent_speech(code, prompt_system, prompt_user, AnalystOutput)
        
        debate_history.append(DebateMessage(
            agent_name=persona["name"],
            avatar_code=persona["avatar_code"],
            message=structured_out.counter_arguments or structured_out.analysis
        ))
        
    return {"debate_history": debate_history}

def risk_assessment_node(state: SwarmState) -> dict:
    """
    Invokes the Risk Manager to audit consensus and recommend safe SL / TP levels using structured output.
    """
    ticker = state["ticker"]
    price = state["current_price"]
    
    # State Reduction: format condensed summaries of Round 1 opinions to save tokens
    opinions_str = ""
    for code, op in state["opinions"].items():
        opinions_str += f"- {op.agent_name}: {op.verdict} ({op.confidence}% confidence) - Key Argument: {op.key_argument}\n"
        
    # Format computed technical indicators to maintain context
    indicators = state.get("market_indicators", {})
    if indicators and indicators.get("status") == "SUCCESS":
        indicators_str = (
            f"- Current Price: {indicators['price']}\n"
            f"- 24h Change Percent: {indicators['change_percent']}%\n"
            f"- RSI (14-period): {indicators['rsi']}\n"
            f"- MACD: Line={indicators['macd_line']}, Signal={indicators['macd_signal']}, Histogram={indicators['macd_hist']} ({indicators['macd_verdict']})\n"
            f"- 50-day SMA: {indicators['sma_50']} ({indicators['sma_50_verdict']})\n"
            f"- Volume: {indicators['volume_24h']:,} (vs 50-day average: {indicators['volume_avg_50d']:,})"
        )
    else:
        indicators_str = "- No live indicators telemetry."
        
    code = "RISK_M"
    persona = AGENT_PERSONAS[code]
    
    prompt_system = f"System Instruction: {persona['prompt']}"
    prompt_user = f"""
    Asset: {ticker}
    Current Price: {price}
    
    Live Technical Indicators:
    {indicators_str}
    
    Specialist Opinions (Summary List):
    {opinions_str}
    
    Provide your risk audit, calculating the Entry zone range, Target Profit (TP), and Stop Loss (SL) boundaries. Return the risk profile clearly as structured output.
    """
    
    structured_out = stream_structured_agent_speech(code, prompt_system, prompt_user, RiskManagerOutput)
    
    risk_profile = {
        "entry": structured_out.entry_zone_max,
        "entry_range": f"{structured_out.entry_zone_min:.2f} - {structured_out.entry_zone_max:.2f}",
        "target": structured_out.target_price,
        "stop_loss": structured_out.stop_loss,
        "risk_verdict": structured_out.risk_verdict,
        "rationale": structured_out.risk_analysis
    }
    
    return {"risk_profile": risk_profile}

def consensus_moderator_node(state: SwarmState) -> dict:
    """
    Invokes the Swarm Moderator (Gemini 1.5 Pro) to synthesize the debate
    and output the final Verdict and confidence rating using structured output.
    """
    ticker = state["ticker"]
    price = state["current_price"]
    
    # State Reduction: format condensed summaries of Round 1 opinions to save tokens
    opinions_str = ""
    for code, op in state["opinions"].items():
        opinions_str += f"- {op.agent_name}: {op.verdict} ({op.confidence}% confidence) - Key Argument: {op.key_argument}\n"
        
    # Format computed technical indicators to maintain context
    indicators = state.get("market_indicators", {})
    if indicators and indicators.get("status") == "SUCCESS":
        indicators_str = (
            f"- Current Price: {indicators['price']}\n"
            f"- 24h Change Percent: {indicators['change_percent']}%\n"
            f"- RSI (14-period): {indicators['rsi']}\n"
            f"- MACD: Line={indicators['macd_line']}, Signal={indicators['macd_signal']}, Histogram={indicators['macd_hist']} ({indicators['macd_verdict']})\n"
            f"- 50-day SMA: {indicators['sma_50']} ({indicators['sma_50_verdict']})\n"
            f"- Volume: {indicators['volume_24h']:,} (vs 50-day average: {indicators['volume_avg_50d']:,})"
        )
    else:
        indicators_str = "- No live indicators telemetry."
        
    debate_str = json.dumps([d.dict() for d in state["debate_history"]], ensure_ascii=False)
    risk_str = json.dumps(state["risk_profile"], ensure_ascii=False)
    kg_paths = state.get("knowledge_graph_paths", [])
    kg_paths_str = "\n".join(kg_paths) if kg_paths else "- No baseline relations."
    
    code = "MOD_O"
    persona = AGENT_PERSONAS[code]
    
    prompt_system = f"System Instruction: {persona['prompt']}"
    
    prompt_user = f"""
    Ticker: {ticker}
    Current Price: {price}
    
    Live Technical Indicators:
    {indicators_str}
    
    Knowledge Graph Paths (Priors & Sector Relationships):
    {kg_paths_str}
    
    Round 1 Opinions (Summary List):
    {opinions_str}
    
    Round 2 Debate:
    {debate_str}
    
    Risk Assessment:
    {risk_str}
    
    Synthesize all arguments. Give a final unified recommendation verdict (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL) and a confidence percentage (0.0 to 100.0) as structured output.
    """
    
    structured_out = stream_structured_agent_speech(code, prompt_system, prompt_user, ModeratorOutput)
    
    return {
        "consensus_verdict": structured_out.consensus_verdict,
        "consensus_confidence": structured_out.consensus_confidence
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
